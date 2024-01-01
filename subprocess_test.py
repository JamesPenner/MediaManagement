import subprocess

exiftool_path = r"C:\Media Management\App\exiftool.exe"
config_path = r"C:\Media Management\App\FamilyArchive.config"
file_path = r"file path"

# data_dict = {
#     'XMP-FamilyArchive:FamilyName08': 'this is a test',
#     # Add more field name-value pairs as needed
# }

data_dict = {'XMP:FamilyName01': 'Carey', 'XMP:MarriedName01': 'Barker', 'XMP:PersonGroup01': 'Elsie Mae Barker (Carey)', 'XMP:FamilyName02': 'Hunter', 'XMP:MarriedName02': 'Capezzuto', 'XMP:PersonGroup02': 'Sandra Capezzuto (Hunter)', 'XMP:FamilyName03': 'Penner', 'XMP:MarriedName03': '', 'XMP:PersonGroup03': 'James Peter Penner', 'XMP:FamilyName04': 'Barker', 'XMP:MarriedName04': '', 'XMP:PersonGroup04': 'Rick Barker', 'XMP:FamilyName05': 'Skinner', 'XMP:MarriedName05': 'Barker', 'XMP:PersonGroup05': 'Connie Barker (Skinner)', 'XMP:Person01': 'James Peter Penner', 'XMP:Person02': 'Sandra Capezzuto (Hunter)', 'XMP:Person03': 'Elsie Mae Barker (Carey)', 'XMP:Person04': 'Rick Barker', 'XMP:Person05': 'Connie Barker (Skinner)'}


def create_metadata_command(exiftool_path, config_path, data_dict):
    command = [exiftool_path, "-config", config_path]
    
    for field, value in data_dict.items():
        command.append(f'-{field}={value}')  # Removed the quotes around {value}

    return command

# Example usage:
exiftool_path = r"C:\Media Management\App\exiftool.exe"
config_path = r"C:\Media Management\App\FamilyArchive.config"
data_dict = {
    'XMP-FamilyArchive:FamilyName01': 'Blackstone',
    # Add more field name-value pairs as needed
}

command = create_metadata_command(exiftool_path, config_path, data_dict)
print(command)  # Use the generated command in subprocess.run() or similar



# command = [
#     exiftool_path,
#     "-config",
#     config_path,
#     f'-XMP-FamilyArchive:FamilyName08="this is a test"',
#     "-m",
#     "-use",
#     "mwg",
#     "-n",
#     "-overwrite_original",
#     "-sep",
#     ", ",
#     r"D:\0_Media-Archive\test-delete\1890s\19920627c_james-peter-penner-rick-barker-elsie-mae-barker-carey-sandra-capezzuto-hunter-conni_0000003804.jpg"
# ]




# Run the command using subprocess
try:
    subprocess.run(update, check=True)
    print("ExifTool command executed successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error executing ExifTool command: {e}")