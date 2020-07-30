## @package errors
#
#  The package which contains all the exceptions of the program


## The subnetworks dictionary is wrongly formed
#
#  Is thrown when the subnetworks dictionary is wrongly formatted.
class WronglyFormedSubnetworksData(Exception):

    def __str__(self):
        return "The subnetworks data given is wrongly formed or missing information. Please verify said data."


## The routers dictionary is wrongly formed
#
#  Is thrown when the routers dictionary is wrongly formatted.
class WronglyFormedRoutersData(Exception):

    def __str__(self):
        return "The routers data given is wrongly formed or missing information. Please verify said data."


## The links dictionary is wrongly formed
#
#  Is thrown when the links dictionary is wrongly formatted.
class WronglyFormedLinksData(Exception):

    def __str__(self):
        return "The link data given is wrongly formed or missing information. Please verify said data."


## The program misses some data
#
#  Thrown when a file misses some crucial data (subnetworks, routers or links).
#  Currently not used, but implemented for later.
class MissingDataParameter(Exception):

    def __str__(self):
        return "Missing one of the required data (subnetworks, routers or links) and could not find an " \
               "already-existing network instance"


## A subnetwork overlaps another
#
#  Thrown when a subnetwork tries to overlap an already-existing subnetwork in the virtual network instance.
class OverlappingError(Exception):

    ##
    #  @param new The new subnetwork range
    #  @param existing The existing subnetwork range
    def __init__(self, new, existing):
        self.new_range = f"{new['start']} - {new['end']}"
        self.existing_range = f"{existing['start']} - {existing['end']}"

    def __str__(self):
        return f"Range {self.new_range} is overlapping range {self.existing_range}"


## No delay is allowed on the router
#
#  Thrown when the program reads a delay set on a router, but equitemporality is set to True.
#  Currently not used because non equitemporality is not implemented yet.
class NoDelayAllowed(Exception):

    def __str__(self):
        return "No delay allowed when equitemporality is set to True. " \
               "Pass equitemporality=False when instancing the Dispatcher class"


## The provided IP is already attributed
#
#  Thrown when the provided IP is already attributed to another router on the subnetwork
class IPAlreadyAttributed(Exception):

    ##
    #  @param subnet_name The name of the subnetwork.
    #  @param ip The concerned IP.
    #  @param attributed The name of the router that possesses this IP.
    #  @param tried_to_attribute The name of the router which tried to get this IP.
    def __init__(self, subnet_name, ip, attributed, tried_to_attribute):
        self.name = subnet_name
        self.ip = ip
        self.attributed = attributed
        self.tried = tried_to_attribute

    def __str__(self):
        return f"The IP {self.ip} on the subnetwork '{self.name}' is already attributed to router " \
               f"'{self.attributed}'; Tried to give it to router '{self.tried}'"


## The name of the subnetwork or router already exists
#
#  Thrown when the user tries to give two subnetworks or routers the same name.
class NameAlreadyExists(NameError):

    ##
    #  @param name The name that already exists.
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Name '{self.name}' already exists"


## A subnetwork is unreachable
#
#  Thrown during the AntsDiscovery process if a subnetwork is unreachable from the master router.
class UnreachableNetwork(Exception):

    ##
    #  @param name The name of the unreachable subnetwork.
    #  @param cidr Its CIDR.
    #  @param total The total number of unreachable subnetworks.
    def __init__(self, name, cidr, total):
        self.name = name
        self.cidr = cidr
        self.total = total

    def __str__(self):
        return f"The subnetwork '{self.name}' (CIDR {self.cidr}) is unreachable from master router. " \
               f"Total number of unreachable subnetworks: {self.total}"


## There was an error with the master router
#
#  Thrown when there is a problem with the master router.
#  Currently, is thrown when the network lacks a master router, or has more than one.
class MasterRouterError(Exception):

    ##
    #  @param no_internet Whether it concerns the network having no internet or more than one master router.
    def __init__(self, no_internet=False):
        if no_internet:
            self.text = "There is no connection to the internet on this network. Please connect one router."
        else:
            self.text = "An exception occured during master router definition. " \
                        "Please verify ONE (and only one) router is connected to internet"

    def __str__(self):
        return self.text
