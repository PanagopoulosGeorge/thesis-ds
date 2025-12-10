# examples = [
#     {"input": "2+2", "output": "4"},
#     {"input": "2+3", "output": "5"},
# ]

simple_fluent_examples = [
    {"input": r"""Given a composite maritime activity description, provide the rules in the language of RTEC.
                 Composite Maritime Activity Description: “withinArea”. 
                 This activity starts when a vessel enters an area of interest. 
                 The activity ends when the vessel leaves the area that it had entered, 
                 or when the vessel stops transmitting its position, 
                 since we can no longer assume that the vessel remains in the same area 
                 in the case of transmission gaps.
                 """,
     "output": r"""
 The activity “withinArea” is expressed as a Boolean simple fluent with two arguments, i.e., “Vessel” and “AreaType”. 
 This activity starts when a vessel enters an area of interest. 
 We use an "initiatedAt" rule to express this initiation condition. 
 The body literals of this rules are an event labelled “entersArea” with two arguments, “Vessel” and “Area”, 
 and a background knowledge predicate named “areaType” with two arguments, 
 “Area” and “AreaType”. This rule in the language of RTEC is the following:
    ```prolog
    initatedAt(withinArea(Vessel, AreaType)=true, T) :-
        happensAt(entersArea(Vessel, Area), T),
        areaType(Area, AreaType).
    ```
The activity “withinArea” ends when a vessel leaves the area that it had entered. 
We use a “terminatedAt” rule to describe this termination condition. 
This rule includes an event named “leavesArea” with two arguments, i.e. “Vessel” and “Area”, 
and the background knowledge predicate “areaType”. This rule in the language of RTEC language is:
    ```prolog
    terminatedAt(withinArea(Vessel, AreaType)=true, T) :-
        happensAt(leavesArea(Vessel, Area), T),
        areaType(Area, AreaType).
    ```

In addition to the aforementioned conditions, the activity “withinArea” ends when the vessel 
stops transmitting its position, i.e. when a communication gap starts. 
We use a “terminatedAt” rule to express this termination condition. 
In this rule, the second argument of the “withinArea” fluent is a ‘free’ Prolog variable, 
i.e. a variable starting with ‘_’. The body of this rule includes a single event 
named “gap_start” with one argument, i.e. “Vessel”. This rule in the language of RTEC is:
    ```prolog
    terminatedAt(withinArea(Vessel, _AreaType)=true, T) :-
        happensAt(gap_start(Vessel), T).
    ```

     """},
    {"input": r"""
Given a composite maritime activity description, provide the rules in the language of RTEC.
Composite Maritime Activity Description: “stopped”. 
This activity starts when a vessel becomes idle near some port or far from all ports. 
The activity ends when the vessel stops being idle, i.e., when it starts to move. 
When there is a gap in signal transmissions, we can no longer assume that the vessel remains stopped.
                 """,
     "output": r"""
The activity “stopped” is expressed as a simple fluent. 
This activity starts when a vessel becomes idle near some port. 
We use an “initiatedAt” rule to describe this initiation condition. 
The output is the fluent “stopped”, which has one argument, i.e. “Vessel”, and value “nearPorts”. 
The “initiatedAt” rule includes an event named “stop_start” with one argument, i.e. “Vessel”. 
We verify that the vessel is currently near some port by requiring that the fluent-value pair “withinArea(Vessel, nearPorts)=true” must hold. 
This condition refers to the activity “withinArea”, which was learned in a previous example. 
This rule in the language of RTEC is:
    ```prolog
    initiatedAt(stopped(Vessel)=nearPorts, T) :-
        happensAt(stop_start(Vessel), T),
        holdsAt(withinArea(Vessel, nearPorts)=true, T).
    ```
The activity “stopped” may also start when a vessel becomes idle far from all ports. 
In this case, the “stopped” fluent has value “farFromPorts”. 
We use an “initiatedAt” rule to express this initiation condition. 
The body of this rule includes an event named “stop_start” with one argument, i.e. “Vessel”. 
We verify that the vessel is currently far from all ports by requiring that the fluent-value pair “withinArea(Vessel, nearPorts)=true” does not hold. 
This rule in the language of RTEC is:
    ```prolog
    initiatedAt(stopped(Vessel)=farFromPorts, T) :-
        happensAt(stop_start(Vessel), T),
        not holdsAt(withinArea(Vessel, nearPorts)=true, T).
    ```

The activity “stopped” ends when a vessel stops being idle, irrespective of the location of the vessel. 
We use a “terminatedAt” rule to express this termination condition. 
Moreover, we use a free Prolog variable to express the value of the “stopped” fluent, called “_Status”, 
i.e. we place no constraints on the value of the “stopped” fluent. 
The “terminatedAt” rule includes a single event named “stop_end” with one argument, i.e. “Vessel”. 
This rule in the language of RTEC is:

    ```prolog
    terminatedAt(stopped(Vessel)=_Status, T) :-
        happensAt(stop_end(Vessel), T).
    ```
The activity “stopped” may also end when a communication gap starts. 
We use a “terminatedAt” rule to express this termination condition. 
This rule includes the built-in “start” event of RTEC, which expresses the start times of the maximal intervals of a given fluent-value pair. 
In this case, the “start” event is applied to the gap fluent, expressing the times at which 
a communication gap for the vessel in question starts. This rule in the language of RTEC is:
    ```prolog
    terminatedAt(stopped(Vessel)=_Status, T) :-
        happensAt(start(gap(Vessel)=_GapStatus), T).
    ``` 
     """}
]

static_fluent_examples = [
    {"input": r"""
Given a composite maritime activity description, provide the rules in the language of RTEC.
Composite Maritime Activity Description: “underWay”. This activity lasts as long as a vessel is not stopped.
""",
     "output": r"""
The activity “underWay” is expressed as a statically determined fluent. 
Rules with “holdsFor” in the head specify the conditions in which a fluent holds. 
We use a “holdsFor” rule to describe that the “underWay” activity lasts as long as a vessel is not stopped. 
The output is Βoolean fluent named “underWay” with one argument, i.e. “Vessel”. 
We specify “underWay” with the use of the fluent “movingSpeed”. 
We express “underWay” as the disjunction of the three values of “movingSpeed”, 
i.e. “below”, “normal” and “above”. Disjunction in “holdsFor” rules is expressed by means of “union_all”. 
This rule is expressed in the language of RTEC as follows:
    ```prolog
    holdsFor(underWay(Vessel)=true, I) :-
        holdsFor(movingSpeed(Vessel)=below, I1),
        holdsFor(movingSpeed(Vessel)=normal, I2),
        holdsFor(movingSpeed(Vessel)=above, I3),
        union_all([I1,I2,I3], I).
    ```
     """},
    {"input": r"""
Given a composite maritime activity description, provide the rules in the language of RTEC.
Composite Maritime Activity Description: “rendezVous”: This activity lasts as long as two vessels 
are close to each other, their speed is low and they are far from the coastline. 
Furthermore, neither of the two vessels should be a tug boat or a pilot vessel. 
We are interested in vessel meetings whose duration exceeds the expected minimum time required 
for a suspicious action, like an illegal cargo transfer.
""",
     "output": r"""
The activity “rendezVous” is expressed as a statically determined fluent. 
We use a “holdsFor” rule to describe that the “rendezVous” activity lasts as long as two vessels, 
neither of which is a tug boat or a pilot vessel, are both sailing at a low speed or are stopped 
far from all ports, while neither of them is close to a port or a coastline. 
The output is a Boolean fluent named “rendezVous” with two arguments, i.e. “Vessel1” and “Vessel2”. 
To express that the two vessels must be close to each other, we use a Boolean fluent named “proximity” with two arguments, i.e. “Vessel1” and “Vessel2”. 
To express that neither of the vessels is a tug boat or a pilot vessel, we use a background knowledge predicate named “oneIsTug” with two arguments, 
i.e. “Vessel1” and “Vessel2”, and a background knowledge predicate named “oneIsPilot” with two arguments, i.e. “Vessel1” and “Vessel2”, 
and require that these predicates do not hold using “not”. To express that “Vessel1” has a low speed 
or it is stopped far from all ports, we use the predicate “union_all”. 
Similarly, we employ “union_all” to express that “Vessel2” has a low speed or it is stopped far from all ports. 
Next, we use the predicate “intersect_all” to express the conjunction of these two events, 
i.e., that both vessels need to have a low speed or be stopped far from all ports. 
Subsequently, we need to express that neither of the two vessels is near a port or a coastline at this time. 
To do this, we employ the predicate “relative_complement_all”, in order to exclude the situations 
where “Vessel1” is near a port, “Vessel1” is near a coastline, “Vessel2” is near a port or “Vessel2” is near a coastline. 
Finally, we need to express that the duration of the activity is greater than the minimum expected duration of a rendez-vous among vessels. 
To do this, we use the background knowledge predicate “thresholds” to retrieve this minimum duration from background knowledge and store it in the variable “RendezvousTime”. 
Then, we use the background knowledge predicate “intDurGreater” in order to filter the intervals that have been computed so far, maintaining only the ones whose duration exceeds “RendezvousTime”. 
This rule in RTEC language is:
```prolog
    holdsFor(rendezVous(Vessel1, Vessel2)=true, I) :-
        holdsFor(proximity(Vessel1, Vessel2)=true, Ip),
        not oneIsTug(Vessel1, Vessel2),
        not oneIsPilot(Vessel1, Vessel2),
        holdsFor(lowSpeed(Vessel1)=true, Il1),
        holdsFor(lowSpeed(Vessel2)=true, Il2),
        holdsFor(stopped(Vessel1)=farFromPorts, Is1),
        holdsFor(stopped(Vessel2)=farFromPorts, Is2),
        union_all([Il1, Is1], I1b),
        union_all([Il2, Is2], I2b),
        intersect_all([I1b, I2b, Ip], If), If\=[],
        holdsFor(withinArea(Vessel1, nearPorts)=true, Iw1),
        holdsFor(withinArea(Vessel2, nearPorts)=true, Iw2),
        holdsFor(withinArea(Vessel1, nearCoast)=true, Iw3),
        holdsFor(withinArea(Vessel2, nearCoast)=true, Iw4),
        relative_complement_all(If,[Iw1, Iw2, Iw3, Iw4], Ii),
        thresholds(rendezvousTime, RendezvousTime),
        intDurGreater(Ii, RendezvousTime, I).
    ```
     """}
]