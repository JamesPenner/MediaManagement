import re
import sys
from datetime import datetime
sys.path.append(r'C:\Media Management\Scripts')
from config import created_date_fields, acdsee_parser, photo_to_video_fields

class metadata_manager:

    def __init__(self, metadata_list):
        if len(metadata_list) != 1:
            raise ValueError("Expected a list containing only one dictionary")
        self.metadata = metadata_list[0]

    def get_earliest_create_date(self):
        """
        This method returns the earliest Create Date found in the specified fields.

        Args:
            created_date_fields: A list of strings representing the metadata fields to check for Create Date.

        Returns:
            datetime object representing the earliest Create Date or None if no Create Date is found.
        """
        create_dates = []

        for field in created_date_fields:
            if field in self.metadata:
                try:
                    create_dates.append(datetime.strptime(self.metadata[field], "%Y:%m:%d %H:%M:%S%z"))
                except ValueError:
                    pass

        # Sort dates and return the earliest one
        if create_dates:
            return min(create_dates)
        else:
            return None

    def filter_metadata(self, metadata, list_of_metadata_fields):
        """
        This method returns a new dictionary containing only filtered metadata fields based on the list of metadata fields provided.

        Args:
            list_of_metadata_fields: A variable or list of strings representing the metadata fields to keep in the dictionary.

        Returns:
            A dictionary containing only the specified metadata fields.
        """
        filtered_metadata = {}

        for field in list_of_metadata_fields:
            if field in self.metadata:
                filtered_metadata[field] = self.metadata[field]

        return filtered_metadata

    def parse_xmp_categories(self):
        """
        This method parses the XMP:Categories metadata and extracts information based on provided regex patterns.

        Args:
            acdsee_parser: A dictionary where keys represent metadata fields and values represent regex expressions.

        Returns:
            A dictionary containing extracted information from XMP:Categories or None if the field is not found.
        """
        parsed_data = {}

        # Get XMP:Categories metadata
        if "XMP:Categories" in self.metadata:
            categories_xml = self.metadata["XMP:Categories"]

            # Parse each regex pattern
            for metadata_field, regex in acdsee_parser.items():
                match = re.search(regex, categories_xml)

                try:

                    # Add extracted value to dictionary if found
                    if match:
                        parsed_data[metadata_field] = match.group(1)
                    else:
                        parsed_data[metadata_field] = None

                except:
                    parsed_data[metadata_field] = None


        else:
            parsed_data = None

        return parsed_data

def match_photo_metadata_to_video(self, photo_folder, video_folder, photo_to_video_fields, threshold_minutes):
    """
    Matches metadata from photos to videos based on reference dates within a threshold.

    Args:
        photo_folder: Path to the root folder containing photos.
        video_folder: Path to the root folder containing videos.
        photo_to_video_fields: List of photo metadata fields to transfer to videos.
        threshold_minutes: Integer representing the maximum time difference in minutes.

    Returns:
        A Pandas DataFrame with both photos and videos, with photo metadata copied to matching videos.
    """

    import pandas as pd

    # Read photo data
    photo_df = self.read_metadata_from_folder(photo_folder)
    photo_df = self.add_earliest_reference_date(photo_df, created_date_fields)

    # Read video data
    video_df = self.read_metadata_from_folder(video_folder)
    video_df = self.add_earliest_reference_date(video_df, created_date_fields)

    # Prepare empty columns in video_df for photo metadata
    for field in photo_to_video_fields:
        if field not in video_df.columns:
            video_df[field] = None

    # Loop through videos and find matching photos
    for video_index, video_row in video_df.iterrows():
        video_date = video_row["reference date"]
        diff_tolerance = pd.Timedelta(minutes=threshold_minutes)
        closest_photo_df = photo_df[(photo_df["reference date"] >= (video_date - diff_tolerance)) &
                                    (photo_df["reference date"] <= (video_date + diff_tolerance))]

    if not closest_photo_df.empty:
        closest_photo_row = closest_photo_df.iloc[0]
        for field in photo_to_video_fields:
            if pd.isna(video_row[field]) and not pd.isna(closest_photo_row[field]):
                video_df.loc[video_index, field] = closest_photo_row[field]

    # Combine dataframes
    combined_df = pd.concat([photo_df, video_df], ignore_index=True)

    return combined_df

