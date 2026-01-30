har_requests = [
    {
        'fluent_name': 'leaving_object',
        'description': """
                        Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the HAR events, the HAR input fluents, and the HAR background knowledge predicates. You may also use any of the HAR output fluents that you have already learned.
                        Composite Activity Description - “leaving_object”: This activity concerns a person and an inactive object. The activity starts when an object ‘appears’, i.e. the cameras start tracking the object, and at the same time a person is very close to the object. The activity ends when an object ‘disappears’, i.e. the cameras stop tracking the object.
                        """.strip(),
        'prolog': r"""
        initiatedAt(leaving_object(Person,Object)=true, T) :-
            happensAt(appear(Object), T), 
            holdsAt(inactive(Object)=true, T),
            holdsAt(person(Person)=true, T),
            thresholds(leavingObjectThr, LeavingObjectThr),
            holdsAt(close(Person,Object,LeavingObjectThr)=true, T).

        terminatedAt(leaving_object(_Person,Object)=true, T) :-
            happensAt(disappear(Object), T).
        """.strip(),
    },
    {
        'fluent_name': 'moving',
        'description': """
                        Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the HAR events, the HAR input fluents, and the HAR background knowledge predicates. You may also use any of the HAR output fluents that you have already learned.
                        Composite Activity Description - “moving”: This activity concerns two people. The activity lasts as long as two people are walking and they are relatively close to each other.
                        """.strip(),
        'prolog': r"""
                holdsFor(moving(P1,P2)=true, MI) :-
                    holdsFor(walking(P1)=true, WP1),
                    holdsFor(walking(P2)=true, WP2),
                    intersect_all([WP1,WP2], WI),
                    thresholds(movingThr, MovingThr),
                    holdsFor(close(P1,P2,MovingThr)=true, CI),
                    intersect_all([WI,CI], MI).
        """.strip(),
    },
    {
        'fluent_name': 'fighting',
        'description': """
                        Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the HAR events, the HAR input fluents, and the HAR background knowledge predicates. You may also use any of the HAR output fluents that you have already learned.
                        Composite Activity Description - “fighting”: This activity concerns two people. The activity lasts as long as two people are close to each other, at least one of them is moving abruptly, and the other is not inactive.
                        """.strip(),
        'prolog': r"""
                holdsFor(fighting(P1,P2)=true, FightingI) :-
                    holdsFor(abrupt(P1)=true, AbruptP1I),
                    holdsFor(abrupt(P2)=true, AbruptP2I),
                    union_all([AbruptP1I,AbruptP2I], AbruptI),
                    thresholds(fightingThr, FightingThr),
                    holdsFor(close(P1,P2,FightingThr)=true, CloseI),
                    intersect_all([AbruptI,CloseI], AbruptCloseI),
                    holdsFor(inactive(P1)=true, InactiveP1I),
                    holdsFor(inactive(P2)=true, InactiveP2I),
                    union_all([InactiveP1I,InactiveP2I], InactiveI),
                    relative_complement_all(AbruptCloseI, [InactiveI], FightingI).
        """.strip()
    }
]