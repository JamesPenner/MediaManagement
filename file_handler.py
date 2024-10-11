import re
import os
import sys
import csv
import stat
import shutil
from datetime import datetime
import subprocess
import mimetypes
import hashlib

sys.path.append(r'C:\Media Management\Scripts')
from config import exiftool_path, exif_config_path, f_warning, f_success, f_default, f_info, filename_validation_rules, filename_validation_report



regex_file_filters = []

class FileHandler:
    def __init__(self, file_list=None):
        self.file_list = file_list if file_list is not None else []

    def compare_files(self, other_handler, ignore_extension=True, csv_output=r"d:\file_comparison.csv"):
        # Helper function to extract filename and file attributes
        def get_file_attributes(file, ignore_extension):
            file_path = os.path.abspath(file)
            file_name = os.path.basename(file)
            if ignore_extension:
                base_name = os.path.splitext(file_name)[0]
            else:
                base_name = file_name
            file_extension = os.path.splitext(file_name)[1]
            file_size = os.path.getsize(file)
            return [file_path, file_name, base_name, file_extension, file_size]

        # Gather file attributes for both file lists
        list1_attrs = [get_file_attributes(f, ignore_extension) for f in self.file_list]
        list2_attrs = [get_file_attributes(f, ignore_extension) for f in other_handler.file_list]

        # Create sets of base filenames (with or without extensions) for comparison
        set1 = {attrs[2] for attrs in list1_attrs}
        set2 = {attrs[2] for attrs in list2_attrs}

        # Find differences
        unique_to_list1 = [attrs for attrs in list1_attrs if attrs[2] not in set2]
        unique_to_list2 = [attrs for attrs in list2_attrs if attrs[2] not in set1]

        # Save differences to a CSV file
        with open(csv_output, mode="w", newline="") as file:
            writer = csv.writer(file)
            # Write headers
            writer.writerow([
                "File Path (List1)", "Full File Name (List1)", "Base Name (List1)", "Extension (List1)", "File Size (List1)",
                "File Path (List2)", "Full File Name (List2)", "Base Name (List2)", "Extension (List2)", "File Size (List2)"
            ])
            
            # Write the differences to CSV row by row
            max_len = max(len(unique_to_list1), len(unique_to_list2))
            for i in range(max_len):
                row = []
                if i < len(unique_to_list1):
                    row.extend(unique_to_list1[i])  # Add details from list1
                else:
                    row.extend([""] * 5)  # Fill with blanks if no more items in list1
                
                if i < len(unique_to_list2):
                    row.extend(unique_to_list2[i])  # Add details from list2
                else:
                    row.extend([""] * 5)  # Fill with blanks if no more items in list2
                
                writer.writerow(row)

        return unique_to_list1, unique_to_list2, csv_output


# Local methods
# ################################################################
    def _get_file_owner(self, file_path):
        """
        Get the owner of a file.

        Args:
        - file_path (str): Path of the file.

        Returns:
        - str: Owner of the file.
        """
        if os.name == 'posix':
            return os.popen(f"ls -l {file_path} | awk '{{print $3}}'").read().strip()
        elif os.name == 'nt':
            return os.popen(f"powershell (Get-Acl '{file_path}').Owner").read().strip()
        else:
            return "Unknown"

    def _display_file_info(self, file_info):
        """
        Display file information in the terminal.

        Args:
        - file_info (dict): Dictionary containing file information.
        """
        for key, value in file_info.items():
            print(f"{key.capitalize()}: {value}")

    def _get_file_permissions(self, file_path):
        """
        Get the permissions of a file.

        Args:
        - file_path (str): Path of the file.

        Returns:
        - str: Permissions of the file.
        """
        return oct(os.stat(file_path).st_mode & 0o777)

    def _get_file_checksum(self, file_path):
        """
        Calculate the checksum (SHA-256) of a file.

        Args:
        - file_path (str): Path of the file.

        Returns:
        - str: Checksum of the file.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as file:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: file.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    # def _validate_filename(self, filename):
    #     """
    #     Validate a filename against specified rules.

    #     Parameters:
    #         filename (str): The filename to validate.

    #     Returns:
    #         dict: A dictionary containing the validation results for each rule.
    #             Each key represents a validation rule, and the corresponding value
    #             is True if the filename passes the rule, False otherwise.
    #     """
    #     validation_results = {}

    #     # Rule 1: Validate path_name_length for the entire filename
    #     validation_results['path_name_length'] = self._apply_validation_rule('path_name_length', filename)

    #     # Rule 2: Validate the first 9 characters for the date_prefix rule
    #     if len(filename) >= 9:
    #         validation_results['date_prefix'] = self._apply_validation_rule('date_prefix', filename[:9])
    #     else:
    #         validation_results['date_prefix'] = False  # Fail if filename is too short

    #     # Rule 3: Validate the last 10 characters (excluding extension) for the guid rule
    #     filename_without_extension = filename.rsplit('.', 1)[0]
    #     if len(filename_without_extension) >= 10:
    #         guid_part = filename_without_extension[-10:]
    #         validation_results['guid'] = self._apply_validation_rule('guid', guid_part)
    #     else:
    #         validation_results['guid'] = False  # Fail if filename is too short

    #     # Rule 4: Validate the title part (text between underscores)
    #     title_part = self._extract_title_part(filename)
    #     validation_results['title'] = self._apply_validation_rule('title', title_part) if title_part else False

    #     # Return the full validation result dictionary
    #     # Optionally, if any validation failed, you could filter only the failed ones
    #     failed_validations = {key: result for key, result in validation_results.items() if not result}
        
    #     if failed_validations:
    #         return failed_validations
    #     return validation_results  # Return full results if all passed

    def _validate_filename(self, filename):
        validation_results = {}

        # Apply path_name_length rule
        validation_results['path_name_length'] = bool(filename_validation_rules['path_name_length'].match(filename))
        print(f"Path name length validation for {filename}: {validation_results['path_name_length']}")

        # Date prefix rule
        date_prefix_part = filename[:9]
        validation_results['date_prefix'] = bool(filename_validation_rules['date_prefix'].match(date_prefix_part))
        print(f"Date prefix validation for {filename}: {validation_results['date_prefix']}")

        # GUID rule
        filename_without_extension = filename.rsplit('.', 1)[0]
        guid_part = filename_without_extension[-10:]
        validation_results['guid'] = bool(filename_validation_rules['guid'].match(guid_part))
        print(f"GUID validation for {filename}: {validation_results['guid']}")

        # Title rule
        title_parts = filename.split('_')
        title_part = title_parts[1] if len(title_parts) >= 2 else ""
        validation_results['title'] = bool(filename_validation_rules['title'].match(title_part))
        print(f"Title validation for {filename}: {validation_results['title']}")

        # Return failed validations or True
        all_true = all(validation_results.values())
        if not all_true:
            false_results = {key: value for key, value in validation_results.items() if not value}
            return false_results

        return True



    def _extract_title_part(self, filename):
        """
        Extract the title part from the filename (text between underscores).

        Parameters:
            filename (str): The filename to extract the title part from.

        Returns:
            str: The extracted title part or an empty string if not found.
        """
        title_parts = filename.split('_')
        return title_parts[1] if len(title_parts) >= 2 else ""

    def _write_failed_validations_to_csv(self, filename, failed_validations_list):
        """
        Write failed validation results to a CSV file.

        Parameters:
            filename (str): The filename to write the CSV file to.
            failed_validations_list (list): A list of dictionaries containing failed validation results.
                                             Each dictionary contains 'file' and 'failed_validations' keys.
        """
        # Define CSV file headers
        fieldnames = ['File_Path', 'Date_Prefix', 'Title', 'GUID']

        # Write failed validations to a CSV file
        with open(filename_validation_report, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for validation in failed_validations_list:
                # Initialize a dictionary to hold the row data
                row_data = {'File_Path': validation['file']}
                
                # Extract the failed validation results from the 'failed_validations' dictionary
                failed_validations = validation['failed_validations']
                
                # Check if each validation key exists in the failed validations dictionary
                # Replace False values with "Failed"
                row_data['Date_Prefix'] = "Failed" if failed_validations.get('date_prefix') is False else ""
                row_data['Title'] = "Failed" if failed_validations.get('title') is False else ""
                row_data['GUID'] = "Failed" if failed_validations.get('guid') is False else ""
                
                # Write the row data to the CSV file
                writer.writerow(row_data)
                



# File Listing methods
# ################################################################


    def retrieve_file_list(self, folder_path, recursive=True, filter_extensions=None):
        """Retrieve file paths from the specified folder."""
        file_list = []
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Path '{folder_path}' does not exist.")
        
        files = []
        if recursive:
            for root, _, file_names in os.walk(folder_path):
                files.extend([os.path.join(root, file) for file in file_names])
        else:
            files = [os.path.join(folder_path, file) for file in os.listdir(folder_path)]
        
        # Filter by extension
        return self._filter_by_extension(files, filter_extensions)

    def _filter_by_extension(self, files, extensions):
        """Filter files by specified extensions."""
        if not extensions:
            return files
        return [file for file in files if any(file.lower().endswith(ext.lower()) for ext in extensions)]

    def validate_files(self, file_list, validation_report_path=None):
        validation_report = []
        valid_files = []

        for file in file_list:
            validation_result = self._validate_filename(os.path.basename(file))

            if isinstance(validation_result, dict):  # If validation failed, add to report
                validation_report.append({"file": file, "failed_validations": validation_result})
            else:
                valid_files.append(file)

        if validation_report_path and validation_report:
            fieldnames = ['file', 'failed_validations']
            with open(validation_report_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for item in validation_report:
                    writer.writerow({
                        'file': item['file'],
                        'failed_validations': str(item['failed_validations'])
                    })
            print(f"Validation report saved to: {validation_report_path}")
        elif validation_report_path:  # All files passed validation
            with open(validation_report_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Message'])
                writer.writerow(['All files passed validation.'])
            print(f"All files passed validation. Report saved to: {validation_report_path}")

        # Return the valid files and the validation report (or a message if all pass)
        if not validation_report:
            validation_report = "All files passed validation."

        return valid_files, validation_report


    def include_metadata(self, file_list):
        """Extract metadata for a list of files."""
        return [self.get_file_info(file) for file in file_list]


    def lazy_retrieve_file_list(self, folder_path, recursive=True, extensions=None):
        """
        A generator function to lazily retrieve file paths from the specified directory and its subdirectories.

        Args:
        - folder_path (str): The path to the directory to retrieve files from.
        - recursive (bool, optional): If True, retrieve files from the specified directory and its subdirectories. Defaults to True.
        - extensions (list, optional): A list of file extensions to filter the retrieved files. Defaults to None.

        Yields:
        - str: Yields file paths one by one based on the specified parameters.
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Path '{folder_path}' does not exist.")

        try:
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if not extensions or any(file.endswith(ext) for ext in extensions):
                            yield file_path
            else:
                files = os.listdir(folder_path)
                for file in files:
                    file_path = os.path.join(folder_path, file)
                    if os.path.isfile(file_path):
                        if not extensions or any(file.endswith(ext) for ext in extensions):
                            yield file_path
        except Exception as e:
            print(f"Error: {e}")


# List Filtering methods
# ################################################################
    def filter_files(self, file_list, extensions=None, min_size=None, max_size=None, regex_patterns=None, case_sensitive=True, date_after=None, date_before=None, file_name_filter=None):
        """
        Filter the provided file list based on specified criteria, including regex patterns, case sensitivity, date range, and file name substring.

        Parameters:
        -----------
        file_list : list
            List of file paths or file metadata.

        extensions : list, optional
            A list of file extensions to filter the files. Defaults to None.

        min_size : int, optional
            Minimum file size in bytes. Defaults to None.

        max_size : int, optional
            Maximum file size in bytes. Defaults to None.

        regex_patterns : list, optional
            A list of pre-compiled regex patterns to filter the files. Defaults to None.

        case_sensitive : bool, optional
            If False, makes regex pattern matching case insensitive. Defaults to True.

        date_after : datetime, optional
            Filter files modified on or after this date. Defaults to None.

        date_before : datetime, optional
            Filter files modified on or before this date. Defaults to None.

        file_name_filter : str, optional
            Substring to filter file names. Defaults to None.

        Returns:
        --------
        list
            Filtered list of file paths or file metadata based on the specified criteria.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled_patterns = regex_patterns if regex_patterns else []
        filtered_files = []

        for file_info in file_list:
            file_path = file_info if isinstance(file_info, str) else file_info['path']
            file_size = file_info['size'] if isinstance(file_info, dict) and 'size' in file_info else os.path.getsize(file_path)
            file_modified_time = os.path.getmtime(file_path)
            file_modified_date = datetime.fromtimestamp(file_modified_time)

            if (not extensions or any(file_path.endswith(ext) for ext in extensions)) and \
            (min_size is None or file_size >= min_size) and \
            (max_size is None or file_size <= max_size) and \
            (not compiled_patterns or any(pattern.search(file_path) for pattern in compiled_patterns)) and \
            (date_after is None or file_modified_date >= date_after) and \
            (date_before is None or file_modified_date <= date_before) and \
            (file_name_filter is None or (case_sensitive and file_name_filter in file_path) or (not case_sensitive and file_name_filter.lower() in file_path.lower())):
                filtered_files.append(file_info)

        return filtered_files


# File Search methods
# ################################################################
    def file_search_with_info(self, folder_path, recursive=True, extensions=None, min_size=None, max_size=None, regex_patterns=None, case_sensitive=True, date_after=None, date_before=None, info_list=None, output='terminal'):
        """
        Search files in a directory with specified file information retrieval.

        Args:
        - folder_path (str): Path of the directory to search.
        - recursive (bool, optional): If True, searches files recursively in subdirectories. Defaults to True.
        - extensions (list, optional): A list of file extensions to search for. Defaults to None (search all file types).
        - min_size (int, optional): Minimum file size in bytes. Defaults to None.
        - max_size (int, optional): Maximum file size in bytes. Defaults to None.
        - regex_patterns (list, optional): A list of pre-compiled regex patterns to filter the files. Defaults to None.
        - case_sensitive (bool, optional): If False, makes regex pattern matching case insensitive. Defaults to True.
        - date_after (datetime, optional): Filter files modified on or after this date. Defaults to None.
        - date_before (datetime, optional): Filter files modified on or before this date. Defaults to None.
        - file_attributes (list, optional): A list of file attributes to report. Defaults to None.
        - output (str, optional): Output destination ('terminal' or 'csv'). Defaults to 'terminal'.

        Returns:
        - list: List of dictionaries containing file/folder information based on specified attributes.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled_patterns = regex_patterns if regex_patterns else []

        file_info_list = []

        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_size = os.path.getsize(file_path)
                file_modified_time = os.path.getmtime(file_path)
                file_modified_date = datetime.utcfromtimestamp(file_modified_time)

                # Check criteria (existing code remains the same)

                # Get file information for the matched file with specified attributes
                file_info = self.get_file_info(file_path, info_list=info_list, output='terminal')
                file_info_list.append(file_info)

                if recursive and os.path.isdir(file_path):
                    # Recursively search subdirectories if recursive is True
                    file_info_list.extend(self.file_search_with_info(folder_path=file_path, recursive=True,
                                                                    extensions=extensions, min_size=min_size,
                                                                    max_size=max_size, regex_patterns=regex_patterns,
                                                                    case_sensitive=case_sensitive,
                                                                    date_after=date_after, date_before=date_before,
                                                                    info_list=info_list))

        if output == 'csv':
            output_file = r'c:\test\file_info_output33.csv'  # Define your CSV file path here
            if file_info_list:
                self.process_files_to_csv(file_info_list, output_file, header=info_list)  # Use the process_files_to_csv method
                return f"File information saved to {output_file}"
            else:
                return "No file information to save to CSV."
        else:
            return file_info_list

    def process_files_to_csv(self, search_results, output_file, header=None, delimiter=',', encoding='utf-8', batch_size=1000):
        """
        Process search results and write to a CSV file with various enhancements.

        Args:
        - search_results (generator): Generator yielding file paths from file_search method.
        - output_file (str): Path of the output CSV file.
        - header (list, optional): List of headers for the CSV file. Defaults to None.
        - delimiter (str, optional): Delimiter for the CSV file. Defaults to ','.
        - encoding (str, optional): Encoding for the CSV file. Defaults to 'utf-8'.
        - batch_size (int, optional): Batch size for writing to the CSV file. Defaults to 1000.
        """
        # Check if the output folder exists, create it if not
        output_folder = os.path.dirname(output_file)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Check if the output_file already exists
        file_name, file_extension = os.path.splitext(output_file)
        count = 1
        while os.path.exists(output_file):
            output_file = f"{file_name}_{count}{file_extension}"
            count += 1

        try:
            with open(output_file, 'w', newline='', encoding=encoding) as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)

                # Write header if provided
                if header:
                    csv_writer.writerow(header)

                # Write file paths to CSV in batches
                for file_info in search_results:
                    if isinstance(file_info, dict):
                        if header is None:
                            header = list(file_info.keys())
                            csv_writer.writerow(header)
                        csv_writer.writerow(file_info.values())
                    elif isinstance(file_info, list):
                        csv_writer.writerows(file_info)
                    else:
                        csv_writer.writerow([file_info])

            print(f"Search Results Saved To: {output_file}")
            open_csv_in_excel(output_file)

        except OSError as e:
            print(f"Error writing to CSV: {e}")


# File Operation methods
# ################################################################
    def get_file_info(self, file_path, info_list=None, output='terminal'):
        """
        Get file information based on the specified attributes.

        Args:
        - file_path (str): Path of the file to retrieve information from.
        - output (str, optional): Output preference - 'terminal' or 'csv'. Defaults to 'terminal'.
        """
        file_info = {}

        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"File '{file_path}' not found.")
            return file_info  # Return an empty dictionary

        # Collect file information based on user specified attributes or retrieve all possible attributes
        info_list = ['file_name', 'full_path', 'folder_path', 'extension', 'size', 'created_time', 'modified_time', 'accessed_time', 'owner', 'permissions', 'mime_type', 'checksum', 'is_file', 'is_directory']
        # Add more attributes as needed (e.g., 'permissions', 'is_directory', etc.)

        for info in info_list:
            if info == 'file_name':
                file_info['file_name'] = os.path.basename(file_path)
            elif info == 'full_path':
                file_info['full_path'] = os.path.abspath(file_path)
            elif info == 'folder_path':
                file_info['folder_path'] = os.path.dirname(file_path)
            elif info == 'extension':
                file_info['extension'] = os.path.splitext(file_path)[1]
            elif info == 'size':
                file_info['size'] = os.path.getsize(file_path)
            elif info == 'created_time':
                file_info['created_time'] = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
            elif info == 'modified_time':
                file_info['modified_time'] = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            elif info == 'accessed_time':
                file_info['accessed_time'] = datetime.fromtimestamp(os.path.getatime(file_path)).isoformat()
            elif info == 'owner':
                file_info['owner'] = self._get_file_owner(file_path)
            elif info == 'permissions':
                file_info['permissions'] = self._get_file_permissions(file_path)
            elif info == 'mime_type':
                file_info['mime_type'] = mimetypes.guess_type(file_path)[0]
            elif info == 'checksum':
                file_info['checksum'] = self._get_file_checksum(file_path)
            elif info == 'is_file':
                file_info['is_file'] = os.path.isfile(file_path)
            elif info == 'is_directory':
                file_info['is_directory'] = os.path.isdir(file_path)
            # Add more attributes as needed

        # Display or save file information based on user preference
        if output == 'terminal':
            self._display_file_info(file_info)  # Display file information in the terminal
        elif output == 'csv':
            # Do something here for CSV output if needed
            pass
        else:
            print("Invalid output option. Please choose 'terminal' or 'csv'.")

        return file_info  # Return the collected file information dictionary

    # def generate_exiftool_command(self, data_dict, file):
    #     """
    #     Generates an ExifTool command to modify metadata for a specified file.

    #     This method utilizes global variables 'exiftool_path' and 'exif_config_path'
    #     set externally to define the path to the ExifTool executable and its configuration.

    #     Args:
    #     data_dict (dict): A dictionary containing key-value pairs for metadata fields and values.
    #     file (str): Path to the file for which metadata is to be modified.

    #     Returns:
    #     list: A list containing the ExifTool command and its parameters.

    #     Example:
    #         Instantiate the file handler
    #         file_handler = FileHandler()
            
    #         Create Exiftool command
    #         update = file_handler.generate_exiftool_command(acdsee_dict, file)
            
    #         Run SubProcess
    #         subprocess.run(update, check=True)
            
    #         Print results to terminal
    #         print(f"{f_success}File {file_count} of {total_files} | {f_success}{file} Updated by subprocess{f_default}")
        
    #     """

        
    #     global exiftool_path, exif_config_path
        
    #     # Initiate first part of the Exiftool command
    #     commandp1 = [exiftool_path, "-config", exif_config_path]
        
    #     # Generate fields and values to update from dictionary
    #     for field, value in data_dict.items():
    #         commandp1.append(f'-{field}={value}')

    #     # Initiate the second part of the Exiftool command
    #     commandp2 = [    
    #     "-m",
    #     "-f",
    #     "-use",
    #     "mwg",
    #     "-n",
    #     "-overwrite_original",
    #     "-sep",
    #     ", ",
    #     file
    #     ]
        
    #     # Merge Exiftool Command parts
    #     command = commandp1 + commandp2

    #     return command




    def generate_exiftool_command(self, data_dict, file):
        """
        Generates an ExifTool command to modify metadata for a specified file.

        This method utilizes global variables 'exiftool_path' and 'exif_config_path'
        set externally to define the path to the ExifTool executable and its configuration.

        Args:
        data_dict (dict): A dictionary containing key-value pairs for metadata fields and values.
        file (str): Path to the file for which metadata is to be modified.

        Returns:
        list: A list containing the ExifTool command and its parameters.

        Example:
            Instantiate the file handler
            file_handler = FileHandler()
            
            Create Exiftool command
            update = file_handler.generate_exiftool_command(acdsee_dict, file)
            
            Run SubProcess
            subprocess.run(update, check=True)
            
            Print results to terminal
            print(f"{f_success}File {file_count} of {total_files} | {f_success}{file} Updated by subprocess{f_default}")
        
        """

        
        global exiftool_path, exif_config_path
        
        # Initiate first part of the Exiftool command
        commandp1 = [
        exiftool_path,
        "-config",
        exif_config_path,
        "-m",
        "-use",
        "mwg",
        "-n",
        "-overwrite_original",
        "-sep",
        ", ",
                     ]
        
        # Generate fields and values to update from dictionary
        for field, value in data_dict.items():
            commandp1.append(f'-{field}={value}')

        # Initiate the second part of the Exiftool command
        commandp2 = [    
        file
        ]
        
        # Merge Exiftool Command parts
        command = commandp1 + commandp2

        return command





    def regex_rename_strings(self, string_list, rename_patterns):
        """
        Renames strings in the given string_list based on specified rename_patterns using regular expressions.

        Args:
        - string_list (list or str): A list of strings to be renamed or a single string.
        - rename_patterns (dict): A dictionary containing regex patterns as keys and their replacements as values.

        Returns:
        - str: A string containing the renamed strings concatenated.

        Raises:
        - ValueError: If string_list is not a list or string.

        Note:
        - This method iterates through each old_string in string_list and applies the rename_patterns using regular expressions.
        - It concatenates the renamed strings based on the provided patterns and returns a single string.
        """
        if not isinstance(string_list, (list, str)):
            raise ValueError("string_list should be a list or a string.")

        if isinstance(string_list, str):
            string_list = [string_list]  # Convert the string to a single-item list
        
        renamed_strings = []
        for old_string in string_list:
            new_string = old_string
            for pattern, replacement in rename_patterns.items():
                new_string = pattern.sub(replacement, new_string)  # Modify string
        
            renamed_strings.append(new_string)
        
        return ''.join(renamed_strings)

    def rename_file(self, old_file_path, new_file_name, check_existing=True):
        # Extract directory path and file extension
        directory, filename = os.path.split(old_file_path)
        new_file_path = os.path.join(directory, new_file_name)

        if check_existing:
            base, extension = os.path.splitext(new_file_name)
            counter = 1

            # Check if the new file name exists; if it does, increment counter
            while os.path.exists(new_file_path):
                new_file_name = f"{base}_{counter}{extension}"
                new_file_path = os.path.join(directory, new_file_name)
                counter += 1

        try:
            os.rename(old_file_path, new_file_path)
            print(f"File renamed successfully to '{new_file_name}'")
            return new_file_path
        except Exception as e:
            print(f"Error: {e}. Failed to rename the file.")
            return None

    def delete_files(self, file_list, preview_only=True, prompt_each=True):
        # if preview_only:
        #     prompt_each = True  # Preview mode defaults to prompting for each file
        
        for file_path in file_list:
            if prompt_each:
                delete_confirmation = input(f"Delete '{file_path}'? (y/n): ").lower()
                if delete_confirmation != 'y':
                    print(f"Skipping deletion of '{file_path}'")
                    continue
            
            if preview_only:
                print(f"File to be deleted: {file_path}")
            else:
                try:
                    os.remove(file_path)
                    print(f"Deleted '{file_path}' successfully.")
                except FileNotFoundError as e:
                    print(f"Error: {e}. File '{file_path}' not found.")
                except PermissionError as e:
                    print(f"Error: {e}. Permission denied to delete '{file_path}'.")

    def move_file_to_new_location(self, old_file_path, new_directory, overwrite=False, rename_if_exists=False):
        # Check if the source file exists
        if not os.path.exists(old_file_path):
            print(f"Error: Source file '{old_file_path}' does not exist.")
            return False

        # Separate file name from file path
        file_directory, file_name = os.path.split(old_file_path)

        # Append new file path to the file name
        new_file_path = os.path.join(new_directory, file_name)

        # Check if the source and destination paths are the same
        if old_file_path == new_file_path:
            print("Error: Source and destination paths are the same. No action taken.")
            return False

        try:
            # Check if the destination directory exists; if not, create it
            if not os.path.exists(new_directory):
                os.makedirs(new_directory)
                print(f"Created directory: {new_directory}")

            # Check if a file with the same name already exists in the destination directory
            while os.path.exists(new_file_path) and rename_if_exists:
                base, ext = os.path.splitext(file_name)
                index = 1
                new_file_name = f"{base}_{index}{ext}"
                new_file_path = os.path.join(new_directory, new_file_name)
                index += 1

            if os.path.exists(new_file_path):
                if overwrite:
                    os.remove(new_file_path)
                    print(f"Existing file '{new_file_path}' overwritten.")
                else:
                    print(f"Error: File '{new_file_path}' already exists in the destination directory.")
                    return False

            # Move the file to the new location
            shutil.move(old_file_path, new_file_path)
            print(f"File moved successfully from '{old_file_path}' to '{new_file_path}'")
            return True
        except Exception as e:
            print(f"Error: {e}. Failed to move the file.")
            return False

    def delete_empty_subfolders(root_folder, preview_only=True, prompt_each=True, use_rmtree=False):
        """
        Delete empty subfolders within a root folder.

        Args:
        - root_folder (str): The path to the root folder to search for empty subfolders.
        - preview_only (bool, optional): If True, only previews which folders would be deleted without actually deleting them. Defaults to True.
        - prompt_each (bool, optional): If True, prompts for confirmation before deleting each empty folder. Defaults to True.
        - use_rmtree (bool, optional): If True, uses shutil.rmtree() for deleting empty folders instead of os.rmdir(). Defaults to False.

        Notes:
        - The function walks through the directory tree starting from root_folder and deletes empty subfolders.
        - When preview_only is True, it shows which folders would be deleted without performing the deletion.
        - If prompt_each is True, it prompts for confirmation before deleting each empty folder.
        - When use_rmtree is True, it uses shutil.rmtree() to bypass path length limitations (Windows) and delete folders.
        - Be cautious when using use_rmtree=True as it can't be undone and may affect the system irreversibly.
        """
        for root, dirs, files in os.walk(root_folder, topdown=False):
            for folder in dirs:
                folder_path = os.path.join(root, folder)
                try:
                    if not os.listdir(folder_path):  # Check if folder is empty
                        if prompt_each:
                            delete_confirmation = input(f"Delete '{folder_path}'? (y/n): ").lower()
                            if delete_confirmation != 'y':
                                print(f"Skipping deletion of '{folder_path}'")
                                continue

                        if preview_only:
                            print(f"Empty folder to be deleted: {folder_path}")
                        else:
                            if use_rmtree:
                                shutil.rmtree(folder_path)
                                print(f"Deleted empty folder: {folder_path}")
                            else:
                                os.rmdir(folder_path)
                                print(f"Deleted empty folder: {folder_path}")
                except Exception as e:
                    print(f"Error: {e}. Failed to delete folder '{folder_path}'")


    def copy_file_to_new_location(self, old_file_path, new_directory, overwrite=False, rename_if_exists=False):
        try:
            # Check if the source file exists
            if not os.path.exists(old_file_path):
                print(f"Error: Source file '{old_file_path}' does not exist.")
                return False

            # Separate file name from file path
            file_directory, file_name = os.path.split(old_file_path)

            # Append new file path to the file name
            new_file_path = os.path.join(new_directory, file_name)

            # Check if the source and destination paths are the same
            if old_file_path == new_file_path:
                print("Error: Source and destination paths are the same. No action taken.")
                return False

            # Check if the destination directory exists; if not, create it
            if not os.path.exists(new_directory):
                os.makedirs(new_directory)
                print(f"Created directory: {new_directory}")

            # Check if a file with the same name already exists in the destination directory
            while os.path.exists(new_file_path) and rename_if_exists:
                base, ext = os.path.splitext(file_name)
                index = 1
                new_file_name = f"{base}_{index}{ext}"
                new_file_path = os.path.join(new_directory, new_file_name)
                index += 1

            if os.path.exists(new_file_path):
                if overwrite:
                    os.remove(new_file_path)
                    print(f"Existing file '{new_file_path}' overwritten.")
                else:
                    print(f"Error: File '{new_file_path}' already exists in the destination directory.")
                    return False

            # Copy the file to the new location
            shutil.copy2(old_file_path, new_file_path)
            print(f"File copied successfully from '{old_file_path}' to '{new_file_path}'")

            # Verify checksums of the source and destination files
            source_checksum = self.calculate_checksum(old_file_path)
            destination_checksum = self.calculate_checksum(new_file_path)
            if source_checksum != destination_checksum:
                print("Warning: Checksum verification failed. Data integrity may be compromised.")

            return True
        except Exception as e:
            print(f"Error: {e}. Failed to copy the file.")
            return False

    def calculate_checksum(file_path, algorithm='md5', chunk_size=65536):
        """Calculate checksum (hash) of a file."""
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as file:
            buffer = file.read(chunk_size)
            while len(buffer) > 0:
                hasher.update(buffer)
                buffer = file.read(chunk_size)
        return hasher.hexdigest()










    # def write_metadata(self, et, metadata_dict, file, total_files=None, file_count=None, default_subprocess = True):
    #     global exiftool_path, exif_config_path

    #     if default_subprocess == True:
    #         try:
    #             update = self.generate_exiftool_command(metadata_dict, file)
    #             subprocess.run(update, check=True)

    #             if total_files is not None and file_count is not None:
    #                 print(f"File {file_count} of {total_files} | {f_success}{file}{f_info} Updated by subprocess{f_default}")
    #             else:
    #                 print(f"{f_success}{file}{f_info} Updated by subprocess{f_default}")

    #         except subprocess.CalledProcessError as e:
    #             print(f"Error executing ExifTool command: {e}")
    #             if total_files is not None and file_count is not None:
    #                 print(f"{f_warning}File {file_count} of {total_files} | {file} Can't be Updated{f_default}")
    #             else:
    #                 print(f"{f_warning}{file} Can't be Updated{f_default}")

    #     else:
    #         try:
    #             et.set_tags(file, metadata_dict)
    #             if total_files is not None and file_count is not None:
    #                 print(f"File {file_count} of {total_files} | {f_success}{file} Updated{f_default}")
    #             else:
    #                 print(f"{f_success}{file} Updated{f_default}")

    #         except:
    #             # Try again, run Exiftool as a subprocess
    #             try:
    #                 update = self.generate_exiftool_command(metadata_dict, file)
    #                 subprocess.run(update, check=True)
    #                 if total_files is not None and file_count is not None:
    #                     print(f"File {file_count} of {total_files} | {f_success}{file}{f_info} Updated by subprocess{f_default}")
    #                 else:
    #                     print(f"{f_success}{file}{f_info} Updated by subprocess{f_default}")

    #             except subprocess.CalledProcessError as e:
    #                 print(f"Error executing ExifTool command: {e}")
    #                 if total_files is not None and file_count is not None:
    #                     print(f"{f_warning}File {file_count} of {total_files} | {file} Can't be Updated{f_default}")
    #                 else:
    #                     print(f"{f_warning}{file} Can't be Updated{f_default}")

    def write_metadata(self, et, metadata_dict, file, total_files=None, file_count=None, default_subprocess=True):
        try:
            if default_subprocess:
                command = self.generate_exiftool_command(metadata_dict, file)
                subprocess.run(command, check=True)
                update_msg = f"{f_success} Updated by subprocess" if total_files is None or file_count is None else f"File {file_count} of {total_files} | Updated by subprocess{f_default}"
            else:
                et.set_tags(file, metadata_dict)
                update_msg = f"{f_success} Updated" if total_files is None or file_count is None else f"File {file_count} of {total_files} | Updated{f_default}"

            if total_files is not None and file_count is not None:
                print(f"{update_msg}: {file}")
            else:
                print(f"{file}{update_msg}")

        except subprocess.CalledProcessError as e:
            print(f"{f_warning}Error executing ExifTool command: {e}{f_default}")
            if total_files is not None and file_count is not None:
                print(f"{f_warning}File {file_count} of {total_files} | {file} Can't be Updated{f_default}")
            else:
                print(f"{f_warning}{file} Can't be Updated{f_default}")




    def move_files(self, source_path, destination_path, recursive=False):
        try:

            print(source_path)
            print(os.path.isfile(source_path))
            print(destination_path)
            print(os.path.basename(destination_path))

            # If both source and destination are files, handle file move
            if os.path.isfile(source_path):
                
                dest_folder = os.path.dirname(destination_path)
                os.makedirs(dest_folder, exist_ok=True)

                dest_file_path = destination_path
                if os.path.exists(dest_file_path):
                    print(f"File '{os.path.basename(destination_path)}' already exists in destination. Renaming before moving.")
                    name, ext = os.path.splitext(os.path.basename(destination_path))
                    counter = 1
                    while os.path.exists(dest_file_path):
                        new_name = f"{name}_{counter}{ext}"
                        dest_file_path = os.path.join(dest_folder, new_name)
                        counter += 1
                    print(f"File renamed to '{os.path.basename(dest_file_path)}'.")

                shutil.move(source_path, dest_file_path)
                print(f"File moved successfully to '{dest_file_path}'")
                return True

        except Exception as e:
            print(f"Error: {e}")
            return False

def delete_empty_subfolders(root_folder, preview_only=True, prompt_each=True, use_rmtree=False):
    """
    Delete empty subfolders within a root folder.

    Args:
    - root_folder (str): The path to the root folder to search for empty subfolders.
    - preview_only (bool, optional): If True, only previews which folders would be deleted without actually deleting them. Defaults to True.
    - prompt_each (bool, optional): If True, prompts for confirmation before deleting each empty folder. Defaults to True.
    - use_rmtree (bool, optional): If True, uses shutil.rmtree() for deleting empty folders instead of os.rmdir(). Defaults to False.

    Notes:
    - The function walks through the directory tree starting from root_folder and deletes empty subfolders.
    - When preview_only is True, it shows which folders would be deleted without performing the deletion.
    - If prompt_each is True, it prompts for confirmation before deleting each empty folder.
    - When use_rmtree is True, it uses shutil.rmtree() to bypass path length limitations (Windows) and delete folders.
    - Be cautious when using use_rmtree=True as it can't be undone and may affect the system irreversibly.
    """
    for root, dirs, files in os.walk(root_folder, topdown=False):
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            try:
                if not os.listdir(folder_path):  # Check if folder is empty
                    if prompt_each:
                        delete_confirmation = input(f"Delete '{folder_path}'? (y/n): ").lower()
                        if delete_confirmation != 'y':
                            print(f"Skipping deletion of '{folder_path}'")
                            continue

                    if preview_only:
                        print(f"Empty folder to be deleted: {folder_path}")
                    else:
                        if use_rmtree:
                            shutil.rmtree(folder_path)
                            print(f"Deleted empty folder: {folder_path}")
                        else:
                            os.rmdir(folder_path)
                            print(f"Deleted empty folder: {folder_path}")
            except Exception as e:
                print(f"Error: {e}. Failed to delete folder '{folder_path}'")



def open_csv_in_excel(file_path):
    # check_excel_path_1 = r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE"
    # check_excel_path_2 = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
    excel_paths = [r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE", r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"]
    
    excel_program_path = None

    for excel_path in excel_paths:

        # Check if EXCEL.EXE exists in check_excel_path_1
        if os.path.exists(excel_path):
            excel_program_path = excel_path

    # # Check if EXCEL.EXE exists in check_excel_path_2
    # if not excel_path and os.path.exists(check_excel_path_2):
    #     excel_path = check_excel_path_2

    if not excel_program_path:
        # Directories to search for EXCEL.EXE
        directories_to_search = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            r"C:\\",
            # Add more directories to search if needed
        ]

        excel_program_path = find_excel_exe(directories_to_search)

    if excel_program_path:
        subprocess.Popen([excel_program_path, file_path])
    else:
        print("Sorry. Cannot open file directly. Excel cannot be found")

def find_excel_exe(directories):
    for directory in directories:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower() == 'excel.exe':
                    return os.path.join(root, file)
    return None