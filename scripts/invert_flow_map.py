# This script swaps the source and target columns of a mapping file and inverts
# the respective conversion factors. Note that this does not work for provider
# mappings.

import csv

from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import cast

# CHANGE THE PATHS TO THE MAPPING FILES HERE:
INP = Path.home() / "Downloads/SimaPro_Import.csv"
OUT = Path.home() / "Downloads/SimaPro_Export.csv"


class Source(Enum):
    FLOW_UUID = 0
    FLOW_NAME = 3
    CATEGORY = 4
    LOCATION_CODE = 5
    FLOW_PROPERTY_UUID = 9
    FLOW_PROPERTY_NAME = 10
    UNIT_UUID = 13
    UNIT_NAME = 14


class Target(Enum):
    FLOW_UUID = 1
    FLOW_NAME = 6
    CATEGORY = 7
    LOCATION_CODE = 8
    FLOW_PROPERTY_UUID = 11
    FLOW_PROPERTY_NAME = 12
    UNIT_UUID = 15
    UNIT_NAME = 16
    PROVIDER_UUID = 17
    PROVIDER_NAME = 18
    PROVIDER_CATEGORY = 19
    PROVIDER_LOCATION = 20


@dataclass
class Row:
    row: list[str | float]

    def swap(self) -> "Row":
        s: list[str | float] = [""] * 20

        # invert the factor
        f = self._f(2)
        s[2] = 0 if f == 0 else 1 / f

        # map fields
        s[Source.FLOW_UUID.value] = self._s(Target.FLOW_UUID.value)
        s[Source.FLOW_NAME.value] = self._s(Target.FLOW_NAME.value)
        s[Source.CATEGORY.value] = self._s(Target.CATEGORY.value)
        s[Source.LOCATION_CODE.value] = self._s(Target.LOCATION_CODE.value)
        s[Source.FLOW_PROPERTY_UUID.value] = self._s(
            Target.FLOW_PROPERTY_UUID.value
        )
        s[Source.FLOW_PROPERTY_NAME.value] = self._s(
            Target.FLOW_PROPERTY_NAME.value
        )
        s[Source.UNIT_UUID.value] = self._s(Target.UNIT_UUID.value)
        s[Source.UNIT_NAME.value] = self._s(Target.UNIT_NAME.value)
        s[Target.FLOW_UUID.value] = self._s(Source.FLOW_UUID.value)
        s[Target.FLOW_NAME.value] = self._s(Source.FLOW_NAME.value)
        s[Target.CATEGORY.value] = self._s(Source.CATEGORY.value)
        s[Target.LOCATION_CODE.value] = self._s(Source.LOCATION_CODE.value)
        s[Target.FLOW_PROPERTY_UUID.value] = self._s(
            Source.FLOW_PROPERTY_UUID.value
        )
        s[Target.FLOW_PROPERTY_NAME.value] = self._s(
            Source.FLOW_PROPERTY_NAME.value
        )
        s[Target.UNIT_UUID.value] = self._s(Source.UNIT_UUID.value)
        s[Target.UNIT_NAME.value] = self._s(Source.UNIT_NAME.value)
        return Row(s)

    def _s(self, i: int) -> str:
        if len(self.row) <= i:
            return ""
        v = self.row[i]
        if v is None:
            return ""
        if isinstance(v, str):
            return v
        return str(v)

    def _f(self, i: int) -> float:
        if len(self.row) <= i:
            return 1.0
        v = self.row[i]
        try:
            return float(v)
        except:
            return 1.0


if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out, delimiter=";")
        with open(INP, "r", encoding="utf-8") as inp:
            reader = csv.reader(inp, delimiter=";")
            for row in reader:
                source = cast(list[str | float], row)
                target = Row(source).swap().row
                writer.writerow(target)
