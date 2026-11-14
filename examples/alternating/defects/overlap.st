(* INTENTIONAL DEFECT: overlap *)
PROGRAM Alternating
VAR_INPUT
    Demand, Available1, Available2 : BOOL;
END_VAR
VAR_OUTPUT
    P1, P2, Alarm : BOOL;
END_VAR
VAR
    Lead : INT := 1;
    Active : INT;
    HadDemand : BOOL;
END_VAR
IF NOT Demand THEN
    IF HadDemand THEN
        IF Lead = 1 THEN Lead := 2; ELSE Lead := 1; END_IF;
    END_IF;
    Active := 0;
ELSE
    CASE Active OF
        0:
            IF (Lead = 1) AND Available1 THEN Active := 1;
            ELSIF (Lead = 2) AND Available2 THEN Active := 2;
            ELSIF Available1 THEN Active := 1;
            ELSIF Available2 THEN Active := 2;
            END_IF;
        1: IF NOT Available1 THEN Active := 0; END_IF;
        2: IF NOT Available2 THEN Active := 0; END_IF;
    END_CASE;
END_IF;
P1 := (Active <> 0) AND Demand AND Available1;
P2 := (Active = 2) AND Demand AND Available2;
Alarm := Demand AND NOT Available1 AND NOT Available2;
HadDemand := Demand;
END_PROGRAM
