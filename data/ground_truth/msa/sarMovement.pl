initiatedAt(sarMovement(Vessel)=true, T):-
    %vesselType(Vessel, sar),
    happensAt(change_in_heading(Vessel), T).

initiatedAt(sarMovement(Vessel)=true , T):-
    %vesselType(Vessel, sar),
    happensAt(change_in_speed_start(Vessel), T).
    %happensAt(start(changingSpeed(Vessel)=true), T).

terminatedAt(sarMovement(Vessel)=true, T):-
    %vesselType(Vessel, sar),
    happensAt(gap_start(Vessel), T).
    %happensAt(start(gap(Vessel)=_Status), T).

%fi(sarMovement(Vessel)=true, sarMovement(Vessel)=false, 1800).
%p(sarMovement(_Vessel)=true).