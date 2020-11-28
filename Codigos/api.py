## Libraires ################################################
import requests, sys, os, copy
import pandas as pd
from io import StringIO
import colorama, json, argparse, geopandas

CENSUSMAP_DATA_URL = "https://censusmapper.ca/api/v1/data.csv"
CENSUSMAP_GEO_URL = "https://censusmapper.ca/api/v1/geo.geojson"
CENSUSMAP_API_KEY = 'CensusMapper_7d6cf359f1b54bcefc61205e032a318d'

## Class definition #########################################
class censusmap_api:
    def __init__(self, api_key = None, directory = None):
        colorama.init()
        self.data_url = CENSUSMAP_DATA_URL
        self.geo_url = CENSUSMAP_GEO_URL
        self.dir = directory
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
                * geo_fomat can be None, "sf", "sp" or "NA"
                * save_file is able to save the file as "data.csv" (when geo_format=None) or "geo.geojson" (else)
        '''
        census_request = copy.deepcopy(locals()) # Save parameters
        del census_request["self"], census_request["save_file"] # And remove insignificant for request
        census_request["api_key"] = self.__api_key # Add api key
        # URL choose and geo_format handdled
        if geo_format is None or (geo_format != "sf" and geo_format != "sp" and geo_format != "NA"):
            del census_request["geo_format"] # Delete geo_format if not match
            url = self.data_url
        else:    
            url = self.geo_url
        
        # Request
        response = requests.post(url = url, json = census_request)
        if response.ok:
            if "geo_format" in census_request.keys(): 
                census_data = response.json()
                if save_file: 
                    fn = 'geo.geojson' if self.dir is None else os.path.join(self.dir, 'geo.geojson')
                    with open(fn, 'w') as fj: json.dump(census_data, fj)
            else: 
                census_data = pd.read_csv(StringIO(response.text))
                if save_file: 
                    fn = 'data.csv' if self.dir is None else os.path.join(self.dir, 'data.csv')
                    census_data.to_csv(fn)
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
def main(args):
    if args.option == "download":
        api = censusmap_api(api_key = args.api_key, directory = args.directory)
        if os.path.isfile(args.infile):
            with open(args.infile, "r") as f: info_dict = json.load(f)
        else:
            print(colorama.Fore.YELLOW + "[WARNING] Invalid input file. Load parameters by default" + colorama.Fore.RESET)
            info_dict = dict(dataset = args.dataset, vectors = args.vectors, regions = {"CT":"5050140.04"}, 
                geo_format = args.geo_format, level = "CT")
        
        if args.vectors is not None: 
            info_dict["vectors"] = args.vectors # Update vectors list
            print("[INFO] Input vectors:",args.vectors)
        if args.geo_format is not None: info_dict["geo_format"] = args.geo_format # Update geo_format
        info_dict["save_file"] = True
        
        census = api.get_census(**info_dict)
        if census is not None:
            try: print(census.info(), census)
            except: print(census["features"][0]["properties"])
    elif args.option == "scheme":
        info_dict = dict(dataset = args.dataset, vectors = [], regions = {}, geo_format = args.geo_format)
        for i_gm, geomap_f in enumerate(args.geo_map):
            if i_gm == 0:
                geo_map = geopandas.read_file(geomap_f, driver = "GeoJSON").rename(columns = {"id":"GeoUID"})
            else:
                geo_map = geo_map.append(geopandas.read_file(geomap_f, driver = "GeoJSON").rename(columns = {"id":"GeoUID"}))
        geo_map = geo_map.groupby(["t","GeoUID"]).head(1).set_index("t")
        for t in geo_map.index.unique():
            info_dict["level"] = t
            info_dict["regions"].update({t:geo_map["GeoUID"].to_list()})
        if args.vectors is not None: info_dict["vectors"] = args.vectors
        with open(args.outfile, "w") as f: json.dump(info_dict, f, indent = 4) # Save consult basic scheme
        print("[INFO]: Scheme save in {} successfully.".format(args.outfile))
    else:
        print("[INFO]: Nothing was doing.")

def parse_args():
    '''parse args'''
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, 
        description = 'Program to download databases from censusmapper.ca api. and generate basic information scheme',
        epilog = '''Example:\n\t >> python3 %(prog)s # Conection with database and simples consult''' + 
        '''\n\nNote: For more information, use python3 {download,scheme} -h to see more help info.''',)
    parser.add_argument('-v', '--version', action = 'version', version='%(prog)s 2.0')
    subparsers = parser.add_subparsers(help = 'Program mode chooses %(metavar)s', dest = "option")#, required = True)

    # Join-parameters
    parent_parser = argparse.ArgumentParser(add_help = False)
    parent_parser.add_argument('-vec', '--vectors', default = None, nargs = '+', help = "Vectors to make consult (default: %(default)s)")
    parent_parser.add_argument('-ds', '--dataset', default = "CA16", type = str, choices = ["CA01", "CA06", "CA11", "CA16"], help = "Dataset value (default: %(default)s)")
    parent_parser.add_argument('-gf', '--geo_format', default = None, type = str, choices = ["sf", "sp", "NA"], help = "Geoformat to geojson download (default: %(default)s)")

    # First program
    parser_a = subparsers.add_parser('download', help = 'Download program mode', description = "Program to download a geomap or csv-data", parents = [parent_parser])
    parser_a.add_argument('-ak', '--api_key', default = CENSUSMAP_API_KEY, type = str, help = "API KEY")
    parser_a.add_argument('-f', '--infile', default = "./Data/Maps/scheme.json", type = str, help = "File to load consult scheme (default: %(default)s)")
    parser_a.add_argument('-d', '--directory', default = None, type = str, help = "Directory to save result (default: %(default)s)")
    
    # Second program
    parser_b = subparsers.add_parser('scheme', help = 'Scheme generator program mode', description = "Program to create scheme with basic download info", parents = [parent_parser])
    parser_b.add_argument('-gm', '--geo_map', default = ["./Data/Maps/all_population_ottawa.geojson"], nargs = '+', help = "Geomap(s) to extraid GeoUID info (default: %(default)s)")
    parser_b.add_argument('-f', '--outfile', default = "./Data/Maps/scheme.json", type = str, help = "File to save basic scheme (default: %(default)s)")
    return parser.parse_args()

if __name__ == "__main__":
    main(parse_args())
    try: os.system("tput bel")
    except: pass

