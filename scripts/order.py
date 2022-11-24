import csv
import operator
from dataclasses import dataclass
from pathlib import Path

Row = list[str]


@dataclass
class CsvFile:
    path: Path
    header: Row
    rows: list[Row]

    @staticmethod
    def read(path: Path) -> "CsvFile":
        with open(path, "r", encoding="utf-8") as inp:
            reader = csv.reader(inp)
            header = next(reader)
            rows = []
            for row in reader:
                rows.append(row)
        return CsvFile(path, header, rows)

    def write(self):
        with open(self.path, "w", encoding="utf-8", newline="") as out:
            writer = csv.writer(out)
            writer.writerow(self.header)
            for row in self.rows:
                writer.writerow(row)

    def sort(self, col_order: list[int]):
        self.rows.sort(key=operator.itemgetter(*col_order))


def apply():
    csv_files = [
        ("currencies.csv", [1, 0]),
        ("flow_properties.csv", [1, 0]),
        ("flows.csv", [1, 3, 0]),
        ("lcia_categories.csv", [1, 0]),
        ("lcia_method_categories.csv", [0, 1]),
        ("lcia_method_nw_sets.csv", [0, 2, 1, 3]),
        ("lcia_methods.csv", [1, 0]),
        ("locations.csv", [1, 0]),
        ("unit_groups.csv", [1, 0]),
        ("units.csv", [1, 0]),
    ]
    folder = Path(__file__).parent.parent / "refdata"
    for (file, order) in csv_files:
        path = folder / file
        csv_file = CsvFile.read(path)
        csv_file.sort(order)
        csv_file.write()

    # LCIA factors
    for path in (folder / 'lcia_factors').iterdir():
        csv_file = CsvFile.read(path)
        csv_file.sort([0, 1])
        csv_file.write()


if __name__ == "__main__":
    apply()
