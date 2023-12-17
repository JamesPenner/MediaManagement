import os
import magic
from enum import Enum
import subprocess

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
    # Use ffmpeg to convert video
    subprocess.run(["ffmpeg", "-i", source_path, "-c:v", "libx264", "-c:a", "aac", target_path])

def convert_image_to_jpg(source_path, target_path):
    # Use ImageMagick to convert image
    subprocess.run(["convert", "-quality", "95", source_path, target_path])

def convert_document_to_pdf(source_path, target_path):
    # Use LibreOffice to convert document
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf:writer_pdf_Export", source_path, "--outdir", os.path.dirname(target_path)])

def convert_audio_to_3gp(source_path, target_path):
    # Use ffmpeg to convert audio
    subprocess.run(["ffmpeg", "-i", source_path, "-c:a", "libfaac", "-b:a", "128k", target_path])

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
mime = magic.Magic(mime=True)

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
