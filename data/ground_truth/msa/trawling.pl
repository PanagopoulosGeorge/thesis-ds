holdsFor(trawling(Vessel)=true, I):-
    holdsFor(trawlSpeed(Vessel)=true, It),
    holdsFor(trawlingMovement(Vessel)=true, Itc),
    intersect_all([It, Itc], Ii),
    thresholds(trawlingTime, TrawlingTime),
    intDurGreater(Ii, TrawlingTime, I).