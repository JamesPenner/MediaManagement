import re
import sys
import pandas as pd
import chardet

sys.path.append(r'C:\Media Management\Scripts')
# from config import created_date_fields, acdsee_parser, Location_fields, city_fields, state_fields, country_fields, country_code_fields, gps_fields, locality_fields, location_lookup, people_lookup, family_names, filename_validation_rules, keyword_lookup, asset_title_length

# This will include a series of common Pandas operations
# Ideas include:
# 1. Search for term and return related terms
# 2. Load multiple csv/text files

class DataFileHandler:
    @staticmethod
    def load_csv_files_to_dataframe(csv_files):
        """
        Loads and merges CSV files from a list of file paths into a single DataFrame.

        Parameters:
        -----------
        csv_files : list
            List of file paths for CSV files to load.

        Returns:
        --------
        pandas.DataFrame or None
            Merged DataFrame containing data from all CSV files. Returns None if no files are loaded.
        """
        def detect_encoding(file):
            with open(file, 'rb') as f:
                rawdata = f.read()
                result = chardet.detect(rawdata)
                return result['encoding']

        loaded_dataframes = []
        total_files = len(csv_files)
        file_count = 0

        for file in csv_files:
            file_count += 1
            print(f"Loading file {file_count} of {total_files}: {file}")
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = pd.read_csv(f)
                    loaded_dataframes.append(data)
            except UnicodeDecodeError:
                encoding = detect_encoding(file)
                with open(file, 'r', encoding=encoding) as f:
                    data = pd.read_csv(f)
                    loaded_dataframes.append(data)
            except pd.errors.EmptyDataError:
                print(f"Empty file: {file}")

        if loaded_dataframes:
            merged_data = pd.concat(loaded_dataframes, ignore_index=True)
            return merged_data
        else:
            return None

    @staticmethod
    def search_dataframe(df, lookup_str, search_column, columns_list, case_sensitive=False, exact_match=False):
        """
        Searches for a specified substring or exact match in a Pandas DataFrame column and retrieves values
        from specified columns corresponding to the match.

        Parameters:
        -----------
        df : pandas.DataFrame
            The DataFrame to search within.
        
        lookup_str : str
            The substring or exact match to look up within the specified search_column.

        search_column : str
            The name of the column in the DataFrame to search for the substring or exact match.

        columns_list : list
            A list of column names in the DataFrame from which to retrieve values
            if a match is found in the search_column.

        case_sensitive : bool, optional (default=True)
            Determines whether the search is case-sensitive. If True, the search
            will be case-sensitive; if False, the search will be case-insensitive.

        exact_match : bool, optional (default=False)
            Determines whether to search for an exact match or a substring match.
            If True, searches for an exact match; if False, searches for a substring match.

        Returns:
        --------
        dict
            A dictionary where keys are column names from columns_list and values
            are the values found in those columns corresponding to the match.
            Returns an empty dictionary if no match is found.
        """
        result = {}

        if not case_sensitive:
            df[search_column] = df[search_column].str.lower()
            lookup_str = lookup_str.lower()

        if exact_match:
            matches = df[df[search_column] == lookup_str]
        else:
            if case_sensitive:
                matches = df[df[search_column].str.contains(re.escape(lookup_str), case=case_sensitive, na=False)]
            else:
                matches = df[df[search_column].str.contains(re.escape(lookup_str), case=case_sensitive, na=False, flags=re.IGNORECASE)]

        if not matches.empty:
            for col in columns_list:
                result[col] = matches[col].values[0] if col in matches.columns else None

        return result

