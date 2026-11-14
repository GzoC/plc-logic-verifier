(* INTENTIONAL DEFECT: reverse_start *)
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
StartDelay(IN := State = 1, PT := T#200ms);
Drain(IN := State = 3, PT := T#200ms);
JamTimer(IN := (State <> 0) AND Jam, PT := T#300ms);
IF JamTimer.Q THEN Fault := TRUE; END_IF;
IF Ack AND NOT Jam AND NOT Start AND NOT Stop THEN Fault := FALSE; END_IF;
IF Fault THEN
    State := 0;
ELSE
    IF Stop AND ((State = 1) OR (State = 2)) THEN State := 3; END_IF;
    CASE State OF
        0: IF StartEdge.Q AND NOT Stop AND NOT Jam THEN State := 1; END_IF;
        1: IF StartDelay.Q THEN State := 2; END_IF;
        3: IF Drain.Q THEN State := 0; END_IF;
    END_CASE;
END_IF;
A := (State <> 0) AND NOT Fault;
B := (State = 2) AND NOT Fault;
END_PROGRAM
