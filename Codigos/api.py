## Libraires ################################################
import requests
import pandas as pd
from io import StringIO
import colorama, json

CENSUSMAP_DATA_URL = "https://censusmapper.ca/api/v1/data.csv"
CENSUSMAP_GEO_URL = "https://censusmapper.ca/api/v1/geo.geojson"
CENSUSMAP_API_KEY = 'CensusMapper_7d6cf359f1b54bcefc61205e032a318d'

## Class definition #########################################
class censusmap_api:
    def __init__(self, api_key = None):
        colorama.init()
        self.data_url = CENSUSMAP_DATA_URL
        self.geo_url = CENSUSMAP_GEO_URL
        if api_key is None: self.__api_key = CENSUSMAP_API_KEY
        else: self.__api_key = api_key

    # Return csv or geojson file from censusmap request.
    def get_census(self, dataset, level, vectors, regions, geo_format = None, save_file = False):
        ''' Function use example (parameters):
            get_census(dataset = "CA16", 
            level = "Regions", 
            vectors = ["v_CA16_1"], 
            regions = {"PR":["60","59","61","48","47","46","62","35","24","10","12","13","11"]})

            Notes:   
                * geo_fomat can be None, "sf" or "sp" 
                * save_file is able to save the file as "data.csv" (when geo_format=None) or "geo.geojson" (else)
        '''
        census_request = locals() # Save parameters
        del census_request["self"], census_request["save_file"] # And remove insignificant for request
        census_request["api_key"] = self.__api_key # Add api key
        # URL choose and geo_format handdled
        if geo_format is None or (geo_format != "sf" and geo_format != "sp"):
            del census_request["geo_format"] # Delete geo_format if not match
            url = self.data_url
        else: url = self.geo_url
        
        # Request
        response = requests.post(url = url, json = census_request)
        if response.ok:
            if "geo_format" in census_request.keys(): 
                census_data = response.json()
                if save_file: 
                    with open('geo.geojson', 'w') as fj: 
                        json.dump(census_data, fj)
            else: 
                census_data = pd.read_csv(StringIO(response.text))
                if save_file: census_data.to_csv("data.csv")
            return census_data
        else:
            print(colorama.Fore.RED + "[INFO]: Invalid request. Please check input parameters." + colorama.Fore.RESET)

    # Return dataframe with datasets information
    def list_census_datasets(self):
        response = requests.get(url="https://censusmapper.ca/api/v1/list_datasets")
        if response.ok:
            return pd.DataFrame(response.json())
        else:
            print(colorama.Fore.RED + "[INFO]: Invalid request." + colorama.Fore.RESET)

## Main #####################################################
if __name__ == "__main__":
    api = censusmap_api()
    census = api.get_census(dataset = "CA16",
        level = "Regions", 
        vectors = ["v_CA16_1"], 
        regions = {"PR":["60","59","61","48","47","46","62","35","24","10","12","13","11"]},
        geo_format = "sp",
        save_file=True
    )
    try: print(census.info())
    except: print(census["features"][0]["properties"])
