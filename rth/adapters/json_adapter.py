import json
from rth.core.errors import MissingFileTag, WrongFileTag, MissingFileInfo
from .general_adapter import GeneralAdapter


class JSONAdapter(GeneralAdapter):

    def evaluate(self):
        with open(self.file_path, 'r') as file:
            decoded = json.load(file)

        found_networks, found_routers, found_links, links_or_connections = False, False, False, 'Links'

        # Capitalise the keys
        decoded = {key.capitalize(): decoded[key] for key in decoded}

        for part in decoded:
            if part == 'Networks':
                found_networks = True
            elif part == 'Routers':
                found_routers = True
            elif part == 'Links' or part == 'Connections':
                links_or_connections = 'Links' if part == 'Links' else 'Connections'
                found_links = True
            elif part == 'Options':
                pass
            else:
                raise WrongFileTag(part, 'json')

        if not found_routers:
            raise MissingFileTag('Routers', 'json')
        if not found_networks:
            raise MissingFileTag('Networks', 'json')
        if not found_links:
            raise MissingFileTag('Links', 'json')

        # we create the dictionary of all subnetworks
        subnetworks = {}
        for name in decoded['Networks']:
            net = decoded['Networks'][name]

            if "cidr" in net:
                # we found a CIDR, so we split it and return the network
                subnetworks[name] = net['cidr']
            elif "ip" in net and "mask" in net:
                # we found an IP and a mask
                ip, mask = net['ip'], net['mask']
                subnetworks[name] = f"{ip}/{mask}"
            else:
                # missing a cidr tag or a couple IP/mask
                raise MissingFileInfo('Networks', str(name), "CIDR or IP/mask couple")

        # then we create the dictionary of all routers
        routers = {}
        for name in decoded['Routers']:
            router = decoded['Routers'][name]

            if router and "internet" in router:
                routers[name] = True
            else:
                routers[name] = None

        # finally, we link all things between them
        list_ = decoded['Links'] if links_or_connections == 'Links' else decoded['Connections']

        # The options if there are any
        options = None
        if 'Options' in decoded:
            options = decoded['Options']

        return self._process(subnetworks, routers, list_, options=options)
