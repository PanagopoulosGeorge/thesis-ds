har_requests = [
    """
Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the HAR events, the HAR input fluents, and the HAR background knowledge predicates. You may also use any of the HAR output fluents that you have already learned.

Composite Activity Description - “leaving_object”: This activity concerns a person and an inanimate object. The activity starts when an object ‘appears’, i.e. the cameras start tracking the object, and at the same time a person is very close to the object. The activity ends when an object ‘disappears’, i.e. the cameras stop tracking the object.
""",
    """
Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the HAR events, the HAR input fluents, and the HAR background knowledge predicates. You may also use any of the HAR output fluents that you have already learned.

Composite Activity Description - “moving”: This activity concerns two people. The activity lasts as long as two people are walking and they are relatively close to each other.
""",
    """
Given a composite activity description, provide the rules in the language of RTEC. You may use the built-in events of RTEC, the HAR events, the HAR input fluents, and the HAR background knowledge predicates. You may also use any of the HAR output fluents that you have already learned.

Composite Activity Description - “fighting”: This activity concerns two people. The activity lasts as long as two people are close to each other, at least one of them is moving abruptly, and the other is not inactive.
"""
]