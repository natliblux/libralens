import argparse
from .loader import load_data

def main():

    parser = argparse.ArgumentParser(description="LibraLens CLI")
    parser.add_argument("input", help="File or directory containing MARC records to be evaluated")
    parser.add_argument("--gold", help="File or directory containing gold standard MARC records")
    parser.add_argument("--tools", nargs="+", help="Evaluation tools to run")

    args = parser.parse_args()
    data = load_data(args.input, args.gold)
    print(f"Loaded {len(data)} record(s)")

    if args.gold:
        print("Gold records loaded")

    if args.tools:
        print(f"Tools: {', '.join(args.tools)}")

if __name__ == "__main__":
    main()