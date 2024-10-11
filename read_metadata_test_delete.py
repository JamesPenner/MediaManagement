import subprocess
from typing import Union, List, Optional

def read_metadata_with_exiftool(file_paths: Union[str, List[str]], fields: Optional[List[str]] = None, batch_size: int = 10) -> List[dict]:
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    # Prepare base command
    command = ["C:\\Media Management\\App\\exiftool", "-a"]
    metadata_list = []

    # Loop through file paths in batches
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i + batch_size]
        
        # Add files to the command
        command.extend(batch)

        # If specific fields are requested, add them to the command
        if fields:
            command.extend([f"-{field}" for field in fields])

        try:
            # Run the command and capture output
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("Raw Output:", result.stdout)  # Print raw output for debugging

            # Parse the output into lines
            output_lines = result.stdout.strip().splitlines()
            
            # Create a dictionary for each line of output
            for line in output_lines:
                parts = line.split(': ', 1)
                if len(parts) == 2:
                    metadata_list.append({parts[0].strip(): parts[1].strip()})

        except subprocess.CalledProcessError as e:
            print(f"Error processing batch: {e.stderr}")

        finally:
            # Reset the command for the next batch
            command = ["C:\\Media Management\\App\\exiftool", "-a"]

    return metadata_list

# Example usage
if __name__ == "__main__":
    file_path = "C:\\Media Management\\Tools\\03_Metadata\\test\\199612xxc_christmas_0000004154.jpg"
    metadata = read_metadata_with_exiftool(file_path, fields="Keywords")
    print("Metadata:", metadata)
