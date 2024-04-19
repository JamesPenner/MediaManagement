import re
import sys
import csv
from datetime import datetime, timezone
import pandas as pd
import Support_functions_Date
from math import radians, sin, cos, sqrt, atan2


import timeit

from fuzzywuzzy import fuzz
sys.path.append(r'C:\Media Management\Scripts')
from config import created_date_fields, acdsee_parser, Location_fields, city_fields, state_fields, country_fields, country_code_fields, gps_fields, locality_fields, people_lookup, family_names, filename_validation_rules, keyword_lookup, asset_title_length, keyword_lookup, people_lookup, location_lookup
from PandasExtension import DataFileHandler


class Metadata_Manager:

    def __init__(self, metadata_list):
        if len(metadata_list) != 1:
            raise ValueError("Expected a list containing only one dictionary")
        self.metadata = metadata_list[0]

    def _filter_unique_values(self, dictionary):
        unique_values = {}
        seen_values = set()

        for key, value in dictionary.items():
            if value not in seen_values:
                unique_values[key] = value
                seen_values.add(value)

        return unique_values

    def _lookup_in_csv(self, location_lookup, lookup_key, lookup_value, return_keys):
        # Load the CSV file into a Pandas DataFrame
        df = pd.read_csv(location_lookup)
        
        # Convert all column names to lowercase for case-insensitive matching
        df.columns = df.columns.str.lower()
        
        # Convert the "lookup_key" column to lowercase for case-insensitive matching
        lookup_key_lower = lookup_key.lower()
        
        # Convert lookup_value to lowercase for case-insensitive matching
        lookup_value_lower = lookup_value.lower()
        
        # Filter the DataFrame based on case-insensitive match for lookup_value in lookup_key
        filtered_df = df[df[lookup_key_lower].str.lower() == lookup_value_lower]
        
        # Create a dictionary to store the results
        result = {}
        
        # Extract values from the return_keys columns for matched rows
        for key in return_keys:
            key_lower = key.lower()
            if key_lower in df.columns:
                result[key] = filtered_df[key_lower].iloc[0] if not filtered_df.empty else None
        
        return result

# Date Related Methods
# ################################################################
    def get_people_dates(self):
        # Find the earliest Create Date
        create_dates = self.filter_date_fields("created")
        # print(create_dates)
        create_date = self.get_earliest_date(create_dates)
        # print(create_date)

        # Check if the date is accurate
        AccurateDate = self.filter_metadata(["XMP:AccurateDate"])
        AccurateDate = AccurateDate["XMP:AccurateDate"]
        # print(AccurateDate)

        # Check if People are in the image
        People_List = self.filter_metadata(["XMP:RegionName"])
        # print(People_List)
        try:
            People_List = People_List["XMP:RegionName"]
        except:
            People_List = ""
        # print(People_List)
        
        if People_List and AccurateDate is True:
            # Find location information in files.
            people_dates = Support_functions_Date.process_metadata_and_people_lookup(create_date,People_List,people_lookup)

            return people_dates

    def get_holiday_dates(self):
        # Find the earliest Create Date
        create_dates = self.filter_date_fields("created")
        # print(create_dates)
        create_date = self.get_earliest_date(create_dates)
        # print(f"This is the Create Date: {create_date}")

        # Check if the date is accurate
        AccurateDate = self.filter_metadata(["XMP:AccurateDate"])
        AccurateDate = AccurateDate["XMP:AccurateDate"]
        # print(AccurateDate)
        
        if AccurateDate is True:
            # Find location information in files.
            holiday_dates = Support_functions_Date.check_holiday(create_date)

            return holiday_dates

    def get_earliest_date(self, dictionary):
        """
        Identifies and retrieves the earliest date value present in a dictionary by attempting multiple date formats.

        Parameters:
        -----------
        dictionary : dict
            A dictionary containing values that may represent dates.

        Returns:
        --------
        datetime.datetime or None
            The earliest date object amongst the identified date values in the dictionary.
            Returns None if no valid date object is found.

        Date Formats Attempted:
        -----------------------
        - '%Y-%m-%d %H:%M:%S%z'
        - '%Y:%m:%d %H:%M:%S%z'
        - '%Y-%m-%d %H:%M:%S'
        - '%Y:%m:%d %H:%M:%S'
        - '%Y-%m-%d'
        - '%Y:%m:%d'
        """
        date_formats = [
            '%Y-%m-%d %H:%M:%S%z',
            '%Y:%m:%d %H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
            '%Y:%m:%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y:%m:%d'
        ]

        dates = []
        for value in dictionary.values():
            if isinstance(value, str):
                for date_format in date_formats:
                    try:
                        date_obj = datetime.strptime(value, date_format)
                        dates.append(date_obj)
                        break  # Move to the next value if a valid date is found
                    except ValueError:
                        pass

        if dates:
            # Convert all datetimes to offset-naive
            dates = [date.replace(tzinfo=None) for date in dates]
            return min(dates)
        else:
            return None

    def get_asset_date_from_filename(self):


        # Check whether an Asset Date is present
        filename = self.metadata["File:FileName"]
        check_for_assetdate = filename[:9].lower()
        regex_pattern = filename_validation_rules.get("date_prefix")
        # print(check_for_assetdate)
        # print(regex_pattern)
        # input("SDF")


        if regex_pattern and re.match(regex_pattern, check_for_assetdate):

            date_format = '%Y:%m:%d'

            metadata_date_data = {}
            media_date = "-"
            metadata_accurate_date = "-"
            media_xdate = "-"
            month = "-"
            day_name = "-"
            day = "-"
            season = "-"


            media_xdate = filename[:9]
            century = filename[:2]
            century_string = filename[:2] + "00-" + filename[:2] + "99"
            decade = filename[:3] + "0s"
            year = filename[:4]
            month_number = filename[4:6]
            day_check = str(filename[0:8]).replace(":","")
            day = filename[6:8]
            date_type = filename[8:9]

            try:
                if day_check.isnumeric():
                    media_date = f"{year}:{filename[4:6]}:{filename[6:8]}"
                    metadata_accurate_date = "True"
                    # Derive the day name from the date string
                    date_object = datetime.strptime(media_date, date_format)
                    # day_name = date_object.strftime("%A")
                    day_of_week = date_object.weekday()
                    day_name = str(day_of_week) + "_" + str(date_object.strftime("%A"))

                    month = month_number + "_" + date_object.strftime("%B")

                    season_lookup = int(month_number)
                    if season_lookup >= 3 <= 5:
                        season = "Spring"
                    if season_lookup >= 6 <= 8:
                        season = "Summer"
                    if season_lookup >= 9 <= 11:
                        season = "Autumn"
                    if season_lookup == 12 or season_lookup == 1 or season_lookup == 2:
                        season = "Winter"



                elif month_number.isnumeric():
                    media_date = f"{year}:{filename[4:6]}:01"
                    metadata_accurate_date = "False"
                    date_object = datetime.strptime(media_date, date_format)
                    month = month_number + "_" + date_object.strftime("%B")
                    day = "-"
                    day_name = "-"

                    season_lookup = int(month_number)
                    if season_lookup >= 3 <= 5:
                        season = "Spring"
                    if season_lookup >= 6 <= 8:
                        season = "Summer"
                    if season_lookup >= 9 <= 11:
                        season = "Autumn"
                    if season_lookup == 12 or season_lookup == 1 or season_lookup == 2:
                        season = "Winter"



                elif year.isnumeric():
                    media_date = f"{year}:01:01"
                    metadata_accurate_date = "False"
                    month = "-"
                    day = "-"
                    day_name = "-"

                elif decade.isnumeric():
                    media_date = f"{decade}0:01:01"
                    metadata_accurate_date = "False"
                    month = "-"
                    day = "-"
                    day_name = "-"
                    year = "-"

                elif century_string[0] == '1' or century_string[0] == '2':
                    media_date = f"{century}00:01:01"
                    metadata_accurate_date = "False"
                    month = "-"
                    day = "-"
                    day_name = "-"
                    year = "-"
                    decade = "-"
                else:
                    media_date = f"-"
                    metadata_accurate_date = "-"
                    month = "-"
                    day = "-"
                    day_name = "-"
                    year = "-"
                    decade = "-"
                    century_string = "-"

            except:
                if century_string[0] == '1' or century_string[0] == '2':
                    media_date = f"{century}00:01:01"
                    metadata_accurate_date = "False"
                    month = "-"
                    day = "-"
                    day_name = "-"
                    year = "-"
                    decade = "-"
                    century = "-"
                else:
                    media_date = "-"
                    metadata_accurate_date = "-"
                    month = "-"
                    day = "-"
                    day_name = "-"
                    year = "-"
                    decade = "-"
                    century_string = "-"

            if date_type == "m":
                metadata_accurate_date = "False"

            metadata_date_data["Century"] = century_string
            metadata_date_data["Decade"] = decade
            metadata_date_data["Year"] = year
            metadata_date_data["Season"] = season
            metadata_date_data["Month"] = month
            metadata_date_data["DayNumber"] = day
            metadata_date_data["DayName"] = day_name
            metadata_date_data["AssetDate"] = media_xdate.lower()
            metadata_date_data["Created Date"] = media_date
            metadata_date_data["AccurateDate"] = metadata_accurate_date
            

            return metadata_date_data

        else:
            return None
        
    # Need to update this
    def process_key_date(key_date):
        metadata_date_data = {}
        century = key_date[:2]
        century_string = key_date[:2] + "00-" + key_date[:2] + "99"
        decade = key_date[:3] + "0s"
        year = key_date[:4]
        month_number = key_date[4:6]
        day_check = str(key_date[0:8]).replace(":","")
        day = key_date[6:8]
        date_type = key_date[8:9]

        if day_check.isnumeric():
            media_date = f"{year}:{key_date[4:6]}:{key_date[6:8]}"
            metadata_accurate_date = "True"
            # Derive the day name from the date string
            date_object = datetime.strptime(media_date, date_format)
            # day_name = date_object.strftime("%A")
            day_of_week = date_object.weekday()
            day_name = str(day_of_week) + "_" + str(date_object.strftime("%A"))

            month = month_number + "_" + date_object.strftime("%B")

        elif month_number.isnumeric():
            media_date = f"{year}:{key_date[4:6]}:01"
            metadata_accurate_date = "False"
            date_object = datetime.strptime(media_date, date_format)
            month = month_number + "_" + date_object.strftime("%B")
            day = "-"
            day_name = "-"

        elif year.isnumeric():
            media_date = f"{year}:01:01"
            metadata_accurate_date = "False"
            month = "-"
            day = "-"
            day_name = "-"

        elif decade.isnumeric():
            media_date = f"{decade}0:01:01"
            metadata_accurate_date = "False"
            month = "-"
            day = "-"
            day_name = "-"
            year = "-"

        elif century.isnumeric():
            media_date = f"{century}00:01:01"
            metadata_accurate_date = "False"
            month = "-"
            day = "-"
            day_name = "-"
            year = "-"
            decade = "-"

        if century.isnumeric():
            media_date = f"{century}00:01:01"
            metadata_accurate_date = "False"
            month = "-"
            day = "-"
            day_name = "-"
            year = "-"
            decade = "-"
        else:
            media_date = "-"
            metadata_accurate_date = "False"
            month = "-"
            day = "-"
            day_name = "-"
            year = "-"
            decade = "-"

        if date_type == "m":
            metadata_accurate_date = "False"

        metadata_date_data["Century"] = century_string
        metadata_date_data["Decade"] = decade
        metadata_date_data["Year"] = year
        metadata_date_data["Month"] = month
        metadata_date_data["DayNumber"] = day
        metadata_date_data["DayName"] = day_name
        metadata_date_data["AssetDate"] = key_date
        metadata_date_data["Created Date"] = media_date
        metadata_date_data["AccurateDate"] = metadata_accurate_date

        return metadata_date_data

    # Need to update this
    def get_media_date_from_filename(file):
        metadata_date_data = {}
        filename = os.path.basename(file)
        media_xdate = filename[:9]
        century = filename[:2]
        century_string = filename[:2] + "00-" + filename[:2] + "99"
        decade = filename[:3] + "0s"
        year = filename[:4]
        month_number = filename[4:6]
        day_check = str(filename[0:8]).replace(":","")
        day = filename[6:8]
        date_type = filename[8:9]

        try:
            if day_check.isnumeric():
                media_date = f"{year}:{filename[4:6]}:{filename[6:8]}"
                metadata_accurate_date = "True"
                # Derive the day name from the date string
                date_object = datetime.strptime(media_date, date_format)
                # day_name = date_object.strftime("%A")
                day_of_week = date_object.weekday()
                day_name = str(day_of_week) + "_" + str(date_object.strftime("%A"))

                month = month_number + "_" + date_object.strftime("%B")

            elif month_number.isnumeric():
                media_date = f"{year}:{filename[4:6]}:01"
                metadata_accurate_date = "False"
                date_object = datetime.strptime(media_date, date_format)
                month = month_number + "_" + date_object.strftime("%B")
                day = "-"
                day_name = "-"

            elif year.isnumeric():
                media_date = f"{year}:01:01"
                metadata_accurate_date = "False"
                month = "-"
                day = "-"
                day_name = "-"

            elif decade.isnumeric():
                media_date = f"{decade}0:01:01"
                metadata_accurate_date = "False"
                month = "-"
                day = "-"
                day_name = "-"
                year = "-"

            elif century.isnumeric():
                media_date = f"{century}00:01:01"
                metadata_accurate_date = "False"
                month = "-"
                day = "-"
                day_name = "-"
                year = "-"
                decade = "-"

        except:
            if century.isnumeric():
                media_date = f"{century}00:01:01"
                metadata_accurate_date = "False"
                month = "-"
                day = "-"
                day_name = "-"
                year = "-"
                decade = "-"
            else:
                media_date = "-"
                metadata_accurate_date = "False"
                month = "-"
                day = "-"
                day_name = "-"
                year = "-"
                decade = "-"

        if date_type == "m":
            metadata_accurate_date = "False"

        metadata_date_data["Century"] = century_string
        metadata_date_data["Decade"] = decade
        metadata_date_data["Year"] = year
        metadata_date_data["Month"] = month
        metadata_date_data["DayNumber"] = day
        metadata_date_data["DayName"] = day_name
        metadata_date_data["AssetDate"] = media_xdate
        metadata_date_data["Created Date"] = media_date
        metadata_date_data["AccurateDate"] = metadata_accurate_date

        return metadata_date_data





# Filter methods
# ################################################################
    def filter_date_fields(self, DateType):
        if DateType.lower() == 'created':
            filtered_dict = {key: value for key, value in self.metadata .items() if 'create' in key.lower() and 'date' in key.lower()}
        elif DateType.lower() == 'modified':
            filtered_dict = {key: value for key, value in self.metadata .items() if 'modif' in key.lower() and 'date' in key.lower()}
        else:
            return {}  # If invalid DateType is provided, return an empty dictionary
        
        return filtered_dict

    def filter_metadata(self, list_of_metadata_fields):
        """
        This method returns a new dictionary containing only filtered metadata fields based on the list of metadata fields provided.

        Args:
            list_of_metadata_fields: A variable or list of strings representing the metadata fields to keep in the dictionary.

        Returns:
            A dictionary containing only the specified metadata fields.
        """
        filtered_metadata = {}

        for field in list_of_metadata_fields:
            if field in self.metadata:
                filtered_metadata[field] = self.metadata[field]
            else:
                filtered_metadata[field] = None  # or any other placeholder value

        return filtered_metadata


# Location-related methods
# ################################################################
  
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the distance between two points on the Earth's surface using the Haversine formula.

        Parameters:
        - lat1 (float): Latitude of the first point in decimal degrees.
        - lon1 (float): Longitude of the first point in decimal degrees.
        - lat2 (float): Latitude of the second point in decimal degrees.
        - lon2 (float): Longitude of the second point in decimal degrees.

        Returns:
        - distance (float): Distance between the two points in meters.

        The Haversine formula determines the great-circle distance between two points on a sphere
        given their longitudes and latitudes. The function converts the inputs from degrees to radians
        and calculates the distance in meters using the Earth's radius of 6371 kilometers.
        """


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

    def find_closest_location(self, latitude, longitude, location_lookup):
        dictionary_update = {}
        
        # Read the CSV file
        try:
            df = pd.read_csv(location_lookup)
        except FileNotFoundError:
            return "CSV file not found"
        
        # Check if required columns exist
        required_columns = ['GPSLatitude', 'GPSLongitude', 'Threshold', 
                            'location', 'city', 'state', 
                            'country', 'countrycode']
        for column in required_columns:
            if column not in df.columns:
                return f"Column '{column}' not found in the CSV"

        # Calculate distances and find the closest location using the Haversine formula
        min_distance = float('inf')
        closest_location = None
        
        for index, row in df.iterrows():
            location_lat = row['GPSLatitude']
            location_long = row['GPSLongitude']
            threshold = row['Threshold']
            
            distance = self.haversine_distance(latitude, longitude, location_lat, location_long)
        

            # print(f"Lookup Value: {(latitude, longitude)}  |  {(location_lat, location_long)}  |  Distance: {distance}")
            
            if distance < min_distance and distance < threshold:
                min_distance = distance
                closest_location = index
        
        if closest_location is not None:
            row_index = closest_location
            dictionary_update["IPTC:Sub-location"] = df.at[row_index, 'location']
            dictionary_update["IPTC:City"] = df.at[row_index, 'city']
            dictionary_update["IPTC:Province-State"] = df.at[row_index, 'state']
            dictionary_update["IPTC:Country-PrimaryLocationName"] = df.at[row_index, 'country']
            dictionary_update["XMP:CountryCode"] = df.at[row_index, 'countrycode']
        
            dictionary_update["XMP:Location"] = df.at[row_index, 'location']
            dictionary_update["XMP:City"] = df.at[row_index, 'city']
            dictionary_update["XMP:State"] = df.at[row_index, 'state']
            dictionary_update["XMP:Country"] = df.at[row_index, 'country']
            dictionary_update["IPTC:Country-PrimaryLocationCode"] = df.at[row_index, 'countrycode']

            dictionary_update["XMP:LocationCreatedLocationName"] = df.at[row_index, 'location']
            dictionary_update["XMP:LocationCreatedCity"] = df.at[row_index, 'city']
            dictionary_update["XMP:LocationCreatedProvinceState"] = df.at[row_index, 'state']
            dictionary_update["XMP:LocationCreatedCountryName"] = df.at[row_index, 'country']
            dictionary_update["XMP:LocationCreatedCountryCode"] = df.at[row_index, 'countrycode']

            dictionary_update["XMP:LocationShownLocationName"] = df.at[row_index, 'location']
            dictionary_update["XMP:LocationShownCity"] = df.at[row_index, 'city']
            dictionary_update["XMP:LocationShownProvinceState"] = df.at[row_index, 'state']
            dictionary_update["XMP:LocationShownCountryName"] = df.at[row_index, 'country']
            dictionary_update["XMP:LocationShownCountryCode"] = df.at[row_index, 'countrycode']

            return dictionary_update
        else:
            return "No matching location found within the threshold distance"

    def expand_locations(self, location_dict):
        dictionary_update = {}
        dictionary_update["IPTC:Sub-location"] = location_dict["XMP:LocationCreatedLocationName"]
        dictionary_update["IPTC:City"] = location_dict["XMP:LocationCreatedCity"]
        dictionary_update["IPTC:Province-State"] = location_dict["XMP:LocationCreatedProvinceState"]
        dictionary_update["IPTC:Country-PrimaryLocationName"] = location_dict["XMP:LocationCreatedCountryName"]
        dictionary_update["XMP:CountryCode"] = location_dict["XMP:CountryCode"]
        dictionary_update["XMP:LocalityGeneral"] = location_dict["XMP:LocalityGeneral"]
        dictionary_update["XMP:LocalityType"] = location_dict["XMP:LocalityType"]
        dictionary_update["XMP:LocalitySpecific"] = location_dict["XMP:LocalitySpecific"]

    
        dictionary_update["XMP:Location"] = location_dict["XMP:LocationCreatedLocationName"]
        dictionary_update["XMP:City"] = location_dict["XMP:LocationCreatedCity"]
        dictionary_update["XMP:State"] = location_dict["XMP:LocationCreatedProvinceState"]
        dictionary_update["XMP:Country"] = location_dict["XMP:LocationCreatedCountryName"]
        dictionary_update["IPTC:Country-PrimaryLocationCode"] = location_dict["XMP:CountryCode"]

        dictionary_update["XMP:LocationCreatedLocationName"] = location_dict["XMP:LocationCreatedLocationName"]
        dictionary_update["XMP:LocationCreatedCity"] = location_dict["XMP:LocationCreatedCity"]
        dictionary_update["XMP:LocationCreatedProvinceState"] = location_dict["XMP:LocationCreatedProvinceState"]
        dictionary_update["XMP:LocationCreatedCountryName"] = location_dict["XMP:LocationCreatedCountryName"]
        dictionary_update["XMP:LocationCreatedCountryCode"] = location_dict["XMP:CountryCode"]

        dictionary_update["XMP:LocationShownLocationName"] = location_dict["XMP:LocationCreatedLocationName"]
        dictionary_update["XMP:LocationShownCity"] = location_dict["XMP:LocationCreatedCity"]
        dictionary_update["XMP:LocationShownProvinceState"] = location_dict["XMP:LocationCreatedProvinceState"]
        dictionary_update["XMP:LocationShownCountryName"] = location_dict["XMP:LocationCreatedCountryName"]
        dictionary_update["XMP:LocationShownCountryCode"] = location_dict["XMP:CountryCode"]

        return dictionary_update

    def update_metadata_based_on_acdsee_location(self):
        key_mapping = {
            "LocalityGeneral": "XMP:LocalityGeneral",
            "LocalitySpecific": "XMP:LocalitySpecific",
            "LocalityType": "XMP:LocalityType",
            "location": "XMP:LocationCreatedLocationName",
            "city": "XMP:LocationCreatedCity",
            "state": "XMP:LocationCreatedProvinceState",
            "country": "XMP:LocationCreatedCountryName",
            "countrycode": "XMP:CountryCode"
        }

        location = self.parse_compiled_xmp_categories({"XMP:LocationCreatedLocationName": acdsee_parser["XMP:LocationCreatedLocationName"]})
        locality = self.parse_compiled_xmp_categories({"XMP:LocalitySpecific": acdsee_parser["XMP:LocalitySpecific"]})
        city = self.parse_compiled_xmp_categories({"XMP:LocationCreatedCity": acdsee_parser["XMP:LocationCreatedCity"]})

        if location[key_mapping["location"]] is not None:
            lookup_key = "location"
            lookup_value = location[key_mapping["location"]]
        elif locality[key_mapping["LocalitySpecific"]] is not None:
            lookup_key = "LocalitySpecific"
            lookup_value = locality[key_mapping["LocalitySpecific"]]
        elif city[key_mapping["city"]] is not None and locality[key_mapping["LocalitySpecific"]] is None:
            lookup_key = "city"
            lookup_value = city[key_mapping["city"]]
        else:
            dict = {'LocalityGeneral': '-', 'LocalitySpecific': '-', 'LocalityType': '-', 'location': '-', 'city': '-', 'state': '-', 'country': '-', 'countrycode': '-'}
            updated_dict  ={key_mapping.get(old_key, old_key): value for old_key, value in dict.items()}
            return self.expand_locations(updated_dict)


        return_keys = ["LocalityGeneral", "LocalitySpecific", "LocalityType", "location", "city", "state", "country", "countrycode"]
        dict = self._lookup_in_csv(location_lookup, lookup_key, lookup_value, return_keys)

        updated_dict  ={key_mapping.get(old_key, old_key): value for old_key, value in dict.items()}
        return self.expand_locations(updated_dict)

        # return {key_mapping.get(old_key, old_key): value for old_key, value in dict.items()}

    def expand_location_descriptions(self, location_name, column_name):
        global location_lookup  # Declare location_lookup as global
        metadata_update = {}

        try:
            df = pd.read_csv(location_lookup)
            # Case-insensitive match for location_name in the specified column_name
            matched_row = df[df[column_name].str.lower() == location_name.lower()]

            if not matched_row.empty:
                result = matched_row.iloc[0].to_dict()

                if column_name.lower() == "location":
                    location_value = result.get("location")
                    city_value = result.get("city")
                    state_value = result.get("state")
                    country_value = result.get("country")
                    country_code_value = result.get("countrycode")

                    for field in Location_fields:
                        metadata_update[field] = location_value if location_value else result.get(field)

                    for field in city_fields:
                        metadata_update[field] = city_value if city_value else result.get(field)

                    for field in state_fields:
                        metadata_update[field] = state_value if state_value else result.get(field)

                    for field in country_fields:
                        metadata_update[field] = country_value if country_value else result.get(field)

                    for field in country_code_fields:
                        metadata_update[field] = country_code_value if country_code_value else result.get(field)

        except Exception as e:
            # Handle exceptions as needed
            print("An error occurred:", str(e))

        return metadata_update  # Return the updated metadata dictionary

    def search_location_in_csv(self, location_name, column_name):
        fields_to_report = ["location","city","state","country","countrycode","locality","localitygeneral","localityspecific","localitytype","gpslatitude","gpslatituderef","gpslongitude","gpslongituderef"]
        result = {}

        try:
            df = pd.read_csv(location_lookup)
            matched_row = df[df[column_name] == location_name]

            if not matched_row.empty:
                result = matched_row.to_dict(orient='records')[0]
                result = {key: value for key, value in result.items() if key in fields_to_report and value != "-"}
        except FileNotFoundError:
            print("CSV file not found.")
        except Exception as e:
            print(f"Error occurred: {e}")

        return result

    def get_location_descriptions(self):
        metadata_update = {}  # Dictionary to hold the collected values
        location_description_fields = [Location_fields, city_fields, state_fields, country_fields, country_code_fields]

        try:
            for field_list in location_description_fields:
                for field in field_list:
                    if field in self.metadata:  # Check if the key exists in the metadata
                        value = self.metadata[field]
                        if field in metadata_update:
                            if not isinstance(metadata_update[field], list):
                                metadata_update[field] = [metadata_update[field]]
                            metadata_update[field].append(value)
                        else:
                            metadata_update[field] = value
        except Exception as e:
            print(f"Error occurred: {e}")
        
        return metadata_update

    def get_location_from_metadata(self, location_type="location"):
        
        # print("self.parse_xmp_categories() time:")
        # start_time = timeit.default_timer()
        # acdsee_metadata = self.parse_xmp_categories()
        # elapsed = timeit.default_timer() - start_time
        # print(f"Elapsed time: {elapsed} seconds")
    
        acdsee_metadata = ""
        
        # print(acdsee_metadata)
        lookup_location = None

        if location_type.lower() == "location":
            pass
            
            # print("acdsee_metadata.get(XMP:LocationCreatedLocationName) time:")
            # start_time = timeit.default_timer()
            # lookup_location = acdsee_metadata.get("XMP:LocationCreatedLocationName")
            # elapsed = timeit.default_timer() - start_time
            # print(f"Elapsed time: {elapsed} seconds")
            

        elif location_type.lower() == "city":
            lookup_location = acdsee_metadata.get("XMP:LocationCreatedCity")

        elif location_type.lower() == "state":
            lookup_location = acdsee_metadata.get("XMP:LocationCreatedProvinceState")

        elif location_type.lower() == "country":
            lookup_location = acdsee_metadata.get("XMP:LocationCreatedCountryName")

        elif location_type.lower() == "locality":
            acdsee_locality_info = {}
            if "XMP:LocalityGeneral" in acdsee_metadata:
                acdsee_locality_info["XMP:LocalityGeneral"] = acdsee_metadata["XMP:LocalityGeneral"]
            if "XMP:LocalityType" in acdsee_metadata:
                acdsee_locality_info["XMP:LocalityType"] = acdsee_metadata["XMP:LocalityType"]
            if "XMP:LocalitySpecific" in acdsee_metadata:
                acdsee_locality_info["XMP:LocalitySpecific"] = acdsee_metadata["XMP:LocalitySpecific"]
            return acdsee_locality_info if acdsee_locality_info else None

        elif location_type.lower() == "gps":
            lookup_location = self.filter_metadata(self.metadata, gps_fields)

        return lookup_location

    def get_location_descriptions(self):
        """
        Collects and organizes location-related descriptions from metadata.

        Returns a dictionary containing collected location descriptions.

        The method iterates through predefined field lists, checks if each field exists
        in the metadata, and gathers their respective values. If multiple values exist
        for a field, it stores them in a list under that field.

        Returns:
        dict: A dictionary containing location-related descriptions from metadata.
        """

        metadata_update = {}  # Dictionary to hold the collected values
        location_description_fields = [Location_fields, city_fields, state_fields, country_fields, country_code_fields]

        try:
            for field_list in location_description_fields:
                for field in field_list:
                    if field in self.metadata:  # Check if the key exists in the metadata
                        value = self.metadata[field]
                        if field in metadata_update:
                            if not isinstance(metadata_update[field], list):
                                metadata_update[field] = [metadata_update[field]]
                            metadata_update[field].append(value)
                        else:
                            metadata_update[field] = value

        except Exception as e:
            print(f"Error occurred: {e}")

        return metadata_update



# People-related methods
# ################################################################
    
    def extract_person_names(self):
        try:
            person_dict = {}
            last_name_count = 1
            married_name_count = 1
            person_group_count = 1

            # Extract the XMP:RegionName value regardless of it being a string or list
            people_names = self.metadata.get('XMP:RegionName', '')
            if isinstance(people_names, str):
                people_names = [people_names]  # Convert single string to list

            with open(people_lookup, mode='r', newline='') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    metadata_name = row['Metadata Name'].strip()  # Remove .lower()
                    # print(f"Checking metadata name: {metadata_name}")

                    # Check each individual name from the list
                    for name in people_names[:30]:  # Limit to 30 names
                        if metadata_name.lower() == name.lower():  # Compare lowercase strings
                            # print(f"Match found for {name}")
                            person_dict[f'XMP:FamilyName{str(last_name_count).zfill(2)}'] = row['Last Name']
                            person_dict[f'XMP:MarriedName{str(married_name_count).zfill(2)}'] = row['Married Names']
                            person_dict[f'XMP:PersonGroup{str(person_group_count).zfill(2)}'] = row['Metadata Name']
                            
                            last_name_count += 1
                            married_name_count += 1
                            person_group_count += 1
                            break  # Move to the next row in the CSV

            # The following section associates each item in the 'XMP:RegionName' list with a specific 'Person' field
            person_count = 1
            for name in people_names[:30]:  # Limit to 30 names
                if person_count <= 30:  # Assign to maximum 30 'Person' fields
                    person_field_name = f'XMP:Person{str(person_count).zfill(2)}'
                    person_dict[person_field_name] = name
                    person_count += 1
                else:
                    break  # Stop adding 'Person' fields after reaching the limit

            return person_dict  # Return dictionary with assigned values

        except Exception as e:
            print(f"Error occurred: {e}")
            return None  # Return None on error


    def extract_person_names_pass_df(self,df):
    
        person_dict = {}

        # Extract the XMP:RegionName value regardless of it being a string or list
        try:
            people_names = self.metadata.get('XMP:RegionName', '')
        except Exception as e:
            print("  Can't Find Names in XMP:RegionName")
            print(f"Error occurred: {e}")
            return None  # Return None on erro

        # print(people_names)
        # print(type(people_names))

        if people_names:

            last_name = ""
            family_name = ""
            married_name = ""
            family_field_name = ""
            married_field_name = ""
            person_count = 0
            family_count = 0
            married_count = 0

            if isinstance(people_names, str):
                people_names = [people_names]  # Convert single string to list
                # print(people_names)

            for name in people_names[:30]:  # Limit to 30 names
                
                try:
                    name_dict = DataFileHandler.search_dataframe(df, name, "Metadata Name", ["Metadata Name","Family","Married Names","Last Name"], case_sensitive=True, exact_match=True)

                except:

                    if person_count <= 30:  # Assign to maximum 30 'Person' fields
                        person_count += 1
                        person_field_name = f'XMP:Person{str(person_count).zfill(2)}'
                        person_dict[person_field_name] = name
                        person_dict[family_field_name] = ""
                        person_dict[married_field_name] = ""
                        continue
                        # print(name_dict["Family"])
                        # print(name_dict["Married Names"])
                        # print(type(name_dict["Married Names"]))

                if name_dict:

                    if person_count <= 30:  # Assign to maximum 30 'Person' fields
                        person_count += 1
                        person_field_name = f'XMP:Person{str(person_count).zfill(2)}'
                        person_dict[person_field_name] = name
                        # person_dict[family_field_name] = ""
                        # person_dict[married_field_name] = ""

                        # family_is_nan = pd.isna(name_dict["Family"])
                        married_is_nan = pd.isna(name_dict["Married Names"])

                        # print(name_dict)
                        
                        # print(f"married_is_nan {type(married_is_nan)} is {married_is_nan}")

                        # input("step 1")

                        # if family_is_nan == False:
                        
                        if name_dict["Family"] == True:
                            # print(f"family Name is {name_dict["Last Name"]}")
                            # input("step 2")
                        # if isinstance(name_dict["Family"],str):
                            family_name = name_dict["Last Name"]
                            family_count += 1
                            family_field_name = f'XMP:FamilyName{str(family_count).zfill(2)}'
                            # print(f"family_field_name {family_field_name}  |  family_name: {family_name}")
                            person_dict[family_field_name] = family_name
                        

                        # if name_dict["Married Names"] == True:
                        if married_is_nan == False:
                        # if isinstance(name_dict["Last Name"],str):
                            married_name = name_dict["Married Names"]
                            married_count += 1
                            married_field_name = f'XMP:MarriedName{str(married_count).zfill(2)}'
                            person_dict[married_field_name] = married_name

                        # else:
                        #     del person_dict["Married Names"]
                else:
                    pass

                # Remove entries with empty strings as both keys and values
                person_dict = {key: value for key, value in person_dict.items() if key != '' and value != ''}


                # print(f"name_dict: {name_dict}")
                # print(f"person_dict: {person_dict}")
                # input("PAUSE")

            return person_dict

                # print(person_dict)
                # input("asdf")

        else:
            pass



    #             person_count += 1
    #         else:
    #             break  # Stop adding 'Person' fields after reaching the limit


    #         break  # Move to the next row in the CSV

    #     # The following section associates each item in the 'XMP:RegionName' list with a specific 'Person' field


    #     return person_dict  # Return dictionary with assigned values

    # except Exception as e:
    #     print(f"Error occurred: {e}")
    #     return None  # Return None on error
       


    def extract_person_names_fuzzy(self):
        try:
            person_dict = {}
            last_name_count = 1
            married_name_count = 1
            person_group_count = 1

            # Extract the XMP:RegionName value regardless of it being a string or list
            people_names = self.metadata.get('XMP:RegionName', '')
            if isinstance(people_names, str):
                people_names = [people_names]  # Convert single string to list

            with open(people_lookup, mode='r', newline='') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    metadata_name = row['Metadata Name'].strip()  # Remove .lower()
                    # print(f"Checking metadata name: {metadata_name}")

                    # Check each individual name from the list using fuzzy matching
                    for name in people_names[:30]:  # Limit to 30 names
                        if isinstance(name, str) and fuzz.ratio(metadata_name.lower(), name.lower()) >= 90:
                            # print(f"Match found for {name}")
                            person_dict[f'XMP:FamilyName{str(last_name_count).zfill(2)}'] = row['Last Name']
                            person_dict[f'XMP:MarriedName{str(married_name_count).zfill(2)}'] = row['Married Names']
                            person_dict[f'XMP:PersonGroup{str(person_group_count).zfill(2)}'] = row['Metadata Name']
                            
                            last_name_count += 1
                            married_name_count += 1
                            person_group_count += 1
                            break  # Move to the next row in the CSV

            print(f"Final dictionary: {person_dict}")  # Debug: Check the final dictionary
            return person_dict  # Return dictionary with assigned values

        except Exception as e:
            print(f"Error occurred: {e}")
            return None  # Return None on error
        

# ACDSee XML Categories Parsing methods
# ################################################################

    def parse_xmp_categories(self):
        """
        This method parses the XMP:Categories metadata and extracts information based on provided regex patterns.

        Args:
            acdsee_parser: A dictionary where keys represent metadata fields and values represent regex expressions.

        Returns:
            A dictionary containing extracted information from XMP:Categories or None if the field is not found.
        """
        parsed_data = {}

        # Get XMP:Categories metadata
        if "XMP:Categories" in self.metadata:
            categories_xml = self.metadata["XMP:Categories"]

            # Parse each regex pattern
            for metadata_field, regex in acdsee_parser.items():
                match = re.search(regex, categories_xml)

                try:

                    # Add extracted value to dictionary if found
                    if match:
                        parsed_data[metadata_field] = match.group(1)
                    else:
                        parsed_data[metadata_field] = None

                except:
                    parsed_data[metadata_field] = None


        else:
            parsed_data = None

        return parsed_data

    def parse_compiled_xmp_categories(self, compiled_patterns, missing_values=None):
        """
        Extracts metadata from XMP:Categories XML based on compiled regex patterns.

        Args:
        - compiled_patterns (dict): A dictionary containing compiled regex patterns for metadata extraction.
        - missing_values (optional): Value to be assigned if metadata field is not found. Default is None.

        Returns:
        - dict: A dictionary containing extracted metadata fields as keys and their corresponding values.
        If metadata is not found or cannot be extracted, returns the 'missing_values' parameter provided.
        """
        parsed_data = {}

        # Get XMP:Categories metadata
        if "XMP:Categories" in self.metadata:
            categories_xml = self.metadata["XMP:Categories"]

            # Parse each compiled regex pattern
            for metadata_field, pattern in compiled_patterns.items():
                match = pattern.search(categories_xml)

                try:
                    # Add extracted value to dictionary if found
                    if match:
                        parsed_data[metadata_field] = match.group(1)
                    else:
                        parsed_data[metadata_field] = missing_values
                except:
                    parsed_data[metadata_field] = missing_values
        else:
            parsed_data = missing_values

        return parsed_data

    def acdsee_metadata_report(self):
        """
        Generates a metadata report based on ACDSee keys mapped to respective XMP keys.

        This method iterates through ACDSee keys and their respective XMP keys, extracting
        location information from the associated parser. It utilizes 'parse_compiled_xmp_categories'
        to extract information and compiles a report based on the available metadata.

        Returns:
        - dict: A dictionary containing extracted metadata fields as keys and their corresponding values.
        If metadata is not found, an empty dictionary is returned.
        """
        # Define the mapping of acdsee keys to their respective XMP keys
        acdsee_xmp_mapping = {
            "XMP:LocationCreatedLocationName": "Location",
            "XMP:LocationCreatedCity": "City",
            "XMP:LocationCreatedProvinceState": "ProvinceState",
            "XMP:LocationCreatedCountryName": "Country",
            "XMP:LocalityGeneral": "LocalityGeneral",
            "XMP:LocalityType": "LocalityType",
            "XMP:LocalitySpecific": "LocalitySpecific",
        }

        update = {}

        # Iterate through the acdsee_xmp_mapping to extract location information
        for acdsee_key, xmp_key in acdsee_xmp_mapping.items():
            location_pattern = {acdsee_key: acdsee_parser[acdsee_key]}
            location_info = self.parse_compiled_xmp_categories(location_pattern, missing_values="-")
            if location_info != "-":
                update.update(location_info)

        return update





# Keyword Parsing methods
# ################################################################
    def find_keywords(self):
        headlines = self.filter_metadata(["XMP:Headline", "IPTC:Headline"])
        # print(headlines)
        unique_dict = self._filter_unique_values(headlines)
        keyword_string = ' '.join(str(value) for value in unique_dict.values())
        keyword_string = keyword_string.split()
        # print(keyword_string)
        
        data_file_handler = DataFileHandler()
        keyword_lookup_df = data_file_handler.load_csv_files_to_dataframe([keyword_lookup])
        
        if keyword_string:

            keywords = []
        
            for string in keyword_string:
                keyword_dict = data_file_handler.search_dataframe(keyword_lookup_df, string, "word_lookup", ["word_return"], case_sensitive=False, exact_match=True)
                if keyword_dict:
                    first_value = keyword_dict[next(iter(keyword_dict))]
                    keywords.append(first_value)

            if keywords:
                return keywords
            else:
                return None
        # print(keywords)
                
                

        # print(keywords)


            # # Read the CSV file into a Pandas DataFrame
            # df = pd.read_csv(keyword_lookup)

            # # Convert the word_lookup column to lowercase for case-insensitive comparison
            # df['word_lookup_lower'] = df['word_lookup'].str.lower()

            # # Convert keyword_string to lowercase for comparison
            # keyword_string_lower = keyword_string.lower()

            # # Find matches using regular expressions to ensure whole word matches
            # for index, row in df.iterrows():
            #     words_to_return = row['word_lookup_lower'].split(', ')
            #     pattern = r'\b(?:{})\b'.format('|'.join(re.escape(word) for word in words_to_return))
            #     if re.search(pattern, keyword_string_lower):
            #         # Retain the original case of words_to_return from the word_return column
            #         keywords.extend(row['word_return'].split(', '))

            # return keywords
                




# Dictionary methods
# ################################################################

    def combine_dicts(**kwargs):
        """
        Merge multiple dictionaries into a single dictionary, prioritizing non-empty values.

        Args:
        **kwargs: Variable number of dictionaries.

        Returns:
        dict: A merged dictionary containing keys and values from input dictionaries.
        If multiple dictionaries have values for the same key, the function
        prioritizes the first non-empty value encountered for that key.
        """
        combined_dict = {}
        for dictionary in kwargs.values():
            for key, value in dictionary.items():
                if key not in combined_dict or not combined_dict[key]:
                    combined_dict[key] = value
        return combined_dict

    def check_dict_consistency(self, data_dict):
        """
        Check the consistency of values within a dictionary.

        Args:
        data_dict (dict): A dictionary to check for value consistency.

        Returns:
        None if the dictionary is empty or contains only None values.
        The consistent value if all non-None values are the same.
        An error message if there are inconsistent non-None values.

        Example:
        If data_dict = {'a': 10, 'b': 10, 'c': 10}, the function returns 10.
        If data_dict = {'a': 10, 'b': 20, 'c': 10}, the function returns
        "Error: inconsistent values in dictionary".
        """
        # Check for empty dictionary or only None values
        if not data_dict or all(value is None for value in data_dict.values()):
            return None

        # Collect non-None values
        values = [value for value in data_dict.values() if value is not None]

        # Check for consistency among non-None values
        if all(value == values[0] for value in values):
            return values[0]
        else:
            return "Error: inconsistent values in dictionary", values

    @staticmethod
    def modify_dictionary(dictionary, search_str, replace_str, target='keys', exact_match=True, case_insensitive=False):
        """
        Modify a dictionary by searching for a string within keys or values and replacing occurrences.

        Args:
        - dictionary (dict): The input dictionary to be modified.
        - search_str (str): The string to search for within keys or values.
        - replace_str (str): The string to replace the found occurrences with.
        - target (str, optional): Indicates whether to search 'keys' or 'values'. Defaults to 'keys'.
        - exact_match (bool, optional): Indicates if the match should be exact or allow substring matches. Defaults to True.
        - case_insensitive (bool, optional): Indicates if the search should be case insensitive. Defaults to False.

        Returns:
        - dict: The modified dictionary with replacements made as per the specified criteria.
        """
        modified_dict = {}

        for key, value in dictionary.items():
            key_to_check = key if target == 'keys' else value

            if case_insensitive:
                key_to_check = str(key_to_check).lower()
                search_str = search_str.lower()

            if exact_match:
                if key_to_check == search_str:
                    if target == 'keys':
                        modified_dict[replace_str] = value
                    else:
                        modified_dict[key] = replace_str
                else:
                    modified_dict[key] = value
            else:
                if search_str in str(key_to_check):
                    if target == 'keys':
                        modified_dict[key.replace(search_str, replace_str)] = value
                    else:
                        modified_dict[key] = str(value).replace(search_str, replace_str)
                else:
                    modified_dict[key] = value

        return modified_dict




# Misc methods
# ################################################################

    def convert_headline_to_title(self, headline):

        regex_search1 = re.compile(r'[^A-Za-z0-9 ]')
        regex_replace1 = ""

        regex_search2 = re.compile(r'^\s+|\s+$')
        regex_replace2 = ""

        regex_search3 = re.compile(r'\s+')
        regex_replace3 = " "

        # truncate title to max characters
        title = headline[:asset_title_length]
        # delete non word/space characters
        title = re.sub(regex_search1, regex_replace1, title)
        # delete leading/trailing spaces
        title = re.sub(regex_search2, regex_replace2, title)
        # convert to lower case
        title = title.lower()
        # replace multiple spaces with single space
        title = re.sub(regex_search3, regex_replace3, title)
        # replace spaces with hyphens
        title = title.replace(" ","-")

        title_update = {}
        title_update["XMP:Headline"] = headline
        title_update["IPTC:Headline"] = headline
        title_update["XMP:Title"] = title
        title_update["IPTC:Title"] = title

        return title_update
