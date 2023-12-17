# START
#############################################################
# Lookup Tables #############################################
#############################################################

location_lookup = r"C:\Media Management\Scripts\Lookup Tables\Index_of_locations.csv"
people_lookup = r"C:\Media Management\Scripts\Lookup Tables\Index_of_people.csv"

#############################################################
# Lookup Tables #############################################
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

Location_fields = ["IPTC:Country-PrimaryLocationName","XMP:Location","XMP:LocationCreatedLocationName","XMP:LocationCreatedSublocation","XMP:LocationShownLocationName","XMP:LocationShownSublocation"]

city_fields = ["IPTC:City","XMP:LocationCreatedCity","XMP:LocationShownCity","XMP:City"]

state_fields = ["IPTC:Province-State","XMP:LocationCreatedProvinceState","XMP:LocationShownProvinceState","XMP:State"]

country_fields = ["XMP:Country","XMP:LocationCreatedCountryName","XMP:LocationShownCountryName"]

country_code_fields = ["IPTC:Country-PrimaryLocationCode","XMP:CountryCode","XMP:LocationCreatedCountryCode","XMP:LocationShownCountryCode"]

gps_fields = ["EXIF:GPSLatitude","EXIF:GPSLatitudeRef","EXIF:GPSLongitude","EXIF:GPSLongitudeRef","GPS:GPSLatitude","GPS:GPSLongitude","XMP:GPSLatitude","XMP:GPSLongitude"]

locality_fields = ["XMP:LocalityGeneral","XMP:LocalitySpecific","XMP:LocalityType",]

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
    'path_name_length': (r'^.{2,250}$', 'File path must be between 2 and 250 characters.'),
    'date_prefix': (r'^[12][\dx]{3}[01x][\dx][0-3x][\dx][cpem]$', 'Date must be YYYYMMDD/x.'),
    'title': (r'^[a-z0-9-]+$', 'Title must be lower case and contain alphanumeric or hyphens only.'),
    'guid': (r'^[0-9]{10}$', 'GUID must be a 10-digit number.'),
}

#############################################################
# Set Validation Rules ######################################
#############################################################
# END



# START
#############################################################
# Set ACDSEE Parser Rules ###################################
#############################################################

acdsee_parser = {
    "XMP:Collection2": ".*><Category Assigned=.\\d.>Collection<Category Assigned=.\\d.>[^<]+<\\/Category><Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:Collection3": ".*><Category Assigned=.\\d.>Collection<Category Assigned=.\\d.>[^<]+<\\/Category><Category Assigned=.\\d.>[^<]+<\\/Category><Category Assigned=.\\d.>([^<]+)<\\/Category><\\/Category>.*",
    "XMP:DayNumber": ".*>Numbered Days<Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:DayName": ".*>Named Days<Category Assigned=.\\d.>([^<]+)<.*",


    "XMP:Event01": ".*>Event<Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:BirthdayName": ".*>Birthday<Category Assigned=.\\d.>([^<]+)<.*",
    
    
    
    # "XMP:Event02": ".*>Named Days<Category Assigned=.\\d.>([^<]+)<.*",
    # "XMP:Event03": ".*>Named Days<Category Assigned=.\\d.>([^<]+)<.*",

    "XMP:Month": ".*Dates<Category Assigned=.\\d.>\\d{4}-\\d{4}<Category Assigned=.\\d.>\\d{4}s<Category Assigned=.\\d.>\\d{4}<Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:Year": ".*Dates<Category Assigned=.\\d.>\\d{4}-\\d{4}<Category Assigned=.\\d.>\\d{4}s<Category Assigned=.\\d.>(\\d{4})<.*",
    "XMP:Decade": ".*Dates<Category Assigned=.\\d.>\\d{4}-\\d{4}<Category Assigned=.\\d.>(\\d{4}s)<.*",
    "XMP:Century": ".*Dates<Category Assigned=.\\d.>(\\d{4}-\\d{4})<.*",
    "XMP:MediaType": ".*>Media Type<Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:GraphicType": ".*>Media Type<Category Assigned=.\\d.>[^<]+<Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:ShotOrientation": ".*>Orientation<Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:ShotType": ".*>Shot Type<Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:LocationCreatedLocationName": ".*>Community<Category Assigned=.\\d.>[^<]+<Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:LocationCreatedCity": ".*>Community<Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:LocationCreatedProvinceState": ".*>Country<Category Assigned=.\\d.>[^<]+<Category Assigned=.\\d.>([^<]+)<.*",
    "XMP:LocationCreatedCountryName": ".*>Country<Category Assigned=.\\d.>[^<]+<Category Assigned=.\\d.>([^<]+)<.*",
}

#############################################################
# Set ACDSEE Parser Rules ###################################
#############################################################
# END



# START
#############################################################
# Set File Types by Extension ###############################
#############################################################

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
f_warning = set_color("none", "red", "black")
f_input = set_color("none", "yellow", "black")
f_success = set_color("none", "green", "black")
f_default = set_color("default", "white", "black")


#############################################################
# Set ANSII Color Codes #####################################
#############################################################
# EMD