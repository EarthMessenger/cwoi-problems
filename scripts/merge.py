import json
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Merge contests data")
    parser.add_argument("files", nargs="+", help="list of contest data files")
    args = parser.parse_args()

    existed_contests_id = set()
    contests = []

    for fname in args.files:
        with open(fname) as f:
            for contest in json.load(f):
                if not contest["_id"] in existed_contests_id:
                    contests.append(contest)
                    existed_contests_id.add(contest["_id"])

    contests.sort(key = lambda c : c["startedAt"], reverse=True)
    print(json.dumps(contests))

if __name__ == "__main__":
    main()
