initiatedAt(drifting(Vessel)=true, T) :-
    happensAt(velocity(Vessel,_Speed, CourseOverGround, TrueHeading), T),
    TrueHeading =\= 511.0,
    absoluteAngleDiff(CourseOverGround, TrueHeading, AngleDiff),
    thresholds(adriftAngThr, AdriftAngThr),
    AngleDiff > AdriftAngThr,
    holdsAt(underWay(Vessel)=true, T).

terminatedAt(drifting(Vessel)=true, T) :-
    happensAt(velocity(Vessel,_Speed, CourseOverGround, TrueHeading), T),
    absoluteAngleDiff(CourseOverGround, TrueHeading, AngleDiff),
    thresholds(adriftAngThr, AdriftAngThr),
    AngleDiff =< AdriftAngThr.

terminatedAt(drifting(Vessel)=true, T) :-
    happensAt(velocity(Vessel,_Speed, _CourseOverGround, 511.0), T).

terminatedAt(drifting(Vessel)=true, T) :-
    happensAt(end(underWay(Vessel)=true), T).