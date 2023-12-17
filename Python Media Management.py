from datetime import datetime
from datetime import timedelta
from tqdm import tqdm
import traceback
import exiftool
# https://sylikc.github.io/pyexiftool/intro.html
# Add Exiftool to Environmental Variables
# set common_args in exiftool.py (common_args: Optional[List[str]] = ["-G", "-n" "-overwrite_original"])
import os
import re
import sys
import csv
import json
# exiftool_path = r"C:\Media Management\App\exiftool.exe"

verbose_output = True
debug = False
date_format = "%Y:%m:%d"

# Import custom functions
sys.path.append(r'C:\Media Management\Scripts')
from Media_Management_Support_Functions import check_holiday, combine_dicts, check_person_event, load_files_to_process, find_earliest_created_date, find_earliest_modified_date, get_media_date_from_filename, find_key_date, process_key_date

# source_image_path = r"D:\0_Media-Archive\03_archive\live-archive\Photos\2000-2099\2020s\2022"

# source_image_path = r"C:\Media Management\test images\New folder"

source_image_path = r"D:\0_Media-Archive\03_archive\live-archive\Photos"
# source_image_path = r"C:\Media Management\test images"
# source_image_path = r"C:\Media Management\test images"


error_log_file = r"D:\0_Media-Archive\error_log.csv"
# error_log_file = r"C:\Media Management\test images"

validation_log_dates = r"D:\0_Media-Archive\Validation_Log_Dates.csv"
# validation_log_dates = r"C:\Media Management\Tools\03_Metadata\New folder\Validation_Log_Dates.csv"
# validation_log_dates = r"C:\Media Management\test images\Validation_Log_Dates.csv"


# digital_sourcetype_values = ["digitalCapture: Original digital capture sampled from real life","negativeFilm","positiveFilm","print","minorHumanEdits","compositeCapture","algorithmicallyEnhanced","dataDrivenMedia","digitalArt","virtualRecording","compositeSynthetic","trainedAlgorithmicMedia","compositeWithTrainedAlgorithmicMedia","algorithmicMedia"]
digital_sourcetype_values = ["digitalcapture","negativefilm","positivefilm","print","minorhumanedits","compositecapture","algorithmicallyenhanced","datadrivenmedia","digitalart","virtualrecording","compositesynthetic","trainedalgorithmicmedia","compositewithtrainedalgorithmicmedia","algorithmicmedia"]

cameras = ["KODAK DC3200 DIGITAL CAMERA", "Canon PowerShot A200", "NIKON D50", "Canon PowerShot A640", "FinePix E510", "PENTAX Optio S6", "COOLPIX L11", "Canon PowerShot A540", "DSC-S40", "NIKON D80", "SP550UZ", "Canon EOS 20D", "COOLPIX P90", "Canon PowerShot A2000 IS", "NIKON D60", "DMC-TS1", "DMC-FZ18", "Canon VIXIA HG20", "NIKON D40X", "Canon EOS DIGITAL REBEL XSi", "uT8000,ST8000", "Canon EOS 7D", "NIKON D300", "NIKON D700", "Canon EOS DIGITAL REBEL XS", "iPod touch", "HDR-CX190", "Canon PowerShot ELPH 520 HS", "iPhone 4S", "GT-N8010", "MP280 series", "iPhone 3GS", "Tegra Camera", "iPhone 4", "Kidizoom camera", "Canon PowerShot SX600 HS", "Oregon 650", "iPhone 5s", "SM-G920W8", "iPhone 6", "NIKON D5300", "iPhone 8", "Pixel 3a", "SM-A530W", "iPhone 8 Plus", "iPhone SE (2nd generation)"]

print_sources = ["LS-5000","CanoScan LiDE 300","CanoScan 8600F","HP Scanjet djf4200","Adobe Illustrator CS2","Adobe Illustrator CS6 (Windows)","Adobe Photoshop 7.0","Adobe Photoshop Camera Raw 8.3 (Windows)","Adobe Photoshop Camera Raw 9.1.1 (Windows)","Adobe Photoshop CS2 Windows","Adobe Photoshop CS3 Windows","Adobe Photoshop CS5 Windows","Adobe Photoshop CS6 (Windows)","Adobe Photoshop Elements 3.0 Windows","Adobe Photoshop Lightroom 4.2 (Windows)","CanoScan Toolbox 5.0","Illustrator","Microsoft Photo Gallery 16.4.3528.331","Microsoft Windows Live Photo Gallery14.0.8081.709","Microsoft Windows Photo Gallery 6.0.6001.18000","Microsoft Windows Photo Viewer 10.0.14393.0","Microsoft Windows Photo Viewer 6.1.7600.16385","Microsoft Windows Photo Viewer 6.3.9600.17415","UMAX MagicScan","Windows Photo Editor 10.0.10011.16384"]

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
    with open(validation_log_dates, 'w', newline='') as date_validation_log_csv:
        validation_log = csv.writer(date_validation_log_csv)
        validation_log.writerow(["File", "Create Date Present", "Modified Date", "File Name Date Present", "DigitalSourceType", "Accurate Date", "Asset Date","Pass Validation", "Error"])
        # Load Exiftool
        with exiftool.ExifToolHelper() as et:

            # Process each file in the list of files to process
            if verbose_output == False:
                # output_option = tqdm(files_to_process, desc="Progress", unit="file")
                output_option = files_to_process
                
            elif verbose_output == True:
                output_option = files_to_process
            
            for file in output_option:
                print(file)
                log_errors = []
                log_filename = "-"
                converted_filename_date = "-"
                log_create_date = "-"
                log_modified_date = "-"
                log_filename_date = "-"
                log_source_type = "-"
                log_pass = ""
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
                    log_error = "No modified Date"
                    log_errors.append(log_error)

                # Check if there's a date present in the file name
                try:
                    date_in_filename = get_media_date_from_filename(file)
                    log_filename_date = date_in_filename["AssetDate"]
                    print(f"found log_filename_date: {log_filename_date}")

                except:
                    log_filename_date = "-"
                    converted_filename_date = ""
                    log_error = "Date Prefix Not Found in File Name"
                    log_errors.append(log_error)

                if log_filename_date:
                    if "x" in log_filename_date:
                        converted_filename_date = log_filename_date
                        # Check decade
                        if log_filename_date[2:3] == 'x':
                            prefix = converted_filename_date[0:2]
                            converted_filename_date = prefix + "0" + converted_filename_date[3:]
                            print(f"{converted_filename_date}: {len(converted_filename_date)}")

                        # Check Year
                        if converted_filename_date[3:4] == 'x':
                            prefix = converted_filename_date[0:3]
                            converted_filename_date = prefix + "0" + converted_filename_date[4:]
                            print(f"{converted_filename_date}: {len(converted_filename_date)}")

                        # Check month
                        if converted_filename_date[4:6] == 'xx':
                            prefix = converted_filename_date[0:4]
                            converted_filename_date = prefix + "01" + converted_filename_date[6:]
                            print(f"{converted_filename_date}: {len(converted_filename_date)}")

                        # Check Day
                        if converted_filename_date[6:8] == 'xx':
                            prefix = converted_filename_date[0:6]
                            converted_filename_date = prefix + "01" + converted_filename_date[8:]
                            print(f"{converted_filename_date}: {len(converted_filename_date)}")

                    else:
                        converted_filename_date = log_filename_date


                # Get metadata for file
                try:
                    metadata = et.get_metadata(file)
                except:
                    log_error = "Can't read file metadata"
                    log_errors.append(log_error)
                
                for d in metadata:
                    # Check for Create Date
                    try:
                        create_date = find_earliest_created_date(metadata)
                        log_create_date = create_date
                        log_create_date = log_create_date.strftime("%Y%m%d")


                        # log_create_date = converted_created_date_string
                            
                        # print(f"found log_create_date: {log_create_date}")
                    except:
                        create_date = "-"
                        log_error = "No Create Date found in Metadata"
                        log_errors.append(log_error)

                    # Check for Accurate Date
                    try:
                        accurate_date = d["XMP:AccurateDate"]
                    except:
                        accurate_date = "-"
                        log_error = "No AccurateDate field value in Metadata"
                        log_errors.append(log_error)

                    # Check for Asset Date
                    try:
                        asset_date = d["XMP:AssetDate"]
                    except:
                        asset_date = "-"
                        log_error = "No AssetDate field value in Metadata"
                        log_errors.append(log_error)

                    # Check DigitalSourceType to determine if the source type is valid
                    try:
                        log_source_type = d["XMP:DigitalSourceType"]
                        if log_source_type.lower() not in digital_sourcetype_values:
                            log_error = "Not a valid DigitalSourceType"
                            log_errors.append(log_error)

                        log_source_type = log_source_type
                        print(f"found log_source_type: {log_source_type}")
                    except:
                        if debug == True:
                            traceback.print_exc()
                        log_source_type = "-"
                        log_error = "No DigitalSourceType Found"
                        log_errors.append(log_error)


                    date_sources = [log_filename, log_create_date, log_modified_date, log_filename_date, log_source_type, converted_filename_date]
                    for i in range(len(date_sources)):
                        if not isinstance(date_sources[i], str):
                            date_sources[i] = str(date_sources[i])
                    
                    
                    
                    print(f"log_filename: {log_filename}")
                    print(f"log_create_date: {log_create_date}")
                    print(f"log_modified_date: {log_modified_date}")
                    print(f"log_filename_date: {log_filename_date}")
                    print(f"log_source_type: {log_source_type}")
                    print(f"converted_filename_date: {converted_filename_date}")

                    
                    print(f"log_filename: {log_filename[:8]}")
                    print(f"log_create_date: {log_create_date[:8]}")
                    print(f"log_modified_date: {log_modified_date[:8]}")
                    print(f"log_filename_date: {log_filename_date[:8]}")
                    print(f"log_source_type: {log_source_type[:8]}")
                    print(f"converted_filename_date: {converted_filename_date[:8]}")


                    if log_filename_date != "-" and accurate_date != "-" and "x" in log_filename_date and accurate_date != False:
                        log_error = "File name date is not precise (contains an 'x'), but AccurateDate field not set to 'False'"
                        log_errors.append(log_error)

                    if log_filename_date != "-" and accurate_date != "-" and "x" not in log_filename_date and accurate_date != True:
                        log_error = "File name date is precise (contains an 'x'), but AccurateDate field not set to 'False'"
                        log_errors.append(log_error)

                    if log_filename_date[:8] != "-" and asset_date[:8] != "-" and log_filename_date[:8] != asset_date[:8]:
                        log_error = "File name date and AssetDate are not the same"
                        log_errors.append(log_error)

                    # If there's both a Create date in the metadata and a Create date in the file name and they are not the same, and the image was not a scan, give preference to the Create Date in the file metadata
                    if len(converted_filename_date) and len(converted_filename_date) >=8:
                        if converted_filename_date and log_create_date and converted_filename_date[:8] != log_create_date[:8] and log_source_type != "print":
                            print(f"{f_warning}{file}\nThe date in the file name {log_filename_date} and the date in the metadata {log_create_date} don't match.\nSynch File Name Date with Metadata Create Date?{f_default}")
                            log_error = "File Name and Create Date Mismatch. Prefer Metadata Create Date?"
                            log_errors.append(log_error)
                        
                    # If there's both a Create date in the metadata and a Create date in the file name and they are not the same, and the image IS a scan, give preference to the Create Date in the file metadata
                    if len(converted_filename_date) and len(converted_filename_date) >=8:
                        if converted_filename_date and log_create_date and converted_filename_date[:8] != log_create_date[:8] and log_source_type == "print":
                            print(f"{f_warning}{file}\nThe date in the file name {log_filename_date} and the date in the metadata {log_create_date} don't match.\nSynch Metadata Create Date with File Name Date?{f_default}")
                            log_error = "File Name and Create Date Mismatch. Prefer Filename Date?"
                            log_errors.append(log_error)
                    else:
                        print(f"File Passes Validation: {log_pass}")
               
                if log_error and log_error != "-":
                    log_pass = "Fail"
                else:
                    log_pass = "Pass"
                validation_log.writerow([log_filename,log_create_date,log_modified_date,log_filename_date,log_source_type,accurate_date,asset_date,log_pass,log_errors])                
                    























                  
# def write_source_type(source_image_path):

#     files_to_process = load_files_to_process(source_image_path)

#     total_files = len(files_to_process)
#     file_counter = 0

#     # Open the CSV file in append mode
#     with open(validation_log_dates, 'w', newline='') as date_validation_log_csv:
#         validation_log = csv.writer(date_validation_log_csv)
#         validation_log.writerow(["File", "DigitalSourceType", "IFD0:Make", "IFD0:Model"])

#         # Load Exiftool
#         with exiftool.ExifToolHelper() as et:

#             # Process each file in the list of files to process
#             if verbose_output == False:
#                 # output_option = tqdm(files_to_process, desc="Progress", unit="file")
#                 output_option = files_to_process
                
#             elif verbose_output == True:
#                 output_option = files_to_process
            
#             for file in output_option:
#                 metadata_update = {}
#                 log_errors = []
#                 log_filename = "-"
#                 log_camera_make = "-"
#                 log_camera_model = "-"
#                 log_pass = ""
#                 log_error = "-"

#                 file_counter += 1
#                 log_filename = file
                
#                 if verbose_output == True:
#                     print(f"Processing file {file_counter} of {total_files}: {file}")
                  
#                 # Get metadata for file
#                 try:
#                     metadata = et.get_metadata(file)
#                 except:
#                     log_error = "Can't read file metadata"
#                     log_errors.append(log_error)
                
#                 for d in metadata:
#                     # Check DigitalSourceType to determine if the source type is valid

#                     # print(d)
#                     # for key,value in d.items():
#                     #     print(f"{key}: {value}")
#                     # input("PAUSE")

#                     try:
#                         log_source_type = d["XMP:DigitalSourceType"]
#                         print(f"log_source_type: {log_source_type}")

#                     except:
#                         if debug == True:
#                             traceback.print_exc()
#                         log_source_type = "-"
#                         log_error = "No DigitalSourceType Found"
#                         log_errors.append(log_error)

#                     # Check CreatorTool to determine if the source type is valid
#                     try:
#                         log_creatortool = d["XMP:CreatorTool"]
#                         print(f"log_creatortool: {log_creatortool}")
  
#                     except:
#                         if debug == True:
#                             traceback.print_exc()
#                         log_creatortool = "-"
#                         log_error = "No CreatorTool Found"
#                         log_errors.append(log_error)

#                     # Check IFD0:Make to determine if the source type is valid
#                     try:
#                         log_camera_make = d["EXIF:Make"]
#                         print(f"log_camera_make: {log_camera_make}")

#                     except:
#                         if debug == True:
#                             traceback.print_exc()
#                         log_camera_make = "-"
#                         log_error = "No IFD0:Make Found"
#                         log_errors.append(log_error)

#                     # Check DigitalSourceType to determine if the source type is valid
#                     try:
#                         log_camera_model = d["EXIF:Model"]
#                         print(f"log_camera_model: {log_camera_model}")

#                     except:
#                         if debug == True:
#                             traceback.print_exc()
#                         log_camera_model = "-"
#                         log_error = "No IFD0:Model Found"
#                         log_errors.append(log_error)

#                 if log_camera_make or log_camera_model:
#                     print("YUP")
#                     if not log_creatortool and not log_source_type:
#                         metadata_update["XMP:DigitalSourceType"] = "digitalCapture"
#                 elif not log_camera_make and not log_camera_model and log_creatortool and not log_source_type:
#                     metadata_update["XMP:DigitalSourceType"] = "print"
#                 else:
#                     metadata_update["XMP:DigitalSourceType"] = ""

                
#                 print(metadata_update)
#                 # et.set_tags(file, metadata_update)
#                 # input("PAUSE")
  

                  
def write_source_type(source_image_path):

    files_to_process = load_files_to_process(source_image_path)

    total_files = len(files_to_process)
    file_counter = 0

    # Open the CSV file in append mode
    with open(validation_log_dates, 'w', newline='') as date_validation_log_csv:
        validation_log = csv.writer(date_validation_log_csv)
        validation_log.writerow(["File", "DigitalSourceType", "IFD0:Make", "IFD0:Model"])

        # Load Exiftool
        with exiftool.ExifToolHelper() as et:

            # Process each file in the list of files to process
            if verbose_output == False:
                # output_option = tqdm(files_to_process, desc="Progress", unit="file")
                output_option = files_to_process
                
            elif verbose_output == True:
                output_option = files_to_process
            
            for file in output_option:
                file_counter += 1
                print(f"Proessing file {file_counter} of {total_files}: {file}")
                metadata_update = {}
                metadata_update["XMP:DigitalSourceType"] = ""
                source_type = ""
                digital_capture = False
                try:
                    metadata = et.get_metadata(file)
                    metadata = json.dumps(metadata)
                except:
                    print(f"{f_warning}No metadata found.{f_default}")
                    continue
                for camera in cameras:
                    if camera in metadata:
                        source_type = "digitalcapture"
                        digital_capture = True
                        print("TRUE")
                for print_source in print_sources:
                        if print_source in metadata and digital_capture == False:
                            source_type = "print"
                
                print(metadata_update)
                if source_type:
                    metadata_update["XMP:DigitalSourceType"] = source_type
                    et.set_tags(file, metadata_update)
                    print(f"{f_success}XMP:DigitalSourceType Updated{f_default}")
                else:
                    print(f"{f_information}No Update Made{f_default}")
  



# Set ascii output colors
f_warning = set_color("none", "red", "black")
f_information = set_color("none", "yellow", "black")
f_success = set_color("none", "green", "black")
f_default = set_color("default", "white", "black")

# process_date_metadata(source_image_path)
validate_dates(source_image_path)
# write_source_type(source_image_path)



















# Step 2: Validate Location















# # Example usage:
# date_to_check = datetime(2023, 3, 17)  # Change the date to the one you want to check
# holiday = check_holiday(date_to_check)
# if holiday:

#     print(f"The date {date_to_check.strftime('%Y-%m-%d')} is {holiday}.")
# else:
#     print(f"The date {date_to_check.strftime('%Y-%m-%d')} is not a known holiday.")
