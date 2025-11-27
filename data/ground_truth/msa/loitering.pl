holdsFor(loitering(Vessel)=true, I) :-
    holdsFor(lowSpeed(Vessel)=true, Il),
    holdsFor(stopped(Vessel)=farFromPorts, Is),
    union_all([Il, Is], Ils),
    holdsFor(withinArea(Vessel, nearCoast)=true, Inc),
    holdsFor(anchoredOrMoored(Vessel)=true, Iam),
    relative_complement_all(Ils, [Inc,Iam], Ii),
    thresholds(loiteringTime, LoiteringTime),
    intDurGreater(Ii, LoiteringTime, I).