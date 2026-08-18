import argparse
from .libralens import LibraLens

def main():

    parser = argparse.ArgumentParser(description="LibraLens CLI")
    parser.add_argument("-e", "--eval", required=True, help="file or directory containing marc records to be evaluated")
    parser.add_argument("-g", "--gold", required=False, help="file or directory containing gold standard marc records")
    parser.add_argument("-p", "--platinum", required=False, help="file or directory containing platinum standard marc records")
    parser.add_argument("-t", "--tools", nargs="+", required=True, help="evaluation tools to run")
    parser.add_argument("-f", "--fields", nargs="+", required=False, default=None, help="fields to be considered")

    args = parser.parse_args()

    try:
        libralens = LibraLens(
            eval=args.eval,
            gold=args.gold,
            platinum=args.platinum,
            tools=args.tools,
            fields=args.fields,
            verbose=True
        )
        libralens.run()

    except ValueError as e:
        parser.error(str(e))

if __name__ == "__main__":
    main()