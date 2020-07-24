import csv
import json

from typing import List, Dict


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

    def unit(self) -> str:
        if self.ref_flow_property is None:
            return ''
        ug = self.ref_flow_property.unit_group
        if ug is None or ug.ref_unit is None:
            return ''
        return ug.ref_unit.name


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


def read_unit_groups() -> Dict[str, UnitGroup]:

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


def read_flow_properties() -> Dict[str, FlowProperty]:
    unit_groups = read_unit_groups()
    props = {}
    for row in read_csv('./refdata/flow_properties.csv'):
        prop = FlowProperty()
        prop.uid = row[0]
        prop.name = row[1]
        props[prop.uid] = prop
        prop.unit_group = unit_groups.get(row[4], UnitGroup.empty)
    return props


def read_flows() -> Dict[str, Flow]:
    paths = read_category_paths()
    flow_props = read_flow_properties()
    flows = {}
    for row in read_csv('./refdata/flows.csv'):
        flow = Flow()
        flow.uid = row[0]
        flow.name = row[1]
        flow.category = paths.get(row[3], '')
        flow.cas = row[5]
        flow.formula = row[6]
        flow.ref_flow_property = flow_props.get(row[7], FlowProperty.empty)
        flows[flow.uid] = flow
    return flows


def read_impact_methods(flows: Dict[str, Flow]) -> Dict[str, Method]:
    methods = {}
    method_rows = read_csv('./impact_data/olca_LCIA_IM_table.csv',
                           separator=',', skip_first=True)
    for row in method_rows:
        method = Method()
        method.uid = row[0]
        method.name = row[1]
        methods[method.uid] = method

    impacts = {}
    impact_rows = read_csv('./impact_data/olca_LCIA_IC_table.csv',
                           separator=',', skip_first=True)
    for row in impact_rows:
        impact = Impact()
        impact.uid = row[0]
        impact.name = row[1]
        impact.unit = row[2]
        impacts[impact.uid] = impact
        method = methods.get(row[3])
        if method is None:
            continue
        method.impacts.append(impact)

    factor_rows = read_csv('./impact_data/olca_LCIA_IF_table.csv',
                           separator=',', skip_first=True)
    for row in factor_rows:
        val = row[2]
        if val == '0':
            continue
        impact = impacts.get(row[0])
        if impact is None:
            continue
        flow = flows.get(row[1])
        if flow is None:
            continue
        factor = ImpactFactor()
        factor.factor = val
        factor.flow = flow
        impact.factors.append(factor)

    return methods


def read_csv(path: str, separator=';', skip_first=False) -> list:
    rows = []
    with open(path, 'r', encoding='utf-8') as stream:
        reader = csv.reader(stream, delimiter=separator)
        if skip_first:
            next(reader)
        for row in reader:
            rows.append(row)
    return rows


def read_category_paths() -> Dict[str, str]:
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


def write_flow_sheet(flows: List[Flow]):
    with open('./scripts/spreadsheet.html', 'r', encoding='utf-8') as f:
        template = f.read()
        template = template.replace('/*title*/', 'Reference flows')
        data = {
            'name': 'Flows',
            'freeze': 'A2',
            'rows': {
                'len': len(flows) + 1,
                0: {
                    'cells': {
                        0: {'text': 'UUID'},
                        1: {'text': 'Category'},
                        2: {'text': 'Name'},
                        3: {'text': 'Ref. flow property'},
                        4: {'text': 'Ref. unit'},
                        5: {'text': 'CAS'},
                        6: {'text': 'Formula'},
                    }
                }
            }
        }
        rows = data['rows']
        for i in range(0, len(flows)):
            flow = flows[i]
            cells = {
                0: {'text': flow.uid},
                1: {'text': flow.category},
                2: {'text': flow.name},
                3: {'text': flow.ref_flow_property.name},
                4: {'text': flow.unit()},
                5: {'text': flow.cas},
                6: {'text': flow.formula},
            }
            rows[i + 1] = {'cells': cells}

        call = 'xs.loadData([%s]);' % json.dumps(data)
        template = template.replace('/*data-call*/', call)
        with open('./build/flows.html', 'w', encoding='utf-8') as out:
            out.write(template)


def write_method_sheets(methods: List[Method]):
    for method in methods:
        sheets = []
        for impact in method.impacts:
            data = {
                'name': impact.name,
                'freeze': 'A2',
                'rows': {
                    'len': len(impact.factors) + 1,
                    0: {
                        'cells': {
                            0: {'text': 'Category'},
                            1: {'text': 'Flow'},
                            2: {'text': 'Factor'},
                            3: {'text': 'Unit'},
                        }
                    }
                }
            }
            rows = data['rows']
            for i in range(0, len(impact.factors)):
                factor = impact.factors[i]
                cells = {
                    0: {'text': factor.flow.category},
                    1: {'text': factor.flow.name},
                    2: {'text': factor.factor},
                    3: {'text': impact.unit + '/' + factor.flow.unit()},
                }
                rows[i + 1] = {'cells': cells}
            sheets.append(data)

        with open('./scripts/spreadsheet.html', 'r', encoding='utf-8') as f:
            template = f.read()
            template = template.replace('/*title*/', method.name)
            call = 'xs.loadData(%s);' % json.dumps(sheets)
            template = template.replace('/*data-call*/', call)
            target = './build/%s.html' % as_file_name(method.name)
            with open(target, 'w', encoding='utf-8') as out:
                out.write(template)


if __name__ == "__main__":
    flow_dict = read_flows()
    flows = [flow for flow in read_flows().values()]
    flows.sort(key=lambda flow: flow.category + flow.name)
    write_flow_sheet(flows)
    method_dict = read_impact_methods(flow_dict)
    methods = [m for m in method_dict.values()]
    methods.sort(key=lambda m: m.name)
    write_method_sheets(methods)

    # write index.html
    print("write the index.html file")
    index = '''<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>openLCA LCIA methods and reference data</title>
    </head>
    <body>
        <h1>openLCA LCIA methods and reference data</h1>
        <ul>
            <li><a href="./flows.html" target="_blank">Reference flows</a></li>
    '''

    for method in methods:
        index += '<li><a href="./%s.html" target="_blank">%s</a></li>' % (
            as_file_name(method.name), method.name)

    index += '''
        </ul>
    </body>
    </html>'''

    with open('./build/index.html', 'w', encoding='utf-8') as out:
        out.write(index)
