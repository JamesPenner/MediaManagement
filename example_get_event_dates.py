import cProfile
import timeit
import subprocess
import sys
sys.path.append(r'C:\Media Management\Scripts')
import exiftool
from metadata_manager import Metadata_Manager
from file_handler import FileHandler
from config import  f_warning, f_info, f_success, f_default, Location_fields, exiftool_path, exif_config_path, people_lookup


# search_folder = r'D:\0_Media-Archive\test-delete\1890s'
search_folder = r'D:\0_Media-Archive\test-delete'

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


def find_people_info2():
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
            # print(etmetadata)


            # Find Events
            print(f"{file}")
            people_dates = mm.get_people_dates()
            holiday_dates = mm.get_holiday_dates()
            print(f"{people_dates} + {holiday_dates}")
            


# get list of image files
file_list = get_list_of_files(search_folder, recursive=False, extensions=["jpg","jpeg"])

find_people_info2()
