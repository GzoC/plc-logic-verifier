(* INTENTIONAL DEFECT: auto_restart *)
PROGRAM Conveyor
VAR_INPUT
    Start, Stop, Jam, Ack : BOOL;
END_VAR
VAR_OUTPUT
    A, B, Fault : BOOL;
END_VAR
VAR
    State : INT;
    StartEdge : R_TRIG;
    StartDelay, Drain, JamTimer : TON;
END_VAR
StartEdge(CLK := Start);
JamTimer(IN := (State <> 0) AND Jam, PT := T#300ms);
IF JamTimer.Q THEN Fault := TRUE; END_IF;
IF NOT Jam THEN Fault := FALSE; END_IF;
IF Fault THEN
    State := 0;
ELSE
    IF Stop AND ((State = 1) OR (State = 2)) THEN State := 3; END_IF;
    IF (State = 0) AND StartEdge.Q AND NOT Stop AND NOT Jam THEN State := 1; END_IF;
END_IF;
(* Enable timers on the scan that publishes the observable transition. *)
StartDelay(IN := State = 1, PT := T#200ms);
Drain(IN := State = 3, PT := T#200ms);
IF (State = 1) AND StartDelay.Q THEN State := 2; END_IF;
IF (State = 3) AND Drain.Q THEN State := 0; END_IF;
A := (State = 2) AND NOT Fault;
B := (State <> 0) AND NOT Fault;
END_PROGRAM
