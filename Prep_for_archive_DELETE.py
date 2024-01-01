import os
import sys
sys.path.append(r'C:\Media Management\Scripts')
import exiftool
from metadata_manager import Metadata_Manager
from file_handler import FileHandler, move_files, delete_empty_subfolders
from detect_file_types_and_convert import convert_image_to_jpg


from config import  f_warning, f_info, f_success, f_default, rename_rules_for_archive, live_archive_file_extensions, asset_title_length, guid_length, created_date_fields, modified_date_fields, all_media_files, image_files, archive_paths


base_guid = 0
guid_count = 0

# search_folder = r'D:\0_Media-Archive\test-delete\1890s'
# search_folder = r'D:\0_Media-Archive\test-delete\1890s\New folder'

search_folder = r'D:\0_Media-Archive\02_metadata-and-rename'


def _create_directory_if_not_exists(directory_path):
    try:
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

            # if asset_date and title and guid:
            new_file_name = f"{directory_path}\\{asset_date}_{title}_{guid}{file_extension.lower()}"
            
            # print(f"Old File Name: {file}\nNew File Name: {new_file_name}")

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

            # print(file_extension.lower())
            
            
            
            if file_extension.lower().replace(".", "") in image_files:
                converted_file_name = f"{archive_paths["prep_live_path"]}\\{asset_date}_{title}_{guid}.jpg"
                
                convert_image_to_jpg(file, converted_file_name)
                file_handler.rename_file(file, new_file_name, check_existing=False)

            # file_handler.write_metadata(et, metadata_update, file, total_files, file_count, default_subprocess = True)






# # Instantiate FileHandler object
# file_handler = FileHandler()

# # get list of static files in prepfiles
# static_file_list = get_list_of_files(search_folder, recursive=True, filter_extensions = all_media_files)

# # Move static files from existing folders to new static-folder in prep folder
# for file in static_file_list:
#     file_handler.move_file_to_new_location(file, archive_paths["prep_static_path"])

# # Delete empty folders in prep folder
# delete_empty_subfolders(archive_paths["prep_path"], preview_only=False, prompt_each=False, use_rmtree=False)

# print(image_files)

prep_static_files_for_archive()
