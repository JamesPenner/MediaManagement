import re
import sys
# sys.path.append(r'C:\Users\Windows\Dropbox\James\Python\Scripts')
# from data_file_handler import DataFileHandler
import chardet
import pandas as pd
import seaborn as sns 
import networkx as nx
from dateutil.parser import parse
# import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg',force=True)
from matplotlib import pyplot as plt
from dateutil import parser

import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression


# from config import created_date_fields, acdsee_parser, Location_fields, city_fields, state_fields, country_fields, country_code_fields, gps_fields, locality_fields, location_lookup, people_lookup, family_names, filename_validation_rules, keyword_lookup, asset_title_length

# This will include a series of common Pandas operations
# Ideas include:
# 1. Search for term and return related terms
# 2. Load multiple csv/text files

class DataFileHandler:

    def __init__(self):
        pass
        # self.data = data
        # Your initialization code here


    def clean_spaces(self, df):
        """
        Clean extra or unnecessary spaces from string columns in a Pandas DataFrame.
        
        Parameters:
            df (DataFrame): Input DataFrame to clean.
            
        Returns:
            DataFrame: DataFrame with extra spaces removed from string columns.
        """
        # Ensure all columns are string type
        df = df.astype(str)
        
        # Clean spaces in string columns
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        
        return df

    def parse_date(self, date_str):
        try:
            return parse(date_str)
        except ValueError:
            return None

    def convert_mixed_date_formats(self, df, date_columns):
        for column in date_columns:
            # Parse dates in the column
            df[column] = df[column].apply(parse_date)
        return df

    def convert_string_columns_to_numeric(self, df):
        """
        Convert string columns to numeric type in a Pandas DataFrame.
        
        Parameters:
            df (DataFrame): Input DataFrame containing string columns to convert.
            
        Returns:
            DataFrame: DataFrame with string columns converted to numeric type, where appropriate.
        """
        # Identify columns containing strings
        string_columns = df.select_dtypes(include=['object']).columns
        
        # Dictionary to store original values of columns that fail conversion
        original_values = {}

        # Inspect string values and attempt conversion
        for column in string_columns:
            try:
                # Attempt conversion
                df[column] = pd.to_numeric(df[column].str.replace(r'[^\d\.]', ''), errors='raise')
            except ValueError:
                # Store original values and revert the column back
                original_values[column] = df[column]
                print(f"Column '{column}' could not be converted to numeric type. Reverting it back to its original state.")
                df[column] = original_values[column]
        
        return df





    def count_unique_values(self, df, dtype_list=None):
        """
        Count the number of unique values in each column of a DataFrame with optional filtering by data types,
        and provide summary statistics.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.
        - dtype_list: list or None, optional (default=None)
            List of data types to include. If None, all columns are considered.

        Returns:
        - pandas.DataFrame
            DataFrame containing summary statistics of unique values in each column.
        """
        if dtype_list is None:
            dtype_list = df.dtypes.unique()

        # Filter columns based on data types
        filtered_columns = [col for col, dtype in df.dtypes.items() if dtype in dtype_list]

        # Calculate the number of unique values in each filtered column
        unique_counts = df[filtered_columns].nunique()

        # Calculate summary statistics
        summary_stats = pd.DataFrame({
            'Column': unique_counts.index,
            'Unique Values': unique_counts.values,
            'Percentage Unique': unique_counts / len(df) * 100
        })

        return summary_stats.describe().transpose()

    def encode_categorical_variables(self, df, threshold=10, prefix=None, drop_first=False):
        """
        Encode categorical and Boolean variables in the DataFrame as dummy variables, automatically identifying
        categorical variables and applying the threshold only to those columns.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.
        - threshold: int, optional (default=10)
            The threshold value to control the number of potential values that will be encoded.
        - prefix: str or list of str, optional (default=None)
            Prefix to be added to the column names in the encoded DataFrame.
        - drop_first: bool, optional (default=False)
            Whether to drop the first level of dummy encoding.

        Returns:
        - pandas.DataFrame
            DataFrame with categorical and Boolean variables encoded as dummy variables.
        """
        # Error handling
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError("Input 'df' must be a non-empty DataFrame.")

        if not isinstance(threshold, int) or threshold <= 0:
            raise ValueError("Threshold must be a positive integer.")

        # Identify categorical columns based on dtype
        categorical_columns = [col for col in df.select_dtypes(include=['category', 'object'])
                            if df[col].nunique() <= threshold]

        # Identify boolean columns
        boolean_columns = [col for col in df.select_dtypes(include=['bool'])]

        # Initialize list to store encoded columns
        encoded_columns = []

        for column in df.columns:
            if column in categorical_columns:
                # Encode the column as dummy variables
                encoded_columns.append(pd.get_dummies(df[column], prefix=prefix, drop_first=drop_first))
            elif column in boolean_columns:
                # Convert boolean columns to integers (0 or 1)
                encoded_columns.append(df[column].astype(int))
            else:
                # Keep non-categorical and non-boolean columns unchanged
                encoded_columns.append(df[column])

        # Concatenate encoded columns into a single DataFrame
        encoded_df = pd.concat(encoded_columns, axis=1)

        return encoded_df


# Datafram loading Methods
    def _convert_object_columns(df):
        for column in df.columns:
            if df[column].dtype == 'O':  # Check if the column is of object type
                try:
                    # Attempt to convert to numeric (integer or float)
                    df[column] = pd.to_numeric(df[column])
                except ValueError:
                    # Revert back to the previous state if the conversion is unsuccessful
                    print(f"Unable to convert column '{column}' to numeric. Reverting to the previous state.")
                    # If needed, you can handle this differently, e.g., keep the original values in a separate column
                    # df[column + '_original'] = df[column]
    

    @staticmethod
    def load_csv_files_to_dataframe(csv_files, encoding='utf-8', convert_object=True, convert_percent=True,
                                     convert_date=True, error_handling='raise', verbose=False, return_empty=False):
        """
        Loads and merges CSV files from a list of file paths into a single DataFrame.

        Parameters:
        -----------
        csv_files : list
            List of file paths for CSV files to load.
        encoding : str, optional
            Encoding to use for reading the CSV files. Default is 'utf-8'.
        convert_object : bool, optional
            Whether to convert object columns to numeric types. Default is True.
        convert_percent : bool, optional
            Whether to convert object columns containing percentages to floats. Default is True.
        convert_date : bool, optional
            Whether to attempt to convert columns containing dates to datetime objects. Default is True.
        error_handling : {'raise', 'ignore', 'warn'}, optional
            Specifies how to handle errors during file loading. Default is 'raise'.
        verbose : bool, optional
            Whether to print information about each file being loaded. Default is False.
        return_empty : bool, optional
            Whether to return None if no files are loaded. Default is False.

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

        def convert_object_columns(df):
            for column in df.columns:
                if pd.api.types.is_object_dtype(df[column].dtype) and convert_object:
                    try:
                        df[column] = pd.to_numeric(df[column].replace(['$', ',', '"'], '', regex=True))
                    except ValueError:
                        if verbose:
                            print(f"Unable to convert column '{column}' to numeric.")

        def convert_percent_columns(df):
            for column in df.columns:
                if pd.api.types.is_object_dtype(df[column].dtype) and convert_percent:
                    try:
                        df[column] = pd.to_numeric(df[column].replace(['%', '"'], '', regex=True), errors='coerce') / 100
                    except ValueError:
                        if verbose:
                            print(f"Unable to convert column '{column}' to percent.")

        def convert_to_date_columns(df):
            if convert_date:
                for column in df.columns:
                    try:
                        df[column] = pd.to_datetime(df[column], errors='raise')
                    except (TypeError, ValueError):
                        try:
                            df[column] = df[column].apply(lambda x: parser.parse(x) if pd.notna(x) else pd.NaT)
                        except (ValueError, TypeError):
                            if verbose:
                                print(f"Unable to convert column '{column}' to datetime.")

        loaded_dataframes = []
        total_files = len(csv_files)
        file_count = 0

        for file in csv_files:
            file_count += 1
            if verbose:
                print(f"Loading file {file_count} of {total_files}: {file}")

            try:
                with open(file, 'r', encoding=encoding) as f:
                    data = pd.read_csv(f, encoding=encoding)
                    convert_object_columns(data)
                    convert_percent_columns(data)
                    convert_to_date_columns(data)
                    loaded_dataframes.append(data)
            except Exception as e:
                if error_handling == 'raise':
                    raise e
                elif error_handling == 'warn':
                    print(f"Error occurred while loading file '{file}': {e}")
                elif error_handling == 'ignore':
                    pass


        if loaded_dataframes:
            merged_data = pd.concat(loaded_dataframes, ignore_index=True)
            return merged_data
        elif return_empty:
            return pd.DataFrame()
        else:
            return None


# Filtering / Search Methods
    # def filter_dataframe_columns(self, df):
    #     # Display the columns and their datatypes with unique reference numbers
    #     print("Columns in the DataFrame:")
    #     for i, (column, dtype) in enumerate(zip(df.columns, df.dtypes), start=1):
    #         print(f"{i}. {column} ({dtype})")

    #     # Ask the user to specify columns
    #     user_input = input("Specify columns (e.g., '1', '1,2', '1-3', '1,3-5'): ")

    #     # Parse user input and filter columns
    #     selected_columns = self.parse_user_input(user_input, len(df.columns))
    #     filtered_df = df.iloc[:, selected_columns]

    #     return filtered_df

    def filter_dataframe_by_datatype(self, df, data_types):
        """
        Filter DataFrame columns by specified data types.

        Parameters:
        - df: pandas.DataFrame
            The DataFrame to filter.
        - data_types: str or list
            The data type(s) to filter by. Can be a single data type string or a list of data type strings.
            Supported data types: 'int', 'float', 'float64', 'object', 'category'.

        Returns:
        - pandas.DataFrame
            Filtered DataFrame containing columns that match the specified data types.
        """
        if isinstance(data_types, str):
            data_types = [data_types]

        filtered_columns = []
        for column, dtype in zip(df.columns, df.dtypes):
            str_dtype = str(dtype)
            for dt in data_types:
                if dt == "float" and ("float" in str_dtype or "float64" in str_dtype):
                    filtered_columns.append(column)
                    break
                elif str_dtype == dt:
                    filtered_columns.append(column)
                    break

        return df[filtered_columns]

    def filter_dataframe_columns(self, df):
        # Display the columns and their datatypes with unique reference numbers
        print("Columns in the DataFrame:")
        for i, (column, dtype) in enumerate(zip(df.columns, df.dtypes), start=1):
            print(f"{i}. {column} ({dtype})")

        # Ask the user to specify columns and data types
        user_input = input("Specify columns and/or data types (e.g., '1', '1,2:int', '1-3:float', '1,3-5:object'): ")

        # Parse user input and filter columns
        selected_columns = self.parse_user_input(user_input, len(df.columns), df)
        filtered_df = df.iloc[:, selected_columns]

        return filtered_df

    def parse_user_input(self, user_input, max_columns, df):
        selected_columns = []

        for selection in user_input.split(','):
            if ':' in selection:
                col_spec, data_types = selection.split(':')
                selected_columns.extend(self.parse_col_spec(col_spec, data_types, max_columns, df))
            else:
                try:
                    selected_columns.append(int(selection) - 1)
                except ValueError:
                    print(f"Invalid input: {selection}")

        return sorted(selected_columns)


    def parse_col_spec(self, col_spec, data_types, max_columns, df):
        selected_columns = []
        start, end = map(int, col_spec.split('-'))

        for col_index in range(start - 1, end):
            for data_type in data_types.split(','):
                if data_type.strip() in ['int', 'float', 'object', 'category']:  # Add more data types as needed
                    dtype_mask = df.iloc[:, col_index].dtype == data_type.strip()
                    if dtype_mask:
                        selected_columns.append(col_index)
                        break  # Once a matching data type is found, break the inner loop

        return selected_columns

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

        # print(type(lookup_str))
        
        df = df.dropna(subset=[search_column])
        df[search_column] = df[search_column].astype(str)
        
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



# Missing Value Methods
    @staticmethod
    def impute_missing_values2(df, approach):
        """
        Impute missing values in a DataFrame using the specified approach.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.
        - approach: str
            The imputation approach to use. Options include:
                - 'mean': Replace missing values with the mean of the column.
                - 'median': Replace missing values with the median of the column.
                - 'mode': Replace missing values with the mode (most frequent value) of the column.
                - 'ffill': Forward fill missing values.
                - 'bfill': Backward fill missing values.
                - 'interpolation': Interpolate missing values using linear interpolation.
                - 'knn': Impute missing values using K-Nearest Neighbors.
                - 'random': Replace missing values with random values drawn from the distribution of non-missing values.

        Returns:
        - pandas.DataFrame
            DataFrame with missing values imputed according to the specified approach.
        """
        if approach == 'mean':
            return df.fillna(df.mean())
        elif approach == 'median':
            return df.fillna(df.median())
        elif approach == 'mode':
            return df.fillna(df.mode().iloc[0])
        elif approach == 'ffill':
            return df.ffill()
        elif approach == 'bfill':
            return df.bfill()
        elif approach == 'interpolation':
            return df.interpolate()
        elif approach == 'knn':
            from sklearn.impute import KNNImputer
            imputer = KNNImputer(n_neighbors=5)  # You can adjust the number of neighbors as needed
            return pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
        elif approach == 'random':
            import numpy as np
            np.random.seed(0)  # For reproducibility
            for col in df.columns:
                if df[col].isnull().sum() > 0:
                    values = df[col].dropna().sample(df[col].isnull().sum(), replace=True)
                    df.loc[df[col].isnull(), col] = values.values
            return df
        else:
            raise ValueError("Invalid imputation approach. Supported approaches are: 'mean', 'median', 'mode', "
                             "'ffill', 'bfill', 'interpolation', 'knn', 'random'.")

    def impute_missing_values(self, df):
        replaced_values_summary = {}

        for column in df.columns:
            missing_values_count = df[column].isnull().sum()
            missing_values_percent = (missing_values_count / len(df)) * 100
            column_dtype = df[column].dtype

            print(f"\nColumn: {column}")
            print(f"  - Data Type: {column_dtype}")
            print(f"  - Missing Values: {missing_values_count} ({missing_values_percent:.2f}%)")

            if missing_values_count == 0:
                print("  - No missing values found. Skipping imputation.")
                continue

            imputation_approach = self.suggest_imputation_approach(df[column])

            if imputation_approach:
                if imputation_approach == "mean":
                    df[column].fillna(df[column].mean(), inplace=True)
                elif imputation_approach == "median":
                    df[column].fillna(df[column].median(), inplace=True)
                elif imputation_approach == "mode":
                    df[column].fillna(df[column].mode()[0], inplace=True)

                replaced_values_count = missing_values_count
                replaced_values_summary[column] = replaced_values_count

        print("\nSummary of Replaced Values:")
        for column, count in replaced_values_summary.items():
            print(f"  - Column: {column}, Replaced Values: {count}")

    def suggest_imputation_approach(self, column_series):
        if pd.api.types.is_numeric_dtype(column_series.dtype):
            return "mean"
        elif pd.api.types.is_categorical_dtype(column_series.dtype):
            return "mode"
        else:
            return None


# Correlation Methods
    
    def multiple_correlation(self, dataframe, threshold):
        """
        Calculate correlations between numeric variables in a DataFrame and return correlations above a specified threshold.

        Parameters:
            dataframe (pandas.DataFrame): The DataFrame containing the variables to calculate correlations for.
            threshold (float): The threshold value to determine which correlations to include in the result.

        Returns:
            pandas.DataFrame: A DataFrame containing the correlated variables and their correlation coefficients
            that exceed the specified threshold. The DataFrame has three columns: 'Variable 1', 'Variable 2', and 'Correlation'.
            The results are sorted in descending order based on the absolute value of the correlation coefficient.

        Example:
            # Assuming df is your DataFrame and threshold is your threshold value
            corr_df = correlation_threshold(df, threshold)
        """
        # Select only numeric columns
        numeric_df = dataframe.select_dtypes(include=['number'])

        # Create an empty list to store correlation results
        corr_results = []

        # Get correlation matrix for Pearson correlation
        pearson_corr_matrix = numeric_df.corr(method='pearson')

        # Get correlation matrix for Spearman correlation
        spearman_corr_matrix = numeric_df.corr(method='spearman')

        # Get correlation matrix for Kendall correlation
        kendall_corr_matrix = numeric_df.corr(method='kendall')

        # Iterate over the columns of the correlation matrices
        for i, col in enumerate(pearson_corr_matrix.columns):
            for j in range(i+1, len(pearson_corr_matrix.columns)):
                # Get absolute correlation values for all methods
                pearson_corr_value = pearson_corr_matrix.iloc[i, j]
                spearman_corr_value = spearman_corr_matrix.iloc[i, j]
                kendall_corr_value = kendall_corr_matrix.iloc[i, j]

                # Select the maximum absolute correlation value among different methods
                max_corr_value = max(abs(pearson_corr_value), abs(spearman_corr_value), abs(kendall_corr_value))

                if max_corr_value >= threshold:
                    # Append correlated variables and their maximum absolute correlation to the list
                    corr_results.append({
                        'Variable 1': pearson_corr_matrix.columns[i],
                        'Variable 2': pearson_corr_matrix.columns[j],
                        'Pearson Correlation': pearson_corr_value,
                        'Spearman Correlation': spearman_corr_value,
                        'Kendall Correlation': kendall_corr_value,
                        'Max Absolute Correlation': max_corr_value
                    })

        # Convert the list of dictionaries into a DataFrame
        corr_df = pd.DataFrame(corr_results)

        # Sort the DataFrame based on the absolute value of the maximum correlation coefficient
        corr_df = corr_df.reindex(corr_df['Max Absolute Correlation'].abs().sort_values(ascending=False).index)

        return corr_df

    def get_correlated_with_column(self, df, target_column, threshold, direction="both"):
        """
        Get column names that have a correlation with the specified column exceeding the threshold.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.
        - target_column: str
            The name of the column for which correlations are calculated.
        - threshold: float
            The correlation threshold.
        - direction: str, optional (default: "both")
            The direction of correlation to consider ("positive", "negative", or 'both').

        Returns:
        - pandas.DataFrame
            DataFrame containing columns that have a correlation with the specified column exceeding the threshold.
            Columns: 'Correlated Column', 'Correlation'
        """
        df = df.select_dtypes('number')

        if direction not in ["positive", "negative", "both"]:
            raise ValueError("Invalid direction. Use 'positive', 'negative', or 'both'.")

        # Calculate the correlation matrix
        correlation_matrix = df.corr()

        # Select columns based on correlation and direction
        if direction == "positive":
            correlated_columns = [(col, correlation_matrix.loc[target_column, col])
                                for col in correlation_matrix.columns
                                if col != target_column and correlation_matrix.loc[target_column, col] >= threshold]
        elif direction == "negative":
            correlated_columns = [(col, correlation_matrix.loc[target_column, col])
                                for col in correlation_matrix.columns
                                if col != target_column and correlation_matrix.loc[target_column, col] <= -threshold]
        elif direction == "both":
            correlated_columns_positive = [(col, correlation_matrix.loc[target_column, col])
                                            for col in correlation_matrix.columns
                                            if col != target_column and correlation_matrix.loc[target_column, col] >= threshold]
            correlated_columns_negative = [(col, correlation_matrix.loc[target_column, col])
                                            for col in correlation_matrix.columns
                                            if col != target_column and correlation_matrix.loc[target_column, col] <= -threshold]
            correlated_columns = correlated_columns_positive + correlated_columns_negative

        # Convert the list of tuples into a DataFrame
        correlated_df = pd.DataFrame(correlated_columns, columns=['Correlated Column', 'Correlation'])

        return correlated_df

    def correlation_matrix(self, df):
        """
        Visualize the correlation matrix of numerical columns in the DataFrame.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.

        Displays a color-coded heatmap representing the correlation matrix of numerical columns in the DataFrame.
        Each cell in the heatmap corresponds to the correlation coefficient between two columns.
        Positive correlations are indicated by warmer colors (closer to 1), and negative correlations by cooler colors (closer to -1).
        The values in each cell are annotated for clarity.

        Example Usage:
        >>> df_handler = DataFileHandler()
        >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6], 'C': [7, 8, 9], 'D': [10, 11, 12]})
        >>> df_handler.correlation_matrix(df)
        """
        df = df.select_dtypes('number')

        # Calculate the correlation matrix
        correl_matrix = df.corr()

        # Set up the matplotlib figure
        plt.figure(figsize=(10, 8))

        # Create a color-coded heatmap using seaborn
        sns.heatmap(correl_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)

        # Show the plot
        plt.show()

    def get_correlated_columns(self, df, threshold, direction="both"):
        """
        Get column names and their correlation coefficients exceeding the specified threshold.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.
        - threshold: float
            The correlation threshold.
        - direction: str, optional (default: "both")
            The direction of correlation to consider ("positive", "negative", or 'both').

        Returns:
        - list of tuples
            List of unique (column1, column2, correlation) tuples for correlations exceeding the threshold.

        Correlation Guide:
        ------------------
        Very High (|r| > 0.9): The variables are very strongly correlated. Changes in one variable are almost perfectly predictable by changes in the other. This is a very strong relationship.
        High (0.7 ≤ |r| ≤ 0.9): The variables are strongly correlated. Changes in one variable are highly predictable by changes in the other. This is a strong relationship.
        Moderate (0.4 ≤ |r| < 0.7): The variables are moderately correlated. There is a moderate degree of predictability between changes in one variable and changes in the other.
        Low (0.2 ≤ |r| < 0.4): The variables are weakly correlated. There is a low degree of predictability between changes in one variable and changes in the other.
        Very Low (|r| < 0.2): The variables have a very weak or negligible correlation. Changes in one variable are not well predicted by changes in the other.
        """
        df = df.select_dtypes('number')

        if direction not in ["positive", "negative", "both"]:
            raise ValueError("Invalid direction. Use 'positive', 'negative', or 'both'.")

        # Calculate the correlation matrix
        correlation_matrix = df.corr()

        # Initialize an empty set to store unique correlated column pairs
        unique_correlated_columns = set()

        # Select columns based on correlation and direction
        if direction == "positive":
            correlated_columns = [(col1, col2, round(correlation_matrix.loc[col1, col2], 2))
                                   for col1, col2 in correlation_matrix.unstack().index
                                   if correlation_matrix.loc[col1, col2] >= threshold and col1 != col2]
        elif direction == "negative":
            correlated_columns = [(col1, col2, round(correlation_matrix.loc[col1, col2], 2))
                                   for col1, col2 in correlation_matrix.unstack().index
                                   if correlation_matrix.loc[col1, col2] <= -threshold and col1 != col2]
        elif direction == "both":
            correlated_columns_positive = [(col1, col2, round(correlation_matrix.loc[col1, col2], 2))
                                            for col1, col2 in correlation_matrix.unstack().index
                                            if correlation_matrix.loc[col1, col2] >= threshold and col1 != col2]
            correlated_columns_negative = [(col1, col2, round(correlation_matrix.loc[col1, col2], 2))
                                            for col1, col2 in correlation_matrix.unstack().index
                                            if correlation_matrix.loc[col1, col2] <= -threshold and col1 != col2]
            correlated_columns = correlated_columns_positive + correlated_columns_negative

        # Add unique pairs to the set
        seen_pairs = set()
        for pair in correlated_columns:
            sorted_pair = tuple(sorted(pair[:-1])) + (pair[-1],)
            reversed_pair = tuple(sorted(pair[1::-1])) + (pair[-1],)
            if sorted_pair not in seen_pairs and reversed_pair not in seen_pairs:
                unique_correlated_columns.add(sorted_pair)

        return list(unique_correlated_columns)
    def correlation_network(self, df, threshold=0.5):
        """
        Generate a correlation network based on pairwise correlation coefficients.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.
        - threshold: float, optional (default: 0.5)
            Threshold for including edges in the network based on correlation strength.

        Returns:
        - networkx.Graph
            A correlation network where nodes represent variables, and edges represent correlations.
        """
        # Calculate the correlation matrix
        correlation_matrix = df.corr()

        # Create a graph
        G = nx.Graph()

        # Add nodes (variables) to the graph
        G.add_nodes_from(correlation_matrix.columns)

        # Add edges (correlations) to the graph based on the threshold
        for col1, col2 in zip(*correlation_matrix.stack().index.levels):
            correlation = correlation_matrix.loc[col1, col2]
            if abs(correlation) >= threshold and col1 != col2:
                G.add_edge(col1, col2, weight=correlation)

        return G

    def plot_correlation_network(self, df, threshold=0.5):
        """
        Generate and plot a correlation network based on pairwise correlation coefficients.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.
        - threshold: float, optional (default: 0.5)
            Threshold for including edges in the network based on correlation strength.
        """
        # Generate the correlation network
        correlation_network = self.correlation_network(df, threshold)

        # Plot the correlation network
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(correlation_network)  # You can choose a different layout if needed
        nx.draw(correlation_network, pos, with_labels=True, font_size=8, font_color="black", font_weight="bold",
                node_color="skyblue", node_size=700, edge_color="gray", linewidths=1, alpha=0.7)

        # Show the plot
        plt.title("Correlation Network")
        plt.show()

    def correlation_network_interactive(self, df, threshold=0.5):
        """
        Generate an interactive correlation network based on pairwise correlation coefficients.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.
        - threshold: float, optional (default: 0.5)
            Threshold for including edges in the network based on correlation strength.

        Returns:
        - plotly.graph_objects.Figure
            An interactive correlation network.
        """
        # Calculate the correlation matrix
        correlation_matrix = df.corr()

        # Create a graph
        G = nx.Graph()

        # Add nodes (variables) to the graph
        G.add_nodes_from(correlation_matrix.columns)

        # Add edges (correlations) to the graph based on the threshold
        for col1, col2 in zip(*correlation_matrix.stack().index.levels):
            correlation = correlation_matrix.loc[col1, col2]
            if abs(correlation) >= threshold and col1 != col2:
                G.add_edge(col1, col2, weight=correlation)

        # Create an interactive network plot using plotly
        pos = nx.spring_layout(G)  # You can choose a different layout if needed

        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_x = []
        node_y = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Node Connections',
                    xanchor='left',
                    titleside='right'
                )
            )
        )

        node_adjacencies = []
        node_text = []
        for node, adjacencies in enumerate(G.adjacency()):
            node_adjacencies.append(len(adjacencies[1]))
            node_text.append('# of connections: '+str(len(adjacencies[1])))

        node_trace.marker.color = node_adjacencies
        node_trace.text = node_text

        # Create the figure
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=0),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                        )

        return fig

    def plot_correlation_network_interactive(self, df, threshold=0.5):
        """
        Generate and display an interactive correlation network based on pairwise correlation coefficients.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.
        - threshold: float, optional (default: 0.5)
            Threshold for including edges in the network based on correlation strength.
        """
        # Generate the interactive correlation network
        fig = self.correlation_network_interactive(df, threshold)

        # Display the plot
        fig.show()




# Plotting Methods
    def generate_scatterplot(self, df, x_column, y_column):
        """
        Generate a scatter plot for two columns in the DataFrame.

        Parameters:
        - df: pandas.DataFrame
            The input DataFrame.
        - x_column: str
            The column name for the x-axis.
        - y_column: str
            The column name for the y-axis.

        Returns:
        - None
            Displays the scatter plot.
        """
        plt.scatter(df[x_column], df[y_column])
        plt.xlabel(x_column)
        plt.ylabel(y_column)
        plt.title(f"Scatter Plot: {x_column} vs {y_column}")
        plt.show()
