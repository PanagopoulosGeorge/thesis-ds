initiatedAt(highSpeedNearCoast(Vessel)=true, T):-
    happensAt(velocity(Vessel, Speed, _, _), T),
    thresholds(hcNearCoastMax, HcNearCoastMax),
    Speed > HcNearCoastMax,
    %\+ inRange(Speed, 0, HcNearCoastMax),
    holdsAt(withinArea(Vessel, nearCoast)=true, T).

terminatedAt(highSpeedNearCoast(Vessel)=true, T):-
    happensAt(velocity(Vessel, Speed, _, _), T),
    thresholds(hcNearCoastMax, HcNearCoastMax),
    %inRange(Speed, 0, HcNearCoastMax),
    Speed < HcNearCoastMax.

terminatedAt(highSpeedNearCoast(Vessel)=true, T):-
    happensAt(end(withinArea(Vessel, nearCoast)=true), T).
