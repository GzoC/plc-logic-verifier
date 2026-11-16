(* INTENTIONAL DEFECT: auto_ack *)
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
    PhaseClock, PressureTimer : TON;
    Deadline : TIME;
END_VAR
StartEdge(CLK := Start);
IF (State <> 0) AND NOT LevelOK THEN Fault := TRUE; END_IF;
IF Pressure THEN Fault := FALSE; END_IF;
IF Stop OR NOT LevelOK OR Fault THEN
    State := 0;
ELSE
    IF (State = 0) AND StartEdge.Q THEN State := 1; Deadline := T#500ms; END_IF;
END_IF;
(* One continuous virtual clock avoids delaying either phase by a scan. *)
PhaseClock(IN := State <> 0, PT := T#596h);
IF (State <> 0) AND (PhaseClock.ET >= Deadline) THEN
    IF State = 1 THEN State := 2; Deadline := PhaseClock.ET + T#300ms;
    ELSE State := 1; Deadline := PhaseClock.ET + T#500ms;
    END_IF;
END_IF;
PressureTimer(IN := (State = 1) AND NOT Pressure, PT := T#300ms);
IF PressureTimer.Q THEN Fault := TRUE; State := 0; END_IF;
Pump := (State = 1) AND LevelOK AND NOT Fault AND NOT Stop;
END_PROGRAM
