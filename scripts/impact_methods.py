import os
import csv
from collections import namedtuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REF_DIR = os.path.join(BASE_DIR, 'refdata')
LCIA_DIR = os.path.join(BASE_DIR, 'LCIA method', 'categories')


LciaMethod = namedtuple('LciaMethod', ('IMPACT_CATEGORY_UUID', 'FILENAME', 'IMPACT_METHOD', 'IMPACT_CATEGORY', 'REFERENCE_UNIT'))


class EmptyMethod(Exception):
    pass


def _read_first_line(filename):
    fullname = os.path.join(LCIA_DIR, filename)
    with open(fullname, 'r', encoding='utf-8-sig') as fp:
        rr = csv.DictReader(fp)
        try:
            d = next(rr)
        except StopIteration:
            raise EmptyMethod
        return d


def generate_impacts_list():
    methods = os.listdir(LCIA_DIR)
    entries = []
    for filename in methods:
        if not filename.lower().endswith('csv'):
            continue
        try:
            firstline = _read_first_line(filename)
        except EmptyMethod:
            print('empty method: %s' % filename)
            continue
        try:
            entries.append(LciaMethod(firstline['IMPACT_CATEGORY_UUID'],
                                      filename,
                                      firstline['IMPACT_METHOD'],
                                      firstline['IMPACT_CATEGORY'], firstline['REFERENCE_UNIT']))
        except KeyError as e:
            print('%s: KeyError %s' % (filename, e))
            continue

    with open(os.path.join(REF_DIR, 'impact_categories.csv'), 'w') as fp:
        wr = csv.DictWriter(fp, fieldnames=LciaMethod._fields, quoting=csv.QUOTE_ALL, delimiter=";")  # _fields is not really protected
        for entry in entries:
            wr.writerow(entry._asdict())  # _asdict is not really protected


if __name__ == '__main__':
    generate_impacts_list()
