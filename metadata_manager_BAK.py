import re
import sys
import csv
from datetime import datetime
import pandas as pd
from fuzzywuzzy import fuzz
sys.path.append(r'C:\Media Management\Scripts')
from config import created_date_fields, acdsee_parser, Location_fields, city_fields, state_fields, country_fields, country_code_fields, gps_fields, locality_fields, location_lookup, people_lookup, family_names



class Metadata_Manager:

    def __init__(self, metadata_list):
        if len(metadata_list) != 1:
            raise ValueError("Expected a list containing only one dictionary")
        self.metadata = metadata_list[0]

    def check_dict_consistency(self, data_dict):
        values = [value for value in data_dict.values() if value is not None]

        if len(values) == 0:
            return None
        elif len(set(values)) == 1:
            return values[0]
        else:
            return "Error: inconsistent values in dictionary"

    def get_earliest_create_date(self):
        """
        This method returns the earliest Create Date found in the specified fields.

        Args:
            created_date_fields: A list of strings representing the metadata fields to check for Create Date.

        Returns:
            datetime object representing the earliest Create Date or None if no Create Date is found.
        """
        create_dates = []

        for field in created_date_fields:
            if field in self.metadata:
                try:
                    create_dates.append(datetime.strptime(self.metadata[field], "%Y:%m:%d %H:%M:%S%z"))
                except ValueError:
                    pass

        # Sort dates and return the earliest one
        if create_dates:
            return min(create_dates)
        else:
            return None

    def filter_metadata(self, metadata, list_of_metadata_fields):
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

        return filtered_metadata

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



    # def get_location_from_metadata(self, location_type="location"):
    #     lookup_location = None
    #     standard_fields = None
    #     standard_location = None
    #     acdsee_locality_info = {}

    #     acdsee_metadata = self.parse_xmp_categories()

    #     if location_type.lower() == "location":
    #         standard_fields = Location_fields

    #         if acdsee_metadata:
    #             if "XMP:LocationCreatedLocationName" in acdsee_metadata:
    #                     acdsee_metadata = acdsee_metadata["XMP:LocationCreatedLocationName"]

    #     elif location_type.lower() == "city":
    #         standard_fields = city_fields

    #         if acdsee_metadata:
    #             if "XMP:LocationCreatedCity" in acdsee_metadata:
    #                     acdsee_metadata = acdsee_metadata["XMP:LocationCreatedCity"]

    #     elif location_type.lower() == "state":
    #         standard_fields = state_fields

    #         if acdsee_metadata:
    #             if "XMP:LocationCreatedProvinceState" in acdsee_metadata:
    #                     acdsee_metadata = acdsee_metadata["XMP:LocationCreatedProvinceState"]

    #     elif location_type.lower() == "country":
    #         standard_fields = country_fields

    #         if acdsee_metadata:
    #             if "XMP:LocationCreatedCountryName" in acdsee_metadata:
    #                     acdsee_metadata = acdsee_metadata["XMP:LocationCreatedCountryName"]

    #     elif  location_type.lower() == "locality":
    #         standard_fields = locality_fields

    #         if acdsee_metadata:
    #             if "XMP:LocalityGeneral" in acdsee_metadata:
    #                     acdsee_locality_info["XMP:LocalityGeneral"] = acdsee_metadata["XMP:LocalityGeneral"]
    #             if "XMP:LocalityType" in acdsee_metadata:
    #                     acdsee_locality_info["XMP:LocalityType"] = acdsee_metadata["XMP:LocalityType"]
    #             if "XMP:LocalitySpecific" in acdsee_metadata:
    #                     acdsee_locality_info["XMP:LocalitySpecific"] = acdsee_metadata["XMP:LocalitySpecific"]

    #     elif  location_type.lower() == "gps":
    #         standard_fields = gps_fields
    #         acdsee_locality_info = None

    #     metadata_locations = self.filter_metadata(self.metadata, standard_fields)

    #         # Check to ensure location metadata is consistent between standard location description fields
    #     if location_type.lower() == "location" or location_type.lower() == "city" or location_type.lower() == "state" or location_type.lower() == "country":
    #         location_Check = self.check_dict_consistency(metadata_locations)
    #         if location_Check and (location_Check is None or "Error" not in location_Check):
    #             standard_location = location_Check

    #         # If there is ACDSee locaiton metadata but there is no location metadata in the standard metadata fields.
    #         if acdsee_metadata and not standard_location:
    #             lookup_location = acdsee_metadata
                
    #         # If there is NO ACDSee locaiton metadata but there IS location metadata in the standard metadata fields.
    #         elif standard_location and not acdsee_metadata:
    #             lookup_location = standard_location
    #         else:
    #             lookup_location = None

    #         return lookup_location

    #     # Check to ensure Locality metadata is consistent between standard location description fields
    #     elif location_type.lower() == "locality":
    #         if acdsee_locality_info and not metadata_locations:
    #             return acdsee_locality_info
    #         elif metadata_locations and not acdsee_locality_info:
    #             return metadata_locations
    #         elif acdsee_locality_info and metadata_locations:
    #             if acdsee_locality_info == metadata_locations:
    #                 return metadata_locations
    #             elif acdsee_locality_info != metadata_locations:
    #                 return ("ERROR: Locality info different in ACDSee Categories and Standard fields.")
                
    #     elif location_type.lower() == "gps":
    #         return metadata_locations
        
    #     return lookup_location


    def expand_location_descriptions(self, location_name, column_name):
        # This is currently working to expand found locations. It should be expanded to include City, Locality and GPS fields as well.
        
        global location_lookup  # Declare location_lookup as global
        result = {}

        fields_to_report = ["location", "city", "state", "country", "countrycode", "locality", "localitygeneral", "localityspecific", "localitytype", "gpslatitude", "gpslatituderef", "gpslongitude", "gpslongituderef"]
        metadata_update = {}

        try:
            df = pd.read_csv(location_lookup)
            matched_row = df[df[column_name] == location_name]

            if not matched_row.empty:
                result = matched_row.to_dict(orient='records')[0]

                for key, value in result.items():
                    if key in fields_to_report and value != "-":
                        metadata_update[key] = value

                        if key == "location" and Location_fields:
                            for field in Location_fields:
                                metadata_update[field] = value

                            for field in city_fields:
                                metadata_update[field] = value

                            for field in state_fields:
                                metadata_update[field] = value

                            for field in country_fields:
                                metadata_update[field] = value

                            for field in country_code_fields:
                                metadata_update[field] = value

                del metadata_update["location"]
                        

        except FileNotFoundError:
            print("CSV file not found.")
        except Exception as e:
            print(f"Error occurred: {e}")

        return metadata_update

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
        acdsee_metadata = self.parse_xmp_categories()
        
        # print(acdsee_metadata)
        lookup_location = None

        if location_type.lower() == "location":
            lookup_location = acdsee_metadata.get("XMP:LocationCreatedLocationName")


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
        





    # def extract_person_names(self):
    #     try:
    #         person_dict = {}
    #         last_name_count = 1
    #         married_name_count = 1
    #         person_group_count = 1

    #         # Extract the XMP:RegionName value regardless of it being a string or list
    #         people_names = self.metadata.get('XMP:RegionName', '')
    #         if isinstance(people_names, str):
    #             people_names = [people_names]  # Convert single string to list

    #         with open(people_lookup, mode='r', newline='') as file:
    #             reader = csv.DictReader(file)

    #             for row in reader:
    #                 metadata_name = row['Metadata Name'].strip()  # Remove .lower()
    #                 # print(f"Checking metadata name: {metadata_name}")

    #                 # Check each individual name from the list
    #                 for name in people_names[:30]:  # Limit to 30 names
    #                     if metadata_name.lower() == name.lower():  # Compare lowercase strings
    #                         # print(f"Match found for {name}")
    #                         person_dict[f'XMP:FamilyName{str(last_name_count).zfill(2)}'] = row['Last Name']
    #                         person_dict[f'XMP:MarriedName{str(married_name_count).zfill(2)}'] = row['Married Names']
    #                         person_dict[f'XMP:PersonGroup{str(person_group_count).zfill(2)}'] = row['Metadata Name']
                            
    #                         last_name_count += 1
    #                         married_name_count += 1
    #                         person_group_count += 1
    #                         break  # Move to the next row in the CSV

    #         # print(f"Final dictionary: {person_dict}")  # Debug: Check the final dictionary
    #         return person_dict  # Return dictionary with assigned values