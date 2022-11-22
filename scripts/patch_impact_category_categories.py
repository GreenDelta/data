"""
This script adds the names of LCIA methods to the category field of the LCIA
categories of the corresponding method. This is just to better structure the
LCIA categories in the openLCA navigation. We moved to stand-alone LCIA
categories in openLCA 2 which results in many LCIA categories with duplicate
names in the navigation. Until we have better names and removed the duplicates,
we use this workaround... but this can be deleted when we cleaned up the LCIA
categories.
"""

import csv

from pathlib import Path
from typing import Iterable

_ref_dir = Path(__file__).parent.parent / "refdata"


def main():
    method_links = collect_method_links()
    method_names = collect_method_names()
    rows = []
    for row in _csv("lcia_categories.csv"):
        rows.append(row)
        impact_id = row[0]
        method_id = method_links.get(impact_id)
        if method_id is None:
            continue
        method_name = method_names.get(method_id)
        if method_name is None:
            continue
        row[3] = method_name

    with open(
        _ref_dir / "lcia_categories.csv", "w", encoding="utf-8", newline=""
    ) as out:
        writer = csv.writer(out)
        writer.writerow(
            [
                "ID",
                "Name",
                "Description",
                "Category",
                "Reference unit",
            ]
        )
        for row in rows:
            writer.writerow(row)


def collect_method_links() -> dict[str, str]:
    links: dict[str, str] = {}
    for row in _csv("lcia_method_categories.csv"):
        links[row[1]] = row[0]
    return links


def collect_method_names() -> dict[str, str]:
    names: dict[str, str] = {}
    for row in _csv("lcia_methods.csv"):
        names[row[0]] = row[1]
        names[row[1]] = row[1]
    return names


def _csv(file: str | Path) -> Iterable[list[str]]:
    path = _ref_dir / file if isinstance(file, str) else file
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as inp:
        reader = csv.reader(inp)
        next(reader)  # skip header
        for row in reader:
            yield row


if __name__ == "__main__":
    main()
