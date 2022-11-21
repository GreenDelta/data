import json
import shutil

import model
import olca_schema as lca
import olca_schema.zipio as zipio

from pathlib import Path
from typing import TypeVar

VERSION = "2.0.0"

_BUILD_DIR = Path(__file__).parent.parent / "build"
E = TypeVar("E", bound=lca.RootEntity)
_UNITS = f"openLCA ref. units {VERSION}"
_FLOWS = f"openLCA ref. flows {VERSION}"


def main():
    if not _BUILD_DIR.exists():
        _BUILD_DIR.mkdir(parents=True)
    _write_flow_lib()

def _write_flow_lib(data: model.RefData | None = None):
    if data is None:
        d = model.RefData.read(model.RefDataSet.FLOWS)
    else:
        d = data
    _write_unit_lib(d)

    flow_dir = _BUILD_DIR / "flows"
    if flow_dir.exists():
        shutil.rmtree(flow_dir)
    flow_dir.mkdir()


def _write_unit_lib(data: model.RefData | None = None):
    if data is None:
        d = model.RefData.read(model.RefDataSet.UNITS)
    else:
        d = data

    unit_dir = _BUILD_DIR / "units"
    if unit_dir.exists():
        shutil.rmtree(unit_dir)
    unit_dir.mkdir()

    with zipio.ZipWriter(str(unit_dir / "meta.zip")) as z:
        _write(z, d.unit_groups)
        _write(z, d.flow_properties)
        _write(z, d.currencies)

    with open(unit_dir / "library.json", "w", encoding="utf-8") as info:
        json.dump({"name": _UNITS}, info)

    unit_pack = _BUILD_DIR / _UNITS
    if unit_pack.exists():
        unit_pack.unlink()
    shutil.make_archive(str(unit_pack), "zip", str(unit_dir))


def _write(writer: zipio.ZipWriter, data: dict[str, E]):
    handled = set()
    for e in data.values():
        if e.id in handled:
            continue
        handled.add(e.id)
        writer.write(e)


if __name__ == "__main__":
    main()
