"""
Filter utilities for Nielsen data processing and bracket creation.

Includes logic for loading filter configs, applying filters, determining grouping,
and creating exclusive bracket groupings for age and income.
"""


import json
import pandas as pd

def load_filter_config(filter: str) -> dict[str, list[str] | str]:
    """Load filter configuration from JSON."""
    with open(f'config/{filter}.json') as f:
        return json.load(f)

def apply_filters(df: pd.DataFrame, config: dict[str, list[str] | str]) -> pd.DataFrame:
    """Filter df by 'daypart', 'demographic', and 'characteristic' from a configuration dict."""
    cols_to_filter = ['daypart', 'demographic', 'characteristic']
    for key, val in config.items():
        if key in cols_to_filter:
            if isinstance(val, list): df = df[df[key].isin(val)]
            else: df = df[df[key] == val]
    return df

def get_group_column(config: dict[str, list[str] | str]) -> str | None:
    """Return name of first column with multiple values, or None if none found."""
    for key in ['daypart', 'demographic', 'characteristic', 'income_bracket', 'age_bracket']:
        val = config.get(key)
        if isinstance(val, list) and len(val) > 1:
            return key
    return None

def set_ordered_categories(
    df: pd.DataFrame, group_col: str | None, 
    config: dict[str, list[str] | str]
 ) -> pd.DataFrame:
    """Set category order for plotly legends, if grouping column exists in config."""
    if group_col and isinstance(config.get(group_col), list):
        df[group_col] = pd.Categorical(
            df[group_col],
            categories=config[group_col],
            ordered=True
        )
    return df
    
def create_wide_brackets(
    df: pd.DataFrame,
    group_cols: list[str],
    source_col: str,
    bracket_expr: dict[str, tuple[str, ...]],
    metrics = ['reach_imp', 'grp_imp']
) -> pd.DataFrame:
    """
    Creates exclusive bracket columns (wide format) from overlapping category data.

    Parameters:
        df (pd.DataFrame): The input DataFrame.
        group_cols (list of str): Columns to group by (e.g., ['month', 'demographic']).
        source_col (str): Name of column containing overlapping categories
                          (e.g., 'characteristic' or 'age_group').
        bracket_expr (dict): A mapping of new bracket names to tuples that define how to 
                             calculate each bracket from overlapping categories: the first label is 
                             is added, and any remaining labels are subtracted.
        metrics (list of str, optional): List of metric columns to apply bracket calculations to.
                                 Defaults to ['reach_imp', 'grp_imp'].

    Returns:
        pd.DataFrame: A wide-format DataFrame with summed values for each exclusive bracket
                      and each metric (e.g., 'reach_imp_25_50k', 'grp_imp_25_50k').
    """    
    df = df.copy()    
    bracket_data = {col: df[col] for col in group_cols}

    for metric in metrics:
        for name, expr in bracket_expr.items():
            col = f'{metric}_{name}'
            if len(expr) == 1:
                bracket_data[col] = df[metric].where(df[source_col] == expr[0], 0)
            else:
                result = df[metric].where(df[source_col] == expr[0], 0)
                for subtract in expr[1:]:
                    result -= df[metric].where(df[source_col] == subtract, 0)
                bracket_data[col] = result

    bracket_df = pd.DataFrame(bracket_data)
    return bracket_df.groupby(group_cols, as_index=False).sum()

def melt_brackets(
    df: pd.DataFrame,
    group_cols: list[str],
    bracket_labels_map: dict[str, str],
    bracket_col: str = 'bracket',
    metrics: list[str] = ['reach_imp', 'grp_imp']    
) -> pd.DataFrame:
    """
    Converts wide bracket columns into long bracket rows with multiple metric columns.
    
    Parameters:
        df (pd.DataFrame): The wide-format DataFrame with bracket columns (e.g., 'reach_imp_25_50k').
        group_cols (list of str): Columns to retain as identifiers during the melt.
        bracket_labels_map (dict): Mapping from internal bracket keys (e.g., '25_50k') to display labels
                                  (e.g., '$25K–$50K').
        bracket_col (str): Name of bracket column.                            
        metrics (list of str, optional): List of metric columns to apply bracket calculations to.
                                         Defaults to ['reach_imp', 'grp_imp'].

    Returns a DataFrame with one row per [group + bracket] and one column per metric.
    """
    bracket_names = list(bracket_labels_map.keys())
    records = []

    for bracket in bracket_names:
        row_group = df[group_cols].copy()
        row_group[bracket_col] = bracket_labels_map[bracket]
        for metric in metrics:
            col = f"{metric}_{bracket}"
            if col in df.columns:
                row_group[metric] = df[col]
        records.append(row_group)

    melted = pd.concat(records, ignore_index=True)
    melted[bracket_col] = melted[bracket_col].astype(str)
    return melted



def create_income_brackets(df: pd.DataFrame, melt: bool = True) -> pd.DataFrame:
    """
    Wrapper to generate exclusive income bracket data from overlapping income categories.

    Parameters:
        df (pd.DataFrame): Input DataFrame with 'characteristic' column for income categories.
        melt (bool): If True, returns long-format DataFrame; if False, returns wide-format.

    Returns:
        pd.DataFrame: Income bracket data (wide or long format) for 'reach_imp' and 'grp_imp'.
    """   
    bracket_expr = {
        '0_25k': ('Less than $25K',),
        '25_50k': ('$25K+', '$50K+'),
        '50_75k': ('$50K+', '$75K+'),
        '75_100k': ('$75K+', '$100K+'),
        '100_200k': ('$100K+', '$200K+'),
        '200k_plus': ('$200K+',),
    }
    bracket_labels = {
        '0_25k': 'Less than $25K',
        '25_50k': '$25K-$50K',
        '50_75k': '$50K-$75K',
        '75_100k': '$75K-$100K',
        '100_200k': '$100K-$200K',
        '200k_plus': '$200K+',
    }
    group_cols = ['daypart', 'demographic', 'month']
    wide_df = create_wide_brackets(df, group_cols, 'characteristic', bracket_expr)
    return melt_brackets(wide_df, group_cols, bracket_labels, 'income_bracket') if melt else wide_df

def create_age_brackets(df: pd.DataFrame, melt: bool = True) -> pd.DataFrame:
    """
    Wrapper to generate exclusive age bracket data from overlapping age categories.

    Parameters:
        df (pd.DataFrame): Input DataFrame with 'demographic' column for age categories.
        melt (bool): If True, returns long-format DataFrame; if False, returns wide-format.

    Returns:
        pd.DataFrame: Age bracket data (wide or long format) for 'reach_imp' and 'grp_imp'.
    """    
    bracket_expr = {
        'P2_11': ('P2-11',),
        'P12_17': ('P2+', 'P2-11', 'P18+'),
        'P18_34': ('P18+', 'P35-64', 'P65+'),
        'P35_64': ('P35-64',),
        'P65_plus': ('P65+',),
    }
    bracket_labels = {
        'P2_11': 'Ages 2-11',
        'P12_17': 'Ages 12-17',
        'P18_34': 'Ages 18-34',
        'P35_64': 'Ages 35-64',
        'P65_plus': 'Ages 65+',
    }
    group_cols = ['daypart', 'characteristic', 'month']
    wide_df = create_wide_brackets(df, group_cols, 'demographic', bracket_expr)
    return melt_brackets(wide_df, group_cols, bracket_labels, 'age_bracket') if melt else wide_df
