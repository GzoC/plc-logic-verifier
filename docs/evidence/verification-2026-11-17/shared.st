PROGRAM Shared
VAR
    tick : INT;
    amount : INT;
    phase : INT;
    enable : BOOL;
    edge : R_TRIG;
    pulse : BOOL;
    immediate : TON;
    aligned : TON;
    rounded : TON;
    q0 : BOOL;
    q100 : BOOL;
    q125 : BOOL;
END_VAR
tick := tick + 1;
enable := (tick <= 4) OR (tick >= 6);
IF enable THEN amount := amount + 2; ELSE amount := amount - 1; END_IF;
CASE tick OF
    1: phase := 3;
    2: phase := 7;
ELSE phase := amount;
END_CASE;
edge(CLK := enable);
pulse := edge.Q;
immediate(IN := enable, PT := T#0ms);
aligned(IN := enable, PT := T#100ms);
rounded(IN := enable, PT := T#125ms);
q0 := immediate.Q;
q100 := aligned.Q;
q125 := rounded.Q;
END_PROGRAM
