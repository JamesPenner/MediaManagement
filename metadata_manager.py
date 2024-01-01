import re
import sys
import csv
from datetime import datetime, timezone
import pandas as pd
import date_support_functions

import timeit

from fuzzywuzzy import fuzz
sys.path.append(r'C:\Media Management\Scripts')
from config import created_date_fields, acdsee_parser, Location_fields, city_fields, state_fields, country_fields, country_code_fields, gps_fields, locality_fields, location_lookup, people_lookup, family_names, filename_validation_rules



class Metadata_Manager:

    def __init__(self, metadata_list):
        if len(metadata_list) != 1:
            raise ValueError("Expected a list containing only one dictionary")
        self.metadata = metadata_list[0]

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
            people_dates = date_support_functions.process_metadata_and_people_lookup(create_date,People_List,people_lookup)

            return people_dates

    def get_holiday_dates(self):
        # Find the earliest Create Date
        create_dates = self.filter_date_fields("created")
        # print(create_dates)
        create_date = self.get_earliest_date(create_dates)
        # print(create_date)

        # Check if the date is accurate
        AccurateDate = self.filter_metadata(["XMP:AccurateDate"])
        AccurateDate = AccurateDate["XMP:AccurateDate"]
        # print(AccurateDate)
        
        if AccurateDate is True:
            # Find location information in files.
            holiday_dates = date_support_functions.check_holiday(create_date)

            return holiday_dates

    def get_earliest_date(self, metadata_dict):
        """
        Finds the earliest date/time object from a dictionary of metadata fields.

        Args:
            metadata_dict: A dictionary containing metadata fields with various values.

        Returns:
            The earliest date/time object found in the dictionary, formatted as %Y:%m:%d %H:%M:%S%z,
            or None if no valid date/time objects are found.
        """

        date_formats = [
        '%Y-%m-%d %H:%M:%S%z',
        '%Y:%m:%d %H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S',
        '%Y:%m:%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y:%m:%d'
    ]


        potential_datetimes = []
        for value in metadata_dict.values():
            if isinstance(value, str):
                value = value[:19]
                # print(value)

                # Try multiple common formats with and without timezones
                for format in date_formats:
                    try:
                        datetime_obj = datetime.strptime(value, format)
                        potential_datetimes.append(datetime_obj)
                        break
                    except:
                        pass

        if potential_datetimes:
            return min(potential_datetimes)
        else:
            return None
                                
                    
                    # print("adding")
                    # break  # Move to the next value if a valid datetime is found

            # try:
            #     print("test")

            # except ValueError:
            #     if potential_datetimes:
            #         print(potential_datetimes)
                
            #     input("sdgfhsdfghH")
            #     pass  # Ignore values that are not valid datetimes

        # if potential_datetimes:
        #     return min(potential_datetimes).strftime("%Y:%m:%d %H:%M:%S%z")
        # else:
        #     return None

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
            metadata_date_data["Month"] = month
            metadata_date_data["DayNumber"] = day
            metadata_date_data["DayName"] = day_name
            metadata_date_data["AssetDate"] = media_xdate.lower()
            metadata_date_data["Created Date"] = media_date
            metadata_date_data["AccurateDate"] = metadata_accurate_date

            return metadata_date_data

        else:
            return None


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

    # def get_earliest_date(self, metadata):
    #     """
    #     This method returns the earliest date found in the specified dictionary.

    #     Args:
    #         metadata: A dictionary containing metadata fields to check for dates.

    #     Returns:
    #         datetime object representing the earliest date or None if no dates are found.
    #     """
    #     date_values = []

    #     for value in metadata.values():
    #         # Check if the value is not a string and convert it to a string
    #         if not isinstance(value, str):
    #             value = str(value)

    #         try:
    #             date_obj = datetime.strptime(value, "%Y:%m:%d %H:%M:%S%z")
    #             date_values.append(date_obj)
    #         except ValueError:
    #             pass

    #     # Sort dates and return the earliest one
    #     if date_values:
    #         return min(date_values)
    #     else:
    #         return None


    # def get_earliest_date(self, metadata):
        earliest_date = None
        date_formats = [
            '%Y-%m-%d %H:%M:%S%z',
            '%Y:%m:%d %H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
            '%Y:%m:%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y:%m:%d'
        ]

        for value in metadata.values():
            if isinstance(value, (str, int, float)):
                if isinstance(value, str):
                    value = value.strip()[:16]
                for date_format in date_formats:
                    try:
                        date = datetime.strptime(str(value), date_format)
                        if earliest_date is None or date < earliest_date:
                            earliest_date = date
                    except (ValueError, TypeError):
                        pass  # Ignore values that can't be converted to datetime

        if earliest_date:
            return earliest_date.strftime('%Y-%m-%d %H:%M:%S%z')
        else:
            return None  # Return None if no valid date was found

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

    def parse_compiled_xmp_categories(self, compiled_patterns):
        """
        This method parses the XMP:Categories metadata and extracts information based on provided compiled regex patterns.

        Args:
            compiled_patterns: A dictionary where keys represent metadata fields and values represent compiled regex patterns.

        Returns:
            A dictionary containing extracted information from XMP:Categories or None if the field is not found.
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
                        parsed_data[metadata_field] = None

                except:
                    parsed_data[metadata_field] = None

        else:
            parsed_data = None

        return parsed_data

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
            return "Error: inconsistent values in dictionary"