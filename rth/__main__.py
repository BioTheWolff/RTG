import argparse
from rth.adapters.json_adapter import JSONAdapter
from rth.core.errors import WrongFileFormat


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="the file path which will be decoded")
    parser.add_argument("-O", "--output", help="outputs the results in a txt file")

    args = parser.parse_args()

    ext = args.input.split('.')[-1]

    if ext not in ['json']:
        raise WrongFileFormat(ext)

    adapter = JSONAdapter(args.input)
    dispatch = adapter()

    if args.output:
        dispatch.output_routing_tables(args.output)
    else:
        dispatch.display_routing_tables()


if __name__ == '__main__':
    main()
