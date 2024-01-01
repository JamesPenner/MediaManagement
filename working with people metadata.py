import sys
sys.path.append(r'C:\Media Management\Scripts')
import exiftool
import subprocess
from metadata_manager import Metadata_Manager
from file_handler import FileHandler
from config import  f_warning, f_info, f_success, f_default, exiftool_path, exif_config_path

# search_folder = r'D:\0_Media-Archive\test-delete\1890s'
search_folder = r'D:\0_Media-Archive\test-delete'
# search_folder = r'D:\0_Media-Archive\03_archive\live-archive\Photos'



def get_list_of_files(search_folder, recursive, extensions):
    # Instantiate the FileHandler
    file_handler = FileHandler()

    return file_handler.retrieve_file_list(search_folder, recursive, extensions)

def update_people_descriptions_o():

    with exiftool.ExifToolHelper() as et:
        total_files = len(file_list)
        file_count = 0
        for file in file_list:

            file_count += 1
            updated_dict = {}
          
            try:
                etmetadata = et.get_metadata([file])
            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)

            people_dict = mm.extract_person_names()
            print(people_dict)
            
            try:
                et.set_tags(file, people_dict)
                print(f"{f_success}File {file_count} of {total_files} | {f_success}{file} Updated{f_default}")
                # print(asdf)
            except:
                # Run the command using subprocess
                try:
                    update = FileHandler.generate_exiftool_command(people_dict, file)
                    subprocess.run(update, check=True)
                    print(f"{f_success}File {file_count} of {total_files} | {f_success}{file} Updated by subprocess{f_default}")
                    # print(update)
                except subprocess.CalledProcessError as e:
                    print(f"Error executing ExifTool command: {e}")
                    print(f"{f_warning}File {file_count} of {total_files} | {f_success}{file} Can't be Updated{f_default}")


def get_acdsee_metadata():
    file_handler = FileHandler()
    with exiftool.ExifToolHelper() as et:

        total_files = len(file_list)
        file_count = 0
        for file in file_list:

            file_count += 1
            updated_dict = {}
          
            try:
                etmetadata = et.get_metadata([file])
            except:
                print(f"{f_warning}Cannot read metadata for: {file}{f_default}")
                continue  # Skip to the next file on error

            mm = Metadata_Manager(etmetadata)

            acdsee_dict = mm.parse_xmp_categories()

            # Instantiate the file handler
            file_handler = FileHandler()
            # Create Exiftool command
            update = file_handler.generate_exiftool_command(acdsee_dict, file)
            # Run SubProcess
            subprocess.run(update, check=True)
            # Print results to terminal
            print(f"{f_success}File {file_count} of {total_files} | {f_success}{file} Updated by subprocess{f_default}")


            # print(file)
            print(acdsee_dict)
            # print(etmetadata)
            
            # try:
            #     et.set_tags(file, people_dict)
            #     print(f"{f_success}File {file_count} of {total_files} | {f_success}{file} Updated{f_default}")
            #     # print(type(test_dict))
            #     # print(test_dict)
            
            # except:
            #     # Run the command using subprocess
            #     try:
            #         update = create_metadata_command(exiftool_path, exif_config_path, people_dict, file)
            #         subprocess.run(update, check=True)
            #         print(f"{f_success}File {file_count} of {total_files} | {f_success}{file} Updated by subprocess{f_default}")
            #         # print(update)
            #     except subprocess.CalledProcessError as e:
            #         print(f"Error executing ExifTool command: {e}")
            #         print(f"{f_warning}File {file_count} of {total_files} | {f_success}{file} Can't be Updated{f_default}")




# get list of image files
file_list = get_list_of_files(search_folder, recursive=True, extensions=["jpg","jpeg"])


# update_people_descriptions()
# 
get_acdsee_metadata()