

system_MSA = """
Now, we will start with the generation of the composite activity definitions for maritime situational awareness (MSA). 
First, we will present the events and input fluents. 
Second, we will present the predicates expressing the background knowledge. 
Third, we will provide the composite activity definitions in natural language and ask for their specification in the language of RTEC.
"""

system_MSA_events = """
In addition to the built-in events of RTEC, you may use the following MSA events:

MSA - Event 1: change_in_speed_start(Vessel)
Meaning: “Vessel” started changing its speed.

MSA - Event 2: change_in_speed_end(Vessel)
Meaning: “Vessel” stopped changing its speed.

MSA - Event 3: change_in_heading(Vessel)
Meaning: “Vessel” changed its heading.

MSA - Event 4: stop_start(Vessel)
Meaning: “Vessel” started being idle.

MSA - Event 5: stop_end(Vessel)
Meaning: “Vessel” stopped being idle.

MSA - Event 6: slow_motion_start(Vessel)
Meaning: “Vessel” started moving at a low speed.

MSA - Event 7: slow_motion_end(Vessel)
Meaning: “Vessel” stopped moving at a low speed.

MSA - Event 8: gap_start(Vessel)
Meaning: “Vessel” stopped sending position signals.

MSA - Event 9: gap_end(Vessel)
Meaning: “Vessel” resumed sending position signals.

MSA - Event 10: entersArea(Vessel,AreaID)
Meaning: “Vessel” enters an area with id “AreaID”.

MSA - Event 11: leavesArea(Vessel,AreaID)
Meaning: “Vessel” leaves an area with id “AreaID”.

MSA - Event 12: velocity(Vessel,Speed,CourseOverGround,TrueHeading)
Meaning: “Vessel” is moving with velocity “Speed”, while it is moving in the direction indicated by angle “CourseOverGround”, 
and its bow is pointing in the direction indicated by angle “TrueHeading”.

Prompt MSA-Fluents:
You may also use the following MSA input fluent:

MSA - Input Fluent 1: proximity(Vessel1, Vessel2) = true
Meaning: “Vessel1” and “Vessel2” are close to each other.
"""

system_MSA_BK = """
You may use a MSA background knowledge predicate named “thresholds” with two arguments. 
The first argument refers to the threshold type and the second one to the threshold value. 
Threshold values can be used to perform mathematical operations and comparisons.

MSA Background Knowledge - Predicate 1: thresholds(hcNearCoastMax,HcNearCoastMax)
Meaning: The maximum sailing speed that is safe for a vessel to have in a coastal area.

MSA Background Knowledge - Predicate 2: thresholds(adriftAngThr,AdriftAngThr)
Meaning: The maximum angle difference between the actual direction of a vessel and the direction of its bow for which we consider that the vessel is not drifting.

MSA Background Knowledge - Predicate 3: thresholds(aOrMTime,AOrMTime)
Meaning: The maximum temporal extent during which a vessel may be idle without being considered anchored or moored.

MSA Background Knowledge - Predicate 4: thresholds(trawlspeedMin,TrawlspeedMin)
Meaning: The minimum speed of a vessel engaged in a trawling activity.

MSA Background Knowledge - Predicate 5: thresholds(trawlspeedMax,TrawlspeedMax)
Meaning: The maximum speed of a vessel engaged in a trawling activity.

MSA Background Knowledge - Predicate 6: thresholds(tuggingMin,TuggingMin)
Meaning: The minimum speed of a vessel engaged in a tugging operation.

MSA Background Knowledge - Predicate 7: thresholds(tuggingMax,TuggingMax)
Meaning: The maximum speed of a vessel engaged in a tugging operation.

MSA Background Knowledge - Predicate 8: thresholds(tuggingTime,TuggingTime)
Meaning: The minimum duration of a tugging operation.

MSA Background Knowledge - Predicate 9: thresholds(movingMin,MovingMin)
Meaning: The minimum speed of a moving vessel.

MSA Background Knowledge - Predicate 10: thresholds(movingMax,MovingMax)
Meaning: The maximum speed of a moving vessel.

MSA Background Knowledge - Predicate 11: thresholds(sarMinSpeed,SarMinSpeed)
Meaning: The minimum speed of a vessel engaged in a search-and-rescue (SAR) operation.

MSA Background Knowledge - Predicate 12: thresholds(trawlingTime,TrawlingTime)
Meaning: The minimum duration of a trawling activity.

MSA Background Knowledge - Predicate 13: thresholds(loiteringTime,LoiteringTime)
Meaning: The minimum duration of a loitering activity.

MSA Background Knowledge - Predicate 14: typeSpeed(Type,Min,Max,Avg)
Meaning: The minimum, maximum, and average speed of each vessel type.

MSA Background Knowledge - Predicate 15: vesselType(Vessel,Type)
Meaning: The vessel type of each vessel.
"""