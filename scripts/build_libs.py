import csv
import json
import logging as log
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Self, TypeVar

import model
import olca_schema as lca
from scipy import sparse
from olca_schema import zipio


VERSION = "2.0.0.alpha"

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
        log.info("init library %s", full_name)
        path = _LIB / full_name
        path.mkdir(exist_ok=True, parents=True)

        # copy dependencies
        if hasdeps := len(deps) > 0:
            log.info("copy dependencies of %s", full_name)
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
        log.info("write data to %s", self.name)
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
        log.info("package library %s", self.name)
        pack = f"{self.name}_lib"
        shutil.make_archive(str(_LIB / pack), "zip", str(self.path))
        return self


def main():
    if _LIB.exists():
        shutil.rmtree(str(_LIB))
    _LIB.mkdir(parents=True)

    data = model.RefData.read(model.RefDataSet.ALL)

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

    impact_lib = LibDir.of(
        "openLCA-LCIA-pack",
        deps=[
            unit_lib,
            flow_lib,
        ],
    )
    _build_impact_matrix(impact_lib.path, data)
    impacts = [i for i in data.impact_categories.values()]
    for i in impacts:
        i.impact_factors = None
    impact_lib.write(
        data.impact_methods.values(),
        impacts,
    ).package()


def _build_impact_matrix(libdir: Path, data: model.RefData):
    log.info("create impact matrix C in %s", libdir)
    flow_idx: dict[str, int] = {}
    impact_idx: dict[str, int] = {}
    rows: list[int] = []
    cols: list[int] = []
    vals: list[float] = []

    for impact in data.impact_categories.values():
        if impact.id is None or impact.impact_factors is None:
            continue
        row = impact_idx.get(impact.id, -1)
        if row == -1:
            row = len(impact_idx)
            impact_idx[impact.id] = row

        for factor in impact.impact_factors:
            if (
                factor.flow is None
                or factor.flow.id is None
                or factor.value is None
                or factor.value == 0
            ):
                continue
            col = flow_idx.get(factor.flow.id, -1)
            if col == -1:
                col = len(flow_idx)
                flow_idx[factor.flow.id] = col
            rows.append(row)
            cols.append(col)
            vals.append(factor.value)

    (k, m) = (len(impact_idx), len(flow_idx))
    if k == 0 or m == 0:
        log.warning("no LCIA factors found")
        return
    log.info("write %ix%i matrix C with %i entries", k, m, len(vals))
    csc = sparse.coo_array((vals, (rows, cols)), shape=(k, m)).tocsc()
    sparse.save_npz(str(libdir / "C.npz"), csc)
    _write_flow_idx(libdir, _swap_idx(flow_idx), data)
    _write_impact_idx(libdir, _swap_idx(impact_idx), data)


def _write_impact_idx(libdir: Path, idx: list[str], data: model.RefData):
    path = libdir / "index_C.csv"
    log.info("write impact category index %s", path)
    with open(path, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(
            [
                "index",
                "indicator ID",
                "indicator name",
                "indicator unit",
            ]
        )
        for (i, impact_id) in enumerate(idx):
            record = [i, impact_id, None, None]
            impact = data.impact_categories.get(impact_id)
            if impact is None:
                continue
            record[2] = impact.name
            record[3] = impact.ref_unit
            writer.writerow(record)


def _write_flow_idx(libdir: Path, idx: list[str], data: model.RefData):
    path = libdir / "index_B.csv"
    log.info("write flow index %s", path)
    with open(path, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(
            [
                "index",  # 0
                "is input",  # 1
                "flow ID",  # 2
                "flow name",  # 3
                "flow category",  # 4
                "flow unit",  # 5
                "flow type",  # 6
                "location ID",  # 7
                "location name",  # 8
                "location code",  # 9
            ]
        )
        for (i, flow_id) in enumerate(idx):
            record: list[Any] = [None] * 10
            record[0] = i
            record[2] = flow_id
            flow = data.flows.get(flow_id)
            if flow is None:
                log.error("invalid flow %s", flow_id)
                continue
            record[1] = _is_probably_input(flow)
            record[3] = flow.name
            record[4] = flow.category
            record[5] = _ref_unit_of(flow, data)
            record[6] = _type_of(flow)
            writer.writerow(record)


def _swap_idx(idx: dict[str, int]) -> list[str]:
    swapped: list[str] = [""] * len(idx)
    for (s, i) in idx.items():
        swapped[i] = s
    return swapped


def _ref_unit_of(flow: lca.Flow, data: model.RefData) -> str | None:
    if flow.flow_properties is None:
        return None
    for f in flow.flow_properties:
        if (
            not f.is_ref_flow_property
            or f.flow_property is None
            or f.flow_property.id is None
        ):
            continue
        prop = data.flow_properties.get(f.flow_property.id)
        if (
            prop is None
            or prop.unit_group is None
            or prop.unit_group.id is None
        ):
            return None
        group = data.unit_groups.get(prop.unit_group.id)
        if group is None or group.units is None:
            return None
        for unit in group.units:
            if unit.is_ref_unit:
                return unit.name
    return None


def _is_probably_input(flow: lca.Flow) -> str:
    if flow.category is None:
        return "false"
    if "resource" in flow.category.lower():
        return "true"
    else:
        return "false"


def _type_of(flow: lca.Flow) -> str:
    match flow.flow_type:
        case lca.FlowType.PRODUCT_FLOW:
            return "product"
        case lca.FlowType.WASTE_FLOW:
            return "waste"
        case _:
            return "elementary"


if __name__ == "__main__":
    main()
