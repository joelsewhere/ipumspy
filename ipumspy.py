import requests
import re
import warnings
import json

class NHGIS:
    '''API wrapper for the IPUMS NHGIS API.
    
    API Documentation: https://developer.ipums.org/docs/get-started/

    Arguments:
        api_key: Authorization key required for use of the IPUMS API. *Required*
                 API keys can be obtained here: https://account.ipums.org/api_keys
    '''
    def __init__(self, api_key):
        NHGIS.header = {"Authorization": api_key}
        self.documentation_link = 'https://developer.ipums.org/docs/get-started/'
        self.geographic_extent_options = {"010": "Nation",
                                    "020": "Region",
                                    "030": "Division2",
                                    "040": "State",
                                    "050": "State-County",
                                    "140": "State-County-Census Tract",
                                    "155": "State-Place-County",
                                    "160": "State-Place",
                                    "250": "American Indian Area/Alaska Native Area Hawaiian Home Land",
                                    "310": "Metropolitan Statistical Area/Micropolitan Statistical Area",
                                    "500": "State-Congressional District"}

        self.dataset = Dataset
        self.time_series = TimeSeries
        
    def dataset_metadata(self, dataset=None, data_table=None):
        '''
        Returns metadata for IPUMS datasets.
        
        Arguments:

        dataset: Default: None. If None, metadata for all available datasets is returned. If the name of a 
                                a dataset is given, metadata for the specified dataset is returned.
        data_table: Default: None. Data table can only be specified when `dataset` != None.
                                    If specified, metadata for the specified table is returned.
        '''
        if not dataset and not data_table:
            url = "https://api.ipums.org/metadata/nhgis/datasets?version=v1"
        elif dataset and not data_table:
            url = f"https://api.ipums.org/metadata/nhgis/datasets/{dataset}?version=v1"
        elif dataset and data_table:
            url = f"https://api.ipums.org/metadata/nhgis/datasets/{dataset}/data_tables/{data_table}?version=v1"
        elif not dataset and data_table:
            raise ValueError('A dataset must be provided when data_table != None')
        
        response = requests.get(url, headers=self.header)
        return self._validate_response(response)
    
    def time_series_metadata(self, data_table=None):
        '''
        Returns metadata for available time-series tables.

        Arguments:

        data_table: Default: None. If None, metadata for all data tables is returned.
                                    If specified, metadata for the specified table is returned.
        '''

        if not data_table:
            url = "https://api.ipums.org/metadata/nhgis/time_series_tables?version=v1"
        else:
            url = f"https://api.ipums.org/metadata/nhgis/time_series_tables/{data_table}?version=v1"
            
        response = requests.get(url, self.header)
        return self._validate_response(response)
    
    def shapefile_metadata(self):
        '''
        Returns metadata for available shapefiles.

        Arguments:

        No arguments are available for this method.
        '''

        url = "https://api.ipums.org/metadata/nhgis/shapefiles?version=v1"
        response = requests.get(url, self.header)
        return self._validate_response(response)
    
    def _validate_response(self, response):
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f'''A {response.status_code} error code was returned.\n 
            
            The following reason was given: {response.reason}
            
            API Keys can be obtained here: https://account.ipums.org/api_keys
            
            API documentation is here: {self.documentation_link}
            
            If need be, api error code documentation can be found here
            https://developer.mozilla.org/en-US/docs/Web/HTTP/Status''')
            
    def _validate_shapefiles(self, shapefiles):
        supported_files = [file['name'] for file in self.shapefile_metadata()]
        for file in shapefiles:
            if file not in supported_files:
                raise ValueError(f'Shapefile: {file} could not be found.')

    def _create_payload(self, datasets=None, time_series_tables=None, shapefiles=None, 
                      data_format='csv_no_header', breakdown_and_data_type_layout='separate_files',
                      time_series_table_layout=None, geographic_extents=None, description=None):
        '''
        Receives Dataset class objects and returns a json payload formatted according to the specifications
        of the IPUMS API.
        '''

        payload = {}
        if datasets:
            if isinstance(datasets, list):
                payload['datasets'] = {}
                for dataset in datasets:
                    if isinstance(dataset, Dataset):
                        if dataset.extent_required and not geographic_extents:
                            warnings.warn(f'''
                                            Geographic extent is required for
                                            Dataset {dataset.dataset} with the provided
                                            geographic levels. It is recommended that this
                                            extent be provided. By default, all geo extents are requested.
                                            
                                            Geograpghic extent options can be accessed with the
                                            NHGIS.geographic_extent_options attribute.''')
                            geographic_extents = ['*']
                        payload['datasets'].update(dataset.to_payload())
                    elif isinstance(dataset, dict):
                        payload['datasets'].update(dataset)
                        warnings.warn('''Validation is not provided for 
                                        dictionary inputs.
                                        
                                        Use of NHGIS.dataset is recommended.''')
                    else:
                        raise ValueError(f'datasets cannot be datatype: {type(dataset)}')
                        
        if time_series_tables:
            payload['time_series_tables'] = {}
            if isinstance(time_series_tables, list):
                for table in time_series_tables:
                    if isinstance(table, TimeSeries):
                        payload['time_series_tables'].update(table.to_payload())
                    elif isinstance(table, dict):
                        payload['time_series_tables'].update(table)
                        warnings.warn('''Validation is not provided for 
                                        dictionary inputs.
                                        
                                        Use of NHGIS.time_series is recommended.''')
                    else:
                        raise ValueError(f'time_series_tables cannot be datatype: {type(table)}')
            elif isinstance(time_series_tables, TimeSeries):
                payload['time_series_tables'].update(time_series_tables.to_payload())
            else:
                raise ValueError('time_series_tables must be a list or a TimeSeries instance.')
                        
        if shapefiles:
            payload['shapefiles'] = shapefiles
        
        if time_series_tables:
            payload['time_series_table_layout'] = time_series_table_layout
        
        if geographic_extents:
            payload['geographic_extents'] = geographic_extents
            
        payload['data_format'] = data_format
        
        if description:
            payload['description'] = description
        else:
            payload['description'] = 'ipumspy extract'
        
        if breakdown_and_data_type_layout:
            payload['breakdown_and_data_type_layout'] = breakdown_and_data_type_layout
        payload_json = json.dumps(payload)
        payload_json = json.loads(payload_json)

        return payload_json

    def create_extract(self, datasets=None, time_series_tables=None, shapefiles=None, 
                      data_format='csv_no_header', breakdown_and_data_type_layout='separate_files',
                      time_series_table_layout=None, geographic_extents=None, description=None):
        '''
        Submit a data extract request to the IPUMS NHGIS API.
        Currently, the IPUMS API does not support downloading directly from the API.
        An email notification will be received confirming your extract request.
        '''
        url = "https://api.ipums.org/extracts/?product=nhgis&version=v1"
        if shapefiles:
            self._validate_shapefiles(shapefiles)
        
        payload = self._create_payload(datasets=datasets, time_series_tables=time_series_tables, shapefiles=shapefiles, 
                      data_format=data_format, breakdown_and_data_type_layout=breakdown_and_data_type_layout,
                      time_series_table_layout=time_series_table_layout, 
                      geographic_extents=geographic_extents, description=description)

        result = requests.post(url, headers=self.header, json=payload).json()
        if 'number' in result:
            self.extract_number = result['number']
        return result
    
    def extract_status(self, status_only = True):
        '''
        Returns that status of the most recent data extract request.
        '''

        url = f"https://api.ipums.org/extracts/{self.extract_number}?product=nhgis&version=v1"
        response = requests.get(url, headers=self.header)
        if status_only:
            return response.json()['status']
        else:
            return response.json()

   

        
class Dataset(NHGIS):
    '''A wrapper for creating validating requests to the IPUMS NHGIS API.
        This class is used to format the json data structure for the NHGIS class.'''

    def __init__(self, dataset, data_tables, geog_levels, years=None, breakdowns=[]):
        self._validate(dataset, data_tables, geog_levels, years=years, breakdowns=breakdowns)
        self.dataset = dataset
        self.data_tables = data_tables
        self.geog_levels = geog_levels
        self.breakdowns = breakdowns
    
    def _validate(self, dataset, data_tables, geog_levels, years=None, breakdowns=[]):
        self.validate_types(dataset, data_tables, geog_levels, years, breakdowns)
        metadata = self.dataset_metadata(dataset=dataset)
        self.validate_data_tables(metadata, data_tables)
        self.validate_geog_levels(metadata, geog_levels)
        self.validate_years(metadata, years)
        self.validate_breakdowns(metadata, breakdowns)

    def validate_data_tables(self, metadata, data_tables):
        supported_tables = [value['name'] for value in metadata['data_tables']]
        for table in data_tables:
            if table not in supported_tables:
                raise ValueError(f'''Data Table: {table} is not supported for dataset: {metadata["name"]}''')
            
    def validate_geog_levels(self, metadata, geog_levels):
        supported_levels = [value['name'] for value in metadata['geog_levels']]
        for level in geog_levels:
            if level not in supported_levels:
                raise ValueError(f'''Geo level: {level} is not supported for dataset: {metadata["name"]}''')
        
        self.extent_required = False      
        for level in metadata['geog_levels']:
            if level['name'] in geog_levels:
                if level['has_geog_extent_selection']:
                    warnings.warn(f"""
                    
                    Geographic level: '{level['name']}' for Dataset: '{metadata['name']}'
                    requires geog_extent selection when extraction is made.
                    Available geographic extent options can be accessed with the
                    `NHGIS.geographic_extent_options` attribute.
                    The `NHGIS.create_extract` method has a default geog_extent of ['*']
                    
                    """)
                    self.extent_required = True
    
                    
    
    def validate_breakdowns(self, metadata, breakdowns):
        if breakdowns:
            if not 'breakdowns' in metadata:
                raise ValueError(f'Breakdowns are not supported for {metadata["name"]}')
            supported_breakdowns_list = metadata['breakdowns']
            supported_breakdowns = []
            for entry in supported_breakdowns_list:
                supported_breakdowns += [value['name'] for value in entry['breakdown_values']]
            for breakdown in breakdowns:
                if breakdown not in supported_breakdowns:
                    raise ValueError(f'''Breakdown: {breakdown} is not supported for dataset: {metadata["name"]}''')
        
    def is_multiyear(self, metadata):
        year_count = re.findall('(\d{4})', metadata['name'])
        if year_count:
            count = len(set(year_count))
        else:
            count = 1
        if count > 1:
            return True
        
    def year_range(self, metadata):
        years = re.findall('(\d{4})', metadata['name'])
        if years:
            years = [int(year) for year in years]
            return [year for year in range(years[0], years[1] + 1)]
            
        
    def validate_years(self, metadata, years):
        multiyear = self.is_multiyear(metadata)
        if multiyear and not years:
            raise ValueError(f'{metadata["name"]} has multiple years. `years` cannot be set to `None`.')
        if multiyear and years:
            supported_years = self.year_range(metadata)
            for year in years:
                if year not in supported_years:
                    raise ValueError(f'''Year: {year} is not support for dataset: {metadata["name"]}.''')
        if not multiyear and years:
            if len(years) > 1:
                raise ValueError(f'Dataset: {metadata["name"]} is not a multi year dataset, but multiple years were given.')
            supported_year = int(re.findall('(\d{4})', metadata["name"])[0])
            if not supported_year == years[0]:
                raise ValueError(f'Dataset: {metadata["name"]} supports the year {supported_year}, but {years[0]} was given.')
        if not multiyear and not years:
            self.years = []
        
        self.years = years

    
    def validate_types(self, dataset, data_tables, geog_levels, years, breakdowns):
        if type(dataset) != str:
            raise ValueError('dataset variable must be string.')
        if not type(data_tables) == list:
            raise ValueError('data_tables variable must be a list.')
        if not all(isinstance(item, str) for item in data_tables):
            raise ValueError('data_tables variable must be a list of strings.')
        if not type(geog_levels) == list:
            raise ValueError('geog_levels variable must be a list.')
        if not all(isinstance(item, str) for item in geog_levels):
            raise ValueError('geog_levels variable must be a list of strings.')
        if years:
            if type(years) != list:
                raise ValueError('year variable must be a list for multi year datasets.')
            if not all(isinstance(item, int) for item in years):
                raise ValueError('year variable must be a list of integers for multi year datasets.')
        if breakdowns:
            if type(breakdowns) != list:
                raise ValueError('If breakdowns != None, the variable must be a list.')
            if not all(isinstance(item, str) for item in breakdowns):
                raise ValueError('If breakdowns != None, the variable must be a list of strings.')
                
                
    def __repr__(self):
        return f'''Dataset(dataset: {self.dataset}, 
        Number of tables: {len(self.data_tables)},
        Number of geographies: {len(self.geog_levels)},
        Number of breakdowns: {len(self.breakdowns) if self.breakdowns else self.breakdowns},
        years: {self.years})'''
    
    def to_payload(self):
        payload = {self.dataset: {
            "years": [str(year) for year in self.years] if self.years else [],
            "breakdown_values": self.breakdowns,
            "data_tables": self.data_tables,
            "geog_levels": self.geog_levels
        }}
        return payload
    
class TimeSeries(NHGIS):
    '''A wrapper for creating validating requests to the IPUMS NHGIS API.
    This class is used to format the json data structure for the NHGIS class.'''
    def __init__(self, data_table, geog_levels='macro'):
        self.validate(data_table, geog_levels)

        
    def validate(self, data_table, geog_levels):
        self.validate_types(data_table, geog_levels)
        metadata = self.time_series_metadata(data_table=data_table)
        self.data_table = data_table
        self.validate_geog_levels(metadata, geog_levels)
        
    def validate_types(self, data_table, geog_levels):
        if type(data_table) != str:
            raise ValueError('`data_table` variable must be a string.')
        if geog_levels != 'macro':
            if type(geog_levels) != list:
                raise ValueError('If `geog_levels` != "macro" `geog_levels` must be a list.')
            if not all(isinstance(item, str) for item in geog_levels):
                raise ValueError('If `geog_levels` != "macro" `geog_levels` must be a list of strings.')
    
    def validate_geog_levels(self, metadata, geog_levels):
        if geog_levels == 'macro':
            self.geog_levels = [metadata['geog_levels'][0]['name']]
        else:
            supported_levels = [value['name'] for value in metadata['geog_levels']]
            for level in geog_levels:
                if level not in supported_levels:
                    raise ValueError(f'Time Series {metadata["name"]} does not support geo level: "{level}"')
            self.geog_levels = geog_levels
            
    def to_payload(self):
        payload = {self.data_table: {
            'geog_levels': self.geog_levels}}
        
        return payload