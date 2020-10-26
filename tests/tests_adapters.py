import unittest
from rth.adapters.json_adapter import JSONAdapter
from os import listdir
from os.path import isfile, join, exists
from json import loads


def get_format_test_files(lang):
    tests = "./files/"
    langtests = [f for f in listdir(tests) if isfile(join(tests, f)) and f.endswith(f".{lang}")]
    final = {}

    for t in langtests:
        filename = "".join(t.split(".")[0:-1])
        if not exists(join(tests, f"{filename}.jsonresult")):
            raise Exception(f"Test file {t} has no result file.")

        final[t] = f"{filename}.jsonresult"

    return final


def read_and_load_from_json(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()
    return loads(content)


class AdaptersTests(unittest.TestCase):

    def test_json_adapter(self):
        files = get_format_test_files('json')

        for f in files:
            path = f"files/{f}"
            respath = f"files/{files[f]}"
            try:
                # Path to run normally using "py -m unittest discover -s tests"
                inst = JSONAdapter(file_path=f"tests/{path}")
                dispatcher = inst.evaluate()
            except FileNotFoundError:
                # Path used by PyCharm when right clicking and selecting "Run tests"
                inst = JSONAdapter(file_path=path)
                dispatcher = inst.evaluate()

            expected_result = read_and_load_from_json(respath)
            result = dispatcher.formatted_raw_routing_tables

            for router in expected_result:
                res = result[str(router)]
                expected = expected_result[router]

                self.assertEqual(expected, res, f'JSON : Table : router {router}')


if __name__ == '__main__':
    unittest.main()
