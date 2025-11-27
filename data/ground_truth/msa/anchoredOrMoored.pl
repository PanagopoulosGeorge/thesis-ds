holdsFor(anchoredOrMoored(Vessel)=true, I) :-
    holdsFor(stopped(Vessel)=farFromPorts, Istfp),
    holdsFor(withinArea(Vessel, anchorage)=true, Ia),
    intersect_all([Istfp, Ia], Ista),
    holdsFor(stopped(Vessel)=nearPorts, Istnp),
    union_all([Ista, Istnp], Ii),
    thresholds(aOrMTime, AOrMTime),
    intDurGreater(Ii, AOrMTime, I).