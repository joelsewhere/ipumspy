# ipumspy

The goal of this project is better incorporate the IPUMS API into the Python ecosystem. 

Below is a recreation of the starter code from the IPUMS API documentation, using ipumspy:

```python
import os
from ipumspy import NHGIS

key = os.getenv('IPUMS_KEY')
api = NHGIS(key)

dataset_1 = api.dataset(dataset = "1988_1997_CBPa", data_tables = ["NT001"],
                        geog_levels = ["county"],
                        breakdowns = ["bs30.si0762", "bs30.si2026"],
                        years=[1988, 1989, 1990, 1991, 1992, 1993, 1994])

dataset_2 = api.dataset(dataset = "2000_SF1b", data_tables = ["NP001A"],
                        geog_levels = ["blck_grp"])

time_series = api.time_series(data_table = "A00", geog_levels = ["state"])

api.create_extract(datasets = [dataset_1, dataset_2], 
                   time_series_tables=time_series,
                   shapefiles = ["us_state_1790_tl2000"],
                   time_series_table_layout = "time_by_file_layout",
                   geographic_extents = ["010"],
                  breakdown_and_data_type_layout = "single_file")
```

# IPUMS

**[IPUMS](https://ipums.org/)**, is an incredibly reliable tool for harmonizing variables across different samples of census data and has been instrumental in making public data easily accessible.

In December of 2019 general access to the NHGIS API [was announced](https://forum.ipums.org/t/announcing-general-availability-of-nhgis-apis/3304).

API Documentation, example code, and developments updates for the API can be found [here](https://developer.ipums.org/)

----------------

<details><summary><b>Development Updates</b></summary>

- *10/24/20* `NHGIS` class developed and pushed to github.
  - This class uses two subclasses `Dataset` and `TimeSeries` to validate and create the json request that aligns with API documentation.
  - To make requests with NHGIS, you can use the `.create_extract` method.
  - **Issues:** The download links that result from a completed data extract request do not seem to work. A demonstration of this problem can be found in the [demo notebook](./demo.ipynb).
</details>

----------------

