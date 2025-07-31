import pandas as pd

def load_data(filepath: str) -> pd.DataFrame:
    """
    Load and clean a CSV file:
    - Standardizes column names
    - Converts 'month' column to datetime

    Parameters:
        filepath (str): Path to CSV file.

    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    df['month'] = pd.to_datetime(df['month'], format="%b %Y", errors='coerce')
    return df
