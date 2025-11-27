# Example prompts for HAR composite activity definitions

har_examples = [
    {
        "input": """
Given a composite activity description, provide the rules in the language of RTEC.
Composite Activity Description - “leaving_object”: This activity concerns a person and an inanimate object. 
The activity starts when an object appears (i.e. the cameras start tracking the object) and at the same time a person is very close to the object.
The activity ends when the object disappears (i.e. the cameras stop tracking the object).
""",
        "output": """
The activity “leaving_object” can be expressed as a simple fluent with two arguments: a person and an object.
The initiation rule is defined by the appearance of the object and the condition that the person is close to it.
Once the object disappears, the fluent terminates.
The rules in the language of RTEC are as follows:
    ```prolog
    initiatedAt(leaving_object(Person, Object)=true, T) :-
        happensAt(appear(Object), T),
        holdsAt(close(Person, Object, 10)=true, T).
    
    terminatedAt(leaving_object(Person, Object)=true, T) :-
        happensAt(disappear(Object), T).
    ```
"""
    },
    {
        "input": """
Given a composite activity description, provide the rules in the language of RTEC.
Composite Activity Description - “moving”: This activity concerns two people.
The activity lasts as long as both people are walking and they remain relatively close to each other.
""",
        "output": """
The activity “moving” is expressed as a statically determined fluent with two arguments: Person1 and Person2.
The fluent holds for the time intervals when both persons are walking and are close together.
A possible specification in RTEC is:
    ```prolog
    holdsFor(moving(Person1, Person2)=true, I) :-
        holdsFor(walking(Person1)=true, I1),
        holdsFor(walking(Person2)=true, I2),
        intersect_all([I1, I2], I_inter),
        holdsFor(close(Person1, Person2, 20)=true, I_close),
        intersect_all([I_inter, I_close], I).
    ```
"""
    },
    {
        "input": """
Given a composite activity description, provide the rules in the language of RTEC.
Composite Activity Description - “fighting”: This activity concerns two people.
The activity lasts as long as the two people are close to each other, at least one of them is moving abruptly,
and the other is not inactive.
""",
        "output": """
The activity “fighting” is expressed as a statically determined fluent with two arguments, Person1 and Person2.
It holds during time intervals where the persons are close, at least one exhibits abrupt movement, and neither is standing still.
A suitable RTEC specification is:
    ```prolog
    holdsFor(fighting(Person1, Person2)=true, I) :-
        holdsFor(close(Person1, Person2, 5)=true, I_close),
        union_all([
            holdsFor(abrupt(Person1)=true, I_abr1),
            holdsFor(abrupt(Person2)=true, I_abr2)
        ], I_abr),
        % Ensure that at least one of the persons is not inactive
        not(holdsAt(inactive(Person1)=true, _)),
        not(holdsAt(inactive(Person2)=true, _)),
        intersect_all([I_close, I_abr], I).
    ```
"""
    }
]