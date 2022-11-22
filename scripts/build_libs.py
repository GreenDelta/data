import json
import shutil

import model
import olca_schema as lca
import olca_schema.zipio as zipio

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Self, TypeVar

VERSION = "2.0.0"

E = TypeVar("E", bound=lca.RootEntity)
_LIB = Path(__file__).parent.parent / "build" / "libraries"


@dataclass
class LibDir:
    path: Path

    @property
    def name(self) -> str:
        return self.path.name

    @staticmethod
    def of(base_name: str, deps: list["LibDir"] = []) -> "LibDir":
        full_name = f"{base_name}-{VERSION}"
        path = _LIB / full_name
        path.mkdir(exist_ok=True, parents=True)

        # copy dependencies
        if hasdeps := len(deps) > 0:
            depdir = path / "dependencies"
            depdir.mkdir(exist_ok=True)
            for dep in deps:
                shutil.copytree(dep.path, depdir / dep.name)

        # create the library manifest
        info: dict[str, Any] = {"name": full_name}
        if hasdeps:
            info["dependencies"] = [dep.name for dep in deps]
        with open(path / "library.json", "w", encoding="utf-8") as out:
            json.dump(info, out, indent="  ")

        return LibDir(path)

    def write(self, *seqs: Iterable[E]) -> Self:
        with zipio.ZipWriter(str(self.path / "meta.zip")) as z:
            for seq in seqs:
                handled = set()
                for e in seq:
                    if e.id in handled:
                        continue
                    handled.add(e.id)
                    z.write(e)
        return self

    def package(self) -> Self:
        shutil.make_archive(str(_LIB / self.name), "zip", str(self.path))
        return self


def main():
    if _LIB.exists():
        shutil.rmtree(str(_LIB))
    _LIB.mkdir(parents=True)

    data = model.RefData.read(model.RefDataSet.FLOWS)

    unit_lib = (
        LibDir.of("openLCA-ref-units")
        .write(
            data.currencies.values(),
            data.unit_groups.values(),
            data.flow_properties.values(),
        )
        .package()
    )

    flow_lib = (
        LibDir.of("openLCA-ref-flows", deps=[unit_lib])
        .write(
            data.flows.values(),
            data.locations.values(),
        )
        .package()
    )


if __name__ == "__main__":
    main()
