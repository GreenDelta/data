import csv


class Unit:

    empty = None

    def __init__(self):
        self.uid = ''
        self.name = ''
        self.factor = 1.0


Unit.empty = Unit()


class UnitGroup:

    empty = None

    def __init__(self):
        self.uid = ''
        self.name = ''
        self.ref_unit = Unit.empty
        self.units = []  # type: List[Unit]


UnitGroup.empty = UnitGroup()


class FlowProperty:

    empty = None

    def __init__(self):
        self.uid = ''
        self.name = ''
        self.unit_group = UnitGroup.empty


FlowProperty.empty = FlowProperty()


class Flow:

    empty = None

    def __init__(self):
        self.uid = ''
        self.name = ''
        self.category = ''
        self.cas = ''
        self.formula = ''
        self.ref_flow_property = FlowProperty.empty


Flow.empty = Flow()


class ImpactFactor:

    def __init__(self):
        self.flow = Flow.empty
        self.factor = 1.0


class Impact:

    def __init__(self):
        self.uid = ''
        self.name = ''
        self.unit = ''
        self.factors = []  # type: List[ImpactFactor]


class Method:

    def __init__(self):
        self.uid = ''
        self.name = ''
        self.impacts = []  # type: List[Impact]


def read_unit_groups() -> dict:

    groups = {}
    ref_units = {}
    for row in read_csv('./refdata/unit_groups.csv'):
        group = UnitGroup()
        group.uid = row[0]
        group.name = row[1]
        groups[group.uid] = group
        ref_units[group.uid] = row[5]

    for row in read_csv('./refdata/units.csv'):
        unit = Unit()
        unit.uid = row[0]
        unit.name = row[1]
        unit.factor = float(row[3])
        group = groups.get(row[5])
        if group is None:
            print('Unknown group for unit %s' % unit.name)
            continue
        group.units.append(unit)
        ref_unit = ref_units[group.uid]
        if ref_unit == unit.uid:
            group.ref_unit = unit

    return groups


def read_flow_properties() -> dict:
    unit_groups = read_unit_groups()
    props = {}
    for row in read_csv('./refdata/flow_properties.csv'):
        prop = FlowProperty()
        prop.uid = row[0]
        prop.name = row[1]
        props[prop.uid] = prop
        ug = unit_groups.get(row[4])
        if ug is None:
            print('Unknown unit group for flow prop. %s' % prop.name)
            continue
        prop.unit_group = ug
    return props


def read_csv(path: str, separator=';', skip_first=False) -> list:
    rows = []
    with open(path, 'r', encoding='utf-8') as stream:
        reader = csv.reader(stream, delimiter=separator)
        if skip_first:
            next(reader)
        for row in reader:
            rows.append(row)
    return rows


def read_category_paths() -> dict:
    cats = {}
    for cat in read_csv('./refdata/categories.csv'):
        cats[cat[0]] = cat

    paths = {}
    for cat in cats.values():
        path = cat[1]
        parent = cats.get(cat[4])
        while parent is not None:
            path = parent[1] + '/' + path
            parent = cats.get(parent[4])

        if path.startswith('Elementary flows/'):
            path = path[17:]
        paths[cat[0]] = path

    return paths


def as_file_name(s: str) -> str:
    fname = ''
    last = ''
    for char in s:
        c = char if char.isalnum() else '_'
        if c == '_' and last == '_':
            continue
        last = c
        fname += c
    return fname.strip('_')


if __name__ == "__main__":

    # ids -> names
    methods = {}
    method_rows = read_csv('./impact_data/olca_LCIA_IM_table.csv',
                           separator=',', skip_first=True)
    for row in method_rows:
        methods[row[0]] = row[1]

    impacts = {}
    impact_rows = read_csv('./impact_data/olca_LCIA_IC_table.csv',
                           separator=',', skip_first=True)
    for row in impact_rows:
        impacts[row[0]] = row

    factors = {}

    for m in methods.values():
        print(as_file_name(m))

    print(read_flow_properties())
