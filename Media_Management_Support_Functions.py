from datetime import datetime
from datetime import datetime, date
from datetime import timedelta
from tqdm import tqdm
import subprocess
import shutil
import exiftool
import csv
import os

verbose_output = True
debug = False

files_to_process = []

exiftool_path = r"C:\Media Management\App\exiftool.exe"

date_format = "%Y:%m:%d"

created_date_fields = [
    "EXIF:CreateDate",
    "IPTC:DateCreated",
    "Composite:DateTimeCreated",
    "XMP:CreateDate",
    # "Composite:SubSecCreateDate",
    # "Composite:SubSecDateTimeOriginal",
]
modified_date_fields = [
    "File:FileModifyDate",
    "EXIF:ModifyDate",
    "XMP:ModifyDate",
    "XMP:ModifyDate",
    "Composite:SubSecModifyDate",
]
custom_date_related_fields = [
    "XMP:DayName",
    "XMP:DayNumber",
    "XMP:Month",
    "XMP:Year",
    "XMP:Decade",
    "XMP:Century",
    "XMP:AssetDate",
    "XMP:AccurateDate",
    "XMP:Season",
]



# load files for processing
def load_files_to_process(directory):
    global files_to_process
    for root, dirs, files in os.walk(directory):
        for file in files:
            if (
                file.lower().endswith(".3gp")
                or file.lower().endswith(".cr2")
                or file.lower().endswith(".cr3")
                or file.lower().endswith(".dng")
                or file.lower().endswith(".heic")
                or file.lower().endswith(".jfif")
                or file.lower().endswith(".jpeg")
                or file.lower().endswith(".jpg")
                or file.lower().endswith(".mov")
                or file.lower().endswith(".mp4")
                or file.lower().endswith(".mts")
                or file.lower().endswith(".mxf")
                or file.lower().endswith(".nef")
                or file.lower().endswith(".png")
                or file.lower().endswith(".tif")
                or file.lower().endswith(".tiff")
                or file.lower().endswith(".gif")
            ):
                files_to_process.append(os.path.join(root, file))
    return files_to_process



# #######################################################################################
# Date Funtions Start ###################################################################
# #######################################################################################

# \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
# Check for Holidays Start \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
# \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

# Function to calculate Easter (Gauss's algorithm)
def calculate_easter(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(year, month, day)

# Function to calculate Good Friday (two days before Easter)
def calculate_good_friday(year):
    easter_date = calculate_easter(year)
    return easter_date - timedelta(days=2)

def calculate_mothers_day(year):
    # Finding the second Sunday of May
    first_may = datetime(year, 5, 1)
    first_sunday = first_may + timedelta(days=(6 - first_may.weekday()))  # first Sunday
    second_sunday = first_sunday + timedelta(weeks=1)  # second Sunday
    return second_sunday

def calculate_fathers_day(year):
    # Finding the second Sunday of June
    first_june = datetime(year, 6, 1)
    first_sunday = first_june + timedelta(days=(6 - first_june.weekday()))  # first Sunday
    second_sunday = first_sunday + timedelta(weeks=1)  # second Sunday
    return second_sunday

def calculate_bc_day(year):
    # Finding the first Monday of August
    first_august = datetime(year, 8, 1)
    first_monday = first_august + timedelta(days=(0 - first_august.weekday() + 7) % 7)
    return first_monday

def calculate_canadian_thanksgiving(year):
    # Finding the second Monday of October
    first_october = datetime(year, 10, 1)
    first_monday = first_october + timedelta(days=(0 - first_october.weekday() + 7) % 7)
    second_monday = first_monday + timedelta(weeks=1)
    return second_monday

def calculate_labour_day(year):
    # Finding the first Monday of September
    first_september = datetime(year, 9, 1)
    first_monday = first_september + timedelta(days=(0 - first_september.weekday() + 7) % 7)
    return first_monday

def calculate_victoria_day(year):
    # Finding the last Monday before May 25
    may_25 = datetime(year, 5, 25)
    last_monday = may_25 - timedelta(days=((may_25.weekday() + 1) % 7) + 1)
    return last_monday

def calculate_truth_and_reconciliation_day(year):
    if year >= 2013:
        return datetime(year, 9, 30)
    else:
        return None  # Returning None for years before 2013

def calculate_family_day_bc(year):
    # Finding the second Monday of February
    first_february = datetime(year, 2, 1)
    first_monday = first_february + timedelta(days=(0 - first_february.weekday() + 7) % 7)
    second_monday = first_monday + timedelta(weeks=1)
    return second_monday

def calculate_family_day_bc(year):
    if year >= 2013:
        # Finding the second Monday of February
        first_february = datetime(year, 2, 1)
        first_monday = first_february + timedelta(days=(0 - first_february.weekday() + 7) % 7)
        second_monday = first_monday + timedelta(weeks=1)
        return second_monday
    else:
        return None  # Returning None for years before 2013
    
    # ##########################################################################################
    # Date Sub Functions #######################################################################
    # ##########################################################################################

def check_holiday(date):
    holidays = {
        "Remembrance Day": (11, 11),
        "Christmas Day": (12, 25),
        "Easter": None,
        "Canada Day": (7, 1),
        "Boxing Day": (12, 26),
        "St. Patrick's Day": (3, 17),
        "Good Friday": None,
        "BC Day": None,
        "Christmas": (12, 25),
        "New Year's Eve": (12, 31),
        "Mother's Day": None,
        "Father's Day": None,
        "Halloween": (10, 31),
        "Thanksgiving": None,
        "Labour Day": None,
        "Valentine's Day": (2, 14),
        "Victoria Day": None,
        "Indigenous Peoples Day": None,
        "Flag of Canada Day": None,
        "Truth and Reconciliation Day": None,
        "Family Day BC": None
    }
    
    for holiday, holiday_date in holidays.items():
        if holiday_date is not None:
            if date.month == holiday_date[0] and date.day == holiday_date[1]:
                return holiday
    
    # For holidays needing special calculations
    if date == calculate_easter(date.year):
        return "Easter"
    if date == calculate_good_friday(date.year):
        return "Good Friday"
    if date == calculate_mothers_day(date.year):
        return "Mother's Day"
    if date == calculate_fathers_day(date.year):
        return "Father's Day"
    if date == calculate_bc_day(date.year):
        return "BC Day"
    if date == calculate_canadian_thanksgiving(date.year):
        return "Thanksgiving"
    if date == calculate_labour_day(date.year):
        return "Labour Day"
    if date == calculate_victoria_day(date.year):
        return "Victoria Day"
    truth_day = calculate_truth_and_reconciliation_day(date.year)
    if truth_day and date == truth_day:
        return "Truth and Reconciliation Day"
    family_day_bc = calculate_family_day_bc(date.year)
    if family_day_bc and date == family_day_bc:
        return "Family Day BC"
    return None

def check_person_event(people_names, date):
    file_path = r'C:\Media Management\Scripts\Lookup Tables\Index of Individuals.csv'
    
    with open(file_path, 'r', newline='') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            for name in people_names:
                if row['Name'] == name:
                    birth_date = row['Birth']
                    marriage_date = row['Marriage']
                    death_date = row['Death']
                    
                    if date == birth_date:
                        return "Birth"
                    elif date == marriage_date:
                        return "Marriage"
                    elif date == death_date:
                        return "Death"
                    
                    birth_month_day = birth_date[5:]  # Extracting month-day part from the birth date
                    given_month_day = date[5:]  # Extracting month-day part from the given date
                    
                    if given_month_day == birth_month_day:
                        birth_year = int(birth_date[:4])
                        death_year = int(death_date[:4])
                        given_year = int(date[:4])
                        
                        if birth_year <= given_year <= death_year:
                            return "Birthday"
                    
        return ""

# # Example usage:
# date_to_check = datetime(2023, 3, 17)  # Change the date to the one you want to check
# holiday = check_holiday(date_to_check)
# if holiday:
#     # print(f"The date {date_to_check.strftime('%Y-%m-%d')} is {holiday}.")
# else:
#     # print(f"The date {date_to_check.strftime('%Y-%m-%d')} is not a known holiday.")

# \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/
# Check for Holidays End \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
# \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

# \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
# Check File and Metadata Dates Start \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
# \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

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





def find_earliest_created_date(metadata):
    found_created_dates = []
    for d in metadata:
        for created_date_field in created_date_fields:
            try:
                metadata_date_field_name = d[created_date_field]
                found_created_dates.append(metadata_date_field_name[:10])
            except:
                pass

    if found_created_dates:
        # Remove any date if it's only zeros
        found_created_dates = [
            date for date in found_created_dates if date != "0000:00:00"
        ]
    if found_created_dates:
        dates = [
            datetime.strptime(date_string, date_format)
            for date_string in found_created_dates
        ]
        earliest_created_date = min(dates)

    else:
        earliest_created_date = ""

    return earliest_created_date

def find_earliest_modified_date(metadata):
    found_modified_dates = []
    for d in metadata:
        for modified_date_field in modified_date_fields:
            try:
                metadata_date_field_name = d[modified_date_field]
                found_modified_dates.append(metadata_date_field_name[:10])
            except:
                pass

    if found_modified_dates:
        # Remove any date if it's only zeros
        found_modified_dates = [
            date for date in found_modified_dates if date != "0000:00:00"
        ]

    if found_modified_dates:
        try:
            dates = [datetime.strptime(date_string, date_format) for date_string in found_modified_dates]
            earliest_modified_date = min(dates)
        except:
            earliest_modified_date = ""    
    else:
        earliest_modified_date = ""

    return earliest_modified_date

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



def combine_dicts(**kwargs):
    combined_dict = {}
    for dictionary in kwargs.values():
        combined_dict.update(dictionary)
    return combined_dict



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







# def list_files(root, recursive=False, include=None, exclude=None):
#     file_list = []

#     if include is None:
#         include = []

#     if exclude is None:
#         exclude = []

#     for dirpath, dirnames, filenames in os.walk(root):
#         for filename in filenames:
#             file_path = os.path.join(dirpath, filename)
#             file_extension = os.path.splitext(filename)[1][1:]  # Get file extension without the '.'

#             # Check if the file extension should be included or excluded
#             if (not include or file_extension in include) and (not file_extension in exclude):
#                 file_list.append(file_path)

#         if not recursive:
#             break  # If not recursive, break the loop after the first iteration of os.walk

#     return file_list


# def filter_file_list_by_extension(file_list, allowed_extensions, ignore_extensions):
#     filtered_files = []
#     for file in file_list:
#         file_extension = file[file.rfind('.'):]  # Extract the extension
#         if file_extension in allowed_extensions and file_extension not in ignore_extensions:
#             filtered_files.append(file)
#     return filtered_files


def list_files(root, recursive=False, include=None, exclude=None):
    """
    Retrieve a list of files within a directory and its subdirectories based on specified criteria.

    Args:
    - root (str): The root directory to start searching for files.
    - recursive (bool): If True, searches through subdirectories recursively. Default is False.
    - include (Optional[List[str]]): A list of file extensions to include. If None, includes all files.
    - exclude (Optional[List[str]]): A list of file extensions to exclude. If None, excludes no files.

    Returns:
    - List[str]: A list of file paths matching the specified criteria.

    Example:
    To retrieve all '.txt' files in the 'root' directory and its subdirectories, excluding '.log' files:
    ```
    files = list_files(root='path/to/root', recursive=True, include=['txt'], exclude=['log'])
    ```

    Notes:
    - 'root' must be a valid directory path.
    - 'include' and 'exclude' should contain file extensions without the period ('.').
    - If 'include' is None, includes all files regardless of extension.
    - If 'exclude' is None, excludes no files based on extension.
    - The returned list includes the full paths of matching files.
    - Uses os.walk() to traverse directories.
    """
    file_list = []

    if include is None:
        include = []

    if exclude is None:
        exclude = []

    # Convert include and exclude lists to lowercase
    include = [ext.lower() for ext in include]
    exclude = [ext.lower() for ext in exclude]

    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_extension = os.path.splitext(filename)[1][1:].lower()  # Get lowercase file extension

            # Check if the lowercase file extension should be included or excluded
            if (not include or file_extension in include) and (not file_extension in exclude):
                file_list.append(file_path)

        if not recursive:
            break  # If not recursive, break the loop after the first iteration of os.walk

    return file_list





def combine_dicts(**kwargs):
    combined_dict = {}
    for dictionary in kwargs.values():
        combined_dict.update(dictionary)
    return combined_dict



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


def copy_files(source, destination_folder, prompt=False):
    """
    Copy one or multiple files to a specified destination folder.

    Args:
        source (str or list): File path or list of file paths to copy.
        destination_folder (str): Destination folder path where files will be copied.
        prompt (bool, optional): If True, prompts the user before copying each file. 
            Defaults to False.

    Returns:
        None

    Raises:
        ValueError: If source is not a valid file path or list of file paths.
        FileNotFoundError: If the destination_folder does not exist.
    """
    def should_copy():
        user_input = input("Do you want to copy this file? (y/n): ").lower()
        return user_input == 'y'

    def copy_single_file(file_path, dest_folder):
        try:
            shutil.copy2(file_path, dest_folder)
            print(f"Copied: {file_path} to {dest_folder}")
        except IOError as e:
            print(f"Unable to copy file: {file_path} - {e}")

    if isinstance(source, str):  # Single file
        source_files = [source]
    elif isinstance(source, list):  # List of files
        source_files = source
    else:
        raise ValueError("Invalid source input. Please provide a single file path or a list of file paths.")

    if not os.path.exists(destination_folder):
        raise FileNotFoundError(f"Destination folder {destination_folder} does not exist.")

    if prompt:
        for file_path in source_files:
            if should_copy():
                copy_single_file(file_path, destination_folder)
            else:
                print(f"Skipping: {file_path}")
    else:  # Copy all files without prompting
        for file_path in source_files:
            copy_single_file(file_path, destination_folder)

def move_files(source, destination_folder, prompt=False):
    """
    Move one or multiple files to a specified destination folder.

    Args:
        source (str or list): File path or list of file paths to move.
        destination_folder (str): Destination folder path where files will be moved.
        prompt (bool, optional): If True, prompts the user before moving each file. 
            Defaults to False.

    Returns:
        None

    Raises:
        ValueError: If source is not a valid file path or list of file paths.
        FileNotFoundError: If the destination_folder does not exist.
    """
    def should_move():
        user_input = input("Do you want to move this file? (y/n): ").lower()
        return user_input == 'y'

    def move_single_file(file_path, dest_folder):
        try:
            shutil.move(file_path, dest_folder)
            print(f"Moved: {file_path} to {dest_folder}")
        except IOError as e:
            print(f"Unable to move file: {file_path} - {e}")

    if isinstance(source, str):  # Single file
        source_files = [source]
    elif isinstance(source, list):  # List of files
        source_files = source
    else:
        raise ValueError("Invalid source input. Please provide a single file path or a list of file paths.")

    if not os.path.exists(destination_folder):
        raise FileNotFoundError(f"Destination folder {destination_folder} does not exist.")

    if prompt:
        for file_path in source_files:
            if should_move():
                move_single_file(file_path, destination_folder)
            else:
                print(f"Skipping: {file_path}")
    else:  # Move all files without prompting
        for file_path in source_files:
            move_single_file(file_path, destination_folder)

def delete_files(source, prompt=False):
    """
    Delete one or multiple files.

    Args:
        source (str or list): File path or list of file paths to delete.
        prompt (bool, optional): If True, prompts the user before deleting each file. 
            Defaults to False.

    Returns:
        None

    Raises:
        ValueError: If source is not a valid file path or list of file paths.
    """
    def should_delete():
        user_input = input("Do you want to delete this file? (y/n): ").lower()
        return user_input == 'y'

    def delete_single_file(file_path):
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except OSError as e:
            print(f"Unable to delete file: {file_path} - {e}")

    if isinstance(source, str):  # Single file
        source_files = [source]
    elif isinstance(source, list):  # List of files
        source_files = source
    else:
        raise ValueError("Invalid source input. Please provide a single file path or a list of file paths.")

    if prompt:
        for file_path in source_files:
            if should_delete():
                delete_single_file(file_path)
            else:
                print(f"Skipping: {file_path}")
    else:  # Delete all files without prompting
        for file_path in source_files:
            delete_single_file(file_path)


def open_csv_in_excel(file_path):
    # check_excel_path_1 = r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE"
    # check_excel_path_2 = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
    excel_paths = [r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE", r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"]
    
    excel_program_path = None

    for excel_path in excel_paths:

        # Check if EXCEL.EXE exists in check_excel_path_1
        if os.path.exists(excel_path):
            excel_program_path = excel_path

    # # Check if EXCEL.EXE exists in check_excel_path_2
    # if not excel_path and os.path.exists(check_excel_path_2):
    #     excel_path = check_excel_path_2

    if not excel_program_path:
        # Directories to search for EXCEL.EXE
        directories_to_search = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            r"C:\\",
            # Add more directories to search if needed
        ]

        excel_program_path = find_excel_exe(directories_to_search)

    if excel_program_path:
        subprocess.Popen([excel_program_path, file_path])
    else:
        print("Sorry. Cannot open file directly. Excel cannot be found")

def find_excel_exe(directories):
    for directory in directories:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower() == 'excel.exe':
                    return os.path.join(root, file)
    return None




# # Example usage:
# dict1 = {'a': 1, 'b': 2}
# dict2 = {'c': 3, 'd': 4}
# dict3 = {'e': 5, 'f': 6}

# result = combine_dicts(first=dict1, second=dict2, third=dict3)
# # print(result)
