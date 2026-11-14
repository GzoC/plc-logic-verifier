"""Formal grammar, source-located AST and closed-world type checker."""

from dataclasses import dataclass, field
from typing import Any

from lark import Lark, Token, Tree, UnexpectedInput

MAX_SOURCE = 65536
GRAMMAR = r"""
start: "PROGRAM"i NAME declaration* statements "END_PROGRAM"i
declaration: SECTION decl+ "END_VAR"i
SECTION.3: /(?:VAR_INPUT|VAR_OUTPUT|VAR)\b/i
decl: names ":" TYPE [":=" expr] ";"
names: NAME ("," NAME)*
TYPE: /BOOL|INT|TIME|TON|R_TRIG/i
statements: statement*
?statement: assign | invoke | if_stmt | case_stmt
assign: NAME ":=" expr ";"
invoke: NAME "(" [argument ("," argument)*] ")" ";"
argument: NAME ":=" expr
if_stmt: "IF"i expr "THEN"i statements ("ELSIF"i expr "THEN"i statements)* ["ELSE"i statements] "END_IF"i ";"
case_stmt: "CASE"i expr "OF"i case_arm+ ["ELSE"i statements] "END_CASE"i ";"
case_arm: labels ":" statements
labels: SIGNED_INT ("," SIGNED_INT)*
?expr: or_expr
?or_expr: and_expr (OR and_expr)*
?and_expr: comparison (AND comparison)*
?comparison: sum (CMP sum)?
?sum: product (ADD product)*
?product: unary (MUL unary)*
?unary: UNARY unary -> unary
      | atom
?atom: TIME_LITERAL -> time
     | BOOL_LITERAL -> boolean
     | INT_LITERAL -> integer
     | NAME "." NAME -> member
     | NAME -> variable
     | "(" expr ")"
OR: /OR|XOR/i
AND: /AND/i
CMP: "<>" | "<=" | ">=" | "=" | "<" | ">"
ADD: "+" | "-"
MUL: "*" | "/" | /MOD/i
UNARY.3: /NOT\b/i | "-" | "+"
BOOL_LITERAL.3: /(?:TRUE|FALSE)\b/i
TIME_LITERAL.3: /(?:TIME|T)#(?:[0-9]+(?:ms|s|m|h))+/i
INT_LITERAL: /[0-9]+/
SIGNED_INT: /-?[0-9]+/
NAME: /[A-Za-z_][A-Za-z0-9_]*/
%import common.WS
%ignore WS
%ignore /\(\*(?s:.*?)\*\)/
%ignore /\/\/[^\n]*/
"""
PARSER = Lark(GRAMMAR, parser="lalr", start=["start", "expr"], propagate_positions=True,
              maybe_placeholders=False)


class VerificationError(Exception):
    def __init__(self, message: str, line: int = 1, column: int = 1, status: str = "ERROR"):
        super().__init__(f"{message} (line {line}, column {column})")
        self.line, self.column, self.status = line, column, status


@dataclass
class Node:
    kind: str
    args: list[Any] = field(default_factory=list)
    line: int = 1
    column: int = 1


@dataclass
class Symbol:
    name: str
    type: str
    section: str
    initial: Node | None
    line: int
    column: int


@dataclass
class Program:
    name: str
    symbols: dict[str, Symbol]
    body: Node
    source: str


def fail(message: str, node: Node, status: str = "ERROR") -> Any:
    raise VerificationError(message, node.line, node.column, status)


def ast(tree: Tree | Token) -> Any:
    if isinstance(tree, Token):
        return str(tree).upper()
    return Node(str(tree.data), [ast(c) for c in tree.children],
                getattr(tree.meta, "line", 1), getattr(tree.meta, "column", 1))


def parse_tree(source: str, start: str) -> Node:
    if len(source.encode("utf-8")) > MAX_SOURCE:
        raise VerificationError("Source exceeds 64 KiB")
    try:
        tree = PARSER.parse(source, start=start)
        pending = [(tree, 0)]
        count = 0
        while pending:
            item, depth = pending.pop()
            count += 1
            if count > 5000 or depth > 64:
                raise VerificationError("AST complexity limit exceeded")
            if isinstance(item, Tree):
                pending.extend((c, depth + 1) for c in item.children)
        return ast(tree)
    except UnexpectedInput as exc:
        raise VerificationError("Unsupported or malformed ST syntax", exc.line, exc.column,
                                "UNSUPPORTED") from exc
    except RecursionError as exc:
        raise VerificationError("Nesting limit exceeded") from exc


def time_ms(text: str) -> int:
    # Lexical splitting of a grammar-validated literal, not an interpreter.
    import re

    units = {"MS": 1, "S": 1000, "M": 60000, "H": 3600000}
    return sum(int(n) * units[u] for n, u in re.findall(r"(\d+)(MS|S|M|H)", text))


def expression_type(node: Node, symbols: dict[str, Symbol]) -> str:
    k, a = node.kind, node.args
    if k in {"integer", "boolean", "time"}:
        return {"integer": "INT", "boolean": "BOOL", "time": "TIME"}[k]
    if k in {"variable", "member"}:
        symbol = symbols.get(a[0])
        if symbol is None:
            fail(f"Undeclared variable {a[0]}", node)
        assert symbol is not None
        if k == "variable":
            if symbol.type in {"TON", "R_TRIG"}:
                fail("Function block requires a member", node)
            return symbol.type
        members = {"TON": {"Q": "BOOL", "ET": "TIME", "IN": "BOOL", "PT": "TIME"},
                   "R_TRIG": {"Q": "BOOL", "CLK": "BOOL"}}
        typ = members.get(symbol.type, {}).get(a[1])
        if typ is None:
            fail(f"Unsupported member {a[0]}.{a[1]}", node, "UNSUPPORTED")
        return str(typ)
    if k == "unary":
        typ = expression_type(a[1], symbols)
        if a[0] == "NOT" and typ == "BOOL":
            return typ
        if a[0] in {"+", "-"} and typ == "INT":
            return typ
        fail("Invalid unary operand", node)
    if k in {"sum", "product", "comparison", "or_expr", "and_expr"}:
        left = expression_type(a[0], symbols)
        for op, right_node in zip(a[1::2], a[2::2], strict=True):
            right = expression_type(right_node, symbols)
            if left != right:
                fail(f"Type mismatch {left} {op} {right}", node)
            if op in {"AND", "OR", "XOR"} and left != "BOOL":
                fail("Boolean operands required", node)
            if op in {"+", "-", "*", "/", "MOD"}:
                if left not in {"INT", "TIME"} or (left == "TIME" and op not in {"+", "-"}):
                    fail("Unsupported arithmetic types", node)
            if op in {"<", ">", "<=", ">="} and left == "BOOL":
                fail("Ordered comparison requires INT or TIME", node)
        return "BOOL" if k == "comparison" else left
    fail(f"Unknown expression {k}", node, "UNSUPPORTED")


def check_body(node: Node, symbols: dict[str, Symbol]) -> None:
    k, a = node.kind, node.args
    if k == "statements":
        for child in a:
            check_body(child, symbols)
    elif k == "assign":
        symbol = symbols.get(a[0])
        if symbol is None:
            fail(f"Undeclared variable {a[0]}", node)
        assert symbol is not None
        if symbol.section == "VAR_INPUT" or symbol.type in {"TON", "R_TRIG"}:
            fail("Cannot assign inputs or entire function blocks", node)
        if expression_type(a[1], symbols) != symbol.type:
            fail("Assignment type mismatch", node)
    elif k == "invoke":
        symbol = symbols.get(a[0])
        if symbol is None or symbol.type not in {"TON", "R_TRIG"}:
            fail("Unknown function block", node)
        expected = {"IN": "BOOL", "PT": "TIME"} if symbol.type == "TON" else {"CLK": "BOOL"}
        names = [arg.args[0] for arg in a[1:]]
        if len(names) != len(set(names)) or set(names) != set(expected):
            fail(f"Expected exactly {list(expected)} arguments", node)
        for arg in a[1:]:
            if expression_type(arg.args[1], symbols) != expected[arg.args[0]]:
                fail("Function block argument type mismatch", arg)
    elif k == "if_stmt":
        i = 0
        while i + 1 < len(a):
            if expression_type(a[i], symbols) != "BOOL":
                fail("IF requires BOOL", a[i])
            check_body(a[i + 1], symbols)
            i += 2
        if i < len(a):
            check_body(a[i], symbols)
    elif k == "case_stmt":
        if expression_type(a[0], symbols) != "INT":
            fail("CASE requires INT", a[0])
        labels: set[int] = set()
        for arm in a[1:]:
            if arm.kind == "statements":
                check_body(arm, symbols)
            else:
                for value in arm.args[0].args:
                    n = int(value)
                    if n in labels or not -32768 <= n <= 32767:
                        fail("Duplicate or out-of-range CASE label", arm)
                    labels.add(n)
                check_body(arm.args[1], symbols)
    else:
        fail(f"Unsupported instruction {k}", node, "UNSUPPORTED")


def parse_program(source: str) -> Program:
    root = parse_tree(source, "start")
    symbols: dict[str, Symbol] = {}
    for section in root.args[1:-1]:
        for decl in section.args[1:]:
            names, typ, *initial = decl.args
            for name in names.args:
                if name in symbols:
                    fail(f"Duplicate variable {name}", decl)
                if len(symbols) >= 128:
                    fail("At most 128 variables supported", decl)
                if typ in {"TON", "R_TRIG"} and (initial or section.args[0] != "VAR"):
                    fail("Function blocks must be internal without initializer", decl)
                if initial and expression_type(initial[0], {}) != typ:
                    fail("Initializer must be a constant of the declared type", decl)
                symbols[name] = Symbol(name, typ, section.args[0], initial[0] if initial else None,
                                       decl.line, decl.column)
    program = Program(root.args[0], symbols, root.args[-1], source)
    check_body(program.body, symbols)
    return program


def parse_expression(source: str, program: Program) -> Node:
    node = parse_tree(source, "expr")
    if expression_type(node, program.symbols) != "BOOL":
        fail("Requirement expression must be BOOL", node)
    return node
