import unittest
from rth.adapters.json_adapter import JSONAdapter


class AdaptersTests(unittest.TestCase):

    def setUp(self) -> None:
        self.results = {
            1: {
                '0.0.0.0/0': {'gateway': '192.168.1.253', 'interface': '192.168.1.254'},
                '10.0.0.0/24': {'gateway': '192.168.0.253', 'interface': '192.168.0.254'},
                '10.0.1.0/24': {'gateway': '192.168.1.253', 'interface': '192.168.1.254'},
                '192.168.0.0/24': {'gateway': '192.168.0.254', 'interface': '192.168.0.254'},
                '192.168.1.0/24': {'gateway': '192.168.1.254', 'interface': '192.168.1.254'}
            },
            2: {
                '0.0.0.0/0': {'gateway': '192.168.0.254', 'interface': '192.168.0.253'},
                '10.0.0.0/24': {'gateway': '10.0.0.254', 'interface': '10.0.0.254'},
                '10.0.1.0/24': {'gateway': '192.168.0.254', 'interface': '192.168.0.253'},
                '192.168.0.0/24': {'gateway': '192.168.0.253', 'interface': '192.168.0.253'},
                '192.168.1.0/24': {'gateway': '192.168.0.254', 'interface': '192.168.0.253'}
            },
            3: {
                '0.0.0.0/0': {'gateway': '10.0.1.254', 'interface': '10.0.1.253'},
                '10.0.0.0/24': {'gateway': '192.168.1.254', 'interface': '192.168.1.253'},
                '10.0.1.0/24': {'gateway': '10.0.1.253', 'interface': '10.0.1.253'},
                '192.168.0.0/24': {'gateway': '192.168.1.254', 'interface': '192.168.1.253'},
                '192.168.1.0/24': {'gateway': '192.168.1.253', 'interface': '192.168.1.253'}
            },
            4: {
                '0.0.0.0/0': {'gateway': '10.0.1.254', 'interface': '10.0.1.254'},
                '10.0.0.0/24': {'gateway': '10.0.1.253', 'interface': '10.0.1.254'},
                '10.0.1.0/24': {'gateway': '10.0.1.254', 'interface': '10.0.1.254'},
                '192.168.0.0/24': {'gateway': '10.0.1.253', 'interface': '10.0.1.254'},
                '192.168.1.0/24': {'gateway': '10.0.1.253', 'interface': '10.0.1.254'}
            }
        }

    def test_json_adapter(self):
        path = "files/test.json"
        try:
            # Path to run normally using "py -m unittest discover -s tests"
            inst = JSONAdapter(file_path=f"tests/{path}")
            dispatcher = inst.evaluate()
        except FileNotFoundError:
            # Path used by PyCharm when right clicking and selecting "Run tests"
            inst = JSONAdapter(file_path=path)
            dispatcher = inst.evaluate()

        result = dispatcher.formatted_raw_routing_tables

        for router in self.results:
            res = result[str(router)]
            expected = self.results[router]

            self.assertEqual(expected, res, f'JSON : Table : router {router}')


if __name__ == '__main__':
    unittest.main()
