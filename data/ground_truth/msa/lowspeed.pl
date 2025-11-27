initiatedAt(lowSpeed(Vessel)=true, T) :-  
    happensAt(slow_motion_start(Vessel), T).

terminatedAt(lowSpeed(Vessel)=true, T) :-
    happensAt(slow_motion_end(Vessel), T).

terminatedAt(lowSpeed(Vessel)=true, T) :-
    %happensAt(start(gap(Vessel)=_Status), T).
    happensAt(gap_start(Vessel), T).