initiatedAt(trawlSpeed(Vessel)=true, T):-
    happensAt(velocity(Vessel, Speed, _Heading,_), T),
    thresholds(trawlspeedMin, TrawlspeedMin),
    thresholds(trawlspeedMax, TrawlspeedMax),
    Speed > TrawlspeedMin,
    Speed < TrawlspeedMax,
    %inRange(Speed, TrawlspeedMin, TrawlspeedMax),
    holdsAt(withinArea(Vessel, fishing)=true, T).

terminatedAt(trawlSpeed(Vessel)=true, T):-
    happensAt(velocity(Vessel, Speed, _Heading,_), T),
    thresholds(trawlspeedMin, TrawlspeedMin),
    thresholds(trawlspeedMax, TrawlspeedMax),
    Speed < TrawlspeedMin.

terminatedAt(trawlSpeed(Vessel)=true, T):-
    happensAt(velocity(Vessel, Speed, _Heading,_), T),
    thresholds(trawlspeedMin, TrawlspeedMin),
    thresholds(trawlspeedMax, TrawlspeedMax),
    Speed > TrawlspeedMax.

terminatedAt(trawlSpeed(Vessel)=true, T):-
    happensAt(gap_start(Vessel), T).
    %happensAt(start(gap(Vessel)=_Status), T).

terminatedAt(trawlSpeed(Vessel)=true, T):-
    happensAt(end(withinArea(Vessel, fishing)=true), T).