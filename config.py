import re

# START
#############################################################
# Lookup Tables #############################################
#############################################################

location_lookup = r"C:\Media Management\Scripts\Lookup Tables\Index_of_Locations.csv"
people_lookup = r"C:\Media Management\Scripts\Lookup Tables\Index_of_people.csv"

#############################################################
# Lookup Tables #############################################
#############################################################
# END


# START
#############################################################
# External Program Paths ####################################
#############################################################

exiftool_path = r"C:\Media Management\App\exiftool.exe"
exif_config_path = r"C:\Media Management\App\FamilyArchive.config"
ffmpeg_path = r"C:\Media Management\App\ffmpeg\bin\ffmpeg.exe"
ImageMagick_path = r"C:\Media Management\App\ImageMagick\magick.exe"

#############################################################
# External Program Paths ####################################
#############################################################
# END



# START
#############################################################
# File Renaming Patterns ####################################
#############################################################

rename_rules_for_archive = {
    re.compile(r'^\s+|\s+$'): '',  # Remove leading and trailing spaces
    re.compile(r'\s+'): ' ',  # Replace multiple spaces with a single space
    re.compile(r'[^a-zA-Z0-9\s]+'): '',  # Remove non-alphanumeric characters except spaces
    re.compile(r'[\s]+'): '-',  # Replace all spaces with hyphens
    re.compile(r'[A-Z]'): lambda match: match.group(0).lower()  # Convert uppercase to lowercase
    }

#############################################################
# File Renaming Patterns ####################################
#############################################################
# END





# START
#############################################################
# Pre-defined metadata field lists ##########################
#############################################################

created_date_fields = [
    "EXIF:CreateDate",
    "IPTC:DateCreated",
    "Composite:DateTimeCreated",
    "XMP:CreateDate",
]
modified_date_fields = [
    "File:FileModifyDate",
    "EXIF:ModifyDate",
    "XMP:ModifyDate",
    "XMP:ModifyDate",
    "Composite:SubSecModifyDate",
]
custom_date_related_fields = [
    "XMP:DayName",
    "XMP:DayNumber",
    "XMP:Month",
    "XMP:Year",
    "XMP:Decade",
    "XMP:Century",
    "XMP:AssetDate",
    "XMP:AccurateDate",
    "XMP:Season",
]

family_names = ["Bailey","Barker","Blackstone","Boldt","Cann","Capezzuto","Carey","Chapman","del Valle","Dight","Enns","Foster","Glover","Greenwood","Hatherell","Heath","Hunter","Lemay","Loewen","Lowden","MacDonald","Mitchell","Norris","Penner","Pongracz","Rand","Skinner","Smith","Stibbe","Trott","Wardle","Winberg","Woods"]


Location_fields = ["XMP:Location","XMP:LocationCreatedLocationName","XMP:LocationCreatedSublocation","XMP:LocationShownLocationName","XMP:LocationShownSublocation"]

city_fields = ["IPTC:City","XMP:LocationCreatedCity","XMP:LocationShownCity","XMP:City"]

state_fields = ["IPTC:Province-State","XMP:LocationCreatedProvinceState","XMP:LocationShownProvinceState","XMP:State"]

country_fields = ["XMP:Country","XMP:LocationCreatedCountryName","XMP:LocationShownCountryName"]

# country_code_fields = ["IPTC:Country-PrimaryLocationCode","XMP:CountryCode","XMP:LocationCreatedCountryCode","XMP:LocationShownCountryCode"]
country_code_fields = ["XMP:CountryCode","XMP:LocationCreatedCountryCode","XMP:LocationShownCountryCode"]

gps_fields = ["EXIF:GPSLatitude","EXIF:GPSLatitudeRef","EXIF:GPSLongitude","EXIF:GPSLongitudeRef"]
# gps_fields = ["EXIF:GPSLatitude","EXIF:GPSLatitudeRef","EXIF:GPSLongitude","EXIF:GPSLongitudeRef","GPS:GPSLatitude","GPS:GPSLongitude","XMP:GPSLatitude","XMP:GPSLongitude"]

locality_fields = ["XMP:LocalityGeneral","XMP:LocalitySpecific","XMP:LocalityType"]

all_location_fields = Location_fields + city_fields + state_fields + country_code_fields + country_code_fields + gps_fields + locality_fields

people_fields = ["XMP:RegionName"]

sourcefile = ["SourceFile"]

# Fields to transfer from photos to videos if careate date for videos are found in close proximity
photo_to_video_fields = sourcefile + Location_fields + city_fields + state_fields + country_code_fields + country_code_fields + gps_fields + locality_fields + people_fields + created_date_fields

#############################################################
# Pre-defined metadata field lists ##########################
#############################################################
# EMD



# START
#############################################################
# Set Validation Rules ######################################
#############################################################

filename_validation_rules = {
    #  'File path must be between 2 and 250 characters.'
    'path_name_length': re.compile(r'^.{2,250}$'),
    #  'Date must be YYYYMMDD/x.'
    'date_prefix': re.compile(r'^[12][\dx]{3}[01x][\dx][0-3x][\dx][cpem]$'),
    # 'Title must be lower case and contain alphanumeric or hyphens only.',
    'title': re.compile(r'^[a-z0-9-]+$'), 
    #  'GUID must be a 10-digit number.'
    'guid': re.compile(r'^[0-9]{10}$')
}

# This is how long the file name's title should be.
asset_title_length = 80

# This is how long the file name's unique ID should be
guid_length = 10

#############################################################
# Set Validation Rules ######################################
#############################################################
# END



# START
#############################################################
# Set ACDSEE Parser Rules ###################################
#############################################################

acdsee_parser = {

    "XMP:SetTitle01": r".*Collections<Category Assigned=.\d.>([^<]+)<.*",
    "XMP:SetSubTitle01": r".*Collections<Category Assigned=.\d.>[^<]+<Category Assigned=.\d.>([^<]+)<.*",
    "XMP:SetTitle02": r".*Collections<Category Assigned=.\d.>[^<]+<Category Assigned=.\d.>[^<]+<\/Category><\/Category><Category Assigned=.\d.>([^<]+)<.*",
    "XMP:SetSubTitle02": r".*Collections<Category Assigned=.\d.>[^<]+<Category Assigned=.\d.>[^<]+<\/Category><\/Category><Category Assigned=.\d.>[^<]+<Category Assigned=.\d.>([^<]+)<.*",
    "XMP:SetTitle03": r"",
    "XMP:SetSubTitle03": r"",

# Event Patterns

    "XMP:Event01": r".*>Event<Category Assigned=.\d.>([^<]+)<.*",
    "XMP:BirthdayName": r".*>Birthday<Category Assigned=.\d.>([^<]+)<.*",
    "XMP:HolidayName": r".*Holiday<Category Assigned=.\d.>([^<]+)<.*",
    "XMP:SchoolGrade": r".*Grade<Category Assigned=.\d.>([^<]+)<.*",
    "XMP:SchoolEvent": r".*School Event<Category Assigned=.\d.>([^<]+)<.*",

# # Date Patterns
#     "XMP:DayNumber": r".*>Numbered Days<Category Assigned=.\d.>([^<]+)<.*",
#     "XMP:DayName": r".*>Named Days<Category Assigned=.\d.>([^<]+)<.*",
#     "XMP:Month": r".*Dates<Category Assigned=.\d.>\d{4}-\d{4}<Category Assigned=.\d.>\d{4}s<Category Assigned=.\d.>\d{4}<Category Assigned=.\d.>([^<]+)<.*",
#     "XMP:Year": r".*Dates<Category Assigned=.\d.>\d{4}-\d{4}<Category Assigned=.\d.>\d{4}s<Category Assigned=.\d.>(\d{4})<.*",
#     "XMP:Decade": r".*Dates<Category Assigned=.\d.>\d{4}-\d{4}<Category Assigned=.\d.>(\d{4}s)<.*",
#     "XMP:Century": r".*Dates<Category Assigned=.\d.>(\d{4}-\d{4})<.*",

# # Media Type Patterns
#     "XMP:MediaType": r".*>Media Type<Category Assigned=.\d.>([^<]+)<.*",
#     "XMP:GraphicType": r".*>Media Type<Category Assigned=.\d.>[^<]+<Category Assigned=.\d.>([^<]+)<.*",
#     "XMP:ShotOrientation": r".*>Orientation<Category Assigned=.\d.>([^<]+)<.*",
#     "XMP:ShotType": r".*>Shot Type<Category Assigned=.\d.>([^<]+)<.*",

# # Location Patterns
#     "XMP:LocationCreatedLocationName": r".*>Community<Category Assigned=.\d.>[^<]+<Category Assigned=.\d.>([^<]+)<.*",
#     "XMP:LocationCreatedCity": r".*>Community<Category Assigned=.\d.>([^<]+)<.*",
#     "XMP:LocationCreatedProvinceState": r".*>Country<Category Assigned=.\d.>[^<]+<Category Assigned=.\d.>([^<]+)<.*",
#     "XMP:LocationCreatedCountryName": r".*>Country<Category Assigned=.\d.>([^<]+)<Category Assigned=.\d.>[^<]+<.*",
#     "XMP:LocalityGeneral": r".*>Locality<Category Assigned=.\d.>([^<]+).*",
#     "XMP:LocalityType": r".*>Locality<Category Assigned=.\d.>[^<]+<Category Assigned=.\d.>([^<]+)<.*",
#     "XMP:LocalitySpecific": r".*>Locality<Category Assigned=.\d.>[^<]+<Category Assigned=.\d.>[^<]+<Category Assigned=.\d.>([^<]+).*",
}

#############################################################
# Set ACDSEE Parser Rules ###################################
#############################################################
# END



# START
#############################################################
# Set File Types by Extension ###############################
#############################################################

live_archive_file_extensions = ["3gp", "jpg", "mp4", "pdf"]

audio_files = [
    "3gp", "aac", "ac3", "aif", "aiff", "alac", "amr", "ape", "au", 
    "caf", "cfa", "dsf", "dts", "essentialsound", "flac", "gsm", "hca", 
    "m3u", "m4a", "m4r", "mid", "midi", "mka", "mp1", "mp2", "mp3", 
    "mpa", "ny", "ogg", "opus", "pcm", "ra", "sequ", "sesx", "sid", 
    "snd", "spx", "tta", "ult", "vlt", "voc", "vox", "wav", "wma", 
    "wv"
]
document_files = [
    "csv", "djvu", "doc", "docm", "docx", "dot", "dotm", "dotx", 
    "glox", "idlk", "idml", "indd", "inx", "mif", "mdi", "md", "mpp", 
    "mmp", "mxd", "o18", "odt", "ods", "oft", "one", "onetoc2", "pap", 
    "pdm", "pdx", "pmd", "pdf", "pptx", "prn", "pub", "rtf", "sdw", 
    "template", "tex", "thmx", "tlx", "tpl", "txt", "wbk", "wpd", "xps", "xls", 
    "xlsx"
]


archive_document_files = [
    "csv", "doc", "docm", "docx", "dot", "dotm", "dotx", 
    "odt", "ods", "oft", "pdf", "pptx", "rtf", "xls", 
    "xlsx"
]


image_files = [
    "8bf", "ai", "arw", "bmp", "cdr", "cr2", "cr3", "cvs", "dds", 
    "dng", "ecw", "emf", "eps", "exr", "gif", "hdr", "heic", "heif", 
    "jfif", "j2k", "jpe", "jpeg", "jpg", "jp2", "jpf", "jxr", "kra", 
    "mvg", "nef", "ora", "pcx", "pct", "pgm", "png", "ppm", "psb", "psd", 
    "psp", "pspimage", "raw", "rtn", "sgi", "sr2", "srf", "svg", "thm", 
    "tga", "tif", "tiff", "webp", "wpx", "wmf", "xbm", "xpm"
]
video_files = [
    "3g2", "3gp", "amv", "asf", "asx", "avi", "avchd", "bik", "divx", 
    "drc", "dvr", "f4v", "flv", "fli", "gxf", "m2t", "m2ts", "m4v", 
    "mkv", "mod", "mov", "mp2v", "mp4", "mpeg", "mpg", "mpg2", "mpg4", 
    "mts", "mxf", "ogm", "ogv", "prproj", "qt", "r3d", "rm", "rme", 
    "rmm", "rmp", "rmvb", "rpl", "rv", "rvc", "swf", "tod", "ts", 
    "vob", "vro", "webm", "wlmp", "wmv", "xesc", "xfl", "xvid", "yt", 
    "ytf", "yuv"
]

all_media_files = audio_files + archive_document_files + image_files + video_files

#############################################################
# Set File Types by Extension ###############################
#############################################################
# END



# START
#############################################################
# Set ANSII Color Codes #####################################
#############################################################

# use this to set colors on text output to the console
def set_color(text_style, text_color, bacground_color):
    text_styles = {
        "default": "0",
        "bold": "1",
        "underline": "2",
        "italic": "3",
        "none": "5",
    }

    text_colors = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "purple": "35",
        "cyan": "36",
        "white": "37",
    }

    text_background_colors = {
        "black": "40",
        "red": "41",
        "green": "42",
        "yellow": "43",
        "blue": "44",
        "purple": "45",
        "cyan": "46",
        "white": "47",
    }

    style = text_styles[text_style]
    color = text_colors[text_color]
    bacground = text_background_colors[bacground_color]

    ascii_color = f"\033[;{style};{color};{bacground}m"
    print(ascii_color)

    return ascii_color

# Set ascii output colors
f_warning = set_color("default", "red", "black")
f_input = set_color("default", "yellow", "black")
f_success = set_color("default", "green", "black")
f_info = set_color("default", "blue", "black")
f_default = set_color("default", "white", "black")


#############################################################
# Set ANSII Color Codes #####################################
#############################################################
# EMD


# START
#############################################################
# Set Archive Paths #########################################
#############################################################

archive_paths = {
  "prep_path": "D:\\0_Media-Archive\\02_metadata-and-rename",
  "prep_static_path": "D:\\0_Media-Archive\\02_metadata-and-rename\\static-archive",
  "prep_live_path": "D:\\0_Media-Archive\\02_metadata-and-rename\\live-archive",
}
#############################################################
# Set Archive Paths #########################################
#############################################################
# END