# Introduction
This contains the algorithm to stitch trips returned from multiple service providers into one single journey.

# Release notes

# Terms



1. **Vertex** is a Stop
2. **Edge** is a directed route between 2 Stops
    1. required attributes of an edge
        1. _edge_length_: Length of the edge (distance in kms for example)
        2. _edge_duration_: Time-to-traverse the length (time in hours for example)
    2. optional attributes of the edge
        3. _edge_cost_: Cost (INR) of using a mobility service to traverse the edge 
3. **MissingLink**: It is also an edge. It is defined as a route that doesn’t exist yet (or has not been instantiated aka not serviced by any MSP at the given iteration). There exists a heuristic to estimate the required edge attributes.
4. **Path**: It is a route connecting two vertices with zero or more vertices (stops) in between. A Path **_may contain _**a MissingLink. A MissingLink is treated as a transfer if it appears in a path. All Paths are simple Paths, no vertex is revisited again.
5. **Legal Path**: A path that meets the criteria specified the client (who is requesting a path)
6. **Transfer**: A self-commutable MissingLink. In other words, a pair of vertices for which there is no service provider, can still appear in a legal path.
7. **(Origin, Destination)**: A tuple of vertices that represent a route between them. Both Origin and Destination will have the following attributes:
    3. **Origin**
        4. Expected Departure Time
        5. Departure Buffer Time
        6. Latitude, Longitude
    4. **Destination**
        7. Expected Arrival Time
        8. Arrival Buffer Time
        9. Latitude, Longitude

# Inputs



1. A pair of vertices S and D for which path(s) needs to be found from S to D. 
2. Graph G with vertices V and edges E. V and E can be empty or they can be loaded from prior knowledge of Beckn Gateway (such as cached routes or published public transport schedules)
3. StoppingCriteria. Apply rules S1-S3 (see below)

# Outputs



1. Return a ranked list of **legal paths** between S and D

## Requires:

### Mandatory:  



1. There exists <span style="text-decoration:underline;">GetRoutes</span> API, which when given a list of origin, destination pairs,

    returns a list of serviceable origin, destination pairs.


    Example:


        routes ←   GetRoutes( [(origin,destination),(origin,destination)])


### Optional:  


    A set of existing routes 

**RuleBase (Rules to configure the algorithm behaviour)**

E1. _edge_length _is greater than _threshold (kms)_

E2. _edge_duration _is greater than _threshold (hours/minutes)_

E3. _edge_cost _is greater than _threshold (INR)_

E4. _edge_centrality _is less than _threshold (%)_

P1. _path_length _is greater than _threshold (kms)_

P2. _path_duration _is greater than _threshold (hours/minutes)_

P3. _path_cost _is greater than _threshold (INR)_

P4. _path_num_transfer _is greater than _threshold (positive integer)_

_	_S1. _stop_num_iterations _is greater than _threshold (positive integer)_

S2. _stop_run_time_limit _is greater than _threshold (milliseconds)_

S3. _stop_num_paths_found _is greater than _threshold (positive integer)_

## New Rules



1. New atomic rules can be added to the RuleBase.
2. New Compound Rules can be obtained by combining the above atomic rules via conjunction (AND ⋀), disjunction (OR ⋁) and negation (NOT ⌐), and by defining new relations. 

    Example:  ⌐E1 ⋀ (E2 ⋁ E3)

3. A set of rules are collectively represented as E* or P* or S*

	

# Algorithm Main Block


---

**Initialize: **


    timeStep ←  0


    V ← [S,D], E ← empty, journeys ← empty


    G ←  CreateGraph(V,E)


    missingLinks ← [(S,D)]

**Do until StoppingCriteria is met:**


    routes ←  GetRoutes(missingLinks)


    G ←  UpdateGraph(G,routes)


    journeys ← FilterRankSelectJourneys(G)

missingLinks ← FilterRankSelectMissingLinks(G)


    timeStep ← timeStep+1

**Return** journeys

---


**Algorithm Subroutines**

---


**FUNCTION FilterRankSelectMissingLink:**

For every (i,j)<sup>th</sup> pair of vertices in G that is a missing link**:**

	 d<sub>ij <strong>← </strong></sub>Assign _edge_length_ via a heuristic (such as Euclidean distance between


    two vertices based on latitude, longitude

d ← Filter(d)

	Filter all missing links, by applying E1 or some function of E*

	d ← Rank(d)

	Rank all missing links, by applying rules E*

d ← Select(d)

	Select top K  missing links

**FUNCTION FilterRankSelectJourneys():**

Update path attributes of all paths between (S,D) in G

p ← Filter(p)

	Filter paths, by applying P1 or some function of P*

	p ← Rank(p)

	Rank paths, by applying rules P*

p ← Select(p)

	Select top K  paths

**Return **p

**FUNCTION UpdateGraph(G):**

For every (origin, destination) pair:



* Add origin, destination to V, if they are distinct w.r.t every vertex attribute from

    existing Vertices. For example, the stops may be the same, but they are serviced


    by another MSP.

* Add an edge between that pair to V, with edge attributes computed based 

    (origin, destination) pairs provided by the MSP.


**Return G**



# Comments



1. A legal path can be defined by specifying the properties that a path needs to satisfy. Only legal paths will be shown to the client. Examples ( ⌐P4 ⋀ ⌐ML2) => (!P4 && !ML2)
    1. [Rule: ⌐P4]: Path can not have more than three transfers 
    2. [Rule: ⌐ML2]: Each transfer can not have more than 20mins of travel time
2. At time step  “t”, Stitcher, 
    3. determines the best subset of MissingLinks, which when converted to routes, as many illegal paths can be turned into legal paths. Some of the existing legal paths can be made better (in the sense of time, distance, for example)
    4. calls _GetRoutes_ API to MSP with the best subset found above. MSPs respond by sending a list of (origin, destination) pairs
    5.  calls **AllPaths** or some variant to update the journeys with the new available routes
    6. selects a best subset of the journeys and presents it to the client
    7. adds paths with at most “t” transfers
    8. progressively refines Journeys. 
3. Heuristics guide the search path towards the goal (reach **D** from **S**).  Otherwise, with every subsequent call to _GetRoutes_, the search frontiers can expand and explode in all directions.
4. The Algorithm has a flavor of **A*** algorithm in the sense that path cost is a function of observed path cost (contributed by edges) plus heuristics path cost (contributed by MissingLinks) when finding the shortest path. Heuristics are used to estimate the MissingLink cost to figure out whether the MissingLinks are worth getting converted into a route.
5. The FilterRankSelectTransfers can be modified to include an explore-vs-exploit strategy.
6. At each iteration, a call is made to **AllPaths** algorithm, which for a given pair of vertices, finds the cost of all paths. We do not need to run AllPaths at each iteration -- some paths will not get updated and they can be cached.
7. If the heuristic underestimates the true cost between a pair of vertices, then **Stitcher** will find the optimal path. Under these conditions, **Stitcher is complete.**
8. Stitcher’s time and space complexity can be controlled by choosing an optimized implementation fo AllPaths or k-simple-paths problem (see [this](https://arxiv.org/pdf/1610.06934.pdf) reference for example)
9. Efficient Data Structures can be used to optimize the performance. For example, one could use priority `ques` for storing both MissingLinks and Journeys. At each iteration, the priorities get updated based on the filtering & ranking criteria, and they will pop’d based on the selection criteria. The selection criteria removes (pops) those MissingLinks from `MissingLink Que` and updates the `Journeys Que`. 
10. **Stitcher **is a non-opinionated sketch and not a reference implementation.



# Appendix



1. Core elements - Vertices, Edges, MissingLinks
    1. **Vertex** is a Stop
    2. **Edge** is a route between 2 stops
        1. Core Attributes of the edge
            1. Length of the edge (distance in KMs for example)
            2. Time to traverse the length (time in hours for example)
        2. Non core attributes of the edge
            3. Cost of using a mobility service to traverse the edge 
    3. **MissingLink**: It is an edge. It is defined as a route that doesn’t exist (or has not been instantiated) yet (aka not serviced by any MSP at the given iteration)
        3. Algorithm’s Goal is to convert missing links to routes
    4. A blueprint of the direction (direction graph) - this is achieved by the ordering of the stops that specify a particular edge
2. Moving from source vertex **S** (an Origin Stop) to destination vertex **D** (a Destination Stop)
3. Parameters of an Origin Stop (vertex)
    5. Expected departure time
    6. Departure Buffer time
    7. Latitude, Longitude
4. Parameters of a Destination Stop (vertex)
    8. Expected arrival time
    9. Arrival Buffer time
    10. Latitude, Longitude
    11. Note: There are buffer times for both arrival and departure, unlike the german reference paper which only had buffer time at departure
5. Databases
    12. AllPaths - list of all paths between **S** and **D**
        4. Includes missing links, transfers, trips
    13. MissingLinks - 
        5. List of all missing links
    14. Transfer
        6. Is of type missing link
        7. Is self-commutable (this has to be defined by a heuristic)
    15. Rule Base
6. For each edge, do the following:
    16. Is the edge a route (that is, is it being served)
    17. If yes, label as route
    18. If no
        8. Label as missinlink
        9. Is missinglink self-commutable
            4. If yes, label as transfer
            5. If no, retain missing link label (do nothing)
7. At t=0
    19. There is a source S
    20. There is a target T
    21. Pre-existing nodes are concretized (eg: public transport stops)
    22. Algo fires GetRoutes(S, T) to MGP, not to MSP
8. At t=1
    23. MGP fires GetRoutes(S, T) to MSPs, updates Journeys
9. How to rank which missinglink to be prioritized for conversion into a route. Parameters:
    24. How many routes does a missinglink impact
    25. Net reduction in travel time
        10. Every missing link has a heuristic (thum brule) - could be based on lat, long
    26. Net reduction in distance
10. Ranking criteria for journeys. Parameters :
    27. Journey length
    28. Journey time
    29. Number of transfers
    30. Total transfer length
    31. Total transfer time
    32. Total number of missinglinks
    33. Total length of missing links 
    34. Total traversal time fo missing links
11. Journey Algo types - Multi Objective Journey Optimation (MOJO)
    35. More than one of the below objectives can be tested at one iteration
    36. least number of transfers
    37. Least number of missinglinks
    38. smallest value of total travel lengths
12. Iteration 2
    39. ASK MSPs for mobility service in missing links (repeat above steps)
13. When does the Algo stop?
    40. Do until
        11. Outcomes based: Eg: Until 5 full journeys are completed or number of transfer is five
        12. Event driven
            6. Internal Event-driven: Eg: MissingLink array is empty
            7. External Event based: Eg: MGP interrupts the algo
        13. Time-out: Until 5 seconds (whether or not MSPs respond fully or partially or not at all)


