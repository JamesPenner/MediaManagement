import sys
import re
import pandas as pd
from typing import List, Union, Optional, Dict, Any
import numpy as np
from sklearn.impute import KNNImputer
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
from datetime import datetime

class DataFrameHandler:
    def __init__(self, df: Optional[pd.DataFrame] = None):
        """
        Initializes the DataFrameHandler with an optional single DataFrame.

        Args:
            df (Optional[pd.DataFrame]): An optional DataFrame to initialize with.
        """
        self.df = df


    def infer_and_convert_dates(self) -> pd.DataFrame:
        """
        Attempts to infer and convert columns in the DataFrame that might be dates.
        If a column cannot be automatically recognized as a date, prompts the user to confirm.
        
        Returns:
            pd.DataFrame: The DataFrame with date columns converted to datetime format.
        """
        if self.df is None:
            raise ValueError("DataFrame is not provided.")
        
        # Function to check if a column can be converted to datetime
        def is_possible_date_series(series: pd.Series) -> bool:
            try:
                # Attempt to parse a sample of values to check if they can be recognized as dates
                sample = series.dropna().sample(min(len(series.dropna()), 10))
                pd.to_datetime(sample, errors='raise')
                return True
            except Exception:
                return False

        # Columns to be confirmed by the user
        potential_date_columns = [col for col in self.df.columns if is_possible_date_series(self.df[col])]
        
        for col in potential_date_columns:
            # Prompt user to confirm if the column should be converted to datetime
            response = input(f"Column '{col}' appears to contain dates. Should it be converted to datetime format? (y/n): ").strip().lower()
            
            if response == 'y':
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
            else:
                print(f"Column '{col}' will not be converted.")
        
        return self.df




    def lookup_value(self, df2: pd.DataFrame, key_col_df1: str, key_col_df2: str, value_col_df2: Union[str, List[str]]) -> pd.DataFrame:
        """
        Lookups values from df2 using the key column from df1 and returns the values from the specified column(s) in df2.
        Merges the values from df2 into self.df based on key column matching.
        """
        # Ensure value_col_df2 is a list
        if not isinstance(value_col_df2, list):
            value_col_df2 = [value_col_df2]

        # Ensure the key columns are present in both DataFrames
        if key_col_df1 not in self.df.columns or key_col_df2 not in df2.columns:
            raise KeyError(f"Key columns must be present in both DataFrames: {key_col_df1}, {key_col_df2}")

        # Handle missing values in key_col_df2 by dropping rows with NaN values
        df2_clean = df2.dropna(subset=[key_col_df2])

        # Ensure the key column in df2 has unique values
        if not df2_clean[key_col_df2].is_unique:
            raise ValueError(f"The key column '{key_col_df2}' in df2 must have unique values.")

        # Perform a left merge to bring in the values from df2 to self.df
        merged_df = pd.merge(self.df, df2_clean[[key_col_df2] + value_col_df2], 
                            left_on=key_col_df1, right_on=key_col_df2, how='left')

        # Drop the duplicated key column from df2 (key_col_df2)
        merged_df = merged_df.drop(columns=[key_col_df2])

        return merged_df
       
    def set_dataframe(self, df: pd.DataFrame):
        """
        Set or update the DataFrame for this instance.

        Args:
            df (pd.DataFrame): The DataFrame to set.
        """
        self.df = df




# Filtering / Search Methods

    def filter_by_date(self, date_column: str, before_date: Optional[Union[str, pd.Timestamp, bool]] = None,
                    after_date: Optional[Union[str, pd.Timestamp, bool]] = None, 
                    days_before: Optional[int] = None, days_after: Optional[int] = None, 
                    include_dates: bool = True, date_format: str = "%Y-%m-%d") -> pd.DataFrame:
        """
        Filters the DataFrame based on date parameters using absolute dates and day thresholds.
        
        Args:
            date_column (str): The name of the date column to filter on.
            before_date (Optional[Union[str, pd.Timestamp, bool]]): End date for filtering. Accepts a date string or 'today' to use the current date.
            after_date (Optional[Union[str, pd.Timestamp, bool]]): Start date for filtering. Accepts a date string or 'today' to use the current date.
            days_before (Optional[int]): Additional days before the `before_date` to include in filtering.
            days_after (Optional[int]): Additional days after the `after_date` to include in filtering.
            include_dates (bool): Whether to include or exclude the dates specified by `before_date` and `after_date`.
            date_format (str): Date format to parse date strings.

        Returns:
            pd.DataFrame: Filtered DataFrame based on the date criteria.
        """
        # Ensure the date_column is in datetime format (with coercion for invalid formats)
        self.df[date_column] = pd.to_datetime(self.df[date_column], format=date_format, errors='coerce')

        # Use today's date if 'today' is passed or if no date is specified
        today = pd.Timestamp.now().normalize()

        after_date = pd.to_datetime(after_date, format=date_format, errors='coerce') if after_date and after_date != 'today' else today
        before_date = pd.to_datetime(before_date, format=date_format, errors='coerce') if before_date and before_date != 'today' else today

        # Apply days_before and days_after adjustments
        if days_after:
            after_date += pd.Timedelta(days=days_after)
        if days_before:
            before_date -= pd.Timedelta(days=days_before)

        # Initialize filtering condition
        if include_dates:
            filter_condition = (self.df[date_column] >= before_date) & (self.df[date_column] <= after_date)
        else:
            filter_condition = (self.df[date_column] < before_date) | (self.df[date_column] > after_date)

        # Return the filtered DataFrame
        return self.df[filter_condition]

    def filter_dataframe_by_datatype(self, df: pd.DataFrame, data_types: Union[str, List[str]]) -> pd.DataFrame:
        """
        Filter DataFrame columns by specified data types.

        Parameters:
        - df: pandas.DataFrame
            The DataFrame to filter.
        - data_types: str or list of str
            The data type(s) to filter by. Can be a single data type string or a list of data type strings.
            Example: 'int', 'float', 'object', 'category', etc.

        Returns:
        - pandas.DataFrame
            Filtered DataFrame containing only columns that match the specified data types.
        """
        # Ensure data_types is a list
        if isinstance(data_types, str):
            data_types = [data_types]
        
        # Use pandas select_dtypes to filter the DataFrame by the specified types
        return df.select_dtypes(include=data_types)

    def filter_dataframe_columns(self, df: pd.DataFrame):
        # Display the columns and their data types with unique reference numbers
        print("Columns in the DataFrame:")
        for i, (column, dtype) in enumerate(zip(df.columns, df.dtypes), start=1):
            print(f"{i}. {column} ({dtype})")

        # Ask the user to specify columns by index and/or data types
        col_input = input("Specify columns by index (e.g., '1', '1,3-5') or leave blank to skip: ")
        dtype_input = input("Specify data types to filter (e.g., 'int', 'float', 'object') or leave blank to skip: ")

        # Handle column selection by index
        selected_columns = self.parse_col_indices(col_input, len(df.columns))

        # Handle data type filtering
        filtered_df = df if dtype_input.strip() == "" else df.select_dtypes(include=[dtype.strip() for dtype in dtype_input.split(',')])

        # If columns were selected by index, apply that filter
        if selected_columns:
            filtered_df = filtered_df.iloc[:, selected_columns]

        return filtered_df

    def parse_col_indices(self, col_input, max_columns):
        selected_columns = []
        if not col_input:
            return selected_columns  # If no column input, return empty list

        # Split user input by commas and parse ranges
        for selection in col_input.split(','):
            if '-' in selection:
                start, end = map(int, selection.split('-'))
                selected_columns.extend(range(start - 1, end))
            else:
                selected_columns.append(int(selection) - 1)

        # Ensure column indices are valid
        selected_columns = [col for col in selected_columns if 0 <= col < max_columns]

        return sorted(selected_columns)
    
    def recommend_imputation_method(self) -> Dict[str, str]:
        """
        Recommends imputation methods for each column based on its data type and percentage of missing values.

        Returns:
        --------
        dict
            A dictionary where keys are column names and values are the recommended imputation approaches.
        """
        recommendations = {}
        
        for col in self.df.columns:
            missing_pct = self.df[col].isnull().mean() * 100
            dtype = self.df[col].dtype
            
            # Numeric columns
            if pd.api.types.is_numeric_dtype(dtype):
                if missing_pct < 5:
                    recommendations[col] = 'mean'
                elif 5 <= missing_pct < 30:
                    recommendations[col] = 'median'
                else:
                    recommendations[col] = 'knn'
            
            # Categorical columns
            elif pd.api.types.is_categorical_dtype(dtype) or pd.api.types.is_object_dtype(dtype):
                if missing_pct < 30:
                    recommendations[col] = 'mode'
                else:
                    recommendations[col] = 'random'
            
            # Time series or ordered data could be treated with forward/backward fill
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                recommendations[col] = 'ffill'
        
        return recommendations

    def impute_missing_values_with_recommendation(self, approach: Optional[Dict[str, str]] = None,
                                                  knn_neighbors: int = 5, random_seed: int = 0) -> pd.DataFrame:
        """
        Impute missing values in the DataFrame using the specified or recommended approach.

        If no approach is specified, the method will recommend an imputation strategy
        based on the column type and percentage of missing values.
        Provides detailed output on imputed values and a summary of replaced values.

        Parameters:
        -----------
        approach : dict, optional
            A dictionary where keys are column names and values are the imputation approaches.
            If not provided, the function will automatically recommend the best approach for each column.

        knn_neighbors : int, optional (default=5)
            Number of neighbors to use for KNN imputation.

        random_seed : int, optional (default=0)
            Seed for random number generator used in random imputation.

        Returns:
        --------
        pandas.DataFrame
            DataFrame with missing values imputed according to the specified or recommended approach.
        """
        
        if approach is None:
            approach = self.recommend_imputation_method()
        
        replaced_values_summary = {}
        
        for col in self.df.columns:
            missing_count = self.df[col].isnull().sum()
            missing_pct = missing_count / len(self.df) * 100
            print(f"\nColumn: {col}")
            print(f"  - Data Type: {self.df[col].dtype}")
            print(f"  - Missing Values: {missing_count} ({missing_pct:.2f}%)")
            
            if missing_count == 0:
                print("  - No missing values found. Skipping imputation.")
                continue
            
            method = approach.get(col, None)
            
            try:
                if method == 'mean':
                    self.df[col].fillna(self.df[col].mean(), inplace=True)
                
                elif method == 'median':
                    self.df[col].fillna(self.df[col].median(), inplace=True)
                
                elif method == 'mode':
                    self.df[col].fillna(self.df[col].mode().iloc[0], inplace=True)
                
                elif method == 'ffill':
                    self.df[col].ffill(inplace=True)
                
                elif method == 'bfill':
                    self.df[col].bfill(inplace=True)
                
                elif method == 'interpolation':
                    self.df[col] = self.df[col].interpolate(method='linear')
                
                elif method == 'knn':
                    imputer = KNNImputer(n_neighbors=knn_neighbors)
                    self.df[[col]] = pd.DataFrame(imputer.fit_transform(self.df[[col]]), columns=[col])
                
                elif method == 'random':
                    np.random.seed(random_seed)
                    if self.df[col].isnull().sum() > 0:
                        values = self.df[col].dropna().sample(self.df[col].isnull().sum(), replace=True)
                        self.df.loc[self.df[col].isnull(), col] = values.values
                
                else:
                    raise ValueError(f"Unsupported imputation method: {method}")

                replaced_values_summary[col] = missing_count

            except Exception as e:
                print(f"Error occurred while imputing column {col}: {e}")

        print("\nSummary of Replaced Values:")
        for column, count in replaced_values_summary.items():
            print(f"  - Column: {column}, Replaced Values: {count}")

        return self.df


    def overall_summary(self) -> pd.DataFrame:
        """
        Get a comprehensive summary of the DataFrame including overall metrics.

        Returns:
            pd.DataFrame: Summary including overall metrics about the DataFrame.
        """
        if self.df is None:
            raise ValueError("DataFrame is not set.")

        # Compute overall metrics
        total_rows = self.df.shape[0]
        total_columns = self.df.shape[1]
        total_memory_kb = (self.df.memory_usage(deep=True).sum() / 1024).round(1)
        total_missing_values = self.df.isna().sum().sum()
        total_duplicates = self.df.duplicated().sum()
        total_unique_values = self.df.nunique().sum()
        total_non_null_values = self.df.notna().sum().sum()
        data_types_count = self.df.dtypes.value_counts()

        # Format the metrics for readability
        formatted_total_rows = f"{total_rows:,}"
        formatted_total_columns = f"{total_columns:,}"
        formatted_total_memory_kb = f"{total_memory_kb:,.1f}"
        formatted_total_missing_values = f"{total_missing_values:,}"
        formatted_total_duplicates = f"{total_duplicates:,}"
        formatted_total_unique_values = f"{total_unique_values:,}"
        formatted_total_non_null_values = f"{total_non_null_values:,}"

        # Format the data types count for human readability
        data_types_summary = "\n".join([f"{dtype}: {count:,}" for dtype, count in data_types_count.items()])

        # Create overall summary DataFrame
        overall_summary = pd.DataFrame({
            'Metric': ['Total Rows', 'Total Columns', 'Total Memory Usage (KB)', 'Total Missing Values', 
                       'Total Duplicates', 'Total Unique Values', 'Total Non-Null Values', 'Data Types Count'],
            'Value': [formatted_total_rows, formatted_total_columns, formatted_total_memory_kb, formatted_total_missing_values, 
                      formatted_total_duplicates, formatted_total_unique_values, formatted_total_non_null_values, data_types_summary]
        })

        return overall_summary

    def data_types_summary(self) -> pd.DataFrame:
        """
        Get the data types of each column along with additional metrics and return them as a DataFrame.
        
        Returns:
            pd.DataFrame: Data types and various metrics for each column.
        """
        if self.df is None:
            raise ValueError("DataFrame is not set.")
        
        # Initialize the summary DataFrame
        summary_dict = {
            'Column Name': self.df.columns,
            'Data Type': self.df.dtypes,
            'Non-Null Count': self.df.notna().sum(),
            'Null Count': self.df.isna().sum(),
            'Total Count': [self.df.shape[0]] * len(self.df.columns),  # Ensure same length
            'Percentage Non-Null': (self.df.notna().sum() / self.df.shape[0] * 100).round(2),
            'Distinct Count': self.df.nunique(),
            'Memory Usage (KB)': (self.df.memory_usage(deep=True, index=False) / 1024).round(1)  # Round to 1 decimal place
        }

        # Add Most Frequent Value (Mode)
        def get_most_frequent(column: pd.Series):
            try:
                mode = column.mode()
                return mode.iloc[0] if not mode.empty else None
            except:
                return None

        summary_dict['Most Frequent Value'] = self.df.apply(get_most_frequent)

        # Add Unique Count (number of values that appear only once)
        def unique_count(column: pd.Series) -> int:
            return (column.value_counts() == 1).sum()
        
        summary_dict['Unique Count'] = self.df.apply(unique_count)

        # Add Empty String Count for string columns
        def empty_string_count(column: pd.Series) -> int:
            if pd.api.types.is_string_dtype(column):
                return column.str.strip().eq('').sum()
            return 0

        summary_dict['Empty String Count'] = self.df.apply(empty_string_count)

        # Create DataFrame from dictionary
        summary = pd.DataFrame(summary_dict)

        # Ensure the DataFrame's index length matches the number of columns
        assert len(summary) == len(self.df.columns), "Mismatch in DataFrame column lengths."

        return summary


    
    # def numeric_metrics(self, column: pd.Series) -> pd.Series:
    #     return pd.Series({
    #         'Min': column.min(),
    #         'Max': column.max(),
    #         'Mean': column.mean(),
    #         'Median': column.median(),
    #         'Standard Deviation': column.std(),
    #         'Distinct Count': column.nunique(),
    #         'Unique Count': (column.value_counts() == 1).sum(),
    #         'Error Count': column.apply(pd.to_numeric, errors='coerce').isna().sum(),
    #         'Error Percentage': (column.apply(pd.to_numeric, errors='coerce').isna().sum() / len(column) * 100).round(2)
    #     })

    # def datetime_metrics(self, column: pd.Series) -> pd.Series:
    #     return pd.Series({
    #         'Min Date': column.min(),
    #         'Max Date': column.max(),
    #         'Distinct Count': column.nunique(),
    #         'Unique Count': (column.value_counts() == 1).sum(),
    #         'Error Count': column.apply(lambda x: pd.to_datetime(x, errors='coerce')).isna().sum(),
    #         'Error Percentage': (column.apply(lambda x: pd.to_datetime(x, errors='coerce')).isna().sum() / len(column) * 100).round(2)
    #     })

    # def string_metrics(self, column: pd.Series) -> pd.Series:
    #     return pd.Series({
    #         'Min Length': column.apply(lambda x: len(str(x)) if pd.notna(x) else 0).min(),
    #         'Max Length': column.apply(lambda x: len(str(x)) if pd.notna(x) else 0).max(),
    #         'Average Length': column.apply(lambda x: len(str(x)) if pd.notna(x) else 0).mean(),
    #         'Distinct Count': column.nunique(),
    #         'Unique Count': (column.value_counts() == 1).sum(),
    #         'Error Count': 0,  # No specific error detection for strings here
    #         'Error Percentage': 0.0
    #     })

    # def boolean_metrics(self, column: pd.Series) -> pd.Series:
    #     return pd.Series({
    #         'True Count': column.sum(),
    #         'False Count': (~column).sum(),
    #         'Distinct Count': column.nunique(),
    #         'Unique Count': (column.value_counts() == 1).sum(),
    #         'Error Count': 0,  # No specific error detection for booleans
    #         'Error Percentage': 0.0
    #     })


    # def numeric_metrics(self, series: pd.Series) -> pd.Series:
    #     # Calculate basic statistics
    #     mean = series.mean()
    #     median = series.median()
    #     min_val = series.min()
    #     max_val = series.max()
    #     std_dev = series.std()
    #     variance = series.var()
    #     missing_values = series.isna().sum()
    #     unique_values = series.nunique()
    #     total_sum = series.sum()
        
    #     # Calculate quartiles and IQR
    #     q1 = series.quantile(0.25)
    #     q3 = series.quantile(0.75)
    #     iqr = q3 - q1

    #     # Calculate outlier bounds
    #     lower_bound = q1 - 1.5 * iqr
    #     upper_bound = q3 + 1.5 * iqr

    #     # Calculate mode(s)
    #     mode = series.mode().values
    #     mode_str = ', '.join(map(str, mode))  # Convert modes to string for display

    #     # Calculate additional metrics
    #     range_val = max_val - min_val
    #     skewness = series.skew()
    #     kurtosis = series.kurtosis()
    #     cv = std_dev / mean if mean != 0 else float('inf')
    #     num_outliers = ((series < lower_bound) | (series > upper_bound)).sum()
    #     abs_mean_dev = (series - mean).abs().mean()

    #     # Compile all metrics into a pandas Series
    #     return pd.Series({
    #         'Mean': mean,
    #         'Median': median,
    #         'Mode': mode_str,
    #         'Min': min_val,
    #         'Max': max_val,
    #         'Range': range_val,
    #         'Std Dev': std_dev,
    #         'Variance': variance,
    #         'Missing Values': missing_values,
    #         'Unique Values': unique_values,
    #         '1st Quartile (Q1)': q1,
    #         '3rd Quartile (Q3)': q3,
    #         'Interquartile Range (IQR)': iqr,

    #         'Lower Bound for Outliers': lower_bound,
    #         'Upper Bound for Outliers': upper_bound,
    #         'Skewness': skewness,
    #         'Kurtosis': kurtosis,
    #         'Coefficient of Variation (CV)': cv,
    #         'Number of Outliers': num_outliers,
    #         'Absolute Mean Deviation': abs_mean_dev,
    #         'Sum': total_sum
    #     })


    def numeric_metrics(self, series: pd.Series) -> pd.Series:
        # Calculate basic statistics
        mean = series.mean()
        median = series.median()
        min_val = series.min()
        max_val = series.max()
        range_val = max_val - min_val
        total_sum = series.sum()
        
        # Calculate dispersion metrics
        std_dev = series.std()
        variance = series.var()
        abs_mean_dev = (series - mean).abs().mean()
        cv = std_dev / mean if mean != 0 else float('inf')
        
        # Calculate quartiles and IQR
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        
        # Calculate outlier bounds
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Calculate mode(s)
        mode_values = series.mode()
        mode_value = mode_values[0] if not mode_values.empty else np.nan
        
        # Calculate additional metrics
        skewness = series.skew()
        kurtosis = series.kurtosis()
        num_outliers = ((series < lower_bound) | (series > upper_bound)).sum()
        missing_values = series.isna().sum()
        unique_values = series.nunique()

        # Format the metrics with thousands separators and up to two decimal places
        def format_number(value):
            if pd.isna(value):
                return 'NaN'
            return f"{value:,.2f}"
        
        # Compile all metrics into a pandas Series with logical grouping
        return pd.Series({
            # Basic Statistics
            'Mean': format_number(mean),
            'Median': format_number(median),
            'Min': format_number(min_val),
            'Max': format_number(max_val),
            'Range': format_number(range_val),
            'Sum': format_number(total_sum),

            # Dispersion
            'Std Dev': format_number(std_dev),
            'Variance': format_number(variance),
            'Absolute Mean Deviation': format_number(abs_mean_dev),
            'Coefficient of Variation (CV)': format_number(cv),

            # Distribution
            'Skewness': format_number(skewness),
            'Kurtosis': format_number(kurtosis),

            # Quartiles and IQR
            '1st Quartile (Q1)': format_number(q1),
            '3rd Quartile (Q3)': format_number(q3),
            'Interquartile Range (IQR)': format_number(iqr),

            # Outliers
            'Lower Bound for Outliers': format_number(lower_bound),
            'Upper Bound for Outliers': format_number(upper_bound),
            'Number of Outliers': num_outliers,

            # Other
            'Mode': mode_value,
            'Missing Values': missing_values,
            'Unique Values': unique_values
        })



    def datetime_metrics(self, series: pd.Series) -> pd.Series:
        # Convert series to datetime format, if not already
        series = pd.to_datetime(series, errors='coerce')
        
        # Calculate basic statistics
        min_date = series.min()
        max_date = series.max()
        mean_date = series.mean()
        median_date = series.median()

        # Convert datetime to string format for reporting using pd.Timestamp
        min_date_str = pd.Timestamp(min_date).strftime('%Y-%m-%d') if pd.notna(min_date) else None
        max_date_str = pd.Timestamp(max_date).strftime('%Y-%m-%d') if pd.notna(max_date) else None
        mean_date_str = pd.Timestamp(mean_date).strftime('%Y-%m-%d') if pd.notna(mean_date) else None
        median_date_str = pd.Timestamp(median_date).strftime('%Y-%m-%d') if pd.notna(median_date) else None
        
        date_range = (max_date - min_date).days if pd.notna(max_date) and pd.notna(min_date) else None
        total_days = date_range  # Same as date_range in this context
        missing_values = series.isna().sum()
        unique_values = series.nunique()
        most_common_date = series.mode().values[0] if not series.mode().empty else None
        
        # Convert most_common_date to string format using pd.Timestamp
        most_common_date_str = pd.Timestamp(most_common_date).strftime('%Y-%m-%d') if pd.notna(most_common_date) else None

        # Return all metrics as a pandas Series
        return pd.Series({
            'Min Date': min_date_str,
            'Max Date': max_date_str,
            'Mean Date': mean_date_str,
            'Median Date': median_date_str,
            'Date Range (Days)': date_range,
            'Total Days': total_days,
            'Missing Values': missing_values,
            'Unique Values': unique_values,
            'Most Common Date': most_common_date_str
        })


    # def string_metrics(self, series: pd.Series) -> pd.Series:
    #     return pd.Series({
    #         'Most Frequent': series.mode()[0] if not series.mode().empty else np.nan,
    #         'Unique Values': series.nunique(),
    #         'Missing Values': series.isna().sum(),
    #         'Empty Strings': (series == '').sum()
    #     })



    def string_metrics(self, series: pd.Series) -> pd.Series:
        # Clean the series
        series = series.fillna('')
        
        # Calculate basic string statistics
        most_frequent = series.mode()[0] if not series.mode().empty else np.nan
        unique_values = series.nunique()
        missing_values = series.isna().sum()
        empty_strings = (series == '').sum()
        
        # String length statistics
        lengths = series.apply(len)
        longest_string = lengths.max()
        shortest_string = lengths.min()
        average_length = lengths.mean()
        
        # Character frequency (top 10 characters)
        char_freq = pd.Series(''.join(series).replace(' ', '')).value_counts().head(10)
        
        # Word frequency (top 10 words, if applicable)
        words = series.str.split(expand=True).stack()
        word_freq = words.value_counts().head(10)
        
        # Return all metrics as a pandas Series
        return pd.Series({
            'Most Frequent': most_frequent,
            'Unique Values': unique_values,
            'Missing Values': missing_values,
            'Empty Strings': empty_strings,
            'Longest String Length': longest_string,
            'Shortest String Length': shortest_string,
            'Average String Length': average_length,
            # 'Top 10 Characters': char_freq.to_dict(),
            'Top 10 Words': word_freq.to_dict()
        })



    def boolean_metrics(self, series: pd.Series) -> pd.Series:
        return pd.Series({
            'True Count': (series == True).sum(),
            'False Count': (series == False).sum(),
            'Missing Values': series.isna().sum()
        })

    def data_type_summaries(self) -> Dict[str, pd.DataFrame]:
        if self.df is None:
            raise ValueError("DataFrame is not set.")

        summaries = {}
        metrics_funcs = {
            np.number: self.numeric_metrics,
            'datetime64[ns]': self.datetime_metrics,
            'object': self.string_metrics,
            'bool': self.boolean_metrics
        }

        for dtype, metrics_func in metrics_funcs.items():
            type_columns = self.df.select_dtypes(include=[dtype])
            summary_list = []

            for column in type_columns:
                metrics = metrics_func(self.df[column])
                metrics.name = column
                summary_list.append(pd.DataFrame(metrics).T)

            if summary_list:
                summary_df = pd.concat(summary_list)
                summary_df.reset_index(inplace=True)
                summary_df.rename(columns={'index': 'Column Name'}, inplace=True)
                summary_df = summary_df.sort_values(by='Column Name').reset_index(drop=True)
                summaries[str(dtype)] = summary_df

        # Printing DataFrames in a readable format
        for dtype, summary_df in summaries.items():
            print(f"\nData Type: {dtype}")
            if get_ipython() is not None:  # Check if running in Jupyter Notebook
                display(summary_df)
            else:
                print(summary_df.to_string(index=False))  # Print DataFrame as string

        return summaries









    def data_type_summaries(self) -> Dict[str, pd.DataFrame]:
        """
        Get comprehensive metrics for each data type in the DataFrame and return them as a dictionary of DataFrames.
        
        Returns:
            Dict[str, pd.DataFrame]: Comprehensive metrics for each data type, separated into individual DataFrames.
        """
        if self.df is None:
            raise ValueError("DataFrame is not set.")

        # Dictionary to hold DataFrames for each data type
        summaries = {}

        # Metrics calculation functions for each data type
        metrics_funcs = {
            np.number: self.numeric_metrics,
            'datetime64[ns]': self.datetime_metrics,
            'object': self.string_metrics,
            'bool': self.boolean_metrics
        }

        # Calculate and store metrics for each data type
        for dtype, metrics_func in metrics_funcs.items():
            type_columns = self.df.select_dtypes(include=[dtype])
            summary_list = []

            for column in type_columns:
                metrics = metrics_func(self.df[column])
                metrics.name = column
                summary_list.append(pd.DataFrame(metrics).T)

            if summary_list:
                summary_df = pd.concat(summary_list)
                summary_df.reset_index(inplace=True)
                summary_df.rename(columns={'index': 'Column Name'}, inplace=True)
                summary_df = summary_df.sort_values(by='Column Name').reset_index(drop=True)
                summaries[str(dtype)] = summary_df

        return summaries






    def correlation_matrix(self) -> pd.DataFrame:
        """
        Generate a correlation matrix for numeric columns in the DataFrame.
        
        Returns:
            pd.DataFrame: Correlation matrix of numeric columns.
        """
        if self.df is None:
            raise ValueError("DataFrame is not set.")
        
        corr_matrix = self.df.corr()
        print("\nCorrelation Matrix:")
        print(corr_matrix)
        return corr_matrix

    def missing_value_heatmap(self):
        """
        Plot a heatmap of missing values in the DataFrame.
        """
        if self.df is None:
            raise ValueError("DataFrame is not set.")
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(self.df.isnull(), cbar=False, cmap='viridis', yticklabels=False)
        plt.title("Missing Values Heatmap")
        plt.show()

    def detect_outliers(self) -> Dict[str, pd.DataFrame]:
        """
        Detect outliers using the IQR method for numeric columns.
        
        Returns:
            Dict[str, pd.DataFrame]: Outliers for each numeric column.
        """
        if self.df is None:
            raise ValueError("DataFrame is not set.")
        
        outliers = {}
        numeric_cols = self.df.select_dtypes(include=[float, int]).columns
        
        for col in numeric_cols:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_data = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
            outliers[col] = outlier_data
            
            print(f"\nOutliers in Column: {col}")
            print(outlier_data)
        
        return outliers

    def unique_value_counts(self) -> pd.DataFrame:
        """
        Count unique values for each column in the DataFrame.
        
        Returns:
            pd.DataFrame: Unique value counts for each column.
        """
        if self.df is None:
            raise ValueError("DataFrame is not set.")
        
        unique_counts = self.df.nunique()
        print("\nUnique Value Counts for Each Column:")
        print(unique_counts)
        return unique_counts

    def create_profiles(self) -> Dict[str, Dict[str, Any]]:
        if self.df is None:
            raise ValueError("DataFrame is not set.")
        
        profiles = {}
        
        for column in self.df.columns:
            col_data = self.df[column]
            column_profile = {
                "Count": col_data.notna().sum(),
                "Empty": col_data.isna().sum(),
                "Distinct": col_data.dropna().nunique(),
                "Unique": len(col_data.dropna().unique()),
                "Empty String": (col_data == '').sum() if col_data.dtype == object else None,
                "Mode": col_data.mode().tolist() if not col_data.mode().empty else None,
                "Top": col_data.mode()[0] if not col_data.mode().empty else None,
            }

            # Add metrics based on column data type
            if pd.api.types.is_numeric_dtype(col_data):
                column_profile.update({
                    "Min": col_data.min(),
                    "Max": col_data.max(),
                    "Mean": col_data.mean(),
                    "Median": col_data.median(),
                    "Standard Deviation": col_data.std()
                })
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                column_profile.update({
                    "Min": col_data.min(),
                    "Max": col_data.max(),
                    "Range": col_data.max() - col_data.min()
                })
            elif pd.api.types.is_bool_dtype(col_data):
                column_profile.update({
                    "True Count": (col_data == True).sum(),
                    "False Count": (col_data == False).sum()
                })

            profiles[column] = column_profile

        self._print_profiles(profiles)
        return profiles

    def _print_profiles(self, profiles: Dict[str, Dict[str, Any]]):
        print("\nDataFrame Column Profiles:")
        for column, profile in profiles.items():
            print(f"\nColumn: {column}")
            for metric, value in profile.items():
                print(f"  {metric}: {value}")
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

        case_sensitive : bool, optional (default=False)
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
            Returns an empty dictionary if no match is found or if columns_list is invalid.
        """
        result = {}

        # Ensure the search column exists
        if search_column not in df.columns:
            raise ValueError(f"Search column '{search_column}' not found in DataFrame")

        # Clean NaN values from search column without modifying the original DataFrame
        search_series = df[search_column].dropna().astype(str)

        # Modify lookup_str and search column based on case sensitivity
        if not case_sensitive:
            search_series = search_series.str.lower()
            lookup_str = lookup_str.lower()

        # Perform search based on exact or substring match
        if exact_match:
            matches = df[search_series == lookup_str]
        else:
            pattern = re.escape(lookup_str)
            matches = df[search_series.str.contains(pattern, case=case_sensitive, na=False)]

        # If matches found, retrieve values from specified columns
        if not matches.empty:
            for col in columns_list:
                if col in matches.columns:
                    result[col] = matches[col].values[0]
                else:
                    raise ValueError(f"Column '{col}' not found in DataFrame")
        
        return result
