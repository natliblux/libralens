import argparse
from .libralens import LibraLens

def main():

    parser = argparse.ArgumentParser(description="LibraLens CLI")
    parser.add_argument("-e", "--eval", required=True, help="file (.xml or .txt) or directory containing marc records to be evaluated")
    parser.add_argument("-m", "--methods", nargs="+", required=True, help="evaluation methods to run")
    parser.add_argument("-f", "--fields", nargs="+", required=False, default=None, help="marc fields to be considered")
    parser.add_argument("-g", "--gold", required=False, help="file (.xml or .txt) or directory containing corresponding gold standard marc records")
    parser.add_argument("-p", "--platinum", required=False, help="file (.xml or .txt) or directory containing corresponding platinum standard marc records")
    parser.add_argument("-t", "--text", required=False, help="file (.txt) or directory containing corresponding document plain text")
    args = parser.parse_args()

    try:
        libralens = LibraLens(
            eval=args.eval,
            methods=args.methods,
            fields=args.fields,
            gold=args.gold,
            platinum=args.platinum,
            text=args.text,
            verbose=True
        )
        libralens.run()

    except ValueError as e:
        parser.error(str(e))

if __name__ == "__main__":
    main()