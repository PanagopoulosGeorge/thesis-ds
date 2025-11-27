holdsFor(pilotOps(Vessel1, Vessel2)=true, I) :-
    holdsFor(proximity(Vessel1, Vessel2)=true, Ip),
    oneIsPilot(Vessel1, Vessel2),
    holdsFor(lowSpeed(Vessel1)=true, Il1),
    holdsFor(lowSpeed(Vessel2)=true, Il2),
    holdsFor(stopped(Vessel1)=farFromPorts, Is1),
    holdsFor(stopped(Vessel2)=farFromPorts, Is2),
    union_all([Il1, Is1], I1b),
    union_all([Il2, Is2], I2b),
    intersect_all([I1b, I2b, Ip], Ii), Ii\=[],
    holdsFor(withinArea(Vessel1, nearCoast)=true, Iw1),
    holdsFor(withinArea(Vessel2, nearCoast)=true, Iw2),
    relative_complement_all(Ii,[Iw1, Iw2], I).