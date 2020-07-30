from enum import Enum
from rth.core.errors import UnreachableNetwork
from rth.virtual_building.utils import *
## @package ants
#
#  The package that contains all the Ants process, including Sweep and Discovery.


## An Enum of the possible states of an Ant
class AntState(Enum):
    Alive = 0
    Dead = 1
    Waiting = 2


## The main Ant class, little thing that allows us to "probe a network"
#
#  Basically, this class, used with the right system (in AntsDiscovery) allows to create readable and understandable
#  data from a mess of figures and strings.
class Ant:
    """
    The main Ant class.
    This class is used for a blind discovery through the virtual network we created, to see links between subnets and
    routers.

    Below,
        - Iteration is the move to the next router or subnet,
        - Explored is the fact a router or network has already been "visited" by an ant.
        - Possibility is an existing subnet or router that has already been explored or not.
    There are three cases each Iteration:
        - One Possibility, not Explored: the ant moves to the possibility and explores it, storing data into its history
        - One or several Possibilities, all Explored: the ant dies and leaves no children.
        - Several Possibilites, one or more not Explored: the ant dies and leaves as many children as there are
            Possibilites to explore. It also gives them the same history plus the possibility, meaning the child will
            "spawn" on the possibility the mother could not explore; Children may then continue exploring normally.
    """

    ##
    #  @param state The AntState state of the ant.
    #  @param pos A dictionary of the current position of the ant.
    def __init__(self, state: AntState, pos: dict):
        self.__state = state
        self.__pos = pos
        # { "subnets": [], "routers": [] }
        self._history = {"subnets": [pos["subnet"]], "routers": [pos["router"]]}

    @property
    def router(self):
        return self.__pos["router"]

    @property
    def subnet(self):
        return self.__pos["subnet"]

    @property
    def dead(self):
        return self.__state == AntState.Dead

    @property
    def alive(self):
        return self.__state == AntState.Alive

    @property
    def waiting(self):
        return self.__state == AntState.Waiting

    @property
    def state(self):
        return self.__state

    ## Kill the ant
    def kill(self):
        self.__state = AntState.Dead

    ## Activate (make alive) the ant
    def activate(self):
        self.__state = AntState.Alive

    ## Moves the ant to the given position
    #  @param pos The position
    def move_to(self, pos):
        hop_type = self.next_hop_type()
        self.__pos[hop_type] = pos
        self._history[f"{hop_type}s"].append(self.__pos[hop_type])

    ## Get the path the ant has taken
    def get_history(self):
        return self._history

    ## Feed the ant's history
    #  @param type_at The type the ant is at, either "routers" or "subnets"
    #  @param hist The history to feed
    def feed_history(self, type_at, hist):
        if type_at == "routers":
            self._history["routers"][0:0] = hist["routers"][:-1]
            self._history["subnets"][0:0] = hist["subnets"]
        elif type_at == "subnets":
            self._history["routers"][0:0] = hist["routers"]
            self._history["subnets"][0:0] = hist["subnets"][:-1]

    ## Returns what the next hop of the ant will be
    def next_hop_type(self):
        sub = self._history['subnets']
        rout = self._history['routers']

        if len(sub) > len(rout):
            # we expect to hop to a router
            return 'router'
        elif len(sub) == len(rout):
            # we expect to hop to a subnet
            return 'subnet'
        else:
            raise Exception("FindAnt history: Router length seems to be greater than subnets length; impossible")


## Ant that sweeps the network to verify all subnetworks are reachable
#
#  The sweep always starts from the subnetwork attached to the master router
class SweepAnt(Ant):

    def __init__(self, state: AntState, pos: dict):
        super().__init__(state, pos)

    ## Check if the next move could be possible
    def check_next_move(self, next_):
        hop_type = self.next_hop_type()

        return next_ not in self._history[f"{hop_type}s"]


## Ant that finds a path between two given subnetworks
class FindAnt(Ant):

    ##
    #  @param objective The UID of the subnetwork we want to reach
    def __init__(self, state: AntState, pos: dict, objective):
        super().__init__(state, pos)
        self.__objective = objective

    ## Whether the ant is on the objective
    def already_on_objective(self):
        return self.subnet == self.__objective

    ## Checks next move type
    #  Can return three different things, depending on if the path is a dead end, there are subnetworks left to explore
    #  here or we found the objective.
    def check_next_move(self, next_):
        hop_type = self.next_hop_type()

        if next_ not in self._history[f"{hop_type}s"]:
            if hop_type == 'subnet' and next_ == self.__objective:
                # means we are going to jump on the good subnet
                return [True, True]
            else:
                return [True, False]
        else:
            return [False, False]


## The class that runs all the process of Discovery
class AntsDiscovery:

    ##
    #  @param subnets The subnetworks data
    #  @param routers The routers data
    def __init__(self, subnets, routers, equitemporality=True, debug=False):
        # given basics
        self.subnets = subnets
        self.routers = routers
        self.equitemporality = True
        # made-up basics
        self.hops = {}
        self.links, self.subnets_table = self.prepare_matrix_and_links()
        self.master_router = get_master_router(self.routers)
        self.debug = debug

    ## Prepares the matrix and the links
    #  The matrix is made of tuples (s,e) with S being the UID of the starting subnetwork, and E the UID of the
    #  subnetwork to find.
    def prepare_matrix_and_links(self):

        # links
        links = {'subnets': {}, 'routers': {}}

        for s in range(len(self.subnets)):
            routers = self.subnets[s]['instance'].routers
            links['subnets'][s] = routers.keys()

        for s in range(len(self.routers)):
            nets = self.routers[s].connected_networks
            links['routers'][s] = nets.keys()

        # matrix
        matrix = []
        for start in range(len(self.subnets)):
            for end in range(len(self.subnets)):
                if start != end:
                    matrix.append([start, end])

        return links, matrix

    ##
    #  @param discovery_type Whether it is a sweep or a search.
    #  @param links The links prepared in the prepare_matrix_and_links function
    #  @param subnet_start The UID of the starting subnetwork
    #  @param subnet_end The UID of the objective (if we are searching for one, and not sweeping)
    #  @param debug The debug param, which you set to True to output a huge load of things processed
    @staticmethod
    def ants_discovery_process(discovery_type, links, subnet_start, subnet_end=None, debug=False):
        """
        This function is the core of the ants process.
        The labels in comments in the code below all refer to this section:

        INIT: we initialise as many ants as there are routers connected to the starting subnet
        PROCESS:
            1. Hop to next subnets
            2. Hop to next routers

                x.1 - If there is only a subnet, we then do test to see which case is here. For cases, see the Ant class
                    docstring for a full explanation of the different cases.
                x.2 - Several possibilities, we kill the ant and generate children

            3. "Cleaning up dead bodies": we delete the dead ants from the ants list

        RESULT: we then return what has to be returned
        """

        visited = {"subnets": [], "routers": []}
        routers, subnets = links['routers'], links['subnets']
        ants = []
        ants_at_objective = []

        def not_visited(type_, pos):
            return pos not in visited[type_]

        def visit(type_, pos):
            visited[type_].append(pos)

        def type_at_pos(type_, where):
            list_ = routers if type_ == 'subnets' else subnets
            return list_[where]

        def activate_ants():
            k = 0
            for ant_ in ants:
                if ant_.waiting:
                    k += 1
                    ant_.activate()
            return k

        # INIT
        for r in type_at_pos('routers', subnet_start):
            if discovery_type == 'sweep':
                ant = SweepAnt(AntState.Alive, {"router": r, "subnet": subnet_start})
            else:
                ant = FindAnt(AntState.Alive, {"router": r, "subnet": subnet_start}, subnet_end)
            ants.append(ant)
            visit('routers', r)

        visit('subnets', subnet_start)

        if debug:
            print("----- PROCESS START -----")

        # PROCESS
        while len(ants):

            if debug:
                print(f"┌────────────────────────────────────────────")
                print(f"│ Starting new round: {len(ants)} ants alive")
                print(f"│ Current visited state: ", visited)

            # Avoid recursion error
            if len(ants) > 100:
                raise RecursionError("Too many ants (>100). Aborting to avoid further problems.")

            # 1. Hop to next subnets
            if debug:
                print(f"├──────────────────────────────────────────")
                print(f"│ Commencing hop to next subnetwork. Activated {activate_ants()} ants "
                      f"({len(ants)} ants in total).")
                print(f"│ Current router pos / history:")
                for ant in ants:
                    print(f"│  - {id(ant)}: {ant.router} / {ant.get_history()}")
                print(f"│ Status:")
            else:
                activate_ants()

            for ant in ants:
                if not ant.alive:
                    continue

                subnets_at_pos = [s_ for s_ in routers[ant.router] if not_visited('subnets', s_)]

                if debug:
                    print(f"│  └ {id(ant)}: {subnets_at_pos}")

                # 1.1: One subnet
                if len(subnets_at_pos) == 0:
                    ant.kill()
                    if debug:
                        print(f"│    » DEAD | Already seen everything from this node")
                elif len(subnets_at_pos) == 1:
                    check = ant.check_next_move(subnets_at_pos[0])

                    if discovery_type == 'sweep':
                        # Special to the sweeping ant
                        if check is True:
                            # We can proceed to next subnet
                            ant.move_to(subnets_at_pos[0])
                            visit('subnets', subnets_at_pos[0])
                            if debug:
                                print(f"│    » ALIVE | Discovered network {subnets_at_pos[0]}")
                        elif check is False:
                            # we already went there
                            ant.kill()
                            if debug:
                                print(f"│    » DEAD | Found a dead end")
                        else:
                            raise Exception("Unexpected to happen at anytime")
                    else:
                        if check[0] is True and check[1] is True:
                            # We found the objective
                            # We stock ant history and kill the ant
                            ants_at_objective.append(ant.get_history()['routers'])
                            ant.kill()
                        elif check[0] is True and check[1] is False:
                            # We can proceed to next subnet
                            ant.move_to(subnets_at_pos[0])
                            visit('subnets', subnets_at_pos[0])
                        elif not check[0]:
                            # We went here
                            ant.kill()
                        else:
                            raise Exception("Unexpected to happen at anytime")

                # 1.2: Several subnets, kills and births
                else:
                    ant.kill()
                    if debug:
                        print(f"│    » DEAD | Found multiple possible paths. Giving birth to:")

                    for subnet_ in subnets_at_pos:
                        if not_visited('subnets', subnet_):
                            if discovery_type == 'sweep':
                                new_ant = SweepAnt(AntState.Waiting, {"router": ant.router, "subnet": subnet_})
                            else:
                                new_ant = FindAnt(AntState.Waiting, {"router": ant.router, "subnet": subnet_},
                                                  subnet_end)

                            new_ant.feed_history("routers", ant.get_history())
                            visit('subnets', subnet_)

                            if debug:
                                print(f"│      » {id(new_ant)} : discovered {subnet_}")

                            if isinstance(new_ant, FindAnt) and new_ant.already_on_objective():
                                ants_at_objective.append(new_ant.get_history()['routers'])
                                new_ant.kill()

                            ants.append(new_ant)

            # 2. Hop to next routers
            if debug:
                print(f"├──────────────────────────────────────────")
                print(f"│ Commencing hop to next router. Activated {activate_ants()} ants ({len(ants)} ants in total).")
                print(f"│ Current subnetwork pos / history:")
                for ant in ants:
                    print(f"│  - {id(ant)}: {ant.subnet} / {ant.get_history()}")
                print(f"│ Status:")
            else:
                activate_ants()

            for ant in ants:
                if not ant.alive:
                    continue

                routers_at_pos = [r for r in subnets[ant.subnet] if not_visited('routers', r)]

                if debug:
                    print(f"│  └ {id(ant)}: {routers_at_pos}")

                # 2.1: One router
                if len(routers_at_pos) == 0:
                    ant.kill()
                    if debug:
                        print(f"│    » DEAD | Already seen everything from this node")
                elif len(routers_at_pos) == 1:
                    check = ant.check_next_move(routers_at_pos[0])
                    if discovery_type == 'sweep':
                        if check is True:
                            ant.move_to(routers_at_pos[0])
                            visit('routers', routers_at_pos[0])

                            if debug:
                                print(f"│    » ALIVE | Discovered router {routers_at_pos[0]}")
                        elif check is False:
                            ant.kill()
                            if debug:
                                print(f"│    » DEAD | Found a dead end")
                        else:
                            raise Exception("Unexpected to happen at anytime")
                    else:
                        if check[0] is True:
                            ant.move_to(routers_at_pos[0])
                            visit('routers', routers_at_pos[0])
                        elif check[0] is False:
                            ant.kill()
                        else:
                            raise Exception("Unexpected to happen at anytime")

                # 2.2: Several routers, kills and births
                else:
                    ant.kill()

                    if debug:
                        print(f"│    » DEAD | Found multiple possible paths. Giving birth to:")
                    for router in routers_at_pos:
                        if not_visited('routers', router):
                            if discovery_type == 'sweep':
                                new_ant = SweepAnt(AntState.Waiting, {"router": router, "subnet": ant.subnet})
                            else:
                                new_ant = FindAnt(AntState.Waiting, {"router": router, "subnet": ant.subnet}, subnet_end)
                            new_ant.feed_history("subnets", ant.get_history())

                            visit('routers', router)
                            if debug:
                                print(f"│      » {id(new_ant)} : discovered {router}")

                            ants.append(new_ant)

            # 3. Cleaning up dead bodies
            if debug:
                print(f"├──────────────────────────────────────────")
                print(f"│ Removing dead ants. Total ants: {len(ants)}")

            for i in reversed(range(len(ants))):
                if debug:
                    print(f"│   » {id(ants[i])}: {ants[i].state}")
                if ants[i].dead:
                    ants.remove(ants[i])

            if debug:
                print(f"│ Ants remaining : {len(ants)}")
                print(f"└──────────────────────────────────────────")

        # RESULT
        if debug:
            print("Final state: ", visited)
            print("----- PROCESS END -----")

        return visited, ants_at_objective

    ## Sweeps the network
    def sweep_network(self):
        """
        We sweep the network from the master router and try to reach every subnetwork.
        This function is a suicider, as to say it will die by raising an error if any subnet is unreachable; else the
        program will continue
        """

        master = self.master_router
        subnet_start = list(self.routers[master].connected_networks.keys())[0]

        result, _ = self.ants_discovery_process('sweep', self.links, subnet_start, debug=self.debug)

        for subnet in self.subnets:
            if subnet not in result['subnets']:
                inst = self.subnets[subnet]['instance']
                total = len(self.subnets) - len(result['subnets'])
                raise UnreachableNetwork(inst.name, inst.cidr, total)

    ## Calculates the hops (path) for each tuple of the matrix
    def calculate_hops(self):
        """
        We calculate the hops for each matrix entry, and either keep the smallest one if there is
        equitemporality, or store each hop for further analysis and calculus by another function
        """

        for i in range(len(self.subnets_table)):
            matrix = self.subnets_table[i]
            s, e = matrix

            _, at_objective = self.ants_discovery_process('find', self.links, s, e, debug=self.debug)

            if self.debug:
                print(f"matrix {matrix}: ", at_objective)

            # If equitemporality is set to False, we take all the paths to calculate later
            if self.equitemporality:
                # Test if there are different paths, and pick the smaller one
                if len(at_objective) == 1:
                    # only one path found
                    self.hops[(s, e)] = at_objective[0]
                else:
                    self.hops[(s, e)] = smaller_of_list(at_objective)
            else:
                self.hops[(s, e)] = at_objective
