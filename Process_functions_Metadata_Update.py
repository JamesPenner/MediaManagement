import os
import re
import sys
import csv
sys.path.append(r'C:\Users\Windows\Dropbox\James\Python\01_Media Archive Scripts')
import exiftool
from datetime import datetime
from metadata_manager import Metadata_Manager
# from Support_functions_Validation import validate_filename
from file_handler import FileHandler, delete_empty_subfolders
from Support_functions_Detect_File_Types_and_Convert import convert_image_to_jpg, convert_video_to_h264_mp4

from config import  f_warning, f_info, f_input, f_success, f_default, rename_rules_for_archive, live_archive_file_extensions, asset_title_length, guid_length, created_date_fields, modified_date_fields, all_media_files, image_files, video_files, document_files, audio_files, filename_validation_rules, archive_paths, acdsee_parser, standard_metadata



base_guid = 0
guid_count = 0

# search_folder = r'D:\0_Media-Archive\test-delete\1890s'
# search_folder = r'D:\0_Media-Archive\test-delete\1890s\New folder'

search_folder = r'D:\0_Media-Archive\02_metadata-and-rename'

def update_location_metadata_based_on_acdsee_categories():
    
    # get list of static files in live-archive folder
    # file_list = _get_list_of_files(archive_paths["prep_live_path"], recursive=False, filter_extensions= ["jpg"])
    file_list = _get_list_of_files(archive_paths["live_archive_path"], recursive=True, filter_extensions= ["jpg"])
    # file_list = _get_list_of_files(archive_paths["TEST_PATH"], recursive=False, filter_extensions= ["jpg"])

    file_handler = FileHandler()

    with exiftool.ExifToolHelper() as et:
        total_files = len(file_list)
        file_count = 0
        ACDSee_Locations = []
        for file in file_list:

            file_count += 1
          
            try:
                etmetadata = et.get_metadata([file])
                # print(etmetadata)
            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)

            acdsee_location = mm.update_metadata_based_on_acdsee_location()
            # Replace "-" values with None using dictionary comprehension
            acdsee_location = {key: ("" if value == "-" else value) for key, value in acdsee_location.items()}

            # print(acdsee_location)
            acdsee_location["XMP:LocationCreatedSublocation"] = ""
            acdsee_location["XMP:LocationShownSublocation"] = ""
            print(f"Processing File {file_count} of {total_files}:  {file}")

            if acdsee_location is not None:
                ACDSee_Locations.append(acdsee_location)
                # print(acdsee_location)

                file_handler.write_metadata(et, acdsee_location, file, total_files, file_count, default_subprocess = True)

def update_headline_and_titles():
    
    # file_to_process = input(f"{input}Enter file path of file to change Headline/Title information: {f_default}")
    # Headline = input(f"{f_input}Enter the new Headline for the asset:")
    file_to_process = r"D:\0_Media-Archive\test-delete\199xxxxxc_don-on-balcony-at-alan-road_0000601080.jpg"

    file_handler = FileHandler()

    with exiftool.ExifToolHelper() as et:

        assetdate = ""
        headline = "This is a Test"
        title = ""
        guid = ""
        
        try:
            etmetadata = et.get_metadata([file_to_process])
            # print(etmetadata)
        except:
            print(f"{f_warning}Cannot read metadata for: {file_to_process}{f_default}")

        mm = Metadata_Manager(etmetadata)

        # Get the file extension
        file_extension = os.path.splitext(file_to_process)
        file_extension = file_extension[1]

        # Get the AssetDate
        assetdate = mm.filter_metadata(["XMP:AssetDate"])
        assetdate = assetdate["XMP:AssetDate"]

        # Get the GUID
        guid_fields = mm.filter_metadata(["EXIF:ImageUniqueID","XMP:ImageUniqueID","XMP:DigitalImageGUID"])
        checked_guid_fields = mm.check_dict_consistency(guid_fields)

        # Convert the headline to title
        headline_dict = mm.convert_headline_to_title(headline)
        title = headline_dict["XMP:Title"]


        if len(checked_guid_fields) == guid_length:
            guid = checked_guid_fields

        if assetdate and title and assetdate:
            new_file_name = f"{assetdate}_{title}_{guid}{file_extension}"
            print(new_file_name)
            file_handler.write_metadata(et, headline_dict, file_to_process, default_subprocess = True)
            file_handler.rename_file(file_to_process, new_file_name, check_existing=True)
        else:
            print(f"{f_warning}Cannot rename file: missing metadata.{f_default}")

# Return a list of files. The list can be filtered by extension, if needed.
def get_list_of_files(search_folder):
    # Instantiate the FileHandler
    file_handler = FileHandler()

    return file_handler.retrieve_file_list(search_folder, recursive=True, filter_extensions=None, include_metadata=False, validate_filename=False, filename_validation_report=None)




# def DEVELOPING_update_people_descriptions_o():
    
#     file_handler = FileHandler()

#     with exiftool.ExifToolHelper() as et:
#         total_files = len(file_list)
#         file_count = 0
#         for file in file_list:

#             file_count += 1
#             updated_dict = {}
          
#             try:
#                 etmetadata = et.get_metadata([file])
#             except:
#                 print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
#                 continue  # Skip to the next file on error

#             mm = Metadata_Manager(etmetadata)

#             people_dict = mm.extract_person_names()
#             # print(people_dict)

#             if people_dict is not None:
#                 file_handler.write_metadata(et, people_dict, file, total_files, file_count, default_subprocess = True)





def report_acdsee_location_information():
    
    report_location = r"D:\0_Media-Archive\02_metadata-and-rename\live-archive\test.csv"

    # get list of static files in live-archive folder
    file_list = _get_list_of_files(archive_paths["prep_live_path"], recursive=False, filter_extensions= ["jpg"])
    # file_list = _get_list_of_files(archive_paths["live_archive_path"], recursive=True, filter_extensions= None)

    file_handler = FileHandler()

    with exiftool.ExifToolHelper() as et:
        total_files = len(file_list)
        file_count = 0
        ACDSee_Locations = []
        for file in file_list:

            file_count += 1
          
            try:
                etmetadata = et.get_metadata([file])
                # print(etmetadata)
            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)

            # acdsee_location = mm.update_metadata_based_on_acdsee_location()
            acdsee_location = mm.acdsee_metadata_report()
            print(f"Processing File {file_count} of {total_files}:  {file}")

            if acdsee_location is not None:
                ACDSee_Locations.append(acdsee_location)
                # print(acdsee_location)

        write_dict_list_to_csv(ACDSee_Locations, report_location)


'''
- Source files for Static Archive should be in their own folders. 
- The folder name will be name used for the file's Headline and Title metadata
- prep_static_files_for_archive takes these files, renames them and creates a Live Archive version of them with standardized file formats
'''

         



def date_report(folder, output_file):
    """
    Generates a CSV report comparing multiple date types for files in fileList.

    Parameters:
        fileList (list): A list of file paths to be included in the report.
        output_file (str): The path to the output CSV file.
        filter_list (list): A list of file extensions to filter fileList.

    Returns:
        None

    Example:
        date_report(['path/to/files'], 'output.csv', ['.jpg', '.png'])
    """
    # Retrieve list of files based on filter_list and optional recursive search
    file_list = get_list_of_files(folder)

    # Define the format of the input date string
    # format_string = "%Y%m%d"
    format_string = "%Y-%m-%d %H:%M:%S"
    

    # Open the CSV file for writing
    with exiftool.ExifToolHelper() as et:
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['Path', 'File Name', 'File Extension', 'Modified Date', 'Created Date', 'Earliest Date', 'Status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            total_files = len(file_list)
            file_count = 0

            # Iterate over each file in the list
            for file in file_list:
                file_count += 1

                # Initialize variables
                date_part = ""
                file_date_string = ""
                
                # Attempt to read metadata using ExifTool
                try:
                    etmetadata = et.get_metadata([file])
                except Exception as e:
                    print(f"Warning: Cannot read metadata for file {file}: {e}")
                    continue  # Skip to the next file on error

                # Extract file metadata
                mm = Metadata_Manager(etmetadata)
                metadata = mm.metadata

                # Get earliest Created Date
                try:
                    earliest_cdate = mm.filter_date_fields("created")
                    earliest_cdate = mm.get_earliest_date(earliest_cdate)
                except:
                    earliest_cdate = None

                # Get earliest Modified Date
                try:
                    earliest_mdate = mm.filter_date_fields("modified")
                    earliest_mdate = mm.get_earliest_date(earliest_mdate)
                except:
                    earliest_mdate = None

                # # Extract filename date and type from the file name
                # try:
                #     file_date_dict = mm.get_asset_date_from_filename()
                #     file_date_string = file_date_dict["AssetDate"]
                #     date_type = file_date_string[8:]  # Extract date type from the last character
                    
                #     # Convert file name date to datetime object
                #     file_date_string = file_date_string[:8]
                #     try:
                #         file_date_object = datetime.strptime(file_date_string, format_string)
                #     except ValueError:
                #         print(f"Error: Invalid date format for file {file}")
                #         continue

                    # Extract file name, extension, and path
                file_name = os.path.basename(file)
                file_extension = os.path.splitext(file)[1]
                file_path = os.path.dirname(file)
                # except:
                #     file_date_object = None

                # Determine the earliest date between file and metadata dates
                # earliest_date = min(file_date_object, earliest_cdate, earliest_mdate)
                earliest_date = min(earliest_cdate, earliest_mdate)

                # Determine status
                # if file_date_object == earliest_date:
                #     status = "Filename Date is Earliest"
                if earliest_date == earliest_cdate:
                    status = "Created Date is Earliest"
                elif earliest_date == earliest_mdate:
                    status = "Modified Date is Earliest"
                else:
                    status = "Error Reading Dates"

                # Write row to CSV
                writer.writerow({
                    'Path': file_path,
                    'File Name': file_name,
                    'File Extension': file_extension,
                    # 'Filename Date': file_date_string + date_type,
                    # 'Converted Filename Date': file_date_object.strftime(format_string),
                    'Modified Date': earliest_mdate.strftime(format_string),
                    'Created Date': earliest_cdate.strftime(format_string),
                    'Earliest Date': earliest_date.strftime(format_string),
                    'Status': status
                })

                print(f"Processed File {file_count} of {total_files}: {file}")






# def validate_filename(filename):
#     """
#     Validate a filename against specified rules.

#     Parameters:
#         filename (str): The filename to validate.

#     Returns:
#         dict: A dictionary containing the validation results for each rule.
#               Each key represents a validation rule, and the corresponding value
#               is True if the filename passes the rule, False otherwise.
#     """
#     validation_results = {}

#     # Apply path_name_length rule to the entire filename
#     validation_results['path_name_length'] = bool(filename_validation_rules['path_name_length'].match(filename))

#     # Extract the first 9 characters for the date_prefix rule
#     date_prefix_part = filename[:9]
#     validation_results['date_prefix'] = bool(filename_validation_rules['date_prefix'].match(date_prefix_part))

#     # Extract the last 10 characters (excluding extension) for the guid rule
#     filename_without_extension = filename.rsplit('.', 1)[0]
#     guid_part = filename_without_extension[-10:]
#     validation_results['guid'] = bool(filename_validation_rules['guid'].match(guid_part))

#     # Extract the text between the first and second underscores for the title rule
#     title_part = filename.split('_')[1]
#     validation_results['title'] = bool(filename_validation_rules['title'].match(title_part))

#     # Check if all values in the dictionary are True
#     all_true = all(validation_results.values())

#     # If any value is False, return only the key-value pairs where the value is False
#     if not all_true:
#         false_results = {key: value for key, value in validation_results.items() if not value}
#         return false_results

#     return True









# def move_archive_files_based_on_metadata(source_directory, destination_directory, image_files, video_files, document_files, audio_files, filename_validation_rules):
def move_files_to_archive(source_directory, create_subfolders_from_sets=True):

    # Instantiate the FileHandler
    file_handler = FileHandler()

    files_list = file_handler.retrieve_file_list(source_directory, recursive=False, filter_extensions=None, include_metadata=False, validate_filename=True)

    # Define the format of the input date string
    format_string = "%Y%m%d"

    total_files = len(files_list)
    file_count = 0

    # Iterate over each file in the list
    for path in files_list:
        file_count += 1

        # Attempt to read metadata using ExifTool
        try:
            with exiftool.ExifToolHelper() as et:
                etmetadata = et.get_metadata([path])
        except Exception as e:
            print(f"Warning: Cannot read metadata for file {path}: {e}")
            return None  # Skip to the next file on error

        # Extract file metadata
        mm = Metadata_Manager(etmetadata)
        metadata = mm.metadata

        destination_path = mm.build_archive_folder_path_based_on_metadata(path, create_subfolders_from_sets=True)

        if destination_path:
            # file_handler.move_file_to_new_location(path, move_path, overwrite=False, rename_if_exists=False)
            # copy_file_to_new_location(path, destination_path, overwrite=True, rename_if_exists=False)

            file_name = os.path.basename(path)
            print(f"Source path: {path}")
            print(f"Destination path: {destination_path}\{file_name}")






    # print(filename_date)
    # print(earliest_cdate)
    # print(file_extension)
    # print(filename_dates)
    # print(filename_dates)

            
    #         # set_title = mm.filter_metadata(["SetTitle01"])
    #         # set_subtitle = mm.filter_metadata(["SetSubTitle01"])


# def move_archive_files_based_on_metadata(source_directory, destination_directory, image_files, video_files, document_files, audio_files, filename_validation_rules):
# def build_archive_folder_path_based_on_metadata(source_directory, create_subfolders_from_sets=True):

#     # Instantiate the FileHandler
#     file_handler = FileHandler()

#     files_list = file_handler.retrieve_file_list(source_directory, recursive=False, filter_extensions=None, include_metadata=False, validate_filename=True)

#     # Define the format of the input date string
#     format_string = "%Y%m%d"

#     total_files = len(files_list)
#     file_count = 0

#     # Iterate over each file in the list
#     for path in files_list:
#         file_count += 1
#         file_name = os.path.basename(path)
#         set = ""
#         subset = ""



#         if "live-archive" in path:
#             path_root = archive_paths["live_archive_path"]
#         elif "static-archive" in path:
#             path_root = archive_paths["static_archive_path"]
#         else:
#             path_root = archive_paths["live_archive_path"]
#             # print("Root path cannot be determined. Exiting. Source path must have reference to 'live-archive' or 'static-archive' ")
#             # sys.exit()

#        # Attempt to read metadata using ExifTool
#         try:
#             with exiftool.ExifToolHelper() as et:
#                 etmetadata = et.get_metadata([path])
#         except Exception as e:
#             print(f"Warning: Cannot read metadata for file {path}: {e}")
#             continue  # Skip to the next file on error

#         # Extract file metadata
#         mm = Metadata_Manager(etmetadata)
#         metadata = mm.metadata

#         filename_dates = mm.get_media_date_from_filename(file_name)
        
#         if filename_dates["Century"] != "-":
#             century = f'\\{filename_dates["Century"]}'
#         else:
#             century = ""

#         if filename_dates["Decade"] != "-":
#             decade = f'\\{filename_dates["Decade"]}'
#         else:
#             decade = ""

#         if filename_dates["Year"] != "-":
#             year = f'\\{filename_dates["Year"]}'
#         else:
#             year = ""

#         if create_subfolders_from_sets:
#             try:
#                 set = mm.filter_metadata(["XMP:SetTitle01"])
#                 print("Found Set data:")
#                 print(set)
#                 set = f"\\{set["XMP:SetTitle01"]}"
#             except:
#                 print("No Set data found")
#                 pass

#             try:
#                 subset = mm.filter_metadata(["XMP:SetSubTitle01"])
#                 # subset = mm.filter_metadata(["XMP:SetSubTitle01"])
#                 print(subset)
#                 subset = f"\\{subset["XMP:SetSubTitle01"]}"
#             except:
#                 print("No Subset data found")
#                 pass
#         try:
#             filename_dates = mm.get_media_date_from_filename(path)
#             filename_date = filename_dates["AssetDate"]
#         except:
#             print(f"Warning: Cannot read AssetDate for file {path}: {e}")
#             continue  # Skip to the next file on error
#         try:
#             # # Get earliest Created Date
#             earliest_cdate = mm.filter_date_fields("created")
#             earliest_cdate = mm.get_earliest_date(earliest_cdate)
#         except:
#             print(f"Warning: Cannot read Create Date for file {path}: {e}")
#             continue  # Skip to the next file on error
#         try:
#             file_extension = os.path.splitext(file_name)[1]
#             file_extension = file_extension.replace(".","")
#         except:
#             print(f"Warning: No file extention for file {path}: {e}")
#             continue  # Skip to the next file on error

#         if file_extension in image_files:
#             file_type = "Photos"
#         elif file_extension in video_files:
#             file_type = "Videos"
#         elif file_extension in audio_files:
#             file_type = "Audio"
#         elif file_extension in document_files:
#             file_type = "Documents"
#         else:
#             print(f"File extension: {file_extension} not recognized. Consider adding to config.py")
#             cont = input("Contiue (Y/N)?")
#             if cont.lower() == "n":
#                 sys.exit()

#         # Build Path
#         print(f"{path}\n  {path_root}\\{file_type}\\{century}{decade}{year}{set}{subset}")





# live_prep_file_count = _count_files_in_directory(archive_paths["prep_live_path"])
# static_prep_file_count = _count_files_in_directory(archive_paths["prep_static_path"])
# prep_file_count = _count_files_in_directory(archive_paths["prep_path"])
# prep_folder_count = _count_folders_in_directory(archive_paths["prep_path"])


# date_report(archive_paths["live_archive_path"], r"d:\metadata_date_output2.csv",all_media_files)
# date_report(r"D:\0_Media-Archive\test", r"d:\metadata_date_output223.csv",all_media_files)

# move_files_to_archive(r"D:\0_Media-Archive\test\live-archive", create_subfolders_from_sets=True)













# if prep_folder_count == 0 and prep_file_count == 0:
#     print(f"There are no files to process in {archive_paths["prep_path"]}. Exiting")
#     exit()


# if prep_folder_count > 0:
#     process_files = input(f"{f_default}\n\n{f_input}Step 1: Rename and sort files in {archive_paths["prep_path"]}? (Y\\N) {f_default}")

#     if process_files.lower() == "y":
#         # # Standardize file names, generate Live Archive
#         # prep_static_files_for_archive()
#         embed_and_archive_menu()
#     else:
#         embed_and_archive_menu()



date_report(r"D:\0_Media-Archive\03_archive\live-archive\Photos\2000-2099", r"d:\image_date_report.csv")
# date_report(r"D:\0_Media-Archive\01_sort", r"d:\video_date_report.csv")