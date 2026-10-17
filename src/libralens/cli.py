import argparse
import sys
from .libralens import LibraLens
from .run import load_runs

def add_eval_arguments(parser):

    parser.add_argument("--eval", required=True, help="file (.xml or .txt) or directory containing marc records to be evaluated")

    run_group = parser.add_mutually_exclusive_group(required=False)
    run_group.add_argument("--methods", nargs="+", help="evaluation methods to run")
    run_group.add_argument("--runs", help="json file defining evaluation runs")

    parser.add_argument("--fields", nargs="+", default=None, help="marc fields to be considered")
    parser.add_argument("--gold", help="file (.xml or .txt) or directory containing corresponding gold standard marc records")
    parser.add_argument("--platinum", help="file (.xml or .txt) or directory containing corresponding platinum standard marc records")
    parser.add_argument("--text", help="file (.txt) or directory containing corresponding document plain text")
    parser.add_argument("--pdf", help="pdf file or directory containing corresponding source pdf documents")
    parser.add_argument("--output", help="directory to write evaluation results and document data")

def evaluate(args):

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
            pdf=args.pdf,
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
            pdf=args.pdf,
            output=args.output,
            verbose=True
        )

    libralens.evaluate()

def main():

    parser = argparse.ArgumentParser(description="LibraLens CLI")
    subparsers = parser.add_subparsers(dest="command")
    eval_parser = subparsers.add_parser("eval", help="evaluate MARC records")
    add_eval_arguments(eval_parser)
    annotate_parser = subparsers.add_parser("annotate", help="open an existing rating session")
    annotate_parser.add_argument("output", help="directory containing an rating session")

    if len(sys.argv) > 1 and sys.argv[1] not in ("eval", "annotate", "-h", "--help"):
        args = parser.parse_args(["eval"] + sys.argv[1:])
    else:
        args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    try:
        if args.command == "annotate":
            LibraLens.annotate(args.output)
        else:
            evaluate(args)

    except ValueError as e:
        parser.error(str(e))

if __name__ == "__main__":
    main()