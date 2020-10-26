from rth.virtual_building.network_creator import NetworkCreator
from rth.virtual_building.ants import AntsDiscovery
from rth.virtual_building.routing_tables_generator import RoutingTablesGenerator
from .errors import WronglyFormedSubnetworksData, WronglyFormedRoutersData, WronglyFormedLinksData, WrongOptionName, \
    WrongOptionValueType
from nettools.utils.ip_class import FourBytesLiteral

## @package dispatcher
#
#  Package of the Dispatcher class.
#  This class aims to simplify the process to the user by regrouping all the functions in one class, executable in
#  one and only simple way.


class Dispatcher:
    """
    Hub that simplifies the process

    Serves as a hub which allows to ease the process to the user by regrouping all the classes and functions into one
    process runnable by providing the right data to a function.
    """

    ## The virtual network (NetworkCreator) instance
    __virtual_network_instance = None

    __possible_options = {
        'preferred_routers': list
    }
    __options = None

    ## Whether the program has been entirely executed and processed (used for display and output functions)
    __executed = None

    subnetworks, routers, links = None, None, None
    equitemporality = None

    gend_subnetworks, gend_routers, gend_routers_names = None, None, None
    hops = None

    ## The raw routing tables returned by the RoutingTablesGenerator instance
    routing_tables = None
    ## The formatted routing tables, prepared for either display or output (with i.e. names instead of IDs)
    formatted_raw_routing_tables = None

    @property
    def available_options(self):
        return list(self.__possible_options.keys())

    def set_option(self, option, value):
        if option not in self.available_options:
            raise WrongOptionName(option)

        if not isinstance(value, type(self.__possible_options[option])):
            raise WrongOptionValueType(option, type(value), type(self.__possible_options[option]))

        self.__options[option] = value

    def __init__(self, debug=False):
        """
        The init function

        Args:
            debug: Triggers the whole debug system if set to True
        """

        self.__virtual_network_instance = NetworkCreator()
        self.debug = debug
        self.__executed = False
        self.__options = {key: None for key in self.available_options}

    def execute(self, subnetworks, routers, links):
        """
        Function that triggers everything

        Args:
            subnetworks: The subnetworks data
            routers: The routers data
            links: The links data

        """

        self.subnetworks = subnetworks
        self.routers = routers
        self.links = links

        self.equitemporality = True
        self.__flow()
        self.__executed = True

    def __flow(self):
        """
        Flow function

        This function is used to trigger the required functions in the right order.
        It is detached from the execute function for more readability
        """

        self.__checks()
        self.__build_virtual_network()
        self.__discover_hops()
        self.__calculate_routing_tables()

    def __checks(self):
        """
        Checks if data are all formatted as required.

        Checks all the provided data (subnetworks, routers and links) to see if they are formatted as required.
        """

        # Subnetworks checks
        s = self.subnetworks
        if not isinstance(s, dict):
            raise WronglyFormedSubnetworksData()

        for name in s:
            v = s[name]
            try:
                ip, _ = v.split("/")
                FourBytesLiteral().set_from_string_literal(ip)
            except (OverflowError, Exception):
                raise WronglyFormedSubnetworksData()

        r = self.routers
        if not isinstance(r, dict):
            raise WronglyFormedRoutersData()
        for name in r:
            if r[name] is not None and not isinstance(r[name], bool):
                raise WronglyFormedRoutersData()

        li = self.links
        if not isinstance(li, dict):
            raise WronglyFormedLinksData()
        for rid in li:
            if not isinstance(li[rid], dict):
                raise WronglyFormedLinksData()
            for subnet in li[rid]:
                if not isinstance(li[rid][subnet], str) and li[rid][subnet] is not None:
                    raise WronglyFormedLinksData()

    def __build_virtual_network(self):
        """
        NetworkCreator related

        Creates the virtual network from scratch with provided data and prepares it for the next function
        """

        inst = self.__virtual_network_instance

        # Create subnets
        for name in self.subnetworks:
            ip, mask = self.subnetworks[name].split('/')
            inst.create_network(ip, int(mask), str(name))

        # Create routers
        for name in self.routers:
            if self.routers[name]:
                inst.create_router(name=str(name), internet_connection=True)
            else:
                inst.create_router(name=str(name))

        # Link both
        for router_name in self.links:
            inst.connect_router_to_networks(router_name, self.links[router_name])

        self.gend_subnetworks = inst.subnetworks
        self.gend_routers = inst.routers
        self.gend_routers_names = inst.routers_names

    def network_raw_output(self):
        """
        Outputs the raw network
        """

        return self.__virtual_network_instance.network_raw_output() if self.__executed else None

    def __discover_hops(self):
        """
        AntsDiscovery related

        Takes the prepared virtual network and runs the Ants process to create virtual links between the subnetworks
        and routers.
        """

        ants_inst = AntsDiscovery(self.gend_subnetworks, self.gend_routers, self.equitemporality, debug=self.debug)

        ants_inst.sweep_network()
        ants_inst.calculate_hops()

        self.links = ants_inst.links
        self.hops = ants_inst.hops

    def __calculate_routing_tables(self):
        """
        RoutingTablesGenerator related

        Generates the routing tables based on the paths ("hops") found by the Ants process.
        """

        if not self.links or self.hops:
            self.__discover_hops()

        rtg_inst = RoutingTablesGenerator(self.__virtual_network_instance, self.gend_subnetworks, self.gend_routers,
                                          self.links, self.hops, equitemporality=self.equitemporality)

        # getting routing tables
        routing_tables = []
        for i in range(len(self.routers)):
            routing_tables.append(rtg_inst.get_routing_table(i))

        self.routing_tables = routing_tables

        # formatting them to be displayed
        final = {}
        for i in range(len(self.routers)):
            name = self.gend_routers_names[i]
            final[name] = routing_tables[i]

        # reformatting final table to print in strings the router IP instead of having a FBL instance
        for router in final:
            for key in final[router]:
                final[router][key]['gateway'] = str(final[router][key]['gateway'])
                final[router][key]['interface'] = str(final[router][key]['interface'])

        self.formatted_raw_routing_tables = final

    def display_routing_tables(self):
        """
        Displays in the console

        Displays the formatted paths and routing tables in the console. Useful for interactive consoles.
        """

        if self.__executed:
            # Hops
            print("----- HOPS -----")
            for tup in self.hops:
                s, e = tup
                path = self.hops[tup]
                string = f"From subnetwork {self.__virtual_network_instance.uid_to_name('subnet', s)} " \
                         f"to subnetwork {self.__virtual_network_instance.uid_to_name('subnet', e)}: "

                if len(path) == 1:
                    string += f"router {self.__virtual_network_instance.uid_to_name('router', path[0])}"
                else:
                    for i in range(len(path)):
                        if i > 0:
                            string += " > "
                        string += f"router {self.__virtual_network_instance.uid_to_name('router', path[i])}"

                print(string)

            # Routing tables
            print("\n\n----- ROUTING TABLES -----")
            for name in self.formatted_raw_routing_tables:
                print(f"Router {name}")
                for subnet in self.formatted_raw_routing_tables[name]:
                    print(f"  - {subnet}", ''.join([' ' for _ in range(18 - len(subnet))]),
                          f": {self.formatted_raw_routing_tables[name][subnet]['gateway']} "
                          f"via {self.formatted_raw_routing_tables[name][subnet]['interface']}")

    def output_routing_tables(self, file_path):
        """
        Outputs to a file

        Outputs the formatted paths and routing tables to a given file path.

        Args:
            file_path: The file path where all the data will be outputted. Preferably a .txt file.
        """

        if self.__executed:
            with open(file_path, encoding="utf-8", mode="w") as f:
                # Hops
                f.write("----- HOPS -----\n")
                for tup in self.hops:
                    s, e = tup
                    path = self.hops[tup]
                    string = f"Subnet {self.__virtual_network_instance.uid_to_name('subnet', s)} " \
                             f"to subnet {self.__virtual_network_instance.uid_to_name('subnet', e)}: "

                    if len(path) == 1:
                        string += f"router {self.__virtual_network_instance.uid_to_name('router', path[0])}"
                    else:
                        for i in range(len(path)):
                            if i > 0:
                                string += " > "
                            string += f"router {self.__virtual_network_instance.uid_to_name('router', path[i])}"

                    f.write(string + '\n')

                # Routing tables
                f.write("\n\n----- ROUTING TABLES -----\n")
                for name in self.formatted_raw_routing_tables:
                    f.write(f"\nRouter {name}\n")
                    for subnet in self.formatted_raw_routing_tables[name]:
                        f.write(f"  - {subnet} {''.join([' ' for _ in range(18 - len(subnet))])} : "
                                f"{self.formatted_raw_routing_tables[name][subnet]['gateway']} "
                                f"via {self.formatted_raw_routing_tables[name][subnet]['interface']}\n")
