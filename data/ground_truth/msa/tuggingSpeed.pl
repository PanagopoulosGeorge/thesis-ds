initiatedAt(tuggingSpeed(Vessel)=true , T) :-
    happensAt(velocity(Vessel, Speed, _, _), T),
    thresholds(tuggingMin, TuggingMin),
    thresholds(tuggingMax, TuggingMax),
    Speed > TuggingMin, 
    Speed < TuggingMax.
    %inRange(Speed, TuggingMin, TuggingMax).

terminatedAt(tuggingSpeed(Vessel)=true , T) :-
    happensAt(velocity(Vessel, Speed, _, _), T),
    thresholds(tuggingMin, TuggingMin),
    thresholds(tuggingMax, TuggingMax),
    Speed < TuggingMin.
terminatedAt(tuggingSpeed(Vessel)=true , T) :-
    happensAt(velocity(Vessel, Speed, _, _), T),
    thresholds(tuggingMin, TuggingMin),
    thresholds(tuggingMax, TuggingMax),
    Speed > TuggingMax.
    %\+inRange(Speed, TuggingMin, TuggingMax).

terminatedAt(tuggingSpeed(Vessel)=true , T) :-
    happensAt(gap_start(Vessel), T).
    %happensAt(start(gap(Vessel)=_Status), T).

holdsFor(tugging(Vessel1, Vessel2)=true, I) :-
    holdsFor(proximity(Vessel1, Vessel2)=true, Ip),
    oneIsTug(Vessel1, Vessel2),
    \+oneIsPilot(Vessel1, Vessel2),
    \+twoAreTugs(Vessel1, Vessel2),
    holdsFor(tuggingSpeed(Vessel1)=true, Its1),
    holdsFor(tuggingSpeed(Vessel2)=true, Its2),
    intersect_all([Ip, Its1, Its2], Ii),
    thresholds(tuggingTime, TuggingTime),
    intDurGreater(Ii, TuggingTime, I).   