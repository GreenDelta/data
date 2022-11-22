import csv

from pathlib import Path


def main():
    catset: set[str] = set()
    path = Path(__file__).parent.parent / "refdata" / "flows.csv"
    with open(path, "r", encoding="utf-8") as inp:
        reader = csv.reader(inp)
        next(reader)  # skip header
        for row in reader:
            catset.add(row[3])

    categories = list(catset)
    categories.sort()
    for cat in categories:
        print(cat)


if __name__ == "__main__":
    main()
