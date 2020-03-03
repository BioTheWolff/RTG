from ruamel.yaml import YAML
from RoutingTablesCalculator.core.errors import MissingYAMLTag, WrongYAMLTag, MissingYAMLInfo
from RoutingTablesCalculator.virtual_building.network_creator import NetworkCreator


class YAMLAdapter:
    def __init__(self, file_path):
        self.file_path = file_path

    def __call__(self, *args, **kwargs):
        yaml = YAML()
        with open(self.file_path, 'r') as file:
            decoded = yaml.load(file)

        found_networks, found_routers, found_links, links_or_connections = False, False, False, 'Links'
        for part in decoded:
            if part == 'Networks':
                found_networks = True
            elif part == 'Routers':
                found_routers = True
            elif part == 'Links' or part == 'Connections':
                links_or_connections = 'Links' if part == 'Links' else 'Connections'
                found_links = True
            else:
                raise WrongYAMLTag(part)

        if not found_routers:
            raise MissingYAMLTag('Routers')
        if not found_networks:
            raise MissingYAMLTag('Networks')
        if not found_links:
            raise MissingYAMLTag('Links')

        # we init the instance
        inst = NetworkCreator()

        # we register all subnets
        for name in decoded['Networks']:
            net = decoded['Networks'][name]

            if "cidr" in net:
                # we found a CIDR, so we split it and return the network
                ip, mask = net['cidr'].split('/')
                inst.create_network(ip, mask, str(name))
            elif "ip" in net and "mask" in net:
                # we found an IP and a mask
                ip, mask = net['ip'], net['mask']
                inst.create_network(ip, mask, str(name))
            else:
                # missing a cidr tag or a couple IP/mask
                raise MissingYAMLInfo('Networks', str(name), "CIDR or IP/mask couple")

        # then we register all routers
        for name in decoded['Routers']:
            router = decoded['Routers'][name]

            if router and "internet" in router:
                inst.create_router(name=str(name), internet_connection=True)
            else:
                inst.create_router(name=str(name))

        # finally, we link all things between them
        list_ = decoded['Links'] if links_or_connections == 'Links' else decoded['Connections']
        for link in list_:
            subnets = list_[link]
            inst.connect_router_to_networks(link, subnets)

        return inst
