import os
# import magic
from wand.image import Image
import sys
from enum import Enum
import subprocess

sys.path.append(r'C:\Users\Windows\Dropbox\James\Python\01_Media Archive Scripts')
from config import exiftool_path, exif_config_path, ffmpeg_path, ImageMagick_path


def convert_ai_to_jpg(input_file, output_file):
    try:
        with Image(filename=input_file, resolution=300) as img:
            img.format = 'jpeg'
            img.save(filename=output_file)
        print(f"Conversion successful: {output_file}")
    except Exception as e:
        print(f"Error during conversion: {e}")




def _create_directory_if_not_exists(path):
    try:
        # Check if the path exists and is a directory
        if os.path.isdir(path):
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"Created directory: {path}")
            else:
                print(f"Directory already exists: {path}")
        else:  # If it's a file path, extract directory and create it if it doesn't exist
            directory_path = os.path.dirname(path)
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
                print(f"Created directory: {directory_path}")
            else:
                print(f"Directory already exists: {directory_path}")
    except Exception as e:
        print(f"Error: {e}. Failed to create the directory.")

# Define file type categories as an enum
class FileCategory(Enum):
    RASTER_IMAGE = "Raster Images"
    VECTOR_IMAGE = "Vector Images"
    DOCUMENT = "Documents"
    VIDEO = "Videos"
    AUDIO = "Audio"
    EXECUTABLE = "Executables"
    ARCHIVE = "Archives"
    DATA = "Data"
    SYSTEM = "System"
    LOG_FILE = "Log Files"
    OTHER = "Other"

# Define conversion functions
def convert_video_to_h264_mp4(source_path, target_path):
    _create_directory_if_not_exists(target_path)
    # Use ffmpeg to convert video and include metadata transfer
    subprocess.run([ffmpeg_path, "-i", source_path, "-c:v", "libx264", "-c:a", "aac", "-map_metadata", "0", target_path])

def convert_image_to_jpg(source_path, target_path, ImageMagick_path="C:\\Media Management\\App\\ImageMagick\\magick.exe"):
    _create_directory_if_not_exists(os.path.dirname(target_path))
    
    # Build the ImageMagick command
    command = [ImageMagick_path, source_path, "-flatten", "-quality", "95", target_path]
    
    try:
        # Run the command and capture output
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Converting {source_path} to {target_path} - Flattened")
    except subprocess.CalledProcessError as e:
        # Print error details
        print(f"Error converting {source_path} to {target_path}")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.output.decode('utf-8')}")
        print(f"Error output: {e.stderr.decode('utf-8')}")

def convert_document_to_pdf(source_path, target_path):
    _create_directory_if_not_exists(target_path)
    # Use LibreOffice to convert document
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf:writer_pdf_Export", source_path, "--outdir", os.path.dirname(target_path)])

def convert_audio_to_3gp(source_path, target_path):
    _create_directory_if_not_exists(target_path)
    # Use ffmpeg to convert audio
    subprocess.run([ffmpeg_path, "-i", source_path, "-c:a", "libfaac", "-b:a", "128k", "-map_metadata", "0", target_path])

# Define file type map with conversion functions
file_type_map = {
    # Raster images
    (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"): (FileCategory.RASTER_IMAGE, convert_image_to_jpg),
    # Vector images
    (".svg", ".eps", ".ai"): (FileCategory.VECTOR_IMAGE, convert_image_to_jpg),
    # Videos
    (".mp4", ".mov", ".avi", ".wmv", ".flv"): (FileCategory.VIDEO, convert_video_to_h264_mp4),
    # Documents
    (".txt", ".doc", ".docx", ".pdf", ".odt", ".rtf"): (FileCategory.DOCUMENT, convert_document_to_pdf),
    # Audio
    (".mp3", ".wav", ".flac", ".aac", ".ogg"): (FileCategory.AUDIO, convert_audio_to_3gp),
}

# Initialize magic library for mimetype detection
# mime = magic.Magic(mime=True)

def detect_file_type(filepath):
    """
    Detects the file type and category of a given file.

    Args:
        filepath: Path to the file.

    Returns:
        A tuple containing the detected file category, file extension, and conversion function,
        or None if the file type cannot be determined.
    """
    # Get file extension
    ext = os.path.splitext(filepath)[1].lower()

    # Check for known file extension mapping
    if ext in file_type_map:
        return file_type_map[ext]

    # Use magic library for mimetype detection
    mime_type = mime.from_file(filepath)

    # Map mimetype to category and conversion function
    if mime_type.startswith("image/"):
        if mime_type in ["image/svg+xml", "image/eps"]:
            return FileCategory.VECTOR_IMAGE, ext, convert_image_to_jpg
        else:
            return FileCategory.RASTER_IMAGE, ext, convert_image_to_jpg
    elif mime_type.startswith("application/"):
        # Some application types have dedicated categories and conversion functions
        if mime_type in ["application/pdf"]:
            return FileCategory.DOCUMENT, ext, None
        elif mime_type in ["application/msword", "application/vnd.ms-powerpoint"]:
            return FileCategory.DOCUMENT, ext, convert_document_to_pdf
        elif mime_type in ["application/x-zip-compressed", "application/x-rar-compressed", "application/x-tar"]:
            return FileCategory.ARCHIVE, ext, None

        # Others fall under the generic "application" category

