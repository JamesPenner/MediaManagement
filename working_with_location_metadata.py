import cProfile
import timeit
import subprocess
import sys
sys.path.append(r'C:\Media Management\Scripts')
import exiftool
from metadata_manager import Metadata_Manager
from file_handler import FileHandler
from config import  f_warning, f_info, f_success, f_default, Location_fields, exiftool_path, exif_config_path

# search_folder = r'D:\0_Media-Archive\test-delete\1890s'
search_folder = r'D:\0_Media-Archive\test-delete'
# search_folder = r'D:\0_Media-Archive\03_archive\live-archive\Photos'

# search_folder = r'D:\0_Media-Archive\03_archive\live-archive\Photos\2000-2099\2020s\2022'



def get_list_of_files(search_folder, recursive, extensions):
    # Instantiate the FileHandler
    file_handler = FileHandler()

    return file_handler.retrieve_file_list(search_folder, recursive, extensions)


def create_metadata_command(exiftool_path, exif_config_path, data_dict, file):
    commandp1 = [exiftool_path, "-config", exif_config_path]
    
    for field, value in data_dict.items():
        commandp1.append(f'-{field}={value}')

    commandp2 = [    
    "-m",
    "-use",
    "mwg",
    "-n",
    "-overwrite_original",
    "-sep",
    ", ",
    file
]
    
    command = commandp1 + commandp2

    return command


def update_location_descriptions(display_only = True):
    location_index_dict = {}


    with exiftool.ExifToolHelper() as et:
        total_files = len(file_list)
        file_count = 0
        for file in file_list:
            location_lookup_value = ""

            file_count += 1
            updated_dict = {}
            
            try:
                etmetadata = et.get_metadata([file])
                # print(etmetadata)

            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)

            # Find location information in files.
            file_location_descriptions = mm.get_location_descriptions()

            for field in Location_fields:
                try:

                        if file_location_descriptions.get(field) is not None:
                            location_lookup_value = file_location_descriptions[field]
                except:

                    f"{f_warning}No Location found: {file}{f_default}"
                    location_index_dict = {}
                    location_lookup_value = ""

            if location_lookup_value != "":
                location_index_dict = mm.expand_location_descriptions(location_lookup_value, "location")
            
            print(f"location_index_dict:\n{location_index_dict}")



            # input("wasdgf")
            
            

            # Check in the Index of Locations if there are any values in any of the Location fields
            
            # # location_lookup_value = mm.get_location_from_metadata("location")
            # location_lookup_value = file_location_descriptions["XMP:Location"]
            # print(location_lookup_value)
            # input("wasdgf")
            
            # # print(f"THIS IS location_lookup_value:  {location_lookup_value}")

            # # If a location is found in the Index of Locations, use any related index information to build up information description dictionary
            
            # location_index_dict = mm.expand_location_descriptions(location_lookup_value, "location")
            # print(location_index_dict)


            # if len(location_index_dict) == 0:
            #     print(f"{f_info}File {file_count} of {total_files} | {file}: No Location Information Found, Skipping Location Update.{f_default}")
            #     continue

            # # elif location_index_dict == file_location_descriptions:
            # #     print(f"File {file_count} of {total_files} | {file}: Metadata current. No update required. Skipping.")

            #     # print()
            #     # print(file_location_descriptions)
            #     # print(f"    file_location_descriptions: {len(file_location_descriptions)}")
            #     # print(f"    file_location_descriptions DETAILS: {file_location_descriptions}")
            #     # print(f"    location_index_dict:        {len(location_index_dict)}")
            #     # print(f"    location_index_dict DETAILS:        {(location_index_dict)}")
            #     # print()
            #     # print()

            #     # continue

            # else:
                # if display_only == True:
                #     if location_index_dict != file_location_descriptions:
                #         print(f"{f_warning}File {file_count} of {total_files} | {file}: Update Required{f_default}")
                #         continue
                #     else:
                #         print(f"File {file_count} of {total_files} | {file}: No update required. Skipping.")

                # elif display_only == False:
                #     if location_index_dict != file_location_descriptions:
            try:
                et.set_tags(file, location_index_dict)
                print(f"File {file_count} of {total_files} | {f_success}{file} Updated{f_default}")
                continue
            # except:
            #     print(f"File {file_count} of {total_files} | {f_warning}{file}: Cannot Update File Metadata{f_default}")


            except:
                # Run the command using subprocess
                try:
                    update = create_metadata_command(exiftool_path, exif_config_path, location_index_dict, file)
                    subprocess.run(update, check=True)
                    print(f"{f_success}File {file_count} of {total_files} | {f_success}{file} Updated by subprocess{f_default}")
                    # print(update)
                except subprocess.CalledProcessError as e:
                    print(f"Error executing ExifTool command: {e}")
                    print(f"{f_warning}File {file_count} of {total_files} | {f_success}{file} Can't be Updated{f_default}")






# get list of image files
file_list = get_list_of_files(search_folder, recursive=True, extensions=["jpg","jpeg"])

# Update Locations

update_location_descriptions(display_only = False)