initiatedAt(trawlingMovement(Vessel)=true , T):-
    %vesselType(Vessel, fishing),
    happensAt(change_in_heading(Vessel), T),
    holdsAt(withinArea(Vessel, fishing)=true, T).

terminatedAt(trawlingMovement(Vessel)=true, T):-
    happensAt(end(withinArea(Vessel, fishing)=true), T).

%fi(trawlingMovement(Vessel)=true, trawlingMovement(Vessel)=false, TrawlingCrs):-
	%thresholds(trawlingCrs, TrawlingCrs).
%p(trawlingMovement(_Vessel)=true).