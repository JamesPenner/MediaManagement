import subprocess

import xml.etree.ElementTree as ET

import sys
import re
sys.path.append(r'C:\Media Management\Scripts')
import exiftool
import pandas as pd
from metadata_manager import Metadata_Manager
from file_handler import FileHandler
from config import  f_warning, f_info, f_success, f_default, Location_fields, exiftool_path, exif_config_path, acdsee_parser

# search_folder = r'D:\0_Media-Archive\test-delete\1890s'
# search_folder = r'D:\0_Media-Archive\test-delete'
search_folder = r'D:\0_Media-Archive\03_archive\live-archive\Photos'

# search_folder = r'D:\0_Media-Archive\03_archive\live-archive\Photos\2000-2099\2020s\2022'
xml_data = '''
<Categories><Category Assigned="1">People<Category Assigned="0">All<Category Assigned="1">Alanya Claire Smith (Wiles)</Category></Category><Category Assigned="0">Last Name<Category Assigned="1">Smith<Category Assigned="1">Alanya Claire Smith (Wiles)</Category></Category></Category></Category><Category Assigned="0">Albums<Category Assigned="0">Media Description<Category Assigned="0">Orientation<Category Assigned="1">Landscape</Category></Category><Category Assigned="0">Aspect Ratio<Category Assigned="1">7:5</Category></Category></Category><Category Assigned="0">Collections<Category Assigned="1">Samantha's Media<Category Assigned="1">Pam's Baby Book</Category></Category><Category Assigned="1">Samantha's Family Photos<Category Assigned="1">Camping</Category></Category><Category Assigned="0">Shared Media<Category Assigned="1">New Album</Category></Category></Category><Category Assigned="0">Dates<Category Assigned="1">1900-1999</Category></Category></Category><Category Assigned="0">Places<Category Assigned="0">Country<Category Assigned="1">England<Category Assigned="1">Southeast England<Category Assigned="0">Community<Category Assigned="1">London<Category Assigned="1">Hampton Court Park</Category></Category></Category></Category></Category></Category></Category></Categories>
'''


# Ideas for work flow

# Find earliest date:
# filtered_created = mm.filter_keys_by_terms('created')
# CreateDate = mm.get_earliest_date(filtered_created)

# Check known Create Date
# filter_metadata("created_date_fields")
# CreateDate = mm.get_earliest_date(filtered_created)

# Compare two dates to validate?

# If no Create date found, use Modified Date

# 
def parse_categories(xml_string):
    stack = []
    root = None
    current_node = None

    for event, elem in ET.iterparse(xml_string, events=("start", "end")):
        if event == "start":
            if not stack:
                root = elem

            stack.append(elem)
            current_node = elem
        elif event == "end":
            if stack[-1] is current_node:
                stack.pop()

            if current_node.text and current_node.tag != root.tag:
                parent = stack[-1] if stack else None
                if parent is not None:
                    if parent.tag not in current_node.text:
                        parent.text = (parent.text or '') + current_node.text

            if current_node.tag == root.tag:
                break

    return root



def compile_regex_dict(regex_dict):
    """Compiles regular expressions in a dictionary.

    Args:
        regex_dict: A dictionary where keys are metadata field names and values are regular expressions.

    Returns:
        A new dictionary with compiled regular expressions as values.
    """

    compiled_dict = {}
    for key, regex_str in regex_dict.items():
        try:
            compiled_dict[key] = re.compile(regex_str)
        except re.error as e:
            print(f"Error compiling regex for key '{key}': {e}")
            # Handle compilation errors appropriately (e.g., skip, raise, log)

    return compiled_dict




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


def find_dates(display_only = True):

    with exiftool.ExifToolHelper() as et:
        total_files = len(file_list)
        file_count = 0
        for file in file_list:
            create_date = ""

            file_count += 1
            
            try:
                etmetadata = et.get_metadata([file])
                # print(etmetadata)

            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)


            filtered_created = mm.filter_keys_by_terms('created')
            CreateDate = mm.get_earliest_date(filtered_created)
            print(f"{file}\nCreate Date: {CreateDate}")


            # print(filtered_created)



def get_acdsee_metadata(file_list):
    compiled_acdsee_regex_parser = compile_acdsee_regex_parser(acdsee_parser)

    with exiftool.ExifToolHelper() as et:
        total_files = len(file_list)
        file_count = 0
        for file in file_list:
            create_date = ""
            file_count += 1
            
            try:
                etmetadata = et.get_metadata([file])
            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)
            acdsee_metadata = mm.parse_compiled_xmp_categories(compiled_acdsee_regex_parser)
            # print(f"{file}\nCreate Date: {acdsee_metadata}")

    
            try:
                et.set_tags(file, acdsee_metadata)
                print(f"File {file_count} of {total_files} | {f_success}{file} Updated{f_default}")
                continue
            # except:
            #     print(f"File {file_count} of {total_files} | {f_warning}{file}: Cannot Update File Metadata{f_default}")


            except:
                # Run the command using subprocess
                try:
                    update = create_metadata_command(exiftool_path, exif_config_path, acdsee_metadata, file)
                    subprocess.run(update, check=True)
                    print(f"{f_success}File {file_count} of {total_files} | {f_success}{file} Updated by subprocess{f_default}")
                    # print(update)
                except subprocess.CalledProcessError as e:
                    print(f"Error executing ExifTool command: {e}")
                    print(f"{f_warning}File {file_count} of {total_files} | {f_success}{file} Can't be Updated{f_default}")


# Parse the XML
parsed_categories = parse_categories(xml_data)

# Display the parsed content
if parsed_categories is not None:
    print(ET.tostring(parsed_categories).decode())