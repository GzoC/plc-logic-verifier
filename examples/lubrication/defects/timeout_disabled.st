(* INTENTIONAL DEFECT: timeout_disabled *)
PROGRAM Lubrication
VAR_INPUT
    Start, Stop, LevelOK, Pressure, Ack : BOOL;
END_VAR
VAR_OUTPUT
    Pump, Fault : BOOL;
END_VAR
VAR
    State : INT;
    StartEdge : R_TRIG;
    Lube, PauseTimer, PressureTimer : TON;
END_VAR
StartEdge(CLK := Start);
Lube(IN := State = 1, PT := T#500ms);
PauseTimer(IN := State = 2, PT := T#300ms);
PressureTimer(IN := (State = 1) AND NOT Pressure, PT := T#300ms);
IF FALSE THEN Fault := TRUE; END_IF;
IF (State <> 0) AND NOT LevelOK THEN Fault := TRUE; END_IF;
IF Ack AND LevelOK AND Pressure AND NOT Start AND NOT Stop THEN Fault := FALSE; END_IF;
IF Stop OR NOT LevelOK OR Fault THEN
    State := 0;
ELSE
    CASE State OF
        0: IF StartEdge.Q THEN State := 1; END_IF;
        1: IF Lube.Q THEN State := 2; END_IF;
        2: IF PauseTimer.Q THEN State := 1; END_IF;
    END_CASE;
END_IF;
Pump := (State = 1) AND LevelOK AND NOT Fault AND NOT Stop;
END_PROGRAM
