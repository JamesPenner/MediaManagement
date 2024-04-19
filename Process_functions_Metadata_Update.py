import os
import sys
import csv
sys.path.append(r'C:\Media Management\Scripts')
import exiftool
from metadata_manager import Metadata_Manager
from file_handler import FileHandler, delete_empty_subfolders
from Support_functions_Detect_File_Types_and_Convert import convert_image_to_jpg, convert_video_to_h264_mp4

from config import  f_warning, f_info, f_input, f_success, f_default, rename_rules_for_archive, live_archive_file_extensions, asset_title_length, guid_length, created_date_fields, modified_date_fields, all_media_files, image_files, video_files, archive_paths, acdsee_parser, standard_metadata

base_guid = 0
guid_count = 0

# search_folder = r'D:\0_Media-Archive\test-delete\1890s'
# search_folder = r'D:\0_Media-Archive\test-delete\1890s\New folder'

search_folder = r'D:\0_Media-Archive\02_metadata-and-rename'


def _create_directory_if_not_exists(path):
    try:
        # Check if the path exists and is a directory
        if os.path.isdir(path):
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"Created directory: {path}")
            else:
                print(f"Directory already exists: {path}")
        else:  # If it's a file path, extract directory and create it if it doesn't exist
            directory_path = os.path.dirname(path)
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
                print(f"Created directory: {directory_path}")
            else:
                print(f"Directory already exists: {directory_path}")
    except Exception as e:
        print(f"Error: {e}. Failed to create the directory.")

def _get_asset_date(mm):
    # Find the asset Dates
    # ====================
    
    # Check the Create Date from the asset's metadata
    try:
        find_create_dates = mm.filter_date_fields("created")
        earliest_create_date = mm.get_earliest_date(find_create_dates)
        create_date = earliest_create_date.strftime("%Y%m%d")+"c"
    except:
        create_date = None

    # Check the Modified Date from the asset's metadata
    try:
        find_modified_dates = mm.filter_date_fields("modified")
        earliest_modified_date = mm.get_earliest_date(find_modified_dates)
        modified_date = earliest_modified_date.strftime("%Y%m%d")+"m"
    except:
        modified_date = None

    # Check the AssetDate from the asset's metadata
    try:
        metadata_asset_date = mm.filter_metadata(["XMP:AssetDate"])
        metadata_asset_date = metadata_asset_date["XMP:AssetDate"]
    except:
        metadata_asset_date = None
    
    # Check the AssetDate from the file name
    try:
        filename_date = mm.get_asset_date_from_filename()
        filename_date = filename_date["AssetDate"]
    except:
        filename_date = None
    
    if filename_date:
        asset_date = filename_date
    elif create_date:
        asset_date = create_date
    elif metadata_asset_date:
        asset_date = metadata_asset_date
    elif modified_date:
        asset_date = modified_date
    else:
        print(f"{f_warning}No AssetDate could be found for {file}{f_default}")

    return asset_date
    # except Exception as e:
    #     print(f"Error extracting creation date: {e}")
    #     return None

def _get_asset_title(mm, file):
    # Get the title from the asset's Headline metadata
    file_handler = FileHandler()
    try:
        xmp_headline = mm.filter_metadata(['XMP:Headline'])
        headline = xmp_headline["XMP:Headline"]
        # print(type(headline))
    except:
        headline = None
    try:
        iptc_headline = mm.filter_metadata(['IPTC:Headline'])
        headline = iptc_headline["IPTC:Headline"]
        # iptc_headline = iptc_headline['XMP:Headline']
    except:
        iptc_headline = None

    if headline is None:
        headline = os.path.basename(os.path.dirname(file))

    title = file_handler.regex_rename_strings(headline, rename_rules_for_archive)
    if title.endswith('-'):
        title = title[:-1]  # Remove the last character using slicing

    return title, headline

def _get_asset_guid(mm):
    # Get the GUID from the asset's GUID metadata
    global base_guid, guid_count
    try:
        guid = mm.filter_metadata(['XMP:ImageUniqueID','ExifIFD:ImageUniqueID','XMP:DigitalImageGUID'])

        if guid["XMP:ImageUniqueID"] and len(guid["XMP:ImageUniqueID"]) == guid_length:
            guid = guid["XMP:ImageUniqueID"]
        elif guid["ExifIFD:ImageUniqueID"] and len(guid["ExifIFD:ImageUniqueID"]) == guid_length:
            guid = guid["ExifIFD:ImageUniqueID"]            
        elif guid["XMP:DigitalImageGUID"] and len(guid["XMP:DigitalImageGUID"]) == guid_length:
            guid = guid["XMP:DigitalImageGUID"]
        else:
            base_guid += 1
            guid = f"{base_guid:010d}"
    except:
        base_guid += 1
        # Convert the integer to a 10-character string with leading zeros
        guid = f"{base_guid:010d}"

    return guid

def _get_highest_unique_identifier(folder_path, valid_extensions):
    highest_value = 0

    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            extension = file_name.split('.')[-1].lower()
            if extension in valid_extensions:
                parts = file_name.split('_')
                if len(parts) == 3:  # Check if the file name follows the specified format
                    identifier = int(parts[2].split('.')[0])
                    if identifier > highest_value:
                        highest_value = identifier
    
    return highest_value

def _count_files_in_directory(folder_path):
    if not os.path.exists(folder_path):
        # print("Directory does not exist.")
        return -1

    if not os.path.isdir(folder_path):
        # print("Provided path is not a directory.")
        return -1

    file_count = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
    return file_count

def _count_folders_in_directory(folder_path):
    if not os.path.exists(folder_path):
        # print("Directory does not exist.")
        return -1

    if not os.path.isdir(folder_path):
        # print("Provided path is not a directory.")
        return -1

    folder_count = len([f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))])
    return folder_count

def write_dict_list_to_csv(dict_list, file_path):
    if not dict_list:
        print("Dictionary list is empty.")
        return
    
    # Get the keys from the first dictionary to use as column headers
    field_names = list(dict_list[0].keys())

    with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        
        # Write header with column names
        writer.writeheader()
        
        # Write each dictionary as a row in the CSV file
        for data in dict_list:
            writer.writerow(data)

def _get_list_of_files(search_folder, recursive, filter_extensions):
    # print(search_folder)
    # print(recursive)
    # print(filter_extensions)

    # Instantiate the FileHandler
    file_handler = FileHandler()

    return file_handler.retrieve_file_list(search_folder, recursive, filter_extensions)


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





def DEVELOPING_update_people_descriptions_o():
    
    file_handler = FileHandler()

    with exiftool.ExifToolHelper() as et:
        total_files = len(file_list)
        file_count = 0
        for file in file_list:

            file_count += 1
            updated_dict = {}
          
            try:
                etmetadata = et.get_metadata([file])
            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)

            people_dict = mm.extract_person_names()
            # print(people_dict)

            if people_dict is not None:
                file_handler.write_metadata(et, people_dict, file, total_files, file_count, default_subprocess = True)





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

# This is what I'm working on
# embed_and_archive()






# FUNCTIONAL:
# report_acdsee_location_information()
# update_headline_and_titles()
# update_location_metadata_based_on_acdsee_categories()





live_prep_file_count = _count_files_in_directory(archive_paths["prep_live_path"])
static_prep_file_count = _count_files_in_directory(archive_paths["prep_static_path"])
prep_file_count = _count_files_in_directory(archive_paths["prep_path"])
prep_folder_count = _count_folders_in_directory(archive_paths["prep_path"])


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