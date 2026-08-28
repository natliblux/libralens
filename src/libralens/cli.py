import argparse
from .libralens import LibraLens
from .config import load_runs

def main():

    parser = argparse.ArgumentParser(description="LibraLens CLI")

    parser.add_argument("-e", "--eval", required=True, help="file (.xml or .txt) or directory containing marc records to be evaluated")

    run_group = parser.add_mutually_exclusive_group(required=True)
    run_group.add_argument("-m", "--methods", nargs="+", help="evaluation methods to run")
    run_group.add_argument("-r", "--runs", help="json file defining evaluation runs")

    parser.add_argument("-f", "--fields", nargs="+", required=False, default=None, help="marc fields to be considered")
    parser.add_argument("-g", "--gold", required=False, help="file (.xml or .txt) or directory containing corresponding gold standard marc records")
    parser.add_argument("-p", "--platinum", required=False, help="file (.xml or .txt) or directory containing corresponding platinum standard marc records")
    parser.add_argument("-t", "--text", required=False, help="file (.txt) or directory containing corresponding document plain text")
    parser.add_argument("-o", "--output", required=False, help="directory to write evaluation results and document data")

    args = parser.parse_args()

    try:

        if args.runs:
            if args.fields is not None:
                raise ValueError("fields cannot be provided together with runs")

            runs = load_runs(args.runs)

            libralens = LibraLens(
                eval=args.eval,
                runs=runs,
                gold=args.gold,
                platinum=args.platinum,
                text=args.text,
                output=args.output,
                verbose=True
            )

        else:
            libralens = LibraLens(
                eval=args.eval,
                methods=args.methods,
                fields=args.fields,
                gold=args.gold,
                platinum=args.platinum,
                text=args.text,
                output=args.output,
                verbose=True
            )

        libralens.run()

    except ValueError as e:
        parser.error(str(e))

if __name__ == "__main__":
    main()