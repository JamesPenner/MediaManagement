import re
import os
import sys
from datetime import datetime
from tqdm import tqdm

sys.path.append(r'C:\Users\Windows\Dropbox\James\Python\01_Media Archive Scripts')
from config import exiftool_path, exif_config_path, f_warning, f_success, f_default, f_info, filename_validation_rules, archive_paths
from file_handler import FileHandler

search_folder = r'C:\test'



# Return a list of files. The list can be filtered by extension, if needed.
def get_list_of_files(search_folder):
    # Instantiate the FileHandler
    file_handler = FileHandler()

    return file_handler.retrieve_file_list(search_folder, recursive=True, extensions=None, include_metadata=False)
   
# Takes a list of files, filters them based on specified criteria, and returns the filtered list of files
def filtered_file_list(files_to_process):

    # Set Search Options
    file_extensions = ['.bat', '.py']
    minsize = 1024
    maxsize=None
    regexpatterns = [re.compile(r'par'), re.compile(r'date', re.IGNORECASE)]
    casesensitive=False
    datebefore = datetime(2023, 12, 14)  # YYYY, MM, DD
    afterdate = datetime(2023, 1, 1)  # YYYY, MM, DD

    # Set file attributes to report
    file_attributes = ['full_path','folder_path','file_name','extension','size','created_time','modified_time','accessed_time','owner','permissions','mime_type','checksum','is_file','is_directory']

    # Instantiate the FileHandler
    file_handler = FileHandler()

    return file_handler.filter_files(files_to_process, extensions=file_extensions, min_size=minsize, max_size=maxsize, regex_patterns=regexpatterns, case_sensitive=casesensitive, date_after=afterdate, date_before=datebefore)
 
 # Example showing how to get csv file with file properties. The recorded files can be filtered based on the search options

# Get information about one or more files
def get_file_information(search_folder):

    search_results_csv = r"c:\test\2e\search_results.csv"

    # Set Search Options
    recursive=True
    filterextensions = ['.bat', '.py']
    min_size = 1024
    max_size=None
    regex_patterns = [re.compile(r'1'), re.compile(r'date', re.IGNORECASE)]
    case_sensitive=False
    date_before = datetime(2023, 12, 14)  # YYYY, MM, DD
    afterdate = datetime(2023, 1, 1)  # YYYY, MM, DD

    # Set file attributes to report
    file_attributes = ['full_path','folder_path','file_name','extension','size','created_time','modified_time','accessed_time','owner','permissions','mime_type','checksum','is_file','is_directory']

    os.system("cls")

    # Instantiate the FileHandler
    file_handler = FileHandler()

    # Search for Files 
    tqdm(file_handler.file_search_with_info(
        search_folder,
        recursive=True,
        extensions=None,
        min_size=None,
        max_size=None,
        regex_patterns=None,
        case_sensitive=True,
        date_after=None,
        date_before=None,
        info_list=file_attributes,  # Change the argument name here
        output='csv'
    ))

# Rename function with preview option if preview_only is True, no renaming will be done. If preview_only is False, renaming will be performed.
def rename_files(file_list):
    # Dictionary of compiled regex patterns for renaming
    rename_patterns = {
        re.compile(r'_'): r'-',   # Search pattern: Matches "file" followed by numbers and underscores
        re.compile(r'geo', re.IGNORECASE): r'',                    # Search pattern: Matches underscores followed by "example"
    }

    # Instantiate the FileHandler
    file_handler = FileHandler()

    # Dictionary of replacements for each pattern
    replacement_patterns = {
        list(rename_patterns)[0]: r'',   # Replace "file" with "renamed_file" and add an underscore after numbers
        list(rename_patterns)[1]: r'',                  # Remove the string "_example"
    }

    return file_handler.regex_rename_files(file_list, rename_patterns, preview_only=False)

# If preview_only is set to True no deletion will happen. It must be set to False to actually delete files.
def deleteFiles(file_list):
    # Instantiate the FileHandler
    file_handler = FileHandler()

    file_handler.delete_files(file_list, preview_only=False, prompt_each=False)

def delete_empty_directories(search_folder):
    # Instantiate the FileHandler
    file_handler = FileHandler()

    file_handler.delete_empty_subfolders(search_folder, preview_only=True, prompt_each=False)



def extract_guid(file_name):
    """
    Extract the 10-digit GUID from a file name.

    Parameters:
    -----------
    file_name : str
        The file name from which to extract the GUID.

    Returns:
    --------
    str
        The extracted GUID, or None if no GUID is found.
    """
    match = re.search(r'_(\d{10})\.', file_name)
    return match.group(1) if match else None

def filter_unique_files(list1, list2):
    """
    Compare two lists of files based on their GUIDs and return unique files from both lists.

    Parameters:
    -----------
    list1 : list
        First list of file paths or file names.

    list2 : list
        Second list of file paths or file names.

    Returns:
    --------
    tuple
        A tuple containing two lists: unique files from list1 and unique files from list2.
    """
    # Extract GUIDs from both lists
    guid_list1 = {file: extract_guid(file) for file in list1}
    guid_list2 = {file: extract_guid(file) for file in list2}

    # Identify GUIDs that are present in both lists
    common_guids = set(guid_list1.values()) & set(guid_list2.values())

    # Filter out files with common GUIDs
    unique_list1 = [file for file, guid in guid_list1.items() if guid not in common_guids]
    unique_list2 = [file for file, guid in guid_list2.items() if guid not in common_guids]

    return unique_list1, unique_list2





# SAMPLE CODE
# Get a list of files
fh = FileHandler()
# directory1 = r"D:\0_Media-Archive\02_metadata-and-rename\live-archive"
# directory2 = r"D:\0_Media-Archive\02_metadata-and-rename\static-archive"

directory1 = archive_paths["live_archive_path"]
directory2 = archive_paths["static_archive_path"]

# retrieve_file_list(folder_path, recursive=True, filter_extensions=None, include_metadata=False, validate_filename=False, filename_validation_report=filename_validation_report)




file_list_1 = fh.retrieve_file_list(directory1, recursive=True)
file_list_2 = fh.retrieve_file_list(directory2, recursive=True)

# print(file_list_1)


pattern = re.compile(r'^.*_\d{10}\.\w{1,5}$')

# Call the filter_files function with the regex pattern
filtered_files1 = fh.filter_files(
    file_list_1,  # Your list of files
    regex_patterns=[pattern]  # Pass the regex pattern as a list
)

# Call the filter_files function with the regex pattern
filtered_files2 = fh.filter_files(
    file_list_2,  # Your list of files
    regex_patterns=[pattern]  # Pass the regex pattern as a list
)


unique_list1, unique_list2 = filter_unique_files(file_list_1, file_list_2)


# print("Unique files in list1:", unique_list1)

print(f"Unique files in {directory1}")
for file in unique_list1:
    print(file)


print(f"Unique files in {directory2}")
for file in unique_list2:
    print(file)
    
    # filprint("Unique files in list2:", unique_list2)

# Filter the list of files, if needed
# final_file_list = filtered_file_list(files_to_process)

# rename_files(files_to_process)
# deleteFiles(files_to_process)

# delete_empty_directories(search_folder)