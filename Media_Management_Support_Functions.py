from datetime import datetime
from datetime import datetime, date
from datetime import timedelta
from tqdm import tqdm
import subprocess
import shutil
import exiftool
import csv
import os






def convert_date_to_string(var):
    if isinstance(var, date):
        var = var.strftime("%Y%m%d")  # Format the date as needed
        # print(f"var is {var} of type: {type(var)}")
        return var
    
    else:
        return "Not a date object"



def find_key_date(metadata, filename):
    try:
        create_date = find_earliest_created_date(metadata)
        create_date = convert_date_to_string(create_date) + "c"
        modified_date = ""
    except:
        modified_date = find_earliest_modified_date(metadata)
        convert_date_to_string(modified_date) + "m"
        create_date = ""
    try:
        filename_date = get_media_date_from_filename(filename)
        filename_date = filename_date["AssetDate"]
    except:
        filename_date = ""

    if create_date and not filename_date:
        return create_date
    elif create_date and filename_date:
        filename.replace("xx","01")
        if create_date == filename_date:
            return filename_date
        else:
            return ""
    elif modified_date and not create_date and not filename_date:
        return modified_date
    else:
        return ""

       

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

# \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
# Check File and Metadata Dates End \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
# \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

# #######################################################################################
# Date Funtions End #####################################################################
# #######################################################################################



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


# #######################################################################################
# Find Locations Based on Lat/Long End ##################################################
# #######################################################################################






def generate_title_based_on_headline(image_folder):

    
    generate_title_error_report = r"C:\Media Management\Reports\generate-title-error_report.csv"
    generate_title_error_report_header = ["File Name", "Error"]
    generate_title_error_report_rows = []
        
    # Create the list of files to process
    files_to_process = load_files_to_process(image_folder)
    total_files = len(files_to_process)
    file_counter = 0
    headlines = ""
      
    # Load Exiftool
    with exiftool.ExifToolHelper() as et:
        # Process each file in the list of files to process
        if verbose_output == False:
            # print("Writing Title metadata based on Headline metadata...")
            output_option = tqdm(files_to_process, desc="Progress", unit="file")
            
        elif verbose_output == True:
            output_option = files_to_process
        for file in output_option:
            file_counter += 1
            generate_title_error_report_row = []
            error = ""
            headline = ""
            title = ""
            
            if verbose_output == True:
                print(f"Processing file {file_counter} of {total_files}: {file}")
    
            # Get metadata for file
            try:
                metadata = et.get_metadata(file)
                # # print(metadata)
            except:
                # Create entry for error log if metadata can't be read
                error = f"Can't read file metadata"
                continue

            try:
              
                # look for any key that contains the term "Headline"
                headlines = filter_metadata(file, metadata, "key", "Headline")
                longest_headline = ''

                # Search the "headlines" dictionary to find the "Headline" entry that's the longest
                for key, value in headlines.items():
                    if 'headline' in key.lower():
                        if len(value) > len(longest_headline):
                            longest_headline = value
               
            except:
                error = "No Headline Metadata in File"
                if debug == True:
                    traceback.print_exc()
                continue
            
            if not longest_headline or len(str(longest_headline)) == 0:
                error = "No Headline Metadata in File"
                print(f"{f_warning}  No Headline Metadata in File{f_default}")
            else:
                # truncate title to max characters
                title = longest_headline[:title_length]
                # delete non word/space characters
                title = re.sub(regex_search1, regex_replace1, title)
                # delete leading/trailing spaces
                title = re.sub(regex_search2, regex_replace2, title)
                # convert to lower case
                title = title.lower()
                # replace spaces with hyphens
                title = title.replace(" ","-")
                # replace multiple hyphens with single hyphen
                title = re.sub(regex_search3, regex_replace3, title)

                title_update = {}
                title_update["XMP:Title"] = title

                try:
                    et.set_tags(file, title_update)
                except:
                    error = "Can't write Title metadata back to file"
                    continue


    # Write an error report
                if error:
                    generate_title_error_report_row.append(file)
                    generate_title_error_report_row.append(error)
                    generate_title_error_report_rows.append(generate_title_error_report_row)

            if generate_title_error_report_rows:
                write_list_to_csv(generate_title_error_report, generate_title_error_report_rows, header=generate_title_error_report_header)



# Process a list of files (copy, move, delete, convert to lower case)
def process_files(files_list, action, archive, prompt):
    """
    Process files based on the specified action and archive.

    Parameters:
        files_list (list): List of file paths to process.
        action (str): Action to perform - "convert to lower case", "move", "copy", or "delete".
        archive (str): Archive type - "live-archive" or "static-archive".
        prompt (bool): Whether to prompt user for confirmation (True or False).

    Action Details:
        - "convert to lower case": Renames file names and extensions to lowercase.
        - "move": Moves files between archives based on the provided archive parameter.
        - "copy": Copies files between archives based on the provided archive parameter.
        - "delete": Deletes files from the specified archive.

    Archive Details:
        - "live-archive": Represents the source or destination of files.
        - "static-archive": Represents the source or destination of files.

    Prompt Details:
        - True: Prompts user for confirmation before processing each file.
        - False: Processes files without prompting.

    Example Usage:
        files_to_process = [
            "path/to/file1.txt",
            "path/to/file2.pdf",
            "path/to/file3.jpg"
        ]

        process_files(files_to_process, "delete", "live-archive", True)
    """

    live_folder = "path/to/live-archive"
    static_folder = "path/to/static-archive"

    for file_path in files_list:
        if prompt:
            confirmation = input(f"Confirm {action} for {file_path} (y/n): ").lower()
            if confirmation != 'y':
                continue  # Skip this file if user does not confirm

        if action == "convert to lower case":
            file_dir, file_name = os.path.split(file_path)
            filename, file_extension = os.path.splitext(file_name)

            # Convert filename and extension to lowercase
            new_filename = filename.lower()
            new_extension = file_extension.lower()

            # Rename file to lowercase filename and extension
            new_file_path = os.path.join(file_dir, new_filename + new_extension)
            os.rename(file_path, new_file_path)
            print(f"Renamed {file_path} to {new_file_path}")

        elif action == "move":
            if archive == "live-archive":
                destination_path = static_folder
            elif archive == "static-archive":
                destination_path = live_folder

            shutil.move(file_path, os.path.join(destination_path, os.path.basename(file_path)))
            print(f"Moved {file_path} to {destination_path}")

        elif action == "copy":
            if archive == "live-archive":
                source_path = live_folder
                destination_path = static_folder
            elif archive == "static-archive":
                source_path = static_folder
                destination_path = live_folder

            shutil.copy2(file_path, os.path.join(destination_path, os.path.basename(file_path)))
            print(f"Copied {file_path} to {destination_path}")

        elif action == "delete":
            if archive == "live-archive":
                archive_path = live_folder
            elif archive == "static-archive":
                archive_path = static_folder

            os.remove(file_path)
            print(f"Deleted {file_path} from {archive_path}")
