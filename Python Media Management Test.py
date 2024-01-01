from datetime import datetime
from datetime import timedelta
from tqdm import tqdm
import traceback
import exiftool
# https://sylikc.github.io/pyexiftool/intro.html
# Add Exiftool to Environmental Variables
import os
import sys
import csv

# exiftool_path = r"C:\Media Management\App\exiftool.exe"

verbose_output = True
debug = False
date_format = "%Y:%m:%d"

# Import custom functions
sys.path.append(r'C:\Media Management\Scripts')
from Media_Management_Support_Functions import check_holiday, combine_dicts, check_person_event, load_files_to_process, find_earliest_created_date, find_earliest_modified_date, get_media_date_from_filename, find_key_date, process_key_date

# source_image_path = r"D:\0_Media-Archive\03_archive\live-archive\Photos\2000-2099\2020s\2022"
source_image_path = r"D:\0_Media-Archive\03_archive\live-archive\Photos"
# source_image_path = r"C:\Media Management\test images"

# error_log_file = r"D:\0_Media-Archive\error_log.csv"
error_log_file = r"C:\Media Management\test images"

validation_log_dates = r"D:\0_Media-Archive\Validation_Log_Dates.csv"
# validation_log_dates = r"C:\Media Management\test images\Validation_Log_Dates.csv"

cameras = ["KODAK DC3200 DIGITAL CAMERA", "Canon PowerShot A200", "NIKON D50", "Canon PowerShot A640", "FinePix E510", "PENTAX Optio S6", "COOLPIX L11", "Canon PowerShot A540", "DSC-S40", "NIKON D80", "SP550UZ", "Canon EOS 20D", "COOLPIX P90", "Canon PowerShot A2000 IS", "NIKON D60", "DMC-TS1", "DMC-FZ18", "Canon VIXIA HG20", "NIKON D40X", "Canon EOS DIGITAL REBEL XSi", "uT8000,ST8000", "Canon EOS 7D", "NIKON D300", "NIKON D700", "Canon EOS DIGITAL REBEL XS", "iPod touch", "HDR-CX190", "Canon PowerShot ELPH 520 HS", "iPhone 4S", "GT-N8010", "MP280 series", "iPhone 3GS", "Tegra Camera", "iPhone 4", "Kidizoom camera", "Canon PowerShot SX600 HS", "Oregon 650", "iPhone 5s", "SM-G920W8", "iPhone 6", "NIKON D5300", "iPhone 8", "Pixel 3a", "SM-A530W", "iPhone 8 Plus", "iPhone SE (2nd generation)"]

# use this to set colors on text output to the console
def set_color(text_style, text_color, bacground_color):
    text_styles = {
        "default": "0",
        "bold": "1",
        "underline": "2",
        "italic": "3",
        "none": "5",
    }

    text_colors = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "purple": "35",
        "cyan": "36",
        "white": "37",
    }

    text_background_colors = {
        "black": "40",
        "red": "41",
        "green": "42",
        "yellow": "43",
        "blue": "44",
        "purple": "45",
        "cyan": "46",
        "white": "47",
    }

    style = text_styles[text_style]
    color = text_colors[text_color]
    bacground = text_background_colors[bacground_color]

    ascii_color = f"\033[;{style};{color};{bacground}m"
    print(ascii_color)

    return ascii_color

def get_modified_date(file_path):
    # Check if the file exists
    if os.path.exists(file_path):
        # Get the file's modification timestamp
        modification_time = os.path.getmtime(file_path)
        # Convert the timestamp to a readable date format
        modified_date = datetime.fromtimestamp(modification_time)
        return modified_date
    else:
        return None  # File doesn't exist


def process_date_metadata(source_image_path):

    files_to_process = load_files_to_process(source_image_path)

    total_files = len(files_to_process)
    file_counter = 0

    # Open the CSV file in append mode
    with open(error_log_file, 'a', newline='') as error_csv:
        error_writer = csv.writer(error_csv)

        # Load Exiftool
        with exiftool.ExifToolHelper() as et:

            # Process each file in the list of files to process
            if verbose_output == False:
                # print("Writing Title metadata based on Headline metadata...")
                # output_option = tqdm(files_to_process, desc="Progress", unit="file")
                output_option = files_to_process
                
            elif verbose_output == True:
                output_option = files_to_process
            
            for file in output_option:
                file_counter += 1
                
                if verbose_output == True:
                    print(f"Processing file {file_counter} of {total_files}: {file}")

                # Get metadata for file
                try:
                    metadata = et.get_metadata(file)
                    # print(metadata)
                except:
                    error = "Can't read file metadata"
                    # Write error to the CSV file
                    error_writer.writerow([file, error])
                    continue

                key_date = find_key_date(metadata, file)
                
                if key_date:
                    date_fields = process_key_date(key_date)
                    print(f"key_date: {key_date}")
                    print(f"Dates Fields: {date_fields}")
                else:
                    error = "No Keydate found."
                    # Write error to the CSV file
                    error_writer.writerow([file, error])
                    continue

                for d in metadata:
                    # Check RegionName for any people's names
                    try:
                        people_names = d["XMP:RegionName"]
                    except:
                        if debug == True:
                            traceback.print_exc()
                        people_names = ""

                    # Check DigitalSourceType to determine 
                    try:
                        digital_source_type = d["XMP:DigitalSourceType"]
                    except:
                        if debug == True:
                            traceback.print_exc()
                        digital_source_type = ""
                    



def validate_dates(source_image_path):

    files_to_process = load_files_to_process(source_image_path)

    total_files = len(files_to_process)
    file_counter = 0

    # Open the CSV file in append mode
    with open(validation_log_dates, 'a', newline='') as date_validation_log_csv:
        validation_log = csv.writer(date_validation_log_csv)

        validation_log.writerow(["File", "Create Date Present", "Modified Date", "File Name Date Present", "DigitalSourceType", "Pass Validation", "Error"])

        # Load Exiftool
        with exiftool.ExifToolHelper() as et:

            # Process each file in the list of files to process
            if verbose_output == False:
                # print("Writing Title metadata based on Headline metadata...")
                # output_option = tqdm(files_to_process, desc="Progress", unit="file")
                output_option = files_to_process
                
            elif verbose_output == True:
                output_option = files_to_process
            
            for file in output_option:
                log_filename = "-"
                log_create_date = "-"
                log_modified_date = "-"
                log_filename_date = "-"
                log_source_type = "-"
                log_pass = "Fail"
                log_error = "-"

                file_counter += 1
                log_filename = file
                
                if verbose_output == True:
                    print(f"Processing file {file_counter} of {total_files}: {file}")

                try:
                    # Get the modified Date
                    log_modified_date = get_modified_date(file)
                    log_modified_date = log_modified_date.strftime("%Y%m%d") + "m"
                    print(f"found log_modified_date: {log_modified_date}")
                except:
                    log_modified_date = "-"

                # Check if there's a date present in the file name
                try:
                    date_in_filename = get_media_date_from_filename(file)
                    log_filename_date = date_in_filename["AssetDate"]
                    print(f"found log_filename_date: {log_filename_date}")
                except:
                    log_filename_date = "-"
                    log_error = "Date Prefix Not Found in File Name"
                    # Write results to log file
                    validation_log.writerow([log_filename,log_create_date,log_modified_date,log_filename_date,log_source_type,log_pass,log_error])
                    continue

                # Get metadata for file
                try:
                    metadata = et.get_metadata(file)
                except:
                    log_error = "Can't read file metadata"
                    # Write results to log file
                    validation_log.writerow([log_filename,log_create_date,log_modified_date,log_filename_date,log_source_type,log_pass,log_error])
                    continue
                
                for d in metadata:
                    # Check for Create Date
                    try:
                        create_date = find_earliest_created_date(metadata)
                        log_create_date = create_date
                        log_create_date = log_create_date.strftime("%Y%m%d") + "c"
                        print(f"found log_create_date: {log_create_date}")
                    except:
                        create_date = "-"
                        log_error = "No Create Date found in Metadata"
                        # Write error to the CSV file
                        validation_log.writerow([log_filename,log_create_date,log_modified_date,log_filename_date,log_source_type,log_pass,log_error])
                        continue

                    # Check DigitalSourceType to determine 
                    try:
                        digital_source_type = d["XMP:DigitalSourceType"]
                        log_source_type = digital_source_type
                        print(f"found log_source_type: {log_source_type}")
                    except:
                        if debug == True:
                            traceback.print_exc()
                        log_source_type = "-"
                        log_error = "No DigitalSourceType Found"
                        validation_log.writerow([log_filename,log_create_date,log_modified_date,log_filename_date,log_source_type,log_pass,log_error])
                        continue

                    # if date_in_filename:
                    #     date_in_filename = date_in_filename["Created Date"]
                        # date_in_filename = datetime.strptime(date_in_filename, '%Y:%m:%d')


                    # If there's both a Create date in the metadata and a Create date in the file name and they are not the same, and the image was not a scan, give preference to the Create Date in the file metadata
                    if log_filename_date and log_create_date and log_filename_date != log_create_date and log_source_type != "Print":
                        print(f"{f_warning}{file}\nThe date in the file name {log_filename_date} and the date in the metadata {log_create_date} don't\nSynch File Name Date with Metadata Create Date?{f_default}")
                        log_error = "File Name and Create Date Mismatch. Prefer Metadata Create Date?"
                        # Write error to the CSV file
                        validation_log.writerow([log_filename,log_create_date,log_modified_date,log_filename_date,log_source_type,log_pass,log_error])
                        continue
                    
                    # If there's both a Create date in the metadata and a Create date in the file name and they are not the same, and the image IS a scan, give preference to the Create Date in the file metadata
                    elif log_filename_date and log_create_date and log_filename_date != log_create_date and log_source_type == "Print":
                        print(f"{f_warning}{file}\nThe date in the file name {log_filename_date} and the date in the metadata {log_create_date} don't\nnSynch Metadata Create Date with File Name Date?{f_default}")
                        log_error = "File Name and Create Date Mismatch. Prefer Filename Date?"
                        # Write error to the CSV file
                        validation_log.writerow([log_filename,log_create_date,log_modified_date,log_filename_date,log_source_type,log_pass,log_error])
                        continue
                    else:
                        log_pass = "Pass"
                        print(f"File Passes Validation: {log_pass}")
                        validation_log.writerow([log_filename,log_create_date,log_modified_date,log_filename_date,log_source_type,log_pass,log_error])
                        continue

# Set ascii output colors
f_warning = set_color("none", "red", "black")
f_information = set_color("none", "yellow", "black")
f_success = set_color("none", "green", "black")
f_default = set_color("default", "white", "black")

# process_date_metadata(source_image_path)
validate_dates(source_image_path)




















# Step 2: Validate Location















# # Example usage:
# date_to_check = datetime(2023, 3, 17)  # Change the date to the one you want to check
# holiday = check_holiday(date_to_check)
# if holiday:

#     print(f"The date {date_to_check.strftime('%Y-%m-%d')} is {holiday}.")
# else:
#     print(f"The date {date_to_check.strftime('%Y-%m-%d')} is not a known holiday.")
