from langchain_core.prompts import SystemMessagePromptTemplate

# Introduction for HAR composite activity definitions
system_HAR = SystemMessagePromptTemplate.from_template("""
Now, we will start with the generation of the composite activity definitions for human activity recognition (HAR).
First, we will present the events and input fluents.
Second, we will present the predicates expressing the background knowledge.
Third, we will provide the composite activity definitions in natural language and ask for their specification in the language of RTEC.
""")

# HAR events prompt
system_HAR_events = SystemMessagePromptTemplate.from_template("""
In addition to the built-in events of RTEC, you may use the following HAR events:

HAR - Event 1: appear(Id)
Meaning: The event “appear(Id)” takes place at the first time that entity “Id” is tracked by the cameras. “Id” may refer to a person or an inanimate object.

HAR - Event 2: disappear(Id)
Meaning: The event “disappear(Id)” takes place at the last time that entity “Id” is tracked by the cameras. “Id” may refer to a person or an inanimate object.
""")

# HAR input fluents prompt
system_HAR_fluents = SystemMessagePromptTemplate.from_template("""
You may also use the following HAR input fluents:

HAR - Input Fluent 1: coord(Id, X, Y) = true
Meaning: The coordinates of the tracked entity “Id” are “X” and “Y”. “Id” may refer to a person or an inanimate object.

HAR - Input Fluent 2: walking(P) = true
Meaning: A person “P” is walking.

HAR - Input Fluent 3: active(P) = true
Meaning: Non-abrupt body movement of person “P” in the same position.

HAR - Input Fluent 4: inactive(P) = true
Meaning: A person “P” is standing still.

HAR - Input Fluent 5: running(P) = true
Meaning: A person “P” is running.

HAR - Input Fluent 6: abrupt(P) = true
Meaning: A person “P” moves abruptly but his position in the global coordinate system does not change significantly.

HAR - Input Fluent 7: person(P) = true
Meaning: The tracked entity “P” is a person.

HAR - Input Fluent 8: close(Id1, Id2, DistanceThreshold) = true
Meaning: The distance between entities “Id1” and “Id2” does not exceed “DistanceThreshold” pixel positions.
""")

# HAR background knowledge prompt
system_HAR_BK = SystemMessagePromptTemplate.from_template("""
You may use a HAR background knowledge predicate named “thresholds” with two arguments.
The first argument refers to the threshold type and the second one to the threshold value.
Threshold values can be used to perform mathematical operations and comparisons.

HAR Background Knowledge - Predicate 1: thresholds(leavingObject, LeavingObjectThreshold)
Meaning: “LeavingObjectThreshold” expresses the maximum distance to consider that a person and an object are in contact.

HAR Background Knowledge - Predicate 2: thresholds(moving, MovingThreshold)
Meaning: “MovingThreshold” expresses the maximum gap distance between two people to be considered moving together.

HAR Background Knowledge - Predicate 3: thresholds(fighting, FightingThreshold)
Meaning: “FightingThreshold” expresses the maximum distance between two people involved in a fight.
""")

har_system_messages = [system_HAR, system_HAR_events, system_HAR_fluents, system_HAR_BK]