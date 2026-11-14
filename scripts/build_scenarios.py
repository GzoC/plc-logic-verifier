"""Author-controlled fixtures. Generates YAML and explicit defect copies, never results."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1] / "examples"


def req(id, kind, description, **kwargs):
    return dict(id=id, kind=kind, description=description, **kwargs)


def event(scan, **values):
    return dict(scan=scan, set=values)


def scenario(case, name, duration, initial, events, requirements):
    data = dict(id=f"{case}-{name}", description=f"Caso {case}: {name}", program="correct.st",
                duration_ms=duration, scan_ms=100, initial=initial, events=events,
                requirements=requirements)
    (ROOT / case / f"{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


scenario("lubrication", "normal", 1600, {"LevelOK": True},
         [event(0, Start=True), event(1, Start=False), event(2, Pressure=True), event(14, Stop=True)], [
    req("L01", "hold", "Arranque permitido", expr="Pump", start_ms=0, end_ms=500),
    req("L02-pause", "hold", "Pausa cíclica", expr="NOT Pump", start_ms=600, end_ms=900),
    req("L02-repeat", "hold", "Nueva lubricación", expr="Pump", start_ms=1000, end_ms=1300),
    req("L04-stop", "response", "Stop para en el mismo scan", trigger="Stop", expr="NOT Pump", within_ms=0),
    req("L-normal", "always", "Presión confirmada evita falla", expr="NOT Fault"),
])
scenario("lubrication", "fault", 1300, {"LevelOK": True},
         [event(0, Start=True), event(6, Pressure=True), event(7, Ack=True),
          event(8, Start=False), event(9, Start=True, Ack=False), event(11, LevelOK=False)], [
    req("L03", "hold", "Timeout de presión enclava falla", expr="Fault AND NOT Pump", start_ms=400, end_ms=700),
    req("L05", "latch", "Recuperar presión no reconoce la falla", trigger="Fault", expr="Fault", until="Ack AND LevelOK AND Pressure AND NOT Start AND NOT Stop"),
    req("L06", "hold", "Reconocimiento inválido con Start sostenido", expr="Fault", start_ms=700, end_ms=700),
    req("L07", "hold", "Reconocimiento válido no rearranca", expr="NOT Pump AND NOT Fault", start_ms=800, end_ms=800),
    req("L07-start", "hold", "Nueva orden explícita", expr="Pump", start_ms=900, end_ms=1000),
    req("L04-level", "never", "Sin nivel no hay salida", when="NOT LevelOK", expr="Pump"),
])
scenario("alternating", "normal", 1000, {"Available1": True, "Available2": True},
         [event(0, Demand=True), event(3, Demand=False), event(5, Demand=True), event(8, Demand=False)], [
    req("B01", "hold", "Principal inicial P1", expr="P1 AND NOT P2", start_ms=0, end_ms=200),
    req("B04", "hold", "Alternancia a P2", expr="P2 AND NOT P1", start_ms=500, end_ms=700),
    req("B02", "mutex", "Exclusión mutua", steps=["P1", "P2"]),
    req("B05", "never", "Sin demanda ambas apagadas", when="NOT Demand", expr="P1 OR P2"),
])
scenario("alternating", "fault", 1000, {"Available1": True, "Available2": True},
         [event(0, Demand=True), event(3, Available1=False), event(6, Available2=False),
          event(8, Available1=True)], [
    req("B03-gap", "hold", "Transferencia con scan apagado", expr="NOT P1 AND NOT P2", start_ms=300, end_ms=300),
    req("B03-transfer", "hold", "Reserva toma demanda", expr="P2 AND NOT P1", start_ms=400, end_ms=500),
    req("B02", "mutex", "Nunca simultáneas", steps=["P1", "P2"]),
    req("B05", "always", "Salidas sólo con disponibilidad", expr="(NOT P1 OR Available1) AND (NOT P2 OR Available2)"),
    req("B06", "hold", "Indisponibilidad total", expr="Alarm AND NOT P1 AND NOT P2", start_ms=600, end_ms=700),
    req("B-recover", "hold", "Recuperación disponible", expr="P1 AND NOT Alarm", start_ms=800, end_ms=900),
])
scenario("conveyor", "normal", 1300, {},
         [event(0, Start=True), event(1, Start=False), event(7, Stop=True)], [
    req("C01-order", "sequence", "Aguas abajo antes de alimentación", steps=["B AND NOT A", "A AND B"]),
    req("C01-delay", "hold", "Espera de arranque", expr="B AND NOT A", start_ms=0, end_ms=200),
    req("C01-run", "hold", "Ambas en marcha", expr="A AND B", start_ms=300, end_ms=600),
    req("C02-drain", "hold", "Vaciado con A apagada", expr="NOT A AND B", start_ms=700, end_ms=900),
    req("C02-stop", "hold", "Parada completada", expr="NOT A AND NOT B", start_ms=1000, end_ms=1200),
])
scenario("conveyor", "fault", 1400, {},
         [event(0, Start=True), event(1, Start=False), event(4, Jam=True), event(6, Ack=True),
          event(8, Ack=False), event(9, Jam=False), event(11, Ack=True), event(12, Start=True, Ack=False)], [
    req("C03", "hold", "Timeout de atasco", expr="Fault AND NOT A AND NOT B", start_ms=700, end_ms=1000),
    req("C04", "latch", "Falla persiste hasta reconocimiento válido", trigger="Fault", expr="Fault", until="Ack AND NOT Jam AND NOT Start AND NOT Stop"),
    req("C05-idle", "hold", "Reconocer no arranca", expr="NOT Fault AND NOT A AND NOT B", start_ms=1100, end_ms=1100),
    req("C05-start", "hold", "Nueva orden arranca aguas abajo", expr="B AND NOT A", start_ms=1200, end_ms=1300),
])

mutations = {
    "lubrication": {
        "timeout_disabled": ("IF PressureTimer.Q THEN", "IF FALSE THEN"),
        "auto_ack": ("IF Ack AND LevelOK AND Pressure AND NOT Start AND NOT Stop THEN", "IF Pressure THEN"),
    },
    "alternating": {
        "overlap": ("P1 := (Active = 1) AND Demand AND Available1;", "P1 := (Active <> 0) AND Demand AND Available1;"),
        "no_alternation": ("IF Lead = 1 THEN Lead := 2; ELSE Lead := 1; END_IF;", "Lead := 1;"),
    },
    "conveyor": {
        "reverse_start": ("A := (State = 2) AND NOT Fault;\nB := (State <> 0) AND NOT Fault;", "A := (State <> 0) AND NOT Fault;\nB := (State = 2) AND NOT Fault;"),
        "auto_restart": ("IF Ack AND NOT Jam AND NOT Start AND NOT Stop THEN", "IF NOT Jam THEN"),
    },
}
for case, defects in mutations.items():
    source = (ROOT / case / "correct.st").read_text(encoding="utf-8")
    folder = ROOT / case / "defects"
    folder.mkdir(exist_ok=True)
    for name, (old, new) in defects.items():
        assert source.count(old) == 1
        (folder / f"{name}.st").write_text("(* INTENTIONAL DEFECT: " + name + " *)\n" + source.replace(old, new), encoding="utf-8")
