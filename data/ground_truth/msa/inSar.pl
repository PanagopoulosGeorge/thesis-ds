holdsFor(inSAR(Vessel)=true, I):-
    holdsFor(sarSpeed(Vessel)=true, Iss),
    holdsFor(sarMovement(Vessel)=true, Isc),
    intersect_all([Iss, Isc], Ii),
    intDurGreater(Ii, 3600, I).