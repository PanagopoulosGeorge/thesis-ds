msa_requests = [
        {
            'fluent_name': 'gap',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “gap”: A communication gap starts when we stop receiving messages from a vessel. We would like to distinguish the cases where a communication gap starts (i) near some port and (ii) far from all ports. A communication gap ends when we resume receiving messages from a vessel.', 
            'prolog': r"""
                        initiatedAt(gap(Vessel)=nearPorts, T) :-
                                happensAt(gap_start(Vessel), T),
                                holdsAt(withinArea(Vessel, nearPorts)=true, T).

                        initiatedAt(gap(Vessel)=farFromPorts, T) :-
                                happensAt(gap_start(Vessel), T),
                                \+holdsAt(withinArea(Vessel, nearPorts)=true, T).

                        terminatedAt(gap(Vessel)=_PortStatus, T) :-
                                happensAt(gap_end(Vessel), T).
        """.strip()
        },
        {
            'fluent_name': 'highSpeedNearCoast',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “highSpeedNearCoast”: This activity starts when a vessel is sailing within a coastal area and its speed surpasses the coastal speed limit. The activity ends when the speed of the vessel becomes less than the coastal speed limit or the vessel exits the coastal area.',
            'prolog': r"""
                        initiatedAt(highSpeedNearCoast(Vessel)=true, T):-
                                happensAt(velocity(Vessel, Speed, _, _), T),
                                thresholds(hcNearCoastMax, HcNearCoastMax),
                                Speed > HcNearCoastMax,
                                holdsAt(withinArea(Vessel, nearCoast)=true, T).

                        terminatedAt(highSpeedNearCoast(Vessel)=true, T):-
                                happensAt(velocity(Vessel, Speed, _, _), T),
                                thresholds(hcNearCoastMax, HcNearCoastMax),
                                Speed < HcNearCoastMax.

                        terminatedAt(highSpeedNearCoast(Vessel)=true, T):-
                                happensAt(end(withinArea(Vessel, nearCoast)=true), T).
    """.strip()
        },

        {
            'fluent_name': 'trawlSpeed',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “trawlSpeed”: The activity starts when the vessel is sailing in a fishing area and its speed is within the expected bounds for a trawling activity. The activity ends when the speed of the vessels falls outside the expected bounds for a trawling activity. When there is a gap in signal transmissions, we can no longer assume that the vessel’s speed remains within the aforementioned bounds.',
            'prolog': r"""
                        initiatedAt(trawlSpeed(Vessel)=true, T):-
                                happensAt(velocity(Vessel, Speed, _Heading,_), T),
                                thresholds(trawlspeedMin, TrawlspeedMin),
                                thresholds(trawlspeedMax, TrawlspeedMax),
                                Speed > TrawlspeedMin,
                                Speed < TrawlspeedMax,
                                holdsAt(withinArea(Vessel, fishing)=true, T).

                        terminatedAt(trawlSpeed(Vessel)=true, T):-
                                happensAt(velocity(Vessel, Speed, _Heading,_), T),
                                thresholds(trawlspeedMin, TrawlspeedMin),
                                thresholds(trawlspeedMax, TrawlspeedMax),
                                Speed < TrawlspeedMin.

                        terminatedAt(trawlSpeed(Vessel)=true, T):-
                                happensAt(velocity(Vessel, Speed, _Heading,_), T),
                                thresholds(trawlspeedMin, TrawlspeedMin),
                                thresholds(trawlspeedMax, TrawlspeedMax),
                                Speed > TrawlspeedMax.

                        terminatedAt(trawlSpeed(Vessel)=true, T):-
                                happensAt(gap_start(Vessel), T).

                        terminatedAt(trawlSpeed(Vessel)=true, T):-
                                happensAt(end(withinArea(Vessel, fishing)=true), T).
            """.strip()
        },
        {
            'fluent_name': 'trawlingMovement',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “trawlingMovement”: This activity expresses that the vessel is sailing in a manner that is typical for a trawling activity. The activity starts when the vessel changes its heading while sailing within a fishing area. The activity ends when the vessel leaves the fishing area.',
            'prolog': r"""
                        initiatedAt(trawlingMovement(Vessel)=true , T):-
                                happensAt(change_in_heading(Vessel), T),
                                holdsAt(withinArea(Vessel, fishing)=true, T).

                        terminatedAt(trawlingMovement(Vessel)=true, T):-
                                happensAt(end(withinArea(Vessel, fishing)=true), T).
            """.strip()
        },
        {
            'fluent_name': 'lowSpeed',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “lowSpeed”: The activity starts when the vessel starts moving at a low speed. The activity ends when the vessel stops moving at a low speed. When there is a gap in signal transmissions, we can no longer assume that the vessel continues moving at a low speed.',
            'prolog': r"""
                        initiatedAt(lowSpeed(Vessel)=true, T) :-  
                                happensAt(slow_motion_start(Vessel), T).

                        terminatedAt(lowSpeed(Vessel)=true, T) :-
                                happensAt(slow_motion_end(Vessel), T).

                        terminatedAt(lowSpeed(Vessel)=true, T) :-
                                happensAt(gap_start(Vessel), T).
            """.strip()
        },
        {
            'fluent_name': 'tuggingSpeed',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “tuggingSpeed”: The activity starts when the vessel is sailing at a speed that is within the expected bounds for a tugging operation. The activity ends when the vessel is no longer sailing at a speed that is within the expected bounds for a tugging operation. When there is a gap in signal transmissions, we can no longer assume that the vessel’s speed remains within the aforementioned bounds.',
            'prolog': r"""
                        initiatedAt(tuggingSpeed(Vessel)=true , T) :-
                                happensAt(velocity(Vessel, Speed, _, _), T),
                                thresholds(tuggingMin, TuggingMin),
                                thresholds(tuggingMax, TuggingMax),
                                Speed > TuggingMin, 
                                Speed < TuggingMax.

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

                        terminatedAt(tuggingSpeed(Vessel)=true , T) :-
                                happensAt(gap_start(Vessel), T).
            """.strip()
        },
        {
            'fluent_name': 'sarSpeed',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “sarSpeed”: The activity starts when the speed of the vessel exceeds the minimum expected speed of a vessel that is engaged in a search-and-rescue (SAR) operation. The activity ends when the speed of the vessel falls below the aforementioned minimum speed threshold. When there is a gap in signal transmissions, we can no longer assume that the vessel’s speed remains above the aforementioned threshold.',
            'prolog': r"""
                        initiatedAt(sarSpeed(Vessel)=true , T):-
                                happensAt(velocity(Vessel, Speed, _, _), T),
                                thresholds(sarMinSpeed, SarMinSpeed),
                                Speed > SarMinSpeed.

                        terminatedAt(sarSpeed(Vessel)=true, T):-
                                happensAt(velocity(Vessel, Speed, _, _), T),
                                thresholds(sarMinSpeed, SarMinSpeed),
                                Speed < SarMinSpeed.

                        terminatedAt(sarSpeed(Vessel)=true, T):-
                                happensAt(gap_start(Vessel), T).
            """.strip()
        },
        {
            'fluent_name': 'changingSpeed',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “changingSpeed”: The activity starts when the speed of the vessel starts changing. The activity ends when the speed of the vessel stops changing. When there is a gap in signal transmissions, we can no longer assume that the vessel’s speed is currently changing.', 
            'prolog': r"""
                        initiatedAt(changingSpeed(Vessel)=true, T) :-  
                                happensAt(change_in_speed_start(Vessel), T).

                        terminatedAt(changingSpeed(Vessel)=true, T) :-
                                happensAt(change_in_speed_end(Vessel), T).

                        terminatedAt(changingSpeed(Vessel)=true, T) :-
                                happensAt(gap_start(Vessel), T).
            """.strip()
        },
        {
            'fluent_name': 'movingSpeed',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “movingSpeed”: The activity monitors the time periods during which a vessel of a certain type is moving at a speed that is “below” the minimum speed expected for a vessel of this type, “normal”, i.e., within the expected bounds for the speed of a vessel of this type, and “above” the maximum speed expected for a vessel of this type. The activity ends when the speed of the vessel falls below the minimum speed expected for a moving vessel. When there is a gap in signal transmissions, we can no longer assume that the vessel’s speed remains the same.', 
            'prolog': r"""
                        initiatedAt(movingSpeed(Vessel)=below, T) :-
                                happensAt(velocity(Vessel, Speed, _, _), T),
                                vesselType(Vessel, Type),
                                typeSpeed(Type, Min, _Max, _Avg),
                                thresholds(movingMin, MovingMin),
                                Speed > MovingMin, 
                                Speed < Min.

                        initiatedAt(movingSpeed(Vessel)=normal, T) :-
                                happensAt(velocity(Vessel, Speed, _, _), T),
                                vesselType(Vessel, Type),
                                typeSpeed(Type, Min, Max, _Avg),
                                Speed > Min, 
                                Speed < Max.

                        initiatedAt(movingSpeed(Vessel)=above, T) :-
                                happensAt(velocity(Vessel, Speed, _,_), T),
                                vesselType(Vessel, Type),
                                typeSpeed(Type, _Min, Max,_Avg),
                                Speed > Max.

                        terminatedAt(movingSpeed(Vessel)=_Status, T) :-
                                happensAt(velocity(Vessel, Speed, _,_), T),
                                thresholds(movingMin,MovingMin),
                                Speed < MovingMin.

                        terminatedAt(movingSpeed(Vessel)=_Status, T) :-
                                happensAt(gap_start(Vessel), T).
            """.strip()
        },
        {
            'fluent_name': 'trawling',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “trawling”: Trawling is a common fishing method that involves a boat - trawler - pulling a fishing net through the water behind it. Trawling lasts as long as the vessel is sailing in a fishing area, its speed is within the expected bounds for a trawling activity and it is sailing in a manner that is typical for a trawling activity. Trawling activities cannot be arbitrarily brief, i.e., the duration of trawling activities exceeds a minimum temporal threshold.', 
            'prolog': r"""
                        holdsFor(trawling(Vessel)=true, I):-
                                holdsFor(trawlSpeed(Vessel)=true, It),
                                holdsFor(trawlingMovement(Vessel)=true, Itc),
                                intersect_all([It, Itc], Ii),
                                thresholds(trawlingTime, TrawlingTime),
                                intDurGreater(Ii, TrawlingTime, I).
            """.strip()
        },      
        {
            'fluent_name': 'anchoredOrMoored',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “anchoredOrMoored”: The activity lasts as long as the vessel is idle in an anchorage area that is far from all ports, or is idle near some port.',
            'prolog': r"""
                        holdsFor(anchoredOrMoored(Vessel)=true, I) :-
                                holdsFor(stopped(Vessel)=farFromPorts, Istfp),
                                holdsFor(withinArea(Vessel, anchorage)=true, Ia),
                                intersect_all([Istfp, Ia], Ista),
                                holdsFor(stopped(Vessel)=nearPorts, Istnp),
                                union_all([Ista, Istnp], Ii),
                                thresholds(aOrMTime, AOrMTime),
                                intDurGreater(Ii, AOrMTime, I).
            """.strip()
        },     
        {
            'fluent_name': 'tugging',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “tugging”: The activity involves a vessel being pulled or towed by a tugboat. Tugging lasts as long as the two involved vessels, one of which must be a tugboat, are sailing close to each other and their speed falls within the expected bounds for a tugging operation. Tugging operations cannot be arbitrarily brief, i.e., the duration of a tugging operation exceeds a minimum temporal threshold.',
            'prolog': r"""
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
            """.strip()
        },
        {
            'fluent_name': 'sarMovement',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “sarMovement”: This activity expresses that the vessel is moving in a manner that is typical for a search-and-rescue (SAR) operation. The activity starts when the vessel changes its speed or its heading. When there is a gap in signal transmissions, we can no longer assume that the vessel keeps moving in a similar fashion.',
            'prolog': r"""
                        initiatedAt(sarMovement(Vessel)=true, T):-
                                happensAt(change_in_heading(Vessel), T).

                        initiatedAt(sarMovement(Vessel)=true , T):-
                                happensAt(change_in_speed_start(Vessel), T).
                        

                        terminatedAt(sarMovement(Vessel)=true, T):-
                                happensAt(gap_start(Vessel), T).
            """.strip()
        },
        {
            'fluent_name': 'pilotOps',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “pilotOps”: This activity expresses that a highly experienced sailor in navigation in specific areas - a maritime pilot - approaches with a pilot vessel, boards and manoeuvres another vessel through dangerous or congested areas. The activity lasts as long as the two involved vessels, one of which being a pilot vessel, are sailing close to each other, each having a low speed or being idle far from all ports, and are not within a coastal area.', 
            'prolog': r"""
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
            """.strip()
        },
        {
            'fluent_name': 'drifting',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “drifting”: This activity expresses that a vessel is drifting due to sea currents or harsh weather conditions. The activity starts when the angle difference between the actual direction of the vessel and the direction of its bow exceeds a maximum limit, expressing a significant divergence. The activity ends when this angle difference falls below the aforementioned threshold or when the vessel stops moving.', 
            'prolog': r"""
                        initiatedAt(drifting(Vessel)=true, T) :-
                                happensAt(velocity(Vessel,_Speed, CourseOverGround, TrueHeading), T),
                                TrueHeading =\= 511.0,
                                absoluteAngleDiff(CourseOverGround, TrueHeading, AngleDiff),
                                thresholds(adriftAngThr, AdriftAngThr),
                                AngleDiff > AdriftAngThr,
                                holdsAt(underWay(Vessel)=true, T).

                        terminatedAt(drifting(Vessel)=true, T) :-
                                happensAt(velocity(Vessel,_Speed, CourseOverGround, TrueHeading), T),
                                absoluteAngleDiff(CourseOverGround, TrueHeading, AngleDiff),
                                thresholds(adriftAngThr, AdriftAngThr),
                                AngleDiff =< AdriftAngThr.

                        terminatedAt(drifting(Vessel)=true, T) :-
                                happensAt(velocity(Vessel,_Speed, _CourseOverGround, 511.0), T).

                        terminatedAt(drifting(Vessel)=true, T) :-
                                happensAt(end(underWay(Vessel)=true), T).
            """.strip()
        },
        {
            'fluent_name': 'inSAR',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “inSAR”: This activity expresses that the vessel is performing a search-and-rescue (SAR) operation. The activity lasts as long as the vessel is sailing at a speed that is typical for a pilot vessel involved in a SAR operation and the vessel is moving in a manner that is typical for such an operation.', 
            'prolog': r"""
                        holdsFor(inSAR(Vessel)=true, I):-
                                holdsFor(sarSpeed(Vessel)=true, Iss),
                                holdsFor(sarMovement(Vessel)=true, Isc),
                                intersect_all([Iss, Isc], Ii),
                                intDurGreater(Ii, 3600, I).
            """.strip()
        },
        {
            'fluent_name': 'loitering',
            'description': 'Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the MSA events, the MSA input fluents, and the MSA background knowledge predicates. You may also use any of the MSA output fluents that you have already learned.\nComposite Maritime Activity Description - “loitering”: This activity expresses that the vessel is in a particular area for a long period without any evident purpose. The activity lasts as long as the vessel has low speed or is idle far from all ports, and it is not near a coast, it is not anchored, and it is not moored. The activity cannot be arbitrarily brief, i.e., we detect “loitering” when the temporal extent during which the vessel is loafing around exceeds a minimum threshold.',
            'prolog': r"""
                        holdsFor(loitering(Vessel)=true, I) :-
                                holdsFor(lowSpeed(Vessel)=true, Il),
                                holdsFor(stopped(Vessel)=farFromPorts, Is),
                                union_all([Il, Is], Ils),
                                holdsFor(withinArea(Vessel, nearCoast)=true, Inc),
                                holdsFor(anchoredOrMoored(Vessel)=true, Iam),
                                relative_complement_all(Ils, [Inc,Iam], Ii),
                                thresholds(loiteringTime, LoiteringTime),
                                intDurGreater(Ii, LoiteringTime, I).
            """.strip()
        }       
]

