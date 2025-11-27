initiatedAt(sarSpeed(Vessel)=true , T):-
    %vesselType(Vessel, sar),
    happensAt(velocity(Vessel, Speed, _, _), T),
    thresholds(sarMinSpeed, SarMinSpeed),
    Speed > SarMinSpeed.
    %inRange(Speed,SarMinSpeed,inf).

terminatedAt(sarSpeed(Vessel)=true, T):-
    %vesselType(Vessel, sar),
    happensAt(velocity(Vessel, Speed, _, _), T),
    thresholds(sarMinSpeed, SarMinSpeed),
    Speed < SarMinSpeed.
    %inRange(Speed,0,SarMinSpeed).

terminatedAt(sarSpeed(Vessel)=true, T):-
    happensAt(gap_start(Vessel), T).
    %happensAt(start(gap(Vessel)=_Status), T).