initiatedAt(changingSpeed(Vessel)=true, T) :-  
    happensAt(change_in_speed_start(Vessel), T).

terminatedAt(changingSpeed(Vessel)=true, T) :-
    happensAt(change_in_speed_end(Vessel), T).

terminatedAt(changingSpeed(Vessel)=true, T) :-
    %happensAt(start(gap(Vessel)=_Status), T).
    happensAt(gap_start(Vessel), T).