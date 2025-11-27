initiatedAt(movingSpeed(Vessel)=below, T) :-
    happensAt(velocity(Vessel, Speed, _, _), T),
    vesselType(Vessel, Type),
    typeSpeed(Type, Min, _Max, _Avg),
    thresholds(movingMin, MovingMin),
    Speed > MovingMin, 
    Speed < Min.
    %inRange(Speed, MovingMin, Min).

initiatedAt(movingSpeed(Vessel)=normal, T) :-
    happensAt(velocity(Vessel, Speed, _, _), T),
    vesselType(Vessel, Type),
    typeSpeed(Type, Min, Max, _Avg),
    Speed > Min, 
    Speed < Max.
    %inRange(Speed, Min, Max).

initiatedAt(movingSpeed(Vessel)=above, T) :-
    happensAt(velocity(Vessel, Speed, _,_), T),
    vesselType(Vessel, Type),
    typeSpeed(Type, _Min, Max,_Avg),
    Speed > Max.
    %inRange(Speed, Max, inf).

terminatedAt(movingSpeed(Vessel)=_Status, T) :-
    happensAt(velocity(Vessel, Speed, _,_), T),
    thresholds(movingMin,MovingMin),
    Speed < MovingMin.
    %\+inRange(Speed, MovingMin, inf).

terminatedAt(movingSpeed(Vessel)=_Status, T) :-
    happensAt(gap_start(Vessel), T).
    %happensAt(start(gap(Vessel)=_GapStatus), T).
