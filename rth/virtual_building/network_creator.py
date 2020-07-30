from nettools.core.ipv4_network import IPv4Network
from nettools.utils.ip_class import FourBytesLiteral
from nettools.utils.utils import Utils
from nettools.utils.errors import IPOffNetworkRangeException

from rth.core.errors import *

## @package network_creator
#
#  This package contains the NetworkCreator class, that builds the virtual network from the provided data.


## Builds a virtual network from the provided data
#
#  This class, based on the IPv4Network from the python package nettools, builds a virtual network of subnetworks and
#  routers. It is the "virtual environment" that makes the base of the program.
#
# WARNING: Every link is supposed virtual, and is actually not an instance of any type. Links will be
# considered and discovered by the Ants system.
# Neither the Network or the Router class stock instances of "links", and only the master program
# can process and understand these connections.
class NetworkCreator:

    subnetworks, routers = None, None
    subnets_names, routers_names = None, None

    ## Subnetworks ranges ( format is [{"start": START, "end": END}, ...] )
    ranges = None
    equitemporality = None

    ##
    #  @param equitemporality Whether to activate equitemporality or not. Forced to True for now because equitemporality
    #  is not yet implemented.
    def __init__(self, equitemporality=True):
        self.equitemporality = True

        self.subnetworks, self.routers = {}, {}
        self.subnets_names, self.routers_names = [], []
        self.ranges = []

    ## The virtual subnetwork class
    #
    #  Used to create virtual subnetworks and link them with routers
    class Network:

        network_range, addresses, mask_length = {}, 0, 0
        routers = None
        uid, name = -1, None

        ##
        #  @param starting_ip The IP for the new subnetwork
        #  @param mask The network mask, either a literal or a length
        #  @param uid The UID of the network
        #  @param name The name of the new subnetwork. If None is provided, defaults to
        #  "<Untitled Network#ID:{ID HERE}>"
        def __init__(self, starting_ip, mask, uid, name=None):

            inst_ = IPv4Network().init_from_couple(starting_ip, mask)

            self.uid = uid
            self.name = name if name else None
            self.cidr = f"{starting_ip}/{inst_.mask_length}"

            self.routers = {}

            self.network_range = inst_.network_range
            self.mask_length = inst_.mask_length
            self.addresses = inst_.addresses

        ## Connects a router to the subnetwork
        #  @param router_uid The router UID
        #  @param router_ip The IP assigned to the router on this subnetwork
        def connect(self, router_uid, router_ip):
            self.routers[router_uid] = router_ip

        ## Disconnects a router from the subnetwork
        #  @param router_uid The router UID
        def disconnect(self, router_uid):
            if router_uid in self.routers:
                del self.routers[router_uid]

    ## The virtual router class
    #
    #  Used to simulate routers and link them with subnetworks
    class Router:

        uid, name = -1, None
        connected_networks, internet = None, False

        ##
        #  @param uid The UID of the router
        #  @param internet Whether the router is connected to internet
        #  @param name The name of the router. If None is provided, defaults to "<Untitled Network#ID:{ID HERE}>"
        #  @param delay The delay of the router in ms. For now, not used because non-equitemporality is not implemented
        def __init__(self, uid, internet=False, name=None, delay=None):
            self.uid = uid
            self.name = name if name else None
            self.internet = internet
            if not NetworkCreator.equitemporality and delay:
                raise NoDelayAllowed()
            else:
                self.delay = delay
            self.connected_networks = {}

        ## Connects the router to a subnetwork
        #  @param subnet_uid The UID of the subnetwork
        #  @param router_ip The IP the router will be assigned
        def connect(self, subnet_uid, router_ip):
            if self.internet and self.connected_networks:
                raise Exception('Master router cannot accept more than one connection')

            self.connected_networks[subnet_uid] = router_ip

        ## Disconnects the router from a subnetwork
        #  @param subnet_uid The UID of the subnetwork
        def disconnect(self, subnet_uid):
            if subnet_uid in self.connected_networks:
                del self.connected_networks[subnet_uid]

    ## Returns IP of router on the subnetwork
    #  If the given router is connected to the given subnetwork, returns its IP; else, returns None.
    #  @param subnet_id The subnet UID
    #  @param router_id The router UID
    def get_ip_of_router_on_subnetwork(self, subnet_id, router_id):
        if subnet_id not in self.subnetworks:
            return None

        subnet = self.subnetworks[subnet_id]['instance']

        if router_id not in subnet.routers:
            return None

        return subnet.routers[router_id]

    ## Takes the name and returns the UID
    #  @param cat The category (either "subnet" or "router")
    #  @param name The name
    def name_to_uid(self, cat, name):
        list_ = self.subnets_names if cat == 'subnet' else self.routers_names
        id_ = 0

        for i in range(len(list_)):
            if list_[i] == str(name):
                id_ = i
                break

        return id_

    ## Takes the UID and returns the name
    #  @param cat The category (either "subnet" or "router")
    #  @param uid The UID
    def uid_to_name(self, cat, uid):
        name_ = 0

        if cat == 'subnet':
            for id_ in self.subnetworks:
                if id_ == uid:
                    name_ = self.subnetworks[id_]['instance'].name
                    break
        else:
            for id_ in self.routers:
                if id_ == uid:
                    name_ = self.routers[id_].name
                    break

        return str(name_)

    ## Returns if the given name exists
    #  @param type_ The type (either "subnet" or "router")
    #  @param name The name we want to check
    def is_name_existing(self, type_, name):
        list_ = self.subnets_names if type_ == 'subnet' else self.routers_names
        return name in list_

    ## Returns if the given router has a connection to internet
    #  @param router_uid The router UID
    def router_has_internet_connection(self, router_uid):
        return self.routers[router_uid].internet

    ## Creates a virtual subnetwork
    #  @param ip The given IP
    #  @param mask_length The network mask length of the subnetwork
    #  @param name The eventual name of the subnetwork
    def create_network(self, ip, mask_length, name=None):

        uid = len(self.subnetworks)

        # Name correspondency
        if name:
            result = self.is_name_existing('subnet', name)
            if result:
                raise NameAlreadyExists(name)
        else:
            name = f"<Untitled Network#ID:{uid}>"

        current = self.Network(ip, mask_length, uid, name)
        current_netr = Utils.netr_to_literal(current.network_range)

        if self.ranges:
            for sid in self.subnetworks:
                subnet = self.subnetworks[sid]['instance']
                subnetr = Utils.netr_to_literal(subnet.network_range)

                overlap = False
                if current.mask_length == subnet.mask_length:
                    # Masks are equal
                    if current_netr['start'] == subnetr['start']:
                        overlap = True
                else:
                    if current.mask_length < subnet.mask_length:
                        # New network mask is bigger, check if the existing subnetwork is inside
                        big = current_netr['start'].split('.')
                        small = subnetr['start']
                    else:
                        # New network is smaller that existing subnetwork, check if it is inside
                        small = current_netr['start']
                        big = subnetr['start'].split('.')

                    if current.mask_length <= 8:
                        if int(big[0]) <= int(small.split('.')[0]):
                            overlap = True
                    elif 8 < current.mask_length <= 16:
                        if small.startswith(f"{big[0]}") and int(big[1]) <= int(small.split('.')[1]):
                            overlap = True
                    elif 16 < current.mask_length <= 24:
                        if small.startswith(f"{big[0]}.{big[1]}") and int(big[2]) <= int(small.split('.')[2]):
                            overlap = True
                    elif 24 < current.mask_length <= 32:
                        if int(big[3]) <= int(small.split('.')[3]):
                            overlap = True

                if overlap:
                    raise OverlappingError(current_netr, subnetr)

        self.subnetworks[uid] = {'instance': current, 'range': current.network_range}

        # adding to network ranges
        self.ranges.append(current.network_range)
        # also adding name if defined
        if name:
            self.subnets_names.append(name)

        return uid

    ## Creates a virtual router
    #  @param internet_connection Whether the router has a connection to internet
    #  @param name The eventual name of the router
    def create_router(self, internet_connection=False, name=None):

        uid = len(self.routers)

        if name:
            result = self.is_name_existing('router', name)
            if result:
                raise NameAlreadyExists(name)
        else:
            name = f"<Untitled Router#ID:{uid}>"

        inst_ = self.Router(uid, internet_connection, name)

        self.routers_names.append(name)

        self.routers[uid] = inst_

        return uid

    ## Connects a router to a set of subnetworks
    #  @param router_name The name of the router
    #  @param subnets_ips The list of subnetworks with the corresponding IP to assign the router to. Format:
    #  {SUBNET_NAME: IP, ...}
    def connect_router_to_networks(self, router_name, subnets_ips):

        ## Checks if an IP is available
        #  This function is a suicider: it will die if any of the tests fail. It will either raise
        #  nettools.core.errors.IPOffNetworkRangeException or rth.core.errors.IPAlreadyAttributed
        #  @param subnet_inst_ The subnetwork instance
        #  @param ip_ The IP that has to be checked
        def check_ip_availability(subnet_inst_, ip_):

            # Checking that ip is effectively in range of the subnet
            if isinstance(ip_, str):
                ip_ = FourBytesLiteral().set_from_string_literal(ip_)

            mask = FourBytesLiteral().set_from_string_literal(Utils.mask_length_to_literal(subnet_inst_.mask_length))
            inst = IPv4Network().init_from_fbl(ip_, mask)

            if inst.address_type != 1:
                # means the address is either a network or a broadcast address
                raise IPOffNetworkRangeException(str(ip))

            # then we check that ip is not used by any of the current routers
            routers = subnet_inst_.routers
            for r in routers:
                if str(routers[r]) == str(ip_):
                    raise IPAlreadyAttributed(name, ip_, self.uid_to_name('router', r), str(router_name))

        router_uid = self.name_to_uid('router', router_name)

        for name in subnets_ips:
            subnet_uid = self.name_to_uid('subnet', name)
            subnet_inst = self.subnetworks[subnet_uid]['instance']
            router_inst = self.routers[router_uid]

            subnet_ip = subnets_ips[name]

            # we want to attribute a "personalised" IP
            if subnet_ip:
                check_ip_availability(subnet_inst, subnet_ip)
                ip = subnet_ip
            # we will let the program set it for us
            else:

                ip = subnet_inst.network_range['end']
                while True:
                    ip = Utils.ip_before(ip)
                    try:
                        check_ip_availability(subnet_inst, ip)
                        break
                    except IPAlreadyAttributed:
                        continue

            subnet_inst.connect(router_uid, ip)
            router_inst.connect(subnet_uid, ip)

            self.subnetworks[subnet_uid]['instance'] = subnet_inst
            self.routers[router_uid] = router_inst

    ## Displays the virtual local network in the console
    def display_network(self):
        for i in self.subnetworks:
            inst = self.subnetworks[i]['instance']

            print(
                f"Network {inst.network_range['start']} - {inst.network_range['end']}"
                f"  ID: {inst.uid}"
                f"  Name: {inst.name if inst.name else '<unnamed>'}"
                "\n"
            )

    ## Returns a raw output of the local network
    def network_raw_output(self):
        final = {'subnets': {}, 'routers': {}}

        for sid in self.subnetworks:
            subnet = self.subnetworks[sid]['instance']

            displayable_connected_routers = subnet.routers.copy()
            for i in displayable_connected_routers:
                displayable_connected_routers[i] = str(displayable_connected_routers[i])

            final['subnets'][sid] = {
                'id': subnet.uid,
                'name': subnet.name,
                'connected_routers': displayable_connected_routers,
                'range': Utils.netr_to_literal(subnet.network_range),
                'mask': subnet.mask_length
            }

        for rid in self.routers:
            router = self.routers[rid]

            displayable_connected_subnets = router.connected_networks.copy()
            for i in displayable_connected_subnets:
                displayable_connected_subnets[i] = str(displayable_connected_subnets[i])

            final['routers'][rid] = {
                'id': router.uid,
                'name': router.name,
                'connected_subnets': displayable_connected_subnets,
                'internet': router.internet
            }

        return final
