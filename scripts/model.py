import csv
import logging as log
import olca_schema as lca

from enum import Enum
from pathlib import Path
from typing import Iterable

_ref_dir = Path(__file__).parent.parent / "refdata"


class RefDataSet(Enum):
    UNITS = 1
    FLOWS = 2
    ALL = 3


class RefData:
    def __init__(self):
        self.units: dict[str, lca.Unit] = {}
        self.unit_groups: dict[str, lca.UnitGroup] = {}
        self.currencies: dict[str, lca.Currency] = {}
        self.flow_properties: dict[str, lca.FlowProperty] = {}
        self.flows: dict[str, lca.Flow] = {}
        self.locations: dict[str, lca.Location] = {}
        self.impact_categories: dict[str, lca.ImpactCategory] = {}
        self.impact_methods: dict[str, lca.ImpactMethod] = {}

    @staticmethod
    def read(subset=RefDataSet.ALL) -> "RefData":
        data = RefData()
        _units_into(data)
        _currencies_into(data)
        if subset == RefDataSet.UNITS:
            return data
        _flows_into(data)
        _locations_into(data)
        if subset == RefDataSet.FLOWS:
            return data
        _impact_categories_into(data)
        _impact_methods_into(data)
        return data


def _units_into(data: RefData):

    # collect units as {group_id -> list[Unit]}
    units: dict[str, list[lca.Unit]] = {}
    for row in _csv("units.csv"):
        unit = lca.Unit()
        unit.id = row[0]
        unit.name = row[1]
        unit.description = row[2]
        unit.conversion_factor = float(row[3])
        if syns := _opt(row[4]):
            unit.synonyms = [s.strip() for s in syns.split(";")]

        data.units[unit.id] = unit
        data.units[unit.name] = unit

        group_id = row[5]
        us = units.get(group_id)
        if us is None:
            units[group_id] = [unit]
        else:
            us.append(unit)

    # collect unit groups
    groups: dict[str, tuple[lca.UnitGroup, str]] = {}
    for row in _csv("unit_groups.csv"):
        group = lca.UnitGroup()
        ids = _fill_head(group, row)
        group.units = []
        ref_unit = row[5]
        for group_id in ids:
            data.unit_groups[group_id] = group
            for unit in units.get(group_id, []):
                group.units.append(unit)
                if ref_unit in (unit.id, unit.name):
                    unit.is_ref_unit = True
            groups[group_id] = (group, row[4])

    # collect flow properties
    for row in _csv("flow_properties.csv"):
        prop = lca.FlowProperty()
        ids = _fill_head(prop, row)
        for prop_id in ids:
            data.flow_properties[prop_id] = prop
        prop_type = _opt(row[5])
        if prop_type and prop_type.lower().startswith("e"):
            prop.flow_property_type = lca.FlowPropertyType.ECONOMIC_QUANTITY
        else:
            prop.flow_property_type = lca.FlowPropertyType.PHYSICAL_QUANTITY
        group_def = groups.get(row[4])
        if group_def is None:
            log.error("invalid unit group %s", row[4])
            continue
        (group, default_prop) = group_def
        prop.unit_group = _ref_of(group)
        if default_prop in ids:
            group.default_flow_property = _ref_of(prop)


def _currencies_into(data: RefData):
    refc: lca.Currency | None = None
    for row in _csv("currencies.csv"):
        c = lca.Currency()
        ids = _fill_head(c, row)
        for cid in ids:
            data.currencies[cid] = c
        c.code = row[5]
        c.conversion_factor = float(row[6])
        if row[4] in ids:
            refc = c

    if not refc:
        log.error("no reference currency defined")
        return
    for c in data.currencies.values():
        c.ref_currency = _ref_of(refc)


def _flows_into(data: RefData):
    for row in _csv("flows.csv"):
        flow = lca.Flow()
        (flow_id, _) = _fill_head(flow, row)
        data.flows[flow_id] = flow
        flow.flow_type = _flow_type_of(row[4])
        flow.cas = _opt(row[5])
        flow.formula = _opt(row[6])
        prop = data.flow_properties.get(row[7])
        if prop is None:
            log.error("invalid flow property %s in flow %s", row[7], flow_id)
            continue
        if prop is not None:
            flow.flow_properties = [
                lca.FlowPropertyFactor(
                    conversion_factor=1,
                    flow_property=_ref_of(prop),
                    is_ref_flow_property=True,
                )
            ]

    for row in _csv("flow_property_factors.csv"):
        flow = data.flows.get(row[0])
        if flow is None:
            log.error("invalid flow %s in flow property factors", row[0])
            continue
        prop = data.flow_properties.get(row[1])
        if prop is None:
            log.error("invalid property %s in flow property factors", row[1])
            continue
        factor = float(row[2])
        if flow.flow_properties is None:
            flow.flow_properties = [
                lca.FlowPropertyFactor(
                    conversion_factor=factor,
                    flow_property=_ref_of(prop),
                    is_ref_flow_property=factor == 1.0,
                )
            ]
            continue

        already_exists = False
        has_ref = False
        for f in flow.flow_properties:
            if not f.flow_property:
                continue
            if f.flow_property and f.flow_property.id == prop.id:
                already_exists = True
                break
            if f.is_ref_flow_property:
                has_ref = True

        if already_exists:
            continue
        flow.flow_properties.append(
            lca.FlowPropertyFactor(
                conversion_factor=factor,
                flow_property=_ref_of(prop),
                is_ref_flow_property=not has_ref and factor == 1.0,
            )
        )


def _locations_into(data: RefData):
    for row in _csv("locations.csv"):
        loc = lca.Location()
        ids = _fill_head(loc, row)
        for loc_id in ids:
            data.locations[loc_id] = loc
        loc.code = row[4]
        loc.latitude = float(row[5])
        loc.longitude = float(row[6])


def _impact_categories_into(data: RefData):

    for row in _csv("lcia_categories.csv"):
        impact = lca.ImpactCategory()
        (imp_id, _) = _fill_head(impact, row)
        impact.ref_unit = _opt(row[4])
        data.impact_categories[imp_id] = impact

    for path in (_ref_dir / "lcia_factors").iterdir():
        for row in _csv(path):
            impact = data.impact_categories.get(row[0])
            if impact is None:
                log.error("invalid impact category %s", row[0])
                continue
            flow = data.flows.get(row[1])
            if flow is None:
                log.error("invalid flow %s", row[1])
                continue
            prop = data.flow_properties.get(row[2])
            if prop is None:
                log.error("invalid flow property %s", row[2])
                continue
            unit = data.units.get(row[3])
            if unit is None:
                log.error("invalid unit %s", row[3])
                continue

            loc_id = _opt(row[4])
            location = data.locations.get(loc_id) if loc_id else None
            factor = lca.ImpactFactor(
                flow=_ref_of(flow),
                flow_property=_ref_of(prop),
                unit=lca.Ref(id=unit.id, name=unit.name, model_type="Unit"),
                location=_ref_of(location) if location else None,
            )
            try:
                factor.value = float(row[5])
            except:
                factor.formula = row[5]

            if impact.impact_factors is None:
                impact.impact_factors = [factor]
            else:
                impact.impact_factors.append(factor)


def _impact_methods_into(data: RefData):

    for row in _csv("lcia_methods.csv"):
        method = lca.ImpactMethod()
        ids = _fill_head(method, row)
        for method_id in ids:
            data.impact_methods[method_id] = method

    for row in _csv("lcia_method_categories.csv"):
        method = data.impact_methods.get(row[0])
        if method is None:
            log.error("invalid LCIA method %s", row[0])
            continue
        impact = data.impact_categories.get(row[1])
        if impact is None:
            log.error("incalid LCIA category %s", row[1])
            continue
        if method.impact_categories is None:
            method.impact_categories = [_ref_of(impact)]
        else:
            method.impact_categories.append(_ref_of(impact))

    for row in _csv("lcia_method_nw_sets.csv"):
        method = data.impact_methods.get(row[0])
        if method is None:
            log.error("invalid LCIA method %s", row[0])
            continue

        nw_set: lca.NwSet | None = None
        if method.nw_sets is None:
            method.nw_sets = []
        for nws in method.nw_sets:
            if nws.id == row[1]:
                nw_set = nws
                break
        if nw_set is None:
            nw_set = lca.NwSet(
                id=row[1],
                name=row[2],
                weighted_score_unit=_opt(row[6]),
            )
            method.nw_sets.append(nw_set)

        impact = data.impact_categories.get(row[3])
        if impact is None:
            log.error("incalid LCIA category %s", row[3])
            continue

        factor = lca.NwFactor(
            impact_category=_ref_of(impact),
            normalisation_factor=_opt_num(row[4]),
            weighting_factor=_opt_num(row[5]),
        )
        if nw_set.factors is None:
            nw_set.factors = [factor]
        else:
            nw_set.factors.append(factor)


def _flow_type_of(s: str) -> lca.FlowType | None:
    if s is None or s == "":
        return None
    match s[0]:
        case "e" | "E":
            return lca.FlowType.ELEMENTARY_FLOW
        case "p" | "P":
            return lca.FlowType.PRODUCT_FLOW
        case "w" | "W":
            return lca.FlowType.WASTE_FLOW


def _fill_head(e: lca.RootEntity, row: list[str]) -> tuple[str, str]:
    e.id = row[0]
    e.name = row[1]
    e.description = row[2]
    e.category = _opt(row[3])
    return (e.id, e.name)


def _csv(file: str | Path) -> Iterable[list[str]]:
    path = _ref_dir / file if isinstance(file, str) else file
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as inp:
        reader = csv.reader(inp)
        next(reader)  # skip header
        for row in reader:
            yield row


def _opt(s: str) -> str | None:
    if s is None or s.strip() == "":
        return s
    return s


def _opt_num(s: str) -> float | None:
    if s is None or s.strip() == "":
        return None
    try:
        return float(s)
    except:
        return None


def _ref_of(entity: lca.RootEntity) -> lca.Ref:
    return lca.Ref(
        model_type=entity.__class__.__name__,
        id=entity.id,
        name=entity.name,
    )
