import re
import os
import sys
from datetime import datetime
from tqdm import tqdm

sys.path.append(r'C:\Media Management\Scripts')
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


# SAMPLE CODE
# Get a list of files
# files_to_process = get_list_of_files(search_folder)

# Filter the list of files, if needed
# final_file_list = filtered_file_list(files_to_process)

# rename_files(files_to_process)
# deleteFiles(files_to_process)

delete_empty_directories(search_folder)
