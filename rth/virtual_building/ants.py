from enum import Enum
from rth.core.errors import UnreachableNetwork
from rth.virtual_building.utils import *
## @package ants
#
#  The package that contains all the Ants process, including Sweep and Discovery.


class AntState(Enum):
    """
    An Enum of the possible states of an Ant
    """

    Alive = 0
    Dead = 1
    Waiting = 2


class Ant:
    """
    The main Ant class, little thing that allows us to build virtual paths in a virtual environment

    This class is used for a blind discovery through the virtual network we created, to see links between subnets and
    routers.

    Below,
        - "Iteration" is the move to the next router or subnet,
        - "Explored" is the fact a router or network has already been "visited" by an ant.
        - "Possibility" is an existing subnet or router that has already been explored or not.
    There are three cases each Iteration:
        - One Possibility, not Explored: the ant moves to the possibility and explores it, storing data into its history
        - One or several Possibilities, all Explored: the ant dies and leaves no children.
        - Several Possibilites, one or more not Explored: the ant dies and leaves as many children as there are
            Possibilites to explore. It also gives them the same history plus the possibility, meaning the child will
            "spawn" on the possibility the mother could not explore; Children may then continue exploring normally.
    """

    def __init__(self, state: AntState, pos: dict):
        """
        Init the Ant

        Args:
            state: The AntState state of the ant.
            pos: A dictionary of the current position of the ant.
        """

        self.__state = state
        self.__pos = pos
        # { "subnets": [], "routers": [] }
        self._history = {"subnets": [pos["subnet"]], "routers": [pos["router"]]}

    @property
    def router(self):
        """
        Returns:
            The current router of the Ant.
        """
        return self.__pos["router"]

    @property
    def subnet(self):
        """
        Returns:
            The current router of the Ant.
        """
        return self.__pos["subnet"]

    @property
    def dead(self):
        """
        Returns:
            True if the Ant is Dead, else False
        """
        return self.__state == AntState.Dead

    @property
    def alive(self):
        """
        Returns:
            True if the Ant is Alive, else False
        """
        return self.__state == AntState.Alive

    @property
    def waiting(self):
        """
        Returns:
            True if the Ant is Waiting, else False
        """
        return self.__state == AntState.Waiting

    @property
    def state(self):
        """
        Returns:
            The current state of the Ant.
        """
        return self.__state

    def kill(self):
        """
        Kill the ant.

        Sets the ant state to Dead.
        """
        self.__state = AntState.Dead

    ## Activate (make alive) the ant
    def activate(self):
        self.__state = AntState.Alive

    def move_to(self, pos):
        """
        Moves the ant to the given position

        Args:
            pos: The position
        """

        hop_type = self.next_hop_type()
        self.__pos[hop_type] = pos
        self._history[f"{hop_type}s"].append(self.__pos[hop_type])

    def get_history(self):
        """
        Get the path the ant has taken
        """
        return self._history

    def feed_history(self, type_at, hist):
        """
        Feed the ant's history

        Args:
            type_at: The type the ant is at, either "routers" or "subnets"
            hist: The history to feed
        """

        if type_at == "routers":
            self._history["routers"][0:0] = hist["routers"][:-1]
            self._history["subnets"][0:0] = hist["subnets"]
        elif type_at == "subnets":
            self._history["routers"][0:0] = hist["routers"]
            self._history["subnets"][0:0] = hist["subnets"][:-1]

    def next_hop_type(self):
        """
        Determines what the next hop of the ant will be

        Returns:
            Either 'router' or 'subnet'

        Raises:
            Exception: if there is more routers seen than subnetworks (this Exception should NEVER be thrown)
        """

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


class SweepAnt(Ant):
    """
    Ant that sweeps the network to verify all subnetworks are reachable

    The sweep always starts from the subnetwork attached to the master router
    """

    def __init__(self, state: AntState, pos: dict):
        super().__init__(state, pos)

    def check_next_move(self, next_):
        """
        Check if the next move could be possible

        Args:
            next_: The UID of the next hop
        """

        hop_type = self.next_hop_type()

        return next_ not in self._history[f"{hop_type}s"]


class FindAnt(Ant):
    """
    Ant that finds a path between two given subnetworks
    """

    def __init__(self, state: AntState, pos: dict, objective):
        """
        Init

        Args:
            state: The AntState of the Ant
            pos: The starting position
            objective: The UID of the objective subnetwork
        """

        super().__init__(state, pos)
        self.__objective = objective

    def already_on_objective(self):
        """
        Returns:
            Whether the ant is on the objective
        """
        return self.subnet == self.__objective

    def check_next_move(self, next_):
        """
        Checks next move type

        Can return three different things, depending on if the path is a dead end, there are subnetworks left to explore
        here or we found the objective.

        Args:
            next_: The UID of the next hop

        Returns:
            A tuple that can be either [True, True], [True, False] or [False, False] depending on the environment
        """

        hop_type = self.next_hop_type()

        if next_ not in self._history[f"{hop_type}s"]:
            if hop_type == 'subnet' and next_ == self.__objective:
                # means we are going to jump on the good subnet
                return [True, True]
            else:
                return [True, False]
        else:
            return [False, False]


class AntsDiscovery:
    """
    The class that runs all the process of Discovery
    """

    def __init__(self, subnets, routers, options=None, debug=False):
        """
        Init

        Args:
            subnets: The subnetworks data
            routers: The routers data
            options: The options
            debug: Debug param
        """

        # given basics
        self.subnets = subnets
        self.routers = routers
        self.options = options
        # made-up basics
        self.hops = {}
        self.links, self.subnets_table = self.prepare_matrix_and_links()
        self.master_router = get_master_router(self.routers)
        self.debug = debug

    def prepare_matrix_and_links(self):
        """
        Prepares the matrix and the links

        The matrix is made of tuples (s,e) with S being the UID of the starting subnetwork, and E the UID of the
        subnetwork to find.

        Returns:
            The prepared matrix and links
        """

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
        
        Args:
            discovery_type: Whether it is a sweep or a search.
            links: The links prepared in the prepare_matrix_and_links function
            subnet_start: The UID of the starting subnetwork
            subnet_end: The UID of the objective (if we are searching for one, and not sweeping)
            debug: The debug param, which you set to True to output a huge load of things processed

        Returns:
            The visited subnetworks and routers, and the paths leading to the objective
        """

        def internal_debug_report(string):
            if debug:
                print(string)

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

        internal_debug_report(f"\n\n\n----- {'SWEEP' if discovery_type == 'sweep' else 'FIND'} START -----")

        # PROCESS
        while len(ants):

            internal_debug_report(f"┌────────────────────────────────────────────")
            internal_debug_report(f"│ Starting new round: {len(ants)} ants alive")
            internal_debug_report(f"│ Current visited state: {visited}")

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

                internal_debug_report(f"│  └ {id(ant)}: {subnets_at_pos}")

                # 1.1: One subnet
                if len(subnets_at_pos) == 0:
                    ant.kill()
                    internal_debug_report(f"│    » DEAD | Already seen everything from this node")
                elif len(subnets_at_pos) == 1:
                    check = ant.check_next_move(subnets_at_pos[0])

                    if discovery_type == 'sweep':
                        # Special to the sweeping ant
                        if check is True:
                            # We can proceed to next subnet
                            ant.move_to(subnets_at_pos[0])
                            visit('subnets', subnets_at_pos[0])
                            internal_debug_report(f"│    » ALIVE | Discovered network {subnets_at_pos[0]}")
                        elif check is False:
                            # we already went there
                            ant.kill()
                            internal_debug_report(f"│    » DEAD | Found a dead end")
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
                    internal_debug_report(f"│    » DEAD | Found multiple possible paths. Giving birth to:")

                    for subnet_ in subnets_at_pos:
                        if not_visited('subnets', subnet_):
                            if discovery_type == 'sweep':
                                new_ant = SweepAnt(AntState.Waiting, {"router": ant.router, "subnet": subnet_})
                            else:
                                new_ant = FindAnt(AntState.Waiting, {"router": ant.router, "subnet": subnet_},
                                                  subnet_end)

                            new_ant.feed_history("routers", ant.get_history())
                            visit('subnets', subnet_)

                            internal_debug_report(f"│      » {id(new_ant)} : discovered {subnet_}")

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
                    if ant.alive:
                        print(f"│  - {id(ant)}: {ant.subnet} / {ant.get_history()}")
                print(f"│ Status:")
            else:
                activate_ants()

            for ant in ants:
                if not ant.alive:
                    continue

                routers_at_pos = [r for r in subnets[ant.subnet] if not_visited('routers', r)]

                internal_debug_report(f"│  └ {id(ant)}: {routers_at_pos}")

                # 2.1: One router
                if len(routers_at_pos) == 0:
                    ant.kill()
                    internal_debug_report(f"│    » DEAD | Already seen everything from this node")
                elif len(routers_at_pos) == 1:
                    check = ant.check_next_move(routers_at_pos[0])
                    if discovery_type == 'sweep':
                        if check is True:
                            ant.move_to(routers_at_pos[0])
                            visit('routers', routers_at_pos[0])

                            internal_debug_report(f"│    » ALIVE | Discovered router {routers_at_pos[0]}")
                        elif check is False:
                            ant.kill()
                            internal_debug_report(f"│    » DEAD | Found a dead end")
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

                    internal_debug_report(f"│    » DEAD | Found multiple possible paths. Giving birth to:")
                    for router in routers_at_pos:
                        if not_visited('routers', router):
                            if discovery_type == 'sweep':
                                new_ant = SweepAnt(AntState.Waiting, {"router": router, "subnet": ant.subnet})
                            else:
                                new_ant = FindAnt(AntState.Waiting, {"router": router, "subnet": ant.subnet}, subnet_end)
                            new_ant.feed_history("subnets", ant.get_history())

                            visit('routers', router)
                            internal_debug_report(f"│      » {id(new_ant)} : discovered {router}")

                            ants.append(new_ant)

            # 3. Cleaning up dead bodies
            internal_debug_report(f"├──────────────────────────────────────────")
            internal_debug_report(f"│ Removing dead ants. Total ants: {len(ants)}")

            for i in reversed(range(len(ants))):
                internal_debug_report(f"│   » {id(ants[i])}: {ants[i].state}")
                if ants[i].dead:
                    ants.remove(ants[i])

            internal_debug_report(f"│ Ants remaining : {len(ants)}")
            internal_debug_report(f"└──────────────────────────────────────────")

        # RESULT
        internal_debug_report(f"Final state: {visited}")
        internal_debug_report(f"----- {'SWEEP' if discovery_type == 'sweep' else 'FIND'} END -----\n")

        return visited, ants_at_objective

    def sweep_network(self):
        """
        Sweeps the network

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

    def calculate_hops(self):
        """
        Calculates the hops (path) for each tuple of the matrix

        We calculate the hops for each matrix entry, and either keep the smallest one if there is
        equitemporality, or store each hop for further analysis and calculus by another function
        """

        for i in range(len(self.subnets_table)):
            matrix = self.subnets_table[i]
            s, e = matrix

            _, at_objective = self.ants_discovery_process('find', self.links, s, e, debug=self.debug)

            self.debug_report(f"matrix {matrix}: {at_objective}")

            # We save all the paths, tests will be done after
            self.hops[(s, e)] = at_objective

        # After all paths are calculated, we filter them with the options
        self.filter_paths_from_hops()

    def filter_paths_from_hops(self):
        self.debug_report("----- FILTERING START -----")

        p = None

        if 'preferred_routers' in self.options:
            p = self.options['preferred_routers']

        for hop in self.hops:
            v = self.hops[hop]
            self.debug_report("┌────────────────────────────────────────────")
            self.debug_report(f" - {hop}: value before filter is {v}")

            # PREFERRED ROUTERS
            if p and len(v) > 1:
                # We don't test if there is only one path, it wouldn't make sense

                # We take the preferences list (number of preferred routers in the path)
                preferences = list_preferences_from_paths(v, p)

                # We take the largest of the list (the more preferred routers there are, the best it is)
                largest = list_of_largest_of_list(preferences, return_index=True)

                # We stock into the final hops the hops which ids are in the "largest" list
                # We also reassign v if any further filtering needs to be done
                self.hops[hop] = v = [path for n, path in enumerate(v) if n in largest]

                self.debug_report(f"    -> Preferred routers filter: now {self.hops[hop]}")

            # EQUITEMPORALITY
            # If equitemporality is set to True, we take the fastest (so shortest) path
            if exists_and_matches(self.options, 'equitemporality', True):
                # Test if there are different paths, and pick the smaller one
                if len(v) == 1:
                    # only one path found
                    self.hops[hop] = v[0]
                else:
                    self.hops[hop] = smaller_of_list(v)
                self.debug_report(f"    -> Equitemporality filter: now {self.hops[hop]}")

        self.debug_report("----- FILTERING END -----\n\n\n")

    def debug_report(self, string):
        if self.debug:
            print(string)
