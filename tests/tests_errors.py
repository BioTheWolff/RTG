import unittest
from rth.core.errors import *


class NetworkCreatorTests(unittest.TestCase):

    #
    # Provided base-data error
    #
    def test_dataerr_subnets(self):
        e = WronglyFormedSubnetworksData()
        self.assertEqual("The subnetworks data given is wrongly formed or missing information. "
                         "Please verify said data.", e.__str__())

    def test_dataerr_routers(self):
        e = WronglyFormedRoutersData()
        self.assertEqual("The routers data given is wrongly formed or missing information. "
                         "Please verify said data.", e.__str__())

    def test_dataerr_links(self):
        e = WronglyFormedLinksData()
        self.assertEqual("The link data given is wrongly formed or missing information. "
                         "Please verify said data.", e.__str__())

    def test_dataerr_missing_param(self):
        e = MissingDataParameter()
        self.assertEqual("Missing one of the required data (subnetworks, routers or links) and could not find an "
                         "already-existing network instance", e.__str__())

    #
    # NetworkCreator specific error
    #
    def test_ncerr_overlapping(self):
        e = OverlappingError({"start": "192.168.1.0", "end": "192.168.1.255"},
                             {"start": "192.168.0.0", "end": "192.168.255.255"})
        self.assertEqual("Range 192.168.1.0 - 192.168.1.255 is overlapping range 192.168.0.0 - 192.168.255.255",
                         e.__str__())

    #
    # Parameter error
    #
    def test_paramerr_no_delay(self):
        e = NoDelayAllowed()
        self.assertEqual("No delay allowed when equitemporality is set to True. "
                         "Pass equitemporality=False when instancing the Dispatcher class", e.__str__())

    #
    # Process errors
    #
    def test_procerr_ip_attributed(self):
        e = IPAlreadyAttributed("My subnetwork", "192.168.1.254", "My router", "The other router")
        self.assertEqual("The IP 192.168.1.254 on the subnetwork 'My subnetwork' is already attributed to router "
                         "'My router'; Tried to give it to router 'The other router'", e.__str__())

    def test_procerr_name_exists(self):
        e = NameAlreadyExists("A random name")
        self.assertEqual("Name 'A random name' already exists", e.__str__())

    def test_procerr_unreachable_network(self):
        e = UnreachableNetwork("Random name again", "192.168.1.0/24", 3)
        self.assertEqual("The subnetwork 'Random name again' (CIDR 192.168.1.0/24) is unreachable from master router. "
                         "Total number of unreachable subnetworks: 3", e.__str__())


if __name__ == '__main__':
    unittest.main()
