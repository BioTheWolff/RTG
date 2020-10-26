## @package errors
#
#  The package which contains all the exceptions of the program


class WronglyFormedSubnetworksData(Exception):
    """
    The subnetworks dictionary is wrongly formed

    Is thrown when the subnetworks dictionary is wrongly formatted.
    """

    def __str__(self):
        return "The subnetworks data given is wrongly formed or missing information. Please verify said data."


class WronglyFormedRoutersData(Exception):
    """
    The routers dictionary is wrongly formed

    Is thrown when the routers dictionary is wrongly formatted.
    """

    def __str__(self):
        return "The routers data given is wrongly formed or missing information. Please verify said data."


class WronglyFormedLinksData(Exception):
    """
    The links dictionary is wrongly formed

    Is thrown when the links dictionary is wrongly formatted.
    """

    def __str__(self):
        return "The link data given is wrongly formed or missing information. Please verify said data."


class MissingDataParameter(Exception):
    """
    The program misses some data

    Thrown when a file misses some crucial data (subnetworks, routers or links).
    Currently not used, but implemented for later.
    """

    def __str__(self):
        return "Missing one of the required data (subnetworks, routers or links) and could not find an " \
               "already-existing network instance"


class OverlappingError(Exception):
    """
    A subnetwork overlaps another

    Thrown when a subnetwork tries to overlap an already-existing subnetwork in the virtual network instance.
    """

    def __init__(self, new, existing):
        """
        Init the new Exception

        Args:
            new: The new subnetwork range
            existing: The existing subnetwork range

        Examples:
            >>> small = {"start": "192.168.1.0", "end": "192.168.1.255"}
            >>> big = {"start": "192.168.0.0", "end": "192.168.255.255"}
            >>> raise OverlappingError(small, big)
            Traceback (most recent call last):
              ...
            rth.core.errors.OverlappingError: Range 192.168.1.0 - 192.168.1.255 is overlapping range 192.168.0.0 - 192.168.255.255
        """

        self.new_range = f"{new['start']} - {new['end']}"
        self.existing_range = f"{existing['start']} - {existing['end']}"

    def __str__(self):
        return f"Range {self.new_range} is overlapping range {self.existing_range}"


class NoDelayAllowed(Exception):
    """
    No delay is allowed on the router

    Thrown when the program reads a delay set on a router, but equitemporality is set to True.
    Currently not used because non equitemporality is not implemented yet.
    """

    def __str__(self):
        return "No delay allowed when equitemporality is set to True. " \
               "Pass equitemporality=False when instancing the Dispatcher class"


class IPAlreadyAttributed(Exception):
    """
    The provided IP is already attributed

    Thrown when the provided IP is already attributed to another router on the subnetwork.
    """

    def __init__(self, subnet_name, ip, attributed, tried_to_attribute):
        """
        Init the new Exception

        Args:
            subnet_name: The name of the subnetwork.
            ip: The concerned IP.
            attributed: The name of the router that possesses this IP.
            tried_to_attribute: The name of the router which tried to get this IP.

        Examples:
            >>> subnet_name = "MySubnet"
            >>> ip = "192.168.1.250"
            >>> attributed = "FirstRouter"
            >>> tried_to_attribute = "ThisOtherRouter"
            >>> raise IPAlreadyAttributed(subnet_name, ip, attributed, tried_to_attribute)
            raise IPAlreadyAttributed("MySubnet", "192.168.1.250", "FirstRouter", "ThisOtherRouter")
            Traceback (most recent call last):
              ...
            rth.core.errors.IPAlreadyAttributed: The IP 192.168.1.250 on the subnetwork 'MySubnet' is already attributed to router 'FirstRouter'; Tried to give it to router 'ThisOtherRouter'
        """

        self.name = subnet_name
        self.ip = ip
        self.attributed = attributed
        self.tried = tried_to_attribute

    def __str__(self):
        return f"The IP {self.ip} on the subnetwork '{self.name}' is already attributed to router " \
               f"'{self.attributed}'; Tried to give it to router '{self.tried}'"


class NameAlreadyExists(NameError):
    """
    The name of the subnetwork or router already exists

    Thrown when the user tries to give two subnetworks or routers the same name.
    """

    def __init__(self, name):
        """
        Init the new Exception

        Args:
            name: The name that already exists.

        Examples:
            >>> raise NameAlreadyExists("This name")
            Traceback (most recent call last):
              ...
            rth.core.errors.NameAlreadyExists: Name 'This name' already exists
        """

        self.name = name

    def __str__(self):
        return f"Name '{self.name}' already exists"


class UnreachableNetwork(Exception):
    """
    A subnetwork is unreachable

    Thrown during the AntsDiscovery process if a subnetwork is unreachable from the master router.
    """

    def __init__(self, name, cidr, total):
        """
        Init the new Exception

        Args:
            name: The name of the unreachable subnetwork.
            cidr: Its CIDR.
            total: The total number of unreachable subnetworks.

        Examples:
            >>> raise UnreachableNetwork("My subnet", "192.168.1.0/24", 4)
            Traceback (most recent call last):
                ...
            rth.core.errors.UnreachableNetwork: The subnetwork 'My subnet' (CIDR 192.168.1.0/24) is unreachable from master router. Total number of unreachable subnetworks: 4
        """

        self.name = name
        self.cidr = cidr
        self.total = total

    def __str__(self):
        return f"The subnetwork '{self.name}' (CIDR {self.cidr}) is unreachable from master router. " \
               f"Total number of unreachable subnetworks: {self.total}"


class MasterRouterError(Exception):
    """
    There was an error with the master router

    Thrown when there is a problem with the master router.
    Currently, is thrown when the network lacks a master router, or has more than one.
    """

    def __init__(self, no_internet=False):
        """
        Init the new Exception

        Args:
            no_internet: Whether it concerns the network having no internet or more than one master router.

        Examples:
            >>> raise MasterRouterError(True)
            Traceback (most recent call last):
              ...
            rth.core.errors.MasterRouterError: There is no connection to the internet on this network. Please connect one router.
            >>> raise MasterRouterError(False)
            Traceback (most recent call last):
              ...
            rth.core.errors.MasterRouterError: An exception occured during master router definition. Please verify ONE (and only one) router is connected to internet
        """

        if no_internet:
            self.text = "There is no connection to the internet on this network. Please connect one router."
        else:
            self.text = "An exception occured during master router definition. " \
                        "Please verify ONE (and only one) router is connected to internet"

    def __str__(self):
        return self.text


class WrongOptionName(Exception):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Option '{self.name}' not recognised."


class WrongOptionValueType(Exception):

    def __init__(self, name, provided, expected):
        self.option = name
        self.p = provided
        self.e = expected

    def __repr__(self):
        return f"Value for option '{self.option}' must be of type {str(self.p)} (provided {str(self.e)}."


class WrongFileFormat(Exception):

    def __init__(self, ext):
        self.ext = ext

    def __str__(self):
        return f"Allowed formats: YAML (.yml), JSON (.json). Found: .{self.ext}"


class WrongJSONTag(Exception):

    def __init__(self, tag):
        self.tag = tag

    def __str__(self):
        return f"Unknown YAML tag: {self.tag}"


class MissingJSONTag(Exception):

    def __init__(self, tag):
        self.tag = tag

    def __str__(self):
        return f"Missing YAML tag: {self.tag}"


class MissingJSONInfo(Exception):

    def __init__(self, cat, name, info):
        self.category = cat
        self.name = name
        self.info = info

    def __str__(self):
        return f"{self.category}: missing {self.info} in {self.category.lower()} {self.name}"
