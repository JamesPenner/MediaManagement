import os
import re
import csv
import sys
import yaml
import pandas as pd
from geopy.geocoders import Nominatim
from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict
from folium import Map, Marker, Icon
from pathlib import Path
from webbrowser import open_new
import traceback
import exiftool
import tqdm
import time
sys.path.append(r'C:\Media Management\Scripts')
# from Media_Management_Support_Functions import list_files, open_csv_in_excel
from config import f_warning, f_input, f_success, f_default, Location_fields, location_lookup, image_files

custom_user_agent = "my-application-test25"  # Replace with your application name or identifier
geolocator = Nominatim(user_agent=custom_user_agent, timeout=10)

# Load file paths in YAML file
yaml_file = r'C:\Media Management\Scripts\paths_config.yml'
with open(yaml_file, 'r') as file:
    config = yaml.safe_load(file)

verbose_output = True
debug = True

def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    radius_earth = 6371  # Radius of the Earth in kilometers
    distance = radius_earth * c * 1000  # Convert kilometers to meters

    return distance




# START
# ################################################################
# Show Locations on a Map Based on Lat/Longs #####################
# ################################################################

def generate_map_object(coordinates, location_name, map_options={}):
    """
    Creates a map centered on the given coordinates and adds a marker with a popup.

    Args:
        coordinates: A tuple of latitude and longitude.
        location_name: The name of the location to display in the popup.
        map_options: (Optional) A dictionary containing map options (zoom_start, map_type, etc.).

    Returns:
        A folium.Map object.
    """

    # Validate coordinates
    if not isinstance(coordinates, tuple) or len(coordinates) != 2:
        raise ValueError(f"Invalid coordinates: {coordinates}")

    # Set default map options
    default_map_options = {
        "zoom_start": 10,
        "map_type": "OpenStreetMap",
    }
    map_options = {**default_map_options, **map_options}

    # Create map and marker
    m = Map(location=coordinates, zoom_start=map_options["zoom_start"], tiles=map_options["map_type"])
    Marker(
        location=coordinates,
        popup=f"<h3>{location_name}</h3>",
        icon=Icon(color="blue", icon="info-sign"),
    ).add_to(m)

    return m

def show_location_on_map(coordinates, description="", filename_prefix="location_map", directory="maps"):
    """
    Shows the location on a map and opens it in a web browser.

    Args:
        coordinates: A tuple of latitude and longitude.
        description: A description of the location.
        filename_prefix: (Optional) Prefix for the map file name.
        directory: (Optional) Directory to save the map file.
    """

    if not coordinates:
        print("Location not found.")
        return

    print(f"The coordinates for {description} are: {coordinates}")

    # Create directory if it doesn't exist
    map_dir = Path(directory)
    map_dir.mkdir(parents=True, exist_ok=True)

    # Generate map and save as HTML file
    try:
        map_obj = generate_map_object(coordinates, description)
        file_path = map_dir / f"{filename_prefix}.html"
        map_obj.save(file_path)
        print(f"Map saved as '{file_path}'.")
    except Exception as e:
        print(f"Error saving the map: {e}")
        return

    # Open the map in a browser
    open_new(file_path)

# ################################################################
# Show Locations on a Map Based on Lat/Longs #####################
# ################################################################
# END


# #######################################################################################
# Find Locations Based on Lat/Long Start ################################################
# #######################################################################################

def find_possible_locations_based_on_gps_metadata(image_folder):
    # FUNCTION SUMMARY:
    # This function uses a csv file that lists location names with known lat/long coordinates. It looks for GPS data in a file. If there is any, the found GPS data is compared to the lat/long coordinates in the csv file. If the distance between those two points are within a specified threshold (the lookup_radius), the location with the smallest distance is listed as the assumed location where the image was taken.

    os.system("cls")

    ####################################
    #### Set variables for function ####
    ####################################

    # lookup_radius is the distance a point has to be from a known location before the point may be considered as a candidate for the known location
    lookup_radius = 0.5
    assumed_location = ""
    output_choice = ""
    min_value = ""
    min_pairs = {}
    file_counter = 0

    # # Check for any files required by this function. Any dependencies are included in the "dependency_list" list
    # dependency_list = [gps_lookup_csv]
    # check_dependencies(dependency_list)

    # Load gps_lookup
    gps_lookup = pd.read_csv(gps_lookup_csv, encoding="utf-8")
    gps_lookup = gps_lookup.mask(gps_lookup == "")

    found_locations = []
    found_locations_csv = r"C:\Media Management\Reports\found_gps_locations.csv"
    found_locations_header = [
        "file",
        "found_location",
        "distance_from_found_location",
        "latitude",
        "longitude",
        "google_map_url",
        "error",
    ]

    # Create the list of files to process
    files_to_process = load_files_to_process(image_folder)
    total_files = len(files_to_process)

    # Load Exiftool
    with exiftool.ExifToolHelper() as et:
        # Process each file in the list of files to process
        if verbose_output == False:
            # print("Finding possible locations based on GPS metadata...")
            output_option = tqdm(files_to_process, desc="Progress", unit="file")

        elif verbose_output == True:
            output_option = files_to_process
        for file in output_option:
            file_counter += 1
            error = "None"
            report_row = []
            location_dict = {}
            merged_dict = {}

            if verbose_output == True:
                print(f"Processing file {file_counter} of {total_files}: {file}")

            # Get metadata for file
            try:
                metadata = et.get_metadata(file)
            except:
                # Create entry for error log if metadata can't be read
                error = f"Can't read file metadata"

                report_row.append(file)
                report_row.append("-")
                report_row.append("-")
                report_row.append("-")
                report_row.append("-")
                report_row.append("-")
                report_row.append(error)
                found_locations.append(report_row)

                if verbose_output == True:
                    print(f"  {f_warning} Cannot read file metadata.{f_default}")

                if debug == True:
                    traceback.print_exc()
                continue

            for nested_dict in metadata:
                merged_dict.update(nested_dict)
            try:
                GPScomp = nested_dict["Composite:GPSPosition"]
            except:
                # Create entry for error log if no GPS data found
                error = "No GPS data found"

                report_row.append(file)
                report_row.append("-")
                report_row.append("-")
                report_row.append("-")
                report_row.append("-")
                report_row.append("-")
                report_row.append(error)
                found_locations.append(report_row)

                if verbose_output == True:
                    print(f"  {f_information} No GPS data found.{f_default}")

                if debug == True:
                    traceback.print_exc()
                continue

            # If GPS data is found, check if it's near a known location
            if GPScomp:
                # split the GPS Composite tag and access each value as a float (lat/long in decimal degrees)
                GPScomp = GPScomp.split()
                latitude1 = float(GPScomp[0])
                longitude1 = float(GPScomp[1])

                for index, row in gps_lookup.iterrows():
                    latitude2 = float(row["Latitude"])
                    longitude2 = float(row["Longitude"])
                    name = row["lookup_name"]

                    # Check the distance between the two points
                    distance = haversine(latitude1, longitude1, latitude2, longitude2)

                    # If the distance between the two points is less than the lookup radius, add the location to the dictionary of possible locations
                    if distance <= lookup_radius:
                        location_dict[name] = distance

                        # If there's a dictionary of possible locations, return the one that has the smallest distance away from the known location. This is the assumed location.
                        if location_dict:
                            min_value = min(location_dict.values())
                            min_pairs = {
                                k: v for k, v in location_dict.items() if v == min_value
                            }

                        assumed_location = list(min_pairs)[0]
                if verbose_output == True:
                    print(
                        f"{f_success}  GPS data indicates image take {min_value} metres from {assumed_location}{f_default}"
                    )

            else:
                if verbose_output == True:
                    print(
                        f"{f_information}  Found GPS data, but nothing found within a {lookup_radius/1000} metre radius.{f_default}"
                    )

            report_row.append(file)
            report_row.append(assumed_location)
            report_row.append(min_value)
            report_row.append(latitude1)
            report_row.append(longitude1)
            report_row.append(
                f"https://www.google.ca/maps/place/{latitude1},{longitude1}"
            )
            report_row.append(error)

            found_locations.append(report_row)

    # Output results to file
    # if write_output_to_file == True:
    # Write found locations to file
    write_list_to_csv(
        found_locations_csv, found_locations, header=found_locations_header
    )





# START
# ################################################################
# TESTING AND DEVELOPMENT ########################################
# ################################################################

# def use_location_lookup(location_name, location_lookup):
#     matching_values = []
#     expected_headers = ["GPSGPSLatitude", "GPSGPSLongitude", "GPSGPSLatitudeRef","GPSGPSLongitudeRef", "XMPiptcCoreLocation"]
    
#     with open(location_lookup, 'r', encoding='utf-8-sig') as file:  # 'utf-8-sig' handles the BOM
#         csv_reader = csv.DictReader(file)
        
#         # Clean the actual headers to remove non-printable characters
#         headers = [re.sub(r'[^\x20-\x7E]', '', header.strip()) for header in csv_reader.fieldnames]
        
#         for row in csv_reader:
#             if all(header in headers for header in expected_headers):
#                 location_column = next(header for header in headers if header == "XMPiptcCoreLocation")
#                 if row[location_column].strip() == location_name:
#                     latitude = float(row["GPSGPSLatitude"].strip())
#                     longitude = float(row["GPSGPSLongitude"].strip())
#                     latituderef = row["GPSGPSLatitudeRef"].strip()
#                     longituderef = row["GPSGPSLongitudeRef"].strip()

#                     # Check latitude reference and add a minus sign if necessary
#                     if latituderef == "S":
#                         latitude = -latitude

#                     # Check longitude reference and add a minus sign if necessary
#                     if longituderef == "W":
#                         longitude = -longitude

#                     # matching_values.append((latitude, longitude))

#             else:
#                 print("Expected column headers not found.")
#                 break

#     return latitude, longitude

def use_location_lookup2(location_name, location_lookup):
    matching_values = []
    expected_headers = ["GPSGPSLatitude", "GPSGPSLongitude", "GPSGPSLatitudeRef","GPSGPSLongitudeRef", "XMPiptcCoreLocation"]
    
    with open(location_lookup, 'r', encoding='utf-8-sig') as file:  # 'utf-8-sig' handles the BOM
        csv_reader = csv.DictReader(file)
        
        # Clean the actual headers to remove non-printable characters
        headers = [re.sub(r'[^\x20-\x7E]', '', header.strip()) for header in csv_reader.fieldnames]
        
        location_data = {}

        for row in csv_reader:
            if all(header in headers for header in expected_headers):
                location_column = next(header for header in headers if header == "XMPiptcCoreLocation")
                if row[location_column].strip() == location_name:
                    latitude = float(row["GPSGPSLatitude"].strip())
                    longitude = float(row["GPSGPSLongitude"].strip())
                    latituderef = row["GPSGPSLatitudeRef"].strip()
                    longituderef = row["GPSGPSLongitudeRef"].strip()
                    location_data["XMP-iptcCore:Location"] = row["XMPiptcCoreLocation"].strip()
                    location_data["XMP-iptcExt:LocationCreatedLocationName"] = row["XMP-iptcExtLocationCreatedLocationName"].strip()
                    location_data["XMP-iptcExt:LocationCreatedSublocation"] = row["XMP-iptcExtLocationCreatedSublocation"].strip()
                    location_data["XMP-iptcExt:LocationShownLocationName"] = row["XMP-iptcExtLocationShownLocationName"].strip()
                    location_data["XMP-iptcExt:LocationShownSublocation"] = row["XMP-iptcExtLocationShownSublocation"].strip()
                    location_data["IPTC:City"] = row["IPTCCity"].strip()
                    location_data["XMP-iptcExt:LocationCreatedCity"] = row["XMP-iptcExtLocationCreatedCity"].strip()
                    location_data["XMP-iptcExt:LocationShownCity"] = row["XMP-iptcExtLocationShownCity"].strip()
                    location_data["XMP-photoshop:City"] = row["XMP-photoshopCity"].strip()
                    location_data["XMP-photoshop:State"] = row["XMP-photoshopState"].strip()
                    location_data["IPTC:Province-State"] = row["IPTCProvince-State"].strip()
                    location_data["XMP-iptcExt:LocationCreatedProvinceState"] = row["XMP-iptcExtLocationCreatedProvinceState"].strip()
                    location_data["XMP-iptcExt:LocationShownProvinceState"] = row["XMP-iptcExtLocationShownProvinceState"].strip()
                    location_data["IPTC:Country-PrimaryLocationName"] = row["IPTCCountry-PrimaryLocationName"].strip()
                    location_data["XMP-iptcExt:LocationCreatedCountryName"] = row["XMP-iptcExtLocationCreatedCountryName"].strip()
                    location_data["XMP-iptcExt:LocationShownCountryName"] = row["XMP-iptcExtLocationShownCountryName"].strip()
                    location_data["XMP-photoshop:Country"] = row["XMP-photoshopCountry"].strip()
                    location_data["IPTC:Country-PrimaryLocationCode"] = row["IPTCCountry-PrimaryLocationCode"].strip()
                    location_data["XMP-iptcExt:LocationShownCountryCode"] = row["XMP-iptcExtLocationShownCountryCode"].strip()
                    location_data["XMP-iptcCore:CountryCode"] = row["XMP-iptcCoreCountryCode"].strip()
                    location_data["XMP-iptcExt:LocationCreatedCountryCode"] = row["XMP-iptcExtLocationCreatedCountryCode"].strip()
                    location_data["XMP-FamilyArchive:LocalityGeneral"] = row["XMP-FamilyArchiveLocalityGeneral"].strip()
                    location_data["XMP-FamilyArchive:LocalitySpecific"] = row["XMP-FamilyArchiveLocalitySpecific"].strip()
                    location_data["XMP-FamilyArchive:LocalityType"] = row["XMP-FamilyArchiveLocalityType"].strip()
                    location_data["GPS:GPSLatitude"] = row["GPSGPSLatitude"].strip()
                    location_data["GPS:GPSLongitude"] = row["GPSGPSLongitude"].strip()

                    # Check latitude reference and add a minus sign if necessary
                    if latituderef == "S":
                        latitude = -latitude
                    location_data["GPS:GPSLatitude"] = latitude

                    # Check longitude reference and add a minus sign if necessary
                    if longituderef == "W":
                        longitude = -longitude
                    location_data["GPS:GPSLongitude"] = longitude

            else:
                print("Expected column headers not found.")
                break

    return location_data

def write_location_data_to_csv(filename, fieldnames, data_dict):
    # Check if the file exists; if not, create a new file and write headers
    file_exists = True
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            if not list(reader):
                file_exists = False
    except FileNotFoundError:
        file_exists = False

    with open(filename, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # If the file is new or empty, write the headers
        if not file_exists:
            writer.writeheader()

        # Write data from the dictionary as a new row
        writer.writerow(data_dict)

# def get_location_metadata(path_to_scan):

#     files_to_process = list_files(path_to_scan, recursive=True, include=["jpg","jpeg","mp4"], exclude=None)
#     # for file in files_to_process:
#         # print(file)

#     file_counter = 0
#     total_files = len(files_to_process)
#     csv_log = r"c:\test\location_data.csv"

#   # Load Exiftool
#     with exiftool.ExifToolHelper() as et:
#         # Process each file in the list of files to process
#         if verbose_output == False:
#             print("Finding possible locations based on GPS metadata...")
#             output_option = tqdm(files_to_process, desc="Progress", unit="file")

#         elif verbose_output == True:
#             output_option = files_to_process
        
#         for file in output_option:
#             csv_headers = ""
#             error = ""
#             file_counter += 1
#             error = "None"
#             report_row = []
#             location_dict = {}
#             merged_dict = {}


#             if verbose_output == True:
#                 print(f"Processing file {file_counter} of {total_files}: {file}")

#             # Get metadata for file
#             try:
#                 metadata = et.get_metadata(file)
#                 # print(metadata)
#             except:
#                 # Create entry for error log if metadata can't be read
#                 error = (f"{f_warning}Can't read file metadata{f_default}")

#                 if verbose_output == True:
#                     print(f"  {f_warning} Cannot read file metadata.{f_default}")

#                 if debug == True:
#                     traceback.print_exc()
#                 continue

#             for nested_dict in metadata:
#                 merged_dict.update(nested_dict)

#             metadata_location = ""
#             location_data = {}
#             for field in Location_fields:
#                 try:
#                     metadata_location = nested_dict[field]
#                 except:
#                     pass

#             if not metadata_location:
#                 print(f"{f_warning}Can't find location description in {file}{f_default}")
#                 continue

#             else:
#                 csv_headers = ["SourceFile","XMP-iptcCore:Location","XMP-iptcExt:LocationCreatedLocationName","XMP-iptcExt:LocationCreatedSublocation","XMP-iptcExt:LocationShownLocationName","XMP-iptcExt:LocationShownSublocation","IPTC:City","XMP-iptcExt:LocationCreatedCity","XMP-iptcExt:LocationShownCity","XMP-photoshop:City","XMP-photoshop:State","IPTC:Province-State","XMP-iptcExt:LocationCreatedProvinceState","XMP-iptcExt:LocationShownProvinceState","IPTC:Country-PrimaryLocationName","XMP-iptcExt:LocationCreatedCountryName","XMP-iptcExt:LocationShownCountryName","XMP-photoshop:Country","IPTC:Country-PrimaryLocationCode","XMP-iptcExt:LocationShownCountryCode","XMP-iptcCore:CountryCode","XMP-iptcExt:LocationCreatedCountryCode","XMP-FamilyArchive:LocalityGeneral","XMP-FamilyArchive:LocalitySpecific","XMP-FamilyArchive:LocalityType","GPS:GPSLatitude","GPS:GPSLongitude","Parser:GPSLatitude","Parser:GPSLongitude","Parser:Address","Parser:Distance"]
                
#                 if isinstance(metadata_location, list):
#                     metadata_location_for_lookup = ', '.join(str(element) for element in metadata_location)
#                     metadata_location_for_geoparser = metadata_location = metadata_location[0]
#                 else:
#                     metadata_location_for_lookup = metadata_location
#                     metadata_location_for_geoparser = metadata_location

#                 location_data = use_location_lookup2(metadata_location_for_lookup, location_lookup)
#                 if location_data:
#                     latitdue = location_data["GPS:GPSLatitude"]
#                     longitude = location_data["GPS:GPSLongitude"]
#                     location_data["SourceFile"] = file
#                     location_lookup_coordinates = (latitdue, longitude)
#                     print(f"{f_success}Location Found in Location Index: {f_default}using {field} {metadata_location_for_lookup}: {location_lookup_coordinates}")
#                     # break
#                 else:
#                     print(f"{f_warning}Can't find location in Index_of_locations.csv{f_default}")    

#                 # If no location found in the Index_of_locations.csv, try the geoparser
#                 # geoparser_coordinates = geoparser(metadata_location_for_geoparser)

#                 geoparser_coordinates = None
#                 geolat = None
#                 geolong = None
#                 geoaddress = ""
#                 try:
#                     geoparser_coordinates = geolocator.geocode(metadata_location_for_geoparser)
#                     geolat = geoparser_coordinates.latitude
#                     geolong = geoparser_coordinates.latitude
#                     geoaddress = geoparser_coordinates.address
#                     geoparser_coordinates = (geolat,geolong)
#                     location_data["Parser:Address"]
#                     # print(f"geoparser_coordinates is a: {type(geoparser_coordinates)}\n{geoparser_coordinates.latitude}")
#                     input("wait")
#                 except:
#                     print(f"{f_warning}Can't get response from server{f_default}")


#                 if geolong and geolat:
#                     geoparser_list = list(geoparser_coordinates)
#                     # print(type(geoparser_list))
#                     # print(type(location_lookup_coordinates))
#                     # input("Sdfasd")
#                     location_data["Parser:GPSLatitude"] = geoparser_list[0]
#                     location_data["Parser:GPSLongitude"] = geoparser_list[1]

#                     print(f"{f_success}metadata_location_for_geoparser: {geoparser_coordinates}{f_default}")
#                     # break
#                 else:
#                     print(f"{f_warning}Can't find a location with the given coordinates for {metadata_location}{f_default}")
#                     # location_lookup_coordinates["GPS:GPSLatitude"] = 

#                 if location_data and geolong:
#                     distance_between = haversine_distance(location_lookup_coordinates, geoparser_coordinates)
#                     print(f"{f_success}Distance between the two points is: {round(distance_between,1)} metres{f_default}")
#                     location_data["Parser:Distance"] = distance_between
                
#                 write_location_data_to_csv(csv_log,csv_headers,location_data)
          
# ################################################################
# TESTING AND DEVELOPMENT ########################################
# ################################################################
# END



# START
# ################################################################
# Show Locations on a Map Based on Lat/Longs #####################
# ################################################################

def generate_map_object(coordinates, location_name, map_options={}):
    """
    Creates a map centered on the given coordinates and adds a marker with a popup.

    Args:
        coordinates: A tuple of latitude and longitude.
        location_name: The name of the location to display in the popup.
        map_options: (Optional) A dictionary containing map options (zoom_start, map_type, etc.).

    Returns:
        A folium.Map object.
    """

    # Validate coordinates
    if not isinstance(coordinates, tuple) or len(coordinates) != 2:
        raise ValueError(f"Invalid coordinates: {coordinates}")

    # Set default map options
    default_map_options = {
        "zoom_start": 10,
        "map_type": "OpenStreetMap",
    }
    map_options = {**default_map_options, **map_options}

    # Create map and marker
    m = Map(location=coordinates, zoom_start=map_options["zoom_start"], tiles=map_options["map_type"])
    Marker(
        location=coordinates,
        popup=f"<h3>{location_name}</h3>",
        icon=Icon(color="blue", icon="info-sign"),
    ).add_to(m)

    return m

def show_location_on_map(coordinates, description="", filename_prefix="location_map", directory="maps"):
    """
    Shows the location on a map and opens it in a web browser.

    Args:
        coordinates: A tuple of latitude and longitude.
        description: A description of the location.
        filename_prefix: (Optional) Prefix for the map file name.
        directory: (Optional) Directory to save the map file.
    """

    if not coordinates:
        print("Location not found.")
        return

    print(f"The coordinates for {description} are: {coordinates}")

    # Create directory if it doesn't exist
    map_dir = Path(directory)
    map_dir.mkdir(parents=True, exist_ok=True)

    # Generate map and save as HTML file
    try:
        map_obj = generate_map_object(coordinates, description)
        file_path = map_dir / f"{filename_prefix}.html"
        map_obj.save(file_path)
        print(f"Map saved as '{file_path}'.")
    except Exception as e:
        print(f"Error saving the map: {e}")
        return

    # Open the map in a browser
    open_new(file_path)

# ################################################################
# Show Locations on a Map Based on Lat/Longs #####################
# ################################################################
# END



# START
# ################################################################
# Validate Location Data #########################################
# ################################################################
 
def validate_gps_data(location_data):
        # Check if all required GPS fields are present and not empty
    # print(location_data)
    required_fields = ["EXIF:GPSLatitudeRef", "EXIF:GPSLatitude", "EXIF:GPSLongitudeRef", "EXIF:GPSLongitude"]

    for field in required_fields:
        # print(f"{location_data}\n\nField verification: {field} in {required_fields}")
        if field not in location_data or not location_data[field]:
            return False
    
    # Check if GPSLatitudeRef is either 'N' or 'S', and GPSLongitudeRef is either 'W' or 'E'
    latitude_ref = location_data['EXIF:GPSLatitudeRef']
    longitude_ref = location_data['EXIF:GPSLongitudeRef']
    if latitude_ref not in ['N', 'S'] or longitude_ref not in ['W', 'E']:
        # print(latitude_ref)
        return False
    
    # Check if GPSLatitude and GPSLongitude are decimal numbers
    try:
        latitude = float(location_data['EXIF:GPSLatitude'])
        longitude = float(location_data['EXIF:GPSLongitude'])
    except (ValueError, TypeError):
        return False
    
    return True

def validate_consistent_values_in_keys(dictionary, keys):
    values = [dictionary[key] for key in keys if key in dictionary and dictionary[key] is not None and dictionary[key] != '']
    
    # If no valid values found or only one unique value, return True
    return len(set(values)) <= 1 if values else True

def assign_common_value(dictionary, keys):
    common_value = None
    
    for key in keys:
        value = dictionary.get(key)
        if value is not None and value != '':
            common_value = value
            break
    
    if common_value is not None:
        for key in keys:
            if key in dictionary:
                dictionary[key] = common_value
    else:
        dictionary = {key: None for key in keys}  # Set dictionary values to None for specified keys

    return dictionary

def lookup_location_info(search_string, csv_file, gps):
    dictionary_update = {}
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        return "CSV file not found"

    # Check if 'XMPiptcCoreLocation' column exists
    if 'XMPiptcCoreLocation' not in df.columns:
        return "Column 'XMPiptcCoreLocation' not found in the CSV"

    # Find the search string in 'XMPiptcCoreLocation' column
    location_info = df[df['XMPiptcCoreLocation'] == search_string]
    
    # If the search string is found, retrieve corresponding values from other columns
    if not location_info.empty:
        row_index = location_info.index[0]  # Get the index of the found location_info
        dictionary_update["IPTC:Sub-location"] = df.at[row_index, 'XMPiptcCoreLocation']
        dictionary_update["IPTC:City"] = df.at[row_index, 'XMP-photoshopCity']
        dictionary_update["IPTC:Province-State"] = df.at[row_index, 'XMP-photoshopState']
        dictionary_update["IPTC:Country-PrimaryLocationName"] = df.at[row_index, 'XMP-photoshopCountry']
        dictionary_update["XMP:CountryCode"] = df.at[row_index, 'XMP-iptcCoreCountryCode']
       
        dictionary_update["XMP:Location"] = df.at[row_index, 'XMPiptcCoreLocation']
        dictionary_update["XMP:City"] = df.at[row_index, 'XMP-photoshopCity']
        dictionary_update["XMP:State"] = df.at[row_index, 'XMP-photoshopState']
        dictionary_update["XMP:Country"] = df.at[row_index, 'XMP-photoshopCountry']
        dictionary_update["IPTC:Country-PrimaryLocationCode"] = df.at[row_index, 'XMP-iptcCoreCountryCode']

        dictionary_update["XMP:LocationCreatedLocationName"] = df.at[row_index, 'XMPiptcCoreLocation']
        dictionary_update["XMP:LocationCreatedCity"] = df.at[row_index, 'XMP-photoshopCity']
        dictionary_update["XMP:LocationCreatedProvinceState"] = df.at[row_index, 'XMP-photoshopState']
        dictionary_update["XMP:LocationCreatedCountryName"] = df.at[row_index, 'XMP-photoshopCountry']
        dictionary_update["XMP:LocationCreatedCountryCode"] = df.at[row_index, 'XMP-iptcCoreCountryCode']

        dictionary_update["XMP:LocationShownLocationName"] = df.at[row_index, 'XMPiptcCoreLocation']
        dictionary_update["XMP:LocationShownCity"] = df.at[row_index, 'XMP-photoshopCity']
        dictionary_update["XMP:LocationShownProvinceState"] = df.at[row_index, 'XMP-photoshopState']
        dictionary_update["XMP:LocationShownCountryName"] = df.at[row_index, 'XMP-photoshopCountry']
        dictionary_update["XMP:LocationShownCountryCode"] = df.at[row_index, 'XMP-iptcCoreCountryCode']

        if gps == True:
            dictionary_update["EXIF:GPSLatitude"] = df.at[row_index, 'GPSGPSLatitude']
            dictionary_update["EXIF:GPSLatitudeRef"] = df.at[row_index, 'GPSGPSLatitudeRef']
            dictionary_update["EXIF:GPSLongitude"] = df.at[row_index, 'GPSGPSLongitude']
            dictionary_update["EXIF:GPSLongitudeRef"] = df.at[row_index, 'GPSGPSLongitudeRef']
            dictionary_update["XMP:GPSLatitude"] = df.at[row_index, 'GPSGPSLatitude']
            dictionary_update["XMP:GPSLongitude"] = df.at[row_index, 'GPSGPSLongitude']

        return dictionary_update
    else:
        return None

def find_closest_location(latitude, longitude, csv_file):
    dictionary_update = {}
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        return "CSV file not found"
    
    # Check if required columns exist
    required_columns = ['GPSGPSLatitude', 'GPSGPSLongitude', 'Threshold', 
                        'XMPiptcCoreLocation', 'XMP-photoshopCity', 'XMP-photoshopState', 
                        'XMP-photoshopCountry', 'XMP-iptcCoreCountryCode']
    for column in required_columns:
        if column not in df.columns:
            return f"Column '{column}' not found in the CSV"

    # Calculate distances and find the closest location using the Haversine formula
    min_distance = float('inf')
    closest_location = None
    
    for index, row in df.iterrows():
        location_lat = row['GPSGPSLatitude']
        location_long = row['GPSGPSLongitude']
        threshold = row['Threshold']
        
        distance = haversine_distance(latitude, longitude, location_lat, location_long)
    

        # print(f"Lookup Value: {(latitude, longitude)}  |  {(location_lat, location_long)}  |  Distance: {distance}")
        
        if distance < min_distance and distance < threshold:
            min_distance = distance
            closest_location = index
    
    if closest_location is not None:
        row_index = closest_location
        dictionary_update["IPTC:Sub-location"] = df.at[row_index, 'XMPiptcCoreLocation']
        dictionary_update["IPTC:City"] = df.at[row_index, 'XMP-photoshopCity']
        dictionary_update["IPTC:Province-State"] = df.at[row_index, 'XMP-photoshopState']
        dictionary_update["IPTC:Country-PrimaryLocationName"] = df.at[row_index, 'XMP-photoshopCountry']
        dictionary_update["XMP:CountryCode"] = df.at[row_index, 'XMP-iptcCoreCountryCode']
     
        dictionary_update["XMP:Location"] = df.at[row_index, 'XMPiptcCoreLocation']
        dictionary_update["XMP:City"] = df.at[row_index, 'XMP-photoshopCity']
        dictionary_update["XMP:State"] = df.at[row_index, 'XMP-photoshopState']
        dictionary_update["XMP:Country"] = df.at[row_index, 'XMP-photoshopCountry']
        dictionary_update["IPTC:Country-PrimaryLocationCode"] = df.at[row_index, 'XMP-iptcCoreCountryCode']

        dictionary_update["XMP:LocationCreatedLocationName"] = df.at[row_index, 'XMPiptcCoreLocation']
        dictionary_update["XMP:LocationCreatedCity"] = df.at[row_index, 'XMP-photoshopCity']
        dictionary_update["XMP:LocationCreatedProvinceState"] = df.at[row_index, 'XMP-photoshopState']
        dictionary_update["XMP:LocationCreatedCountryName"] = df.at[row_index, 'XMP-photoshopCountry']
        dictionary_update["XMP:LocationCreatedCountryCode"] = df.at[row_index, 'XMP-iptcCoreCountryCode']

        dictionary_update["XMP:LocationShownLocationName"] = df.at[row_index, 'XMPiptcCoreLocation']
        dictionary_update["XMP:LocationShownCity"] = df.at[row_index, 'XMP-photoshopCity']
        dictionary_update["XMP:LocationShownProvinceState"] = df.at[row_index, 'XMP-photoshopState']
        dictionary_update["XMP:LocationShownCountryName"] = df.at[row_index, 'XMP-photoshopCountry']
        dictionary_update["XMP:LocationShownCountryCode"] = df.at[row_index, 'XMP-iptcCoreCountryCode']

        return dictionary_update
    else:
        return "No matching location found within the threshold distance"

# ################################################################
# Validate Location Data #########################################
# ################################################################
# END

 

# START
# ################################################################
# Process list of lat/longs and return results in csv file #######
# ################################################################

locations = ["witty's lagoon metchosin", "empress hotel, victoria bc", "4020 grange road victoria bc"]


def process_list_of_location_names(locations):
    """
    Processes a list of location names and retrieves their lat/long coordinates.

    Args:
        locations: A list of location names.

    Returns:
        A list of tuples containing location name, latitude, and longitude.
    """
    csv_file_output = r"c:\test\location_output7.csv"
    csv_header = ["Location", "Latitude", "Longitude"]

    processed_locations = []

    with open(csv_file_output, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_header)

        for location in locations:
            try:
                coordinates_tuple = geoparser(location)
                if coordinates_tuple is None:
                    raise ValueError(f"Failed to obtain coordinates for '{location}'")

                lat, long = coordinates_tuple
                if any(x is None for x in (lat, long)):
                    raise ValueError(f"Missing lat/long information for '{location}'")

                # Process location data
                processed_locations.append((location, lat, long))
                

                # Write data to CSV
                csv_line = [location, lat, long]
                writer.writerow(csv_line)
                print(f"Processed location: {csv_line}")
            except (ValueError, Exception) as e:
                print(f"Error processing location '{location}': {e}")

    time.sleep(2)
    return processed_locations

# ################################################################
# Process list of lat/longs and return results in csv file #######
# ################################################################
# END




# image = r"C:\test\200204xxc_horne-lake_0000006846.jpg"
image = r"C:\test\test.jpg"
# image = r"C:\test\nogps.jpg"

def get_location_metadata(file_path):
    """
    Extracts all location-related information from EXIF, IPTC legacy, and XMP
    metadata fields, including missing fields with null values.

    Args:
        file_path: Path to the file.

    Returns:
        A dictionary containing all extracted location data, including null values
        for missing fields.
    """

    location_data = {}

    try:
        with exiftool.ExifToolHelper() as et:
            metadata = et.get_metadata([file_path])[0]  # Get metadata for the file
            # print(metadata)
            # input("asdf")

            # Define all relevant metadata tags in a single list
            all_tags = [
"EXIF:GPSLatitude","EXIF:GPSLatitudeRef","EXIF:GPSLongitude","EXIF:GPSLongitudeRef","IPTC:City","IPTC:Country-PrimaryLocationCode","IPTC:Country-PrimaryLocationName","IPTC:Province-State","IPTC:Sub-location","XMP:City","XMP:Country","XMP:CountryCode","XMP:GPSLatitude","XMP:GPSLongitude","XMP:Location","XMP:LocationCreatedCity","XMP:LocationCreatedCountryCode","XMP:LocationCreatedCountryName","XMP:LocationCreatedLocationName","XMP:LocationCreatedProvinceState","XMP:LocationCreatedSublocation","XMP:LocationShownCity","XMP:LocationShownCountryCode","XMP:LocationShownCountryName","XMP:LocationShownLocationName","XMP:LocationShownProvinceState","XMP:LocationShownSublocation","XMP:State"]

            # Create Dictionary from all_tags list
            location_data = {key: metadata.get(key) for key in all_tags}

            # Validate GPS Data
            gps_data_validation = validate_gps_data(location_data)
            # print(f"gps_data_validation: {gps_data_validation}")

            # If a location IS present, and there IS GPS coordinates, write all tags back to file
            if gps_data_validation == True and location_data["XMP:Location"]:
   
                # Update locations based on Location Index
                location_data = lookup_location_info(location_data["XMP:Location"], location_lookup, gps=True)
                try:
                    et.set_tags(file_path, location_data)
                    print({f"{f_success} Location metadata updated{f_default}"})
                except:
                    print({f"{f_warning} Can't update file metadata{f_default}"})


                
                # print(f"\n\nGPS: TRUE  |  LOCATION: TRUE\n: {location_data}")
                # et.set_tags(file_path, location_data)
                # continue


            # If a location IS present, and there are NO GPS coordinates, lookup the location and gps info in the Location Index
            elif gps_data_validation == False and location_data["XMP:Location"]:
   
                # Update locations based on Location Index
                location_data = lookup_location_info(location_data["XMP:Location"], location_lookup, gps=False)
                try:
                    et.set_tags(file_path, location_data)
                    print({f"{f_success} Location metadata updated{f_default}"})
                except:
                    print({f"{f_warning} Can't update file metadata{f_default}"})

                # print("There are no geocoordinates, but there is a location defined.")
                # print(f"\n\nGPS: FALSE  |  LOCATION: TRUE\n: {location_data}")
                # print(location_data)
                # input("asdfladksfh11")

            # If a location is NOT present, and there ARE GPS coordinates, lookup the location but NOT gps info in the Location Index
            elif gps_data_validation == True and not location_data["XMP:Location"]:
   
                lat = location_data["EXIF:GPSLatitude"]
                long = location_data["EXIF:GPSLongitude"]
                latref = location_data["EXIF:GPSLatitudeRef"]
                longref = location_data["EXIF:GPSLongitudeRef"]
                
                # Check and adjust latitude based on latref
                if latref == "S" and lat >= 0:
                    lat = -lat  # Convert latitude to negative if latref is 'S'
                elif latref == "N" and lat < 0:
                    lat = abs(lat)  # Make latitude positive if latref is 'N'

                # Check and adjust longitude based on longref
                if longref == "W" and long >= 0:
                    long = -long  # Convert longitude to negative if longref is 'W'
                elif longref == "E" and long < 0:
                    long = abs(long)  # Make longitude positive if longref is 'E'

                found_closest_location = find_closest_location(lat, long, location_lookup)
                try:
                    et.set_tags(file_path, found_closest_location)
                    print({f"{f_success} Location metadata updated{f_default}"})
                except:
                    print({f"{f_warning} Can't update file metadata{f_default}"})
                # print(f"\n\nGPS: TRUE  |  CLOSEST LOCATION: TRUE\n: {found_closest_location}")
                # input("asdfladksfh22")

            else:
                print("No location information found.")

    except Exception as e:
        print(f"Error extracting location data for '{file_path}': {e}")

    return location_data



# Get coordinates for these:
more_coordinates = ["Airlie Beach","Ballarat","Campbell River","Coombs","Denarau Island","Duncan","East Sooke","Errington","Fremantle","Katoomba","Parksville","Perth","Port Alberni","Port Macquarie","Powell River","Richmond","San Juan","Seattle","Sooke","South Sea Island","Sydney","Victoria","West Swan","Woodbridge"]

# files_to_process = list_files(r"c:\test")
folder = r"D:\0_Media-Archive\03_archive\live-archive"
files_to_process = list_files(folder, recursive=True, include=image_files, exclude=None)

os.system("cls")
for file in files_to_process:
    location_data = get_location_metadata(file)
    




