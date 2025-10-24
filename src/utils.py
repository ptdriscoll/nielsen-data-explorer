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

def get_selected_months(df: pd.DataFrame, args)-> tuple[pd.Timestamp, pd.Timestamp | None]:
    """
    Determine which months to use for plotting based on args and available data.

    Parameters:
        df (pd.DataFrame): The dataset containing a 'month' column.
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        tuple[pd.Timestamp, pd.Timestamp | None]: (month_dt, compare_dt)
            For bar charts:
                - month_dt is the main month (defaults to latest)
                - compare_dt is optional
            For timelines:
                - month_dt is the end month (defaults to latest)
                - compare_dt is the start month (defaults to earliest)
    """
    latest = df['month'].max()
    earliest = df['month'].min()

    month = args.month or latest.strftime('%Y-%m')
    if args.plot == 'timeline': compare = args.compare_month or earliest.strftime('%Y-%m')
    else: compare = args.compare_month

    try:
        month_dt = pd.to_datetime(month, format='%Y-%m')
        compare_dt = pd.to_datetime(compare, format='%Y-%m') if compare else None 
    except ValueError as e:
        raise ValueError('Month format must be YYYY-MM, e.g., 2025-03') from e

    return month_dt, compare_dt
