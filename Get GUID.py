import os 
import csv
import shutil
from PIL import Image
import subprocess

live_archive_path = r"D:\0_Media-Archive\03_archive\live-archive"
static_archive_path = r"D:\0_Media-Archive\03_archive\static-archive2"

def convert_to_jpg(image_path, output_path):
    # Open the image using PIL
    try:
        img = Image.open(image_path)
        # Convert and save the image as JPEG
        img = img.convert("RGB")
        img.save(output_path, "JPEG")
        return True
    except Exception as e:
        print(f"Error converting image: {e}")
        return False
    
def convert_to_h264(input_video_path, output_video_path):
    try:
        # Use ffmpeg command to convert video to H.264 MP4
        subprocess.run(['ffmpeg', '-i', input_video_path, '-c:v', 'libx264', output_video_path])
        return True
    except Exception as e:
        print(f"Error converting video: {e}")
        return False

def convert_to_3gp(input_audio_path, output_audio_path):
    try:
        # Use ffmpeg command to convert audio to 3GP
        subprocess.run(['ffmpeg', '-i', input_audio_path, '-c:a', 'amr_nb', '-strict', 'experimental', output_audio_path])
        return True
    except Exception as e:
        print(f"Error converting audio: {e}")
        return False

def find_invalid_files(folder, archive_type, create_csv=False, display_reason=True):
    csv_output_path = r"D:\0_Media-Archive\Validation_Report.csv"
    invalid_files = []
    allowed_extensions_live = {"pdf", "3gp", "jpg", "mp4"}

    csv_columns = ['File_Path', 'File_Name', 'Extension', 'Reason']
    csv_rows = []

    for root, _, files in os.walk(folder):
        for file_name in files:
            parts = file_name.split('_')
            if len(parts) == 3:
                date_part = parts[0]
                title_part = parts[1]
                identifier_part = parts[2].split('.')[0]

                failure_reason = ''

                # Rule 1: Date format validation
                if not (len(date_part) == 10 and date_part[:8].isdigit() and
                        date_part[8] in ("c", "m", "e", "m") and date_part[9] == "x"):
                    failure_reason += 'Invalid date format. '

                # Rule 2: Title validation
                if not (1 <= len(title_part) <= 80 and title_part.islower() and
                        title_part.isalnum() and '-' in title_part):
                    failure_reason += 'Invalid title format. '

                # Rule 3: Identifier validation
                if not (len(identifier_part) == 10 and identifier_part.isdigit()):
                    failure_reason += 'Invalid identifier format. '

                # Rule 4: File extension validation for live-archive
                if archive_type == "live-archive":
                    file_extension = parts[2].split('.')[-1]
                    if file_extension not in allowed_extensions_live:
                        failure_reason += 'Invalid file extension for live-archive. '

                if failure_reason:
                    invalid_file_path = os.path.join(root, file_name)
                    invalid_files.append(invalid_file_path)

                    # Save details for CSV file
                    if create_csv:
                        extension = parts[2].split('.')[-1]
                        csv_rows.append({'File_Path': invalid_file_path,
                                         'File_Name': file_name,
                                         'Extension': extension,
                                         'Reason': failure_reason})

                    # Display reason to terminal if requested
                    if display_reason:
                        print(f"File: {invalid_file_path} | Reason: {failure_reason}")

    # Write to CSV file if requested
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

def delete_files(file_list):
    for file_path in file_list:
        print(f"File without a 10-digit identifier: {file_path}")
        response = input("Do you want to delete this file? (y/n): ")
        if response.lower() == 'y':
            try:
                os.remove(file_path)
                print(f"File deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

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
            new_static_path = os.path.join(static_folder, new_static_name)
            old_static_path = os.path.join(static_folder, file_name)
            shutil.move(old_static_path, new_static_path)
            print(f"Renamed {file_name} to {new_static_name}")

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

def compare_file_counts(live_folder, static_folder):
    live_files = set()
    static_files = set()

    # Collect unique identifiers from files in live-archive folder
    for root, dirs, files in os.walk(live_folder):
        for file_name in files:
            parts = file_name.split('_')
            if len(parts) >= 3:
                identifier = parts[-1].split('.')[0]
                live_files.add(identifier)

    # Collect unique identifiers from files in static-archive folder
    for root, dirs, files in os.walk(static_folder):
        for file_name in files:
            parts = file_name.split('_')
            if len(parts) >= 3:
                identifier = parts[-1].split('.')[0]
                static_files.add(identifier)

    # Compare the number of unique identifiers in both folders
    live_count = len(live_files)
    static_count = len(static_files)

    if live_count == static_count:
        return True, live_count, static_count
    else:
        return False, live_count, static_count

def archive_validation():
    archive_comparison = compare_file_counts(live_archive_path, static_archive_path)
    live_count = archive_comparison[1]
    static_count = archive_comparison[2]
    if archive_comparison[0] == True:
        print(f"Live archive and static archive both contain {live_count} files.")
    else:
        print(f"File count mismatch between live archive ({live_count}) and static archive ({static_count}).")
        syncy_archives = input(f"Attempt to synch live and static archives? 'Y/N'")
        if syncy_archives.lower() == "y":
            synchronize_folders(live_archive_path, static_archive_path)



def validation_menu(options):
    print("Validation Menu:")
    for idx, option in enumerate(options, start=1):
        print(f"{idx}. {option}")
    validation_choice = input("Select option 1-3: ")
    print("---------------")
    if validation_choice == "1":
        live_folder_types = count_file_extensions_sorted(live_archive_path)
        print("\nLive Archive File Extensions:")
        print("-----------------------------")
        for extension, count in live_folder_types:
            print(f"Extension: {extension}, Count: {count}")
        static_folder_types = count_file_extensions_sorted(static_archive_path)
        print("\n\nStatic Archive File Extensions:")
        print("-------------------------------")
        for extension, count in static_folder_types:
            print(f"Extension: {extension}, Count: {count}")
    elif validation_choice == "2":
        archive_validation()
    elif validation_choice == "3":
        compare_and_rename_files(live_archive_path, static_archive_path)
    elif validation_choice == "4":
        # find_files_without_identifier(live_archive_path)
        static_files_to_delete = find_files_without_identifier(static_archive_path)
        delete_files(static_files_to_delete)



# live_archive_path = r"D:\0_Media-Archive\03_archive\live-archive"
# static_archive_path = r"D:\0_Media-Archive\03_archive\static-archive"


validation_options_menu_list = [
    "List File Types",
    "Synch Files",
    "Rename Static Archive Based on Live Archive",
    "Remove Unnecessary files"
]

validation_menu(validation_options_menu_list)
