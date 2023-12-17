import os
import re
import csv
import sys
import yaml
sys.path.append(r'C:\Media Management\Scripts')

# Load file paths in YAML file
yaml_file = r'C:\Media Management\Scripts\paths_config.yml'
with open(yaml_file, 'r') as file:
    config = yaml.safe_load(file)

from config import filename_validation_rules, f_warning, f_input, f_success, f_default, audio_files, document_files, image_files, video_files

from Media_Management_Support_Functions import process_files, list_files, delete_files, open_csv_in_excel
import shutil


def compare_and_rename_files(live_folder, static_folder):
    live_files = {}
    static_files = {}

    # Get all files in live-archive folder and store their identifiers
    for root, dirs, files in os.walk(live_folder):
        for file_name in files:
            parts = file_name.split('_')
            if len(parts) >= 3:
                identifier = parts[-1].split('.')[0]
                live_files[identifier] = file_name

    # Get all files in static-archive folder and store their identifiers
    for root, dirs, files in os.walk(static_folder):
        for file_name in files:
            file_base, file_extension = os.path.splitext(file_name)
            if len(file_base) > 10:
                identifier = file_base[-10:]  # Extract last 10 characters of the file base
                static_files[identifier] = os.path.join(root, file_name)  # Store full path

    print("Static Files:", static_files)

    # Compare identifiers and rename files in static-archive if they differ from live-archive
    for identifier, file_path in static_files.items():
        if identifier in live_files:
            live_name = live_files[identifier]

            # Get the base name without extension for both live and static files
            live_base, _ = os.path.splitext(live_name)
            static_base, _ = os.path.splitext(os.path.basename(file_path))

            new_static_path = os.path.join(config['paths']['static_folder'], live_base + os.path.splitext(file_path)[-1])

            if os.path.exists(file_path):
                old_file_name = os.path.basename(file_path)
                new_file_name = os.path.basename(new_static_path)

                if os.path.exists(new_static_path):
                    print(f"File {new_static_path} already exists. Skipping renaming.")
                else:
                    print(f"Renaming {old_file_name} to {new_file_name}")
                    os.rename(file_path, new_static_path)
            else:
                print(f"File {os.path.basename(file_path)} not found in the static folder.")

def validate_file_name(file_paths):
    failed_validations = []

    for file_path in file_paths:
        errors = []
        # Check file path length...
        
        # Extract file name without extension from file path
        file_name, file_extension = os.path.splitext(os.path.basename(file_path))

        # Split file name by underscores
        components = file_name.split('_')

        # Check if there are exactly three components after splitting
        if len(components) != 3:
            errors.append('File name must consist of three elements separated by underscores.')
        else:
            # Validate each component...
            # Adjust the index for GUID check to ignore file extension
            for index, component in enumerate(components):
                rule_key = list(filename_validation_rules.keys())[index + 1]  # Skip path_name_length
                pattern, error_message = filename_validation_rules[rule_key]
                if index == 2:  # Check for the GUID (third component)
                    component_without_extension = component.split('.')[0]  # Ignore file extension
                    if not re.match(pattern, component_without_extension):
                        errors.append(error_message)
                else:
                    if not re.match(pattern, component):
                        errors.append(error_message)

        if errors:
            failed_validations.append({'file_path': file_path, 'reasons': errors})

    return failed_validations

def find_invalid_files(folder, archive_type, create_csv=False, display_reason=False):
    invalid_files = []
    allowed_extensions_live = {"pdf", "3gp", "jpg", "mp4", "xmp", "ini"}

    ignore_extensions = ["ini"]

    # If ignore_extensions is not provided, initialize it as an empty list
    if ignore_extensions is None:
        ignore_extensions = []

    csv_columns = ['File_Path', 'File_Name', 'Extension', 'Reason']
    csv_rows = []

    date_pattern = re.compile(r'^[\dx]{8}[cpem]')
    title_pattern = re.compile(r'[a-z0-9-]{1,80}')

    for root, _, files in os.walk(folder):
        for file_name in files:
            parts = file_name.split('_')

            if len(parts) < 3:
                file_extension = parts[-1].split('.')[-1].lower()

                if file_extension in ignore_extensions:
                    continue

                if archive_type == "live-archive" and file_extension not in allowed_extensions_live:
                    invalid_file_path = os.path.join(root, file_name)
                    invalid_files.append(invalid_file_path)

                    if create_csv:
                        extension = parts[-1].split('.')[-1]
                        csv_rows.append({'File_Path': invalid_file_path,
                                         'File_Name': file_name,
                                         'Extension': extension,
                                         'Reason': 'Invalid file extension for live-archive'})

                    if display_reason:
                        print(f"{f_warning}File: {invalid_file_path}{f_default} | Reason: Invalid file extension for live-archive")

            else:
                date_part = parts[0]
                title_part = parts[1]
                identifier_part = parts[2].split('.')[0]

                failure_reason = ''

                valid_date = bool(date_pattern.match(date_part))

                if not valid_date:
                    failure_reason += 'Invalid date format. '

                valid_title = bool(title_pattern.match(title_part))

                if not valid_title:
                    failure_reason += 'Invalid title format. '

                if not (len(identifier_part) == 10 and identifier_part.isdigit()):
                    failure_reason += 'Invalid identifier format. '

                if failure_reason:
                    invalid_file_path = os.path.join(root, file_name)
                    invalid_files.append(invalid_file_path)

                    if create_csv:
                        extension = parts[2].split('.')[-1]
                        csv_rows.append({'File_Path': invalid_file_path,
                                         'File_Name': file_name,
                                         'Extension': extension,
                                         'Reason': failure_reason})

                    if display_reason:
                        print(f"{f_warning}File: {invalid_file_path}{f_default} | Reason: {failure_reason}")

    if create_csv and csv_rows:
        csv_file_path = 'invalid_files_details.csv'
        try:
            with open(csv_file_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                writer.writeheader()
                for data in csv_rows:
                    writer.writerow(data)
            print(f"CSV file created: {csv_file_path}")
        except IOError:
            print("Error creating CSV file.")

    return invalid_files

def compare_and_rename_files(live_folder, static_folder):
    live_files = {}
    static_files = {}

    # Get all files in live-archive folder and store their identifiers
    for root, dirs, files in os.walk(live_folder):
        for file_name in files:
            parts = file_name.split('_')
            if len(parts) >= 3 and parts[-1].count('.') == 1:
                identifier = parts[-1].split('.')[0]
                live_files[identifier] = file_name

    # Get all files in static-archive folder and store their identifiers
    for root, dirs, files in os.walk(static_folder):
        for file_name in files:
            parts = file_name.split('_')
            if len(parts) >= 3 and parts[-1].count('.') == 1:
                identifier = parts[-1].split('.')[0]
                static_files[identifier] = file_name

    # Compare identifiers and rename files in static-archive if they differ from live-archive
    for identifier, file_name in static_files.items():
        if identifier in live_files and live_files[identifier] != file_name:
            live_name = live_files[identifier]
            new_static_name = '_'.join(file_name.split('_')[:-1]) + '_' + identifier + '.' + file_name.split('.')[-1]
            new_static_path = os.path.join(config['paths']['static_folder'], new_static_name)
            old_static_path = os.path.join(config['paths']['static_folder'], file_name)
            try:
                shutil.move(old_static_path, new_static_path)
                print(f"Renamed {file_name} to {new_static_name}")
            except:
                print("Could not rename file.")
            

def synchronize_folders(src_folder, dest_folder):
    def get_files_identifiers(folder):
        files_identifiers = set()
        for root, _, files in os.walk(folder):
            for file_name in files:
                parts = file_name.split('_')
                if len(parts) >= 3 and parts[-1].count('.') == 1:
                    identifier = parts[-1].split('.')[0]
                    files_identifiers.add(identifier)
        return files_identifiers

    src_files = get_files_identifiers(src_folder)
    dest_files = get_files_identifiers(dest_folder)

    # Copy missing files from src_folder to dest_folder
    missing_files_src_to_dest = src_files - dest_files
    print(rf"The Live Archive has these files, which are missing from the Static Archive\n{missing_files_src_to_dest}")
    input("LKSDIJH")
    for identifier in missing_files_src_to_dest:
        for root, _, files in os.walk(src_folder):
            
            
            for file_name in files:
                parts = file_name.split('_')
                if len(parts) >= 3 and parts[-1].split('.')[0] == identifier:
                    source_path = os.path.join(src_folder, file_name)
                    destination_path = os.path.join(dest_folder, file_name)
                    if os.path.isfile(source_path):  # Check if source file exists
                        shutil.copy2(source_path, destination_path)
                        print(f"Copied {file_name} to {dest_folder}")
                    else:
                        print(f"Source file {file_name} is not an archive file. Skipping...")
    
    # Copy missing files from dest_folder to src_folder
    missing_files_dest_to_src = dest_files - src_files
    print(rf"The Static Archive has these files, which are missing from the Live Archive\n{missing_files_dest_to_src}")
    input("LKSDIJH")
    for identifier in missing_files_dest_to_src:
        for root, _, files in os.walk(dest_folder):
            for file_name in files:
                parts = file_name.split('_')
                if len(parts) >= 3 and parts[-1].split('.')[0] == identifier:
                    source_path = os.path.join(dest_folder, file_name)
                    destination_path = os.path.join(src_folder, file_name)
                    if os.path.isfile(source_path):  # Check if source file exists
                        shutil.copy2(source_path, destination_path)
                        print(f"Copied {file_name} to {src_folder}")
                    else:
                        print(f"Source file {file_name} is not a valid archive file. Skipping...")

def count_file_extensions_sorted(folder_path):
    extensions_count = {}
    
    # Walk through all folders and subfolders
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            # Extract the file extension
            _, extension = os.path.splitext(file_name)
            extension = extension.lower()  # Convert to lowercase for consistency
            
            # Count the file extensions
            if extension:
                extensions_count[extension] = extensions_count.get(extension, 0) + 1
    
    # Sort extensions by count in descending order
    sorted_extensions = sorted(extensions_count.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_extensions

def get_highest_unique_identifier(folder_path, valid_extensions):
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


def get_unique_ids(folder_path):
    """
    Get a list of unique IDs in a folder.

    Args:
        folder_path (str): Path to the folder.

    Returns:
        list: List of unique IDs in the folder.
    """
    unique_ids = set()
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            # Check for the pattern: underscore + 10 digits + file extension
            if "_" in file_name and file_name.rfind(".") > file_name.rfind("_") and file_name[file_name.rfind("_")+1:].isdigit():
                unique_id = file_name[file_name.rfind("_")+1:file_name.rfind(".")]
                unique_ids.add(unique_id)
    return list(unique_ids)


# START
# ################################################################
# Rename Static Files Based on Live File Names Using the GUID ####
# ################################################################

def extract_unique_id(file_path):
    file_name = os.path.basename(file_path)
    parts = file_name.split('_')
    if len(parts) >= 2:
        unique_id_with_extension = parts[-1]
        unique_id = unique_id_with_extension.split('.')[0]
        return unique_id
    return None

def rename_static_filenames_with_live(live_root_folder, static_root_folder):
    live_files = {}

    for root, _, files in os.walk(live_root_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            unique_id = extract_unique_id(file_path)
            if unique_id:
                live_files[unique_id] = file_name

    for root, _, files in os.walk(static_root_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            unique_id = extract_unique_id(file_path)
            if unique_id and unique_id in live_files:
                live_file_name = live_files[unique_id]
                if live_file_name != file_name:
                    live_parts = live_file_name.split('.')
                    static_parts = file_name.split('.')
                    new_static_file_name = f"{live_parts[0]}.{static_parts[1]}"
                    # print(new_static_file_name)
                    new_static_file_path = os.path.join(root, new_static_file_name)
                    print(f"Old Name: {file_path} || New Name: {new_static_file_path}")
                    if not os.path.exists(new_static_file_path):
                        shutil.move(file_path, new_static_file_path)






# ################################################################
# Rename Static Files Based on Live File Names Using the GUID ####
# ################################################################
# END





# START
# ################################################################
# Compare the files between the Live and Static Archives #########
# ################################################################


def compare_file_counts(live_folder, static_folder):
    live_files = {}
    static_files = {}

    # Collect file paths and identifiers from files in live-archive folder
    for root, dirs, files in os.walk(live_folder):
        for file_name in files:
            parts = file_name.split('_')
            if len(parts) >= 3:
                identifier = parts[-1].split('.')[0]
                live_files[identifier] = os.path.join(root, file_name)

    # Collect file paths and identifiers from files in static-archive folder
    for root, dirs, files in os.walk(static_folder):
        for file_name in files:
            parts = file_name.split('_')
            if len(parts) >= 3:
                identifier = parts[-1].split('.')[0]
                static_files[identifier] = os.path.join(root, file_name)

    # Identify files present in live-archive but not in static-archive
    missing_in_static = []
    for identifier, file_path in live_files.items():
        if identifier not in static_files:
            missing_in_static.append(file_path)

    # Identify files present in static-archive but not in live-archive
    missing_in_live = []
    for identifier, file_path in static_files.items():
        if identifier not in live_files:
            missing_in_live.append(file_path)

    # Compare the number of unique identifiers in both folders
    live_count = len(live_files)
    static_count = len(static_files)

    if live_count == static_count:
        return True, live_count, static_count, missing_in_live, missing_in_static
    else:
        return False, live_count, static_count, missing_in_live, missing_in_static

def print_comparison_results(results):
    success, live_count, static_count, missing_in_live, missing_in_static = results

    print("Comparing Static and Live Archive")
    print("---------------------------------")
    print("Comparison Results:")
    print(f"Do Files Match: {success}")
    print(f"Number of Files in Live: {live_count}")
    print(f"Number of Files in Static: {static_count}")

    if missing_in_live:
        print("\nFiles Missing in Live:")
        for file_path in missing_in_live:
            print(f" - {file_path}")

    if missing_in_static:
        print("\nFiles Missing in Static:")
        for file_path in missing_in_static:
            print(f" - {file_path}")







def compare_archives(live_archive_path, static_archive_path, ignore_extensions=None):
    if ignore_extensions is None:
        ignore_extensions = []

    differences = []
    
    for root, _, _ in os.walk(live_archive_path):
        static_folder = root.replace(live_archive_path, static_archive_path, 1)
        
        if os.path.exists(static_folder):
            live_files = set(os.path.splitext(file)[0] for file in os.listdir(root) if os.path.splitext(file)[1] not in ignore_extensions)
            static_files = set(os.path.splitext(file)[0] for file in os.listdir(static_folder) if os.path.splitext(file)[1] not in ignore_extensions)
            
            extra_in_static = live_files - static_files
            extra_in_live = static_files - live_files
            
            for file in extra_in_static:
                file_in_static_archive = os.path.join(static_folder, file)
                if not os.path.exists(file_in_static_archive):
                    differences.append((file, root, static_folder, 'Present in Static Archive'))
            
            for file in extra_in_live:
                file_in_live_archive = os.path.join(root, file)
                if not os.path.exists(file_in_live_archive):
                    differences.append((file, root, static_folder, 'Present in Live Archive'))

    return differences

def write_diff_to_csv(differences, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['File Name', 'Live Archive Path', 'Static Archive Path', 'Presence']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for diff in differences:
            writer.writerow({'File Name': diff[0], 'Live Archive Path': diff[1], 'Static Archive Path': diff[2], 'Presence': diff[3]})


# ################################################################
# Compare the files between the Live and Static Archives #########
# ################################################################
# END



# START
# ################################################################
# Check for file types that don't belong in archive folders ######
# ################################################################

def print_summary(summary_result):
    for category, extensions in summary_result.items():
        print(f"\n{category.capitalize()} Summary:")
        if extensions:
            for extension, count in extensions.items():
                print(f"{f_warning}  - {extension}: {count} files{f_default}")
        else:
            print(f"{f_success}No inappropriate files found for this category.{f_default}")

def print_detailed_with_csv(detailed_result, export_to_csv=False):
    for category, files in detailed_result.items():
        print(f"\n{category.capitalize()} Detailed Information:")
        if files:
            for file_path in files:
                print(f"{f_warning}  - {file_path}{f_default}")
        else:
            print(f"{f_success}No inappropriate files found for this category.{f_default}")

    if export_to_csv:
        user_choice = input(f"\n{f_input}Do you want to export the detailed information to a CSV file? (y/n): {f_default}").lower()
        if user_choice == 'y':
            csv_filename = input(f"{f_input}Enter CSV filename (e.g., detailed_info.csv): {f_default}")
            csv_data = []
            for category, files in detailed_result.items():
                for file_path in files:
                    file_name = os.path.basename(file_path)
                    folder = os.path.dirname(file_path)
                    file_extension = os.path.splitext(file_path)[1]
                    csv_data.append([file_name, file_path, file_extension, folder, f"Inappropriate {category} file"])

            if csv_data:
                if not os.path.exists(os.path.dirname(csv_filename)):
                    os.makedirs(os.path.dirname(csv_filename))

                with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(['File Name', 'File Path', 'File Extension', 'Folder', 'Status'])
                    csv_writer.writerows(csv_data)

                if os.path.exists(csv_filename):
                    print(f"\n{f_success}Detailed information exported to '{csv_filename}' successfully.{f_default}")
                    open_csv_in_excel(csv_filename)
                else:
                    print(f"{f_warning}Failed to export to CSV file.{f_default}")
            else:
                print("No data to export.")
        else:
            print("CSV export cancelled.")

def list_inappropriate_files_in_static_archive(summary=False, detailed=False):
    inappropriate_static_audio_files = list_files(config['paths']['static_audio_root'], recursive=True, include=None, exclude=audio_files)
    inappropriate_static_document_files = list_files(config['paths']['static_document_root'], recursive=True, include=None, exclude=document_files)
    inappropriate_static_image_files = list_files(config['paths']['static_image_root'], recursive=True, include=None, exclude=image_files)
    inappropriate_static_video_files = list_files(config['paths']['static_video_root'], recursive=True, include=None, exclude=video_files)

    result = {}

    if summary:
        result['audio_summary'] = {}
        result['document_summary'] = {}
        result['image_summary'] = {}
        result['video_summary'] = {}

        # Function to count file extensions
        def count_extensions(files):
            extension_count = {}
            for file in files:
                extension = os.path.splitext(file)[1]
                extension_count[extension] = extension_count.get(extension, 0) + 1
            return extension_count

        result['audio_summary'] = count_extensions(inappropriate_static_audio_files)
        result['document_summary'] = count_extensions(inappropriate_static_document_files)
        result['image_summary'] = count_extensions(inappropriate_static_image_files)
        result['video_summary'] = count_extensions(inappropriate_static_video_files)

    elif detailed:
        result['audio_detailed'] = inappropriate_static_audio_files
        result['document_detailed'] = inappropriate_static_document_files
        result['image_detailed'] = inappropriate_static_image_files
        result['video_detailed'] = inappropriate_static_video_files

    return result

def list_inappropriate_files_in_live_archive(summary=False, detailed=False):
    inappropriate_live_audio_files = list_files(config['paths']['live_audio_root'], recursive=True, include=None, exclude=["ini","xmp","3gp"])
    inappropriate_live_document_files = list_files(config['paths']['live_document_root'], recursive=True, include=None, exclude=["ini","xmp","pdf"])
    inappropriate_live_image_files = list_files(config['paths']['live_image_root'], recursive=True, include=None, exclude=["ini","xmp","jpg"])
    inappropriate_live_video_files = list_files(config['paths']['live_video_root'], recursive=True, include=None, exclude=["ini","xmp","mp4"])

    result = {}

    if summary:
        result['audio_summary'] = {}
        result['document_summary'] = {}
        result['image_summary'] = {}
        result['video_summary'] = {}

        # Function to count file extensions
        def count_extensions(files):
            extension_count = {}
            for file in files:
                extension = os.path.splitext(file)[1]
                extension_count[extension] = extension_count.get(extension, 0) + 1
            return extension_count

        result['audio_summary'] = count_extensions(inappropriate_live_audio_files)
        result['document_summary'] = count_extensions(inappropriate_live_document_files)
        result['image_summary'] = count_extensions(inappropriate_live_image_files)
        result['video_summary'] = count_extensions(inappropriate_live_video_files)

    elif detailed:
        result['audio_detailed'] = inappropriate_live_audio_files
        result['document_detailed'] = inappropriate_live_document_files
        result['image_detailed'] = inappropriate_live_image_files
        result['video_detailed'] = inappropriate_live_video_files

    return result

def inappropriate_file_review():
    os.system("cls")
    print("Static Archive File Review:")
    inapropriate_static_file_summary = list_inappropriate_files_in_static_archive(summary=True)
    print_summary(inapropriate_static_file_summary)
    static_details = input(f"{f_input}Do you want to view file details? (Y/N){f_default}")

    if static_details.lower() == "y":
        os.system("cls")
        inapropriate_static_file_details = list_inappropriate_files_in_static_archive(detailed=True)
        print_detailed_with_csv(inapropriate_static_file_details, export_to_csv=True)

    os.system("cls")
    print("Live Archive File Review:")
    inapropriate_live_file_summary = list_inappropriate_files_in_live_archive(summary=True)
    print_summary(inapropriate_live_file_summary)
    live_details = input(f"{f_input}Do you want to view file details? (Y/N){f_default}")

    if live_details.lower() == "y":
        os.system("cls")
        inapropriate_live_file_details = list_inappropriate_files_in_live_archive(detailed=True)
        print_detailed_with_csv(inapropriate_live_file_details, export_to_csv=True)

# ################################################################
# Check for file types that don't belong in archive folders ######
# ################################################################
# END


validation_options_menu_list = [
    "List File Types",
    "Find Inappropriate Files",
    # "Synch Files",
    # "Rename Static Archive Based on Live Archive",
    # "convert all live-archive file names to lower case",
    # "Remove Unnecessary files",
    # "Use option 5 for current validation test"
]


def validation_menu(validation_options_menu_list):
    
    while True:
        os.system("cls")
        print("Validation Menu:")
        print("----------------")
        for idx, option in enumerate(validation_options_menu_list, start=1):
            print(f"{idx}. {option}")
        print("---------------")
        validation_choice = input(f"{f_input}Select option 1-3: {f_default}")
        
        if validation_choice == "1":
            os.system("cls")
            live_folder_types = count_file_extensions_sorted(config['paths']['live_folder'])
            print("\nLive Archive File Extensions:")
            print("-----------------------------")
            for extension, count in live_folder_types:
                print(f"Extension: {extension}, Count: {count:,}")
            static_folder_types = count_file_extensions_sorted(config['paths']['static_folder'])
            print("\n\nStatic Archive File Extensions:")
            print("-------------------------------")
            for extension, count in static_folder_types:
                print(f"Extension: {extension}, Count: {count:,}")
            input(f"{f_input}Press 'Enter' to continue.{f_default}")

        elif validation_choice == "2":
            os.system("cls")
            inappropriate_file_review()
            input(f"{f_input}Press 'Enter' to continue.{f_default}")



        # elif validation_choice == "2":
        #     os.system("cls")
        #     # archive_validation()
        #     input(f"{f_input}Press 'Enter' to continue.{f_default}")
        # elif validation_choice == "3":
        #     os.system("cls")
        #     compare_and_rename_files(config['paths']['live_folder'], config['paths']['static_folder'])
        #     input(f"{f_input}Press 'Enter' to continue.{f_default}")
        elif validation_choice == "4":
            os.system("cls")

            invalid_files = find_invalid_files(config['paths']['live_folder'], "live-archive", create_csv=False, display_reason=True)
            if invalid_files:
                print(f"\n\nThere are {len(invalid_files)} files in the Live Archive that failed validation:")
                delete_files(invalid_files, prompt=True)
                # for file in invalid_files:
                    # print(file)
                # delete_option = input(f"{f_input}Prompt before deleting? (Y/N): {f_default}")
                # if delete_option.lower() == "y":
                    # process_files(invalid_files, "delete", "live-archive", prompt=True)

                # elif delete_option.lower() == "n":
                    # process_files(invalid_files, "delete", "live-archive", prompt=False)
                # else:
                    # continue
            else:
                print(f"{f_success}No invalid files found in the Live Archive.{f_default}")

            invalid_files = find_invalid_files(config['paths']['static_folder'], "static-archive", create_csv=False, display_reason=True)
            if invalid_files:
                # print(f"There are {len(invalid_files)} files in the Live Archive that failed validation:")
                print(f"\n\nThere are {len(invalid_files)} files in the Static Archive that failed validation:")
                # for file in invalid_files:
                #     print(file)
                delete_option = input(f"{f_input}Prompt before deleting? (Y/N): {f_default}")
                if delete_option.lower() == "y":
                    process_files(invalid_files, "delete", "static-archive", prompt=True)
                elif delete_option.lower() == "n":
                    process_files(invalid_files, "delete", "static-archive", prompt=False)
                else:
                    continue
            print(f"{f_success}No invalid files found in the Static Archive.{f_default}")
            
            input(f"{f_input}Press 'Enter' to continue.{f_default}")

        elif validation_choice == "5":
            os.system("cls")
            # Validate Live files
            file_to_validate = list_files(config['paths']['live_folder'], recursive=True, include=None, exclude=["ini","xmp"])
            failed_validations = validate_file_name(file_to_validate)
            for file in failed_validations:
                print(file)
            print(f"{len(failed_validations)} files failed validation")
            input(f"{f_input}Press 'Enter' to continue.{f_default}")

            # Validate Static files
            file_to_validate = list_files(config['paths']['static_folder'], recursive=True, include=None, exclude=["ini","xmp"])
            failed_validations = validate_file_name(file_to_validate)
            for file in failed_validations:
                print(file)
            print(f"{len(failed_validations)} files failed validation")
            input(f"{f_input}Press 'Enter' to continue.{f_default}")

        else:
            exit()
        
    # elif validation_choice == "5":
    #     # find_files_without_identifier(config['paths']['live_folder'])
    #     static_files_to_delete = find_invalid_files(config['paths']['live_folder'], "static-archive", create_csv=False, display_reason=True)
    #     # print(static_files_to_delete)
            # for file in files_to_process:
            #     validation = validate_file_name(file)
            #     print(f"{file}  |  {validation}")
            # input(f"{f_input}Press 'Enter' to continue.{f_default}")


            # else:
            #     print(f"{f_success}No invalid files found in the Static Archive.{f_default}")

            # invalid_files = find_invalid_files(config['paths']['static_folder'], "static-archive", create_csv=False, display_reason=True)
            # if invalid_files:
            #     print(f"{f_warning}There are {len(invalid_files)} files in the Static Archive that failed validation:{f_default}")
            #     process_files(invalid_files, "delete", "static-archive", prompt=True)
            # else:
            #     print(f"{f_success}No invalid files found in the Static Archive.{f_default}")
            # input("Press 'Enter' to continue.")
        # else:
        #     exit()
        
    # elif validation_choice == "5":
    #     # find_files_without_identifier(config['paths']['live_folder'])
    #     static_files_to_delete = find_invalid_files(config['paths']['live_folder'], "static-archive", create_csv=False, display_reason=True)
    #     # print(static_files_to_delete)


# validation_menu(validation_options_menu_list)
# test = compare_file_counts(config['paths']['live_folder'], config['paths']['static_folder'])
# print_comparison_results(test)






# def clean_filenames(root_folder):
#     for dirpath, dirnames, filenames in os.walk(root_folder):
#         for filename in filenames:
#             original_file = os.path.join(dirpath, filename)
#             new_filename = re.sub(r'\s+', '-', filename.lower())  # Replace spaces with hyphens and convert to lowercase
#             new_filename = re.sub(r'[^\w\s.-]', '', new_filename)  # Keep only alphanumeric, underscore, hyphen, and period
#             new_filename = re.sub(r'_+', '_', new_filename)  # Remove multiple underscores
#             new_filename = re.sub(r'-_', '_', new_filename)  # Remove hyphen followed by underscore
#             new_filename = re.sub(r'_-', '_', new_filename)  # Remove underscore followed by hyphen
#             new_filename = re.sub(r'-\.', '.', new_filename)  # Remove hyphen before file extension

#             if new_filename != filename:
#                 new_file = os.path.join(dirpath, new_filename)
#                 os.rename(original_file, new_file)


# clean_filenames(config['paths']['static_folder'])







test2 = compare_archives(config['paths']['live_folder'], config['paths']['static_folder'], ignore_extensions=[".ini",".xmp"])

output_csv = r'c:\test\comparetest.csv'

# List of file extensions to ignore
extensions_to_ignore = ['.ini', '.xmp']

#  Compare the two folder structures
differences = compare_archives(config['paths']['live_folder'], config['paths']['static_folder'],ignore_extensions=extensions_to_ignore)
# write_diff_to_csv(test2, r"c:\test\comparetest.csv")
write_diff_to_csv(differences,output_csv)




# rename_static_filenames_with_live(config['paths']['live_folder'], config['paths']['static_folder'])