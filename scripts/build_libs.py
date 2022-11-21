import shutil

import model
import olca_schema.zipio as zipio

from pathlib import Path

BUILD_DIR = Path(__file__).parent.parent / 'build'


def main():
    if not BUILD_DIR.exists():
        BUILD_DIR.mkdir(parents=True)

    data = model.RefData.read()

    unit_dir = BUILD_DIR / 'units'
    if unit_dir.exists():
        shutil.rmtree(unit_dir)
    unit_dir.mkdir()

    with zipio.ZipWriter(str(unit_dir / 'meta.zip')) as meta:
        for unit_group in data.unit_groups.values():
            meta.write(unit_group)
        for flow_prop in data.flow_properties.values():
            meta.write(flow_prop)
        for currency in data.currencies.values():
            meta.write(currency)


if __name__ == '__main__':
    main()
