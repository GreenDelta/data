from enum import StrEnum
from pathlib import Path
from typing import TypeVar

import model
import olca_schema as lca
from olca_schema import zipio

VERSION = "2.0.0.alpha"

E = TypeVar("E", bound=lca.RootEntity)


class Pack(StrEnum):
    UNITS = "openLCA-ref-units"
    FLOWS = "openLCA-ref-flows"
    ALL = "openLCA-LCIA-pack"


def main():
    data = model.RefData.read()
    for pack in Pack:
        _package(pack, data)


def _package(pack: Pack, data: model.RefData):
    path = (
        Path(__file__).parent.parent / "build" / f"{pack.value}_{VERSION}.zip"
    )
    print(f"write package: {path.name}")
    if path.exists():
        path.unlink()
    with zipio.ZipWriter(str(path)) as w:
        _write_all(data.unit_groups, w)
        _write_all(data.flow_properties, w)
        _write_all(data.currencies, w)
        if pack == Pack.UNITS:
            return
        _write_all(data.flows, w)
        _write_all(data.locations, w)
        if pack == Pack.FLOWS:
            return
        _write_all(data.impact_categories, w)
        _write_all(data.impact_methods, w)


def _write_all(d: dict[str, E], writer: zipio.ZipWriter):
    handled: set[str] = set()
    for e in d.values():
        if e.id is None or e.id in handled:
            continue
        writer.write(e)
        handled.add(e.id)


if __name__ == "__main__":
    main()
