# (ref)data

__Note__ that the data files in this repository are only compatible with openLCA
2. See the version tags for older versions of these files.

This repository contains reference data (units, flow properties, flows etc.) and
Life Cycle Impact Assessment (LCIA) methods for
[openLCA](https://www.openlca.org/) and the databases on [openLCA
Nexus](https://nexus.openlca.org). The database templates in openLCA are
directly created from the main branch of this repository. Contributions like bug
reports or pull requests are very welcome.


## Content

* [docs](./docs): contains the documentation of the CSV format for
  [reference data](./docs/format_csv_ref_data.md) and
  [mapping files](./docs/format_csv_flow_mapping.md)
* [refdata](./refdata/): contains files with reference data, LCIA methods, and
  mapping files
* [scripts](./scripts/): contains utilities for packaging and validation


## Usage

We may provide prepared packages as releases. The current LCIA method package
is available on openLCA Nexus. The data in the `refdata` folder can be
directly imported into openLCA via the integrated Python editor:

```py

# 1. create an empty database and activate it
# 2. checkout or download the data repository
# 3. let the path below point to the `refdata` folder

refdata_path = '/full/path/top/data/refdata'


from java.util.function import Consumer

class MessageLog(Consumer):

  def __init__(self, fn):
    self.accept = fn

imp = RefDataImport(File(refdata_path), db)
imp.log().listen(MessageLog(lambda m: m.log()))  # log import messages
imp.run()  # this can take a bit

```

You can also export the reference data of a database via the integrated
Python editor in openLCA:

```py
refdata_path = '/full/path/top/data/refdata'
RefDataExport(File(refdata_path), db).run()
```

----

<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img
alt="Creative Commons License" style="border-width:0"
src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />This work
is licensed under a <a rel="license"
href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons
Attribution-ShareAlike 4.0 International License</a>.
