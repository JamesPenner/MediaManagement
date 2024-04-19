import os
import sys
import csv
sys.path.append(r'C:\Media Management\Scripts')
import exiftool
from metadata_manager import Metadata_Manager
from file_handler import FileHandler, delete_empty_subfolders
from Support_functions_Detect_File_Types_and_Convert import convert_image_to_jpg, convert_video_to_h264_mp4
from PandasExtension import DataFileHandler

from config import  f_warning, f_info, f_input, f_success, f_default, rename_rules_for_archive, live_archive_file_extensions, asset_title_length, guid_length, created_date_fields, modified_date_fields, all_media_files, image_files, video_files, archive_paths, acdsee_parser, standard_metadata, keyword_lookup, people_lookup, location_lookup


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


def get_list_of_files(search_folder, recursive, filter_extensions):
    # print(search_folder)
    # print(recursive)
    # print(filter_extensions)

    # Instantiate the FileHandler
    file_handler = FileHandler()

    return file_handler.retrieve_file_list(search_folder, recursive, filter_extensions)

def prep_static_files_for_archive():
    
    global base_guid, guid_count
    metadata_update = {}

    # get list of static files in prepfiles
    static_file_list = get_list_of_files(archive_paths["prep_path"], recursive=True, filter_extensions = all_media_files)
    # static_file_list = get_list_of_files(search_folder, recursive=True, filter_extensions = all_media_files)

    # Create the live-archive and static-archive prep folders
    _create_directory_if_not_exists(archive_paths["prep_live_path"])
    _create_directory_if_not_exists(archive_paths["prep_static_path"])

    # Get the base guid for file renaming. The base guid is the 
    base_guid = _get_highest_unique_identifier(r'D:\0_Media-Archive\03_archive\live-archive', live_archive_file_extensions) + 1

    file_handler = FileHandler()

    with exiftool.ExifToolHelper() as et:
        total_files = len(static_file_list)
        file_count = 0
        for file in static_file_list:

            file_count += 1
          
            try:
                etmetadata = et.get_metadata([file])
            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)
            # print(etmetadata[0])

            asset_date = _get_asset_date(mm)
            headline = _get_asset_title(mm, file)[1]
            title = _get_asset_title(mm, file)[0]
            guid = _get_asset_guid(mm)

            file_extension = os.path.splitext(file)[1]
            # file_path = os.path.dirname(file)
            directory_path, file_name = os.path.split(file)

            # Generate metadata Update
            metadata_update['XMP:Headline'] = headline
            metadata_update['IPTC:Headline'] = headline
            metadata_update['XMP:Title'] = title
            metadata_update['IPTC:Title'] = title
            metadata_update['XMP:AssetDate'] = asset_date
            metadata_update['ExifIFD:ImageUniqueID'] = guid
            metadata_update['XMP:ImageUniqueID'] = guid
            metadata_update['XMP:DigitalImageGUID'] = guid
            metadata_update['XMP:OriginalDirectory'] = directory_path
            metadata_update['XMP:OriginalFileName'] = file_name
            metadata_update['XMP:OriginalPath'] = file
            
            # if asset_date and title and guid:
            if asset_date and title and guid:
                
                # ############################
                # Process Image Files ########
                # ############################

                if file_extension.lower().replace(".", "") in image_files:

                    # Update metadata dictionary with SourceMediaFormat Type
                    metadata_update["XMP:SourceMediaFormat"] = "Image"

                    # Create new names for static and live archive files
                    converted_file_name = f"{archive_paths["prep_live_path"]}\\{asset_date}_{title}_{guid}.jpg"
                    new_file_name = f"{archive_paths["prep_static_path"]}\\{asset_date}_{title}_{guid}{file_extension.lower()}"
                    static_folder_name = f"{archive_paths["prep_static_path"]}\\"

                    # Create a converted live archive file with the new file name
                    convert_image_to_jpg(file, converted_file_name)

                    # Rename
                    file_handler.move_files(file, new_file_name)

                    file_handler.write_metadata(et, metadata_update, new_file_name, total_files, file_count, default_subprocess = True)
                    file_handler.write_metadata(et, metadata_update, converted_file_name, total_files, file_count, default_subprocess = True)
                    print('\n\n')


                # ############################
                # Process Video Files ########
                # ############################

                if file_extension.lower().replace(".", "") in video_files:

                    # Update metadata dictionary with SourceMediaFormat Type
                    metadata_update["XMP:SourceMediaFormat"] = "Video"

                    # Create new names for static and live archive files
                    converted_file_name = f"{archive_paths["prep_live_path"]}\\{asset_date}_{title}_{guid}.mp4"
                    new_file_name = f"{archive_paths["prep_static_path"]}\\{asset_date}_{title}_{guid}{file_extension.lower()}"
                    static_folder_name = f"{archive_paths["prep_static_path"]}\\"

                    # Create a converted live archive file with the new file name
                    convert_video_to_h264_mp4(file, converted_file_name)

                    # Rename
                    file_handler.move_files(file, new_file_name)

                    file_handler.write_metadata(et, metadata_update, new_file_name, total_files, file_count, default_subprocess = True)
                    file_handler.write_metadata(et, metadata_update, converted_file_name, total_files, file_count, default_subprocess = True)
                    print('\n\n')

        # Delete empty folders in prep folder
        delete_empty_subfolders(archive_paths["prep_path"], preview_only=False, prompt_each=False, use_rmtree=False)



def convert_media_no_name_change():
    
    # get list of static files in prepfiles
    # source_files = input("Enter Source directory: ")
    source_files = r"D:\0_Media-Archive\02_metadata-and-rename\static-archive"
    # destination_files = input("Enter Destination directory: ")
    destination_files = r"D:\0_Media-Archive\02_metadata-and-rename\live-archive"
    files_to_process = get_list_of_files(source_files, recursive=False, filter_extensions = all_media_files)

    # Create the live-archive and static-archive prep folders
    _create_directory_if_not_exists(destination_files)

    file_handler = FileHandler()

    with exiftool.ExifToolHelper() as et:
        total_files = len(files_to_process)
        file_count = 0
        for file in files_to_process:

            file_count += 1
          
            try:
                etmetadata = et.get_metadata([file])
            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)

            metadata_update = {}

            file_extension = os.path.splitext(file)[1]
            file_name = os.path.basename(file)
            file_name_no_extension = file_name.replace(file_extension,"")

            # print(file_name_no_extension)
            # print(file_name)

            ############################
            # Process Image Files ########
            ############################

            if file_extension.lower().replace(".", "") in image_files:

                # Update metadata dictionary with SourceMediaFormat Type
                metadata_update["XMP:SourceMediaFormat"] = "Image"

                # Create new names for static and live archive files
                converted_file_name = f"{destination_files}\\{file_name_no_extension}.jpg"

                # Create a converted live archive file with the new file name
                convert_image_to_jpg(file, converted_file_name)

                print('\n\n')


            # # ############################
            # # Process Video Files ########
            # # ############################

            if file_extension.lower().replace(".", "") in video_files:

                # Update metadata dictionary with SourceMediaFormat Type
                metadata_update["XMP:SourceMediaFormat"] = "Video"

                # Create new names for static and live archive files
                converted_file_name = f"{destination_files}\\{file_name_no_extension}.mp4"

                # Create a converted live archive file with the new file name
                convert_video_to_h264_mp4(file, converted_file_name)

                print('\n\n')


def embed_and_archive():
    
    # get list of static files in live-archive folder
    file_list = get_list_of_files(archive_paths["prep_live_path"], recursive=False, filter_extensions= ["jpg"])
    # file_list = get_list_of_files(archive_paths["TEST_PATH"], recursive=False, filter_extensions= ["jpg"])
    # file_list = get_list_of_files(archive_paths["live_archive_path"], recursive=True, filter_extensions= None)

    file_handler = FileHandler()
    data_file_handler = DataFileHandler()

    people_df = data_file_handler.load_csv_files_to_dataframe([people_lookup])
    # location_df = data_file_handler.load_csv_files_to_dataframe([location_lookup])
    # keyword_df = data_file_handler.load_csv_files_to_dataframe([keyword_lookup])

    with exiftool.ExifToolHelper() as et:
        total_files = len(file_list)
        file_count = 0
        ACDSee_Locations = []
        for file in file_list:

            location_update = {}
            metadata_update = {}

            location_patterns = {}
            file_count += 1
          
            try:
                etmetadata = et.get_metadata([file])
                # print(etmetadata)
            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)


            # #####################################################
            # # Update Location Information #######################
            # #####################################################
            
            try:
                acdsee_location = mm.update_metadata_based_on_acdsee_location()
                # acdsee_location = mm.acdsee_metadata_report()
                print(f"Processing File {file_count} of {total_files}:  {file}")

                if acdsee_location is not None:
                    ACDSee_Locations.append(acdsee_location)
                    metadata_update.update(ACDSee_Locations[0])

            except:
                pass

            # #####################################################
            # # Update Standard Information #######################
            # #####################################################

            if standard_metadata:
                metadata_update.update(standard_metadata)

            # # #####################################################
            # # # Update Date Information ###########################
            # # #####################################################

            date_info = {}
            date_update = {}

            people_dates = mm.get_people_dates()
            if people_dates is not None:
                metadata_update.update(people_dates)

            holiday_dates = mm.get_holiday_dates()
            if holiday_dates is not None:
                date_update["XMP:HolidayName"] = holiday_dates

            date_info = mm.get_asset_date_from_filename()
            date_update["XMP:Century"] = date_info["Century"]
            date_update["XMP:Decade"] = date_info["Decade"]
            date_update["XMP:Year"] = date_info["Year"]
            date_update["XMP:Season"] = date_info["Season"]
            date_update["XMP:Month"] = date_info["Month"]
            date_update["XMP:DayNumber"] = date_info["DayNumber"]
            date_update["XMP:DayName"] = date_info["DayName"]
            date_update["XMP:AssetDate"] = date_info["AssetDate"]
            date_update["XMP:AccurateDate"] = date_info["AccurateDate"]

            metadata_update.update(date_update)


            #####################################################
            # Update People Information #########################
            #####################################################

            try:
                people_update = mm.extract_person_names_pass_df(people_df)
                metadata_update.update(people_update)
            except:
                pass
            # print(people_metadata)
            # input("WAIT HERE")

            #####################################################
            # Update Keyword Information ########################
            #####################################################

            FindKeywords = mm.find_keywords()
            # print(FindKeywords)

            if FindKeywords:
                comma_separated_string = ', '.join(FindKeywords)
                metadata_update["IPTC:Keywords"] = comma_separated_string
                metadata_update["XMP:Keywords"] = comma_separated_string
                metadata_update.update(FindKeywords)
            metadata_update = mm.modify_dictionary(metadata_update, "-", "", target='values', exact_match=True, case_insensitive=False)
            # print(metadata_update)
        

            #####################################################
            # Write Metadata to File ############################
            #####################################################
            file_handler.write_metadata(et, metadata_update, file, total_files, file_count, default_subprocess=True)


            

def update_location_metadata_based_on_acdsee_categories():
    
    # get list of static files in live-archive folder
    # file_list = get_list_of_files(archive_paths["prep_live_path"], recursive=False, filter_extensions= ["jpg"])
    file_list = get_list_of_files(archive_paths["live_archive_path"], recursive=True, filter_extensions= ["jpg"])

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
            print(f"Processing File {file_count} of {total_files}:  {file}")

            if acdsee_location is not None:
                ACDSee_Locations.append(acdsee_location)
                # print(acdsee_location)

                file_handler.write_metadata(et, acdsee_location, file, total_files, file_count, default_subprocess = True)


def report_acdsee_location_information():
    
    report_location = r"D:\0_Media-Archive\02_metadata-and-rename\live-archive\test.csv"

    # get list of static files in live-archive folder
    file_list = get_list_of_files(archive_paths["prep_live_path"], recursive=False, filter_extensions= ["jpg"])
    # file_list = get_list_of_files(archive_paths["live_archive_path"], recursive=True, filter_extensions= None)

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





def embed_and_archive_menu():

    if (live_prep_file_count > 0 and static_prep_file_count > 0) and (live_prep_file_count == static_prep_file_count) and prep_file_count == 0 and prep_folder_count == 2:
        print(f"Step 2: Embed Metadata and Archive.\nThere are files in {archive_paths["prep_path"]}.")

        print("Before proceeding, ensure the following:\n  - 1. Any people names are recorded in XMP:RegionName ([XMP-mwg-rs]    RegionName)\n  - 2. Any Location names are recorded in XMP:Categories RegionName ([XMP-acdsee]    Categories)")

        process_files = input(f"\n\n{f_input}Process files? (Y\\N) {f_default}")

        if process_files.lower() == "y":
            # Standardize file names, generate Live Archive
            print("blurp")

        else:
            exit()

# convert_media_no_name_change()

'''
- Source files for Static Archive should be in their own folders. 
- The folder name will be name used for the file's Headline and Title metadata
- prep_static_files_for_archive takes these files, renames them and creates a Live Archive version of them with standardized file formats
'''

# This is what I'm working on
embed_and_archive()

# update_location_metadata_based_on_acdsee_categories()







# WORKING:
# report_acdsee_location_information()






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