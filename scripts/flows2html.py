import csv

from typing import Dict, Iterator, List


def read_csv(path: str, separator=';', skip_first=False) -> Iterator[List[str]]:
    with open(path, 'r', encoding='utf-8') as stream:
        reader = csv.reader(stream, delimiter=separator)
        if skip_first:
            next(reader)
        for row in reader:
            yield row


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


if __name__ == "__main__":
    category_paths = read_category_paths()
    props = {}
    for prop in read_csv('./refdata/flow_properties.csv'):
        props[prop[0]] = prop

    flows = [flow for flow in read_csv('./refdata/flows.csv')]
    flows.sort(key=lambda flow: flow[1])

    text = '''
    <!DOCTYPE html>
    <html lang="en">

    <head>
        <meta charset="utf-8">
        <title>openLCA reference flows</title>
        <style>
            body {
                font-family: Arial, Helvetica, sans-serif;
            }
            td {
                padding: 5px;
            }
            thead {
                font-weight: bold;
            }
            .even {
                background-color: lavender;
            }
        </style>
    </head>

    <body>
        <h1>openLCA reference flows</h1>
        <table>
            <thead>
                <tr>
                    <td>Name</td>
                    <td>Category</td>
                    <td>CAS</td>
                    <td>Formula</td>
                    <td>Flow property</td>
                </tr>
            </thead>
            <tbody>
    '''.strip()
    i = 0
    for flow in flows:
        if i % 2 == 0:
            text += '<tr class="even">'
        else:
            text += '<tr>'
        text += '<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            flow[1], category_paths.get(flow[3]), flow[5], flow[6],
            props.get(flow[7])[1])
        i += 1
    text += '</tbody></table></body></html>'

    with open('flows.html', 'w', encoding='utf-8') as stream:
        stream.write(text)
