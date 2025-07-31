"""
Main entry point for Nielsen Data Explorer CLI tool.

This script loads audience data, applies filters, and generates plots
(timelines or bar charts) based on specified metrics and configurations.

Usage examples:
    python main.py
    python main.py --filter dayparts --metric "reach%"
    python main.py --filter age-brackets
    python main.py --plot bar --filter income-brackets --month 2025-03
    python main.py --plot bar --filter race --month 2025-03 --compare-month 2023-03
"""


import os
import argparse, webbrowser
import pandas as pd
from src import utils, filters, plotting

# custom values
DATA_FILE = '2023-01_2025-03.csv'
OUTPUT_DIR = 'output'

DATA_PATH = os.path.join('data', DATA_FILE)
HTML_OUTPUT_DIR = os.path.join(OUTPUT_DIR, 'html')
CSV_OUTPUT_DIR = os.path.join(OUTPUT_DIR, 'csv')

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--metric', default='reach_imp',
                        help=(
                             'metric to plot (e.g., reach_imp, grp_imp, "reach%%", avg_freq), but for the '
                             'filters income-brackets and age-brackets, only reach_imp and grp_imp apply'))
    parser.add_argument('-f', '--filter', default='totals', 
                        help='name of JSON filter (without file extension) in config/')
    parser.add_argument('-p', '--plot', choices=['timeline', 'bar'], default='timeline')
    parser.add_argument('--month', help='Month to plot, in YYYY-MM format')
    parser.add_argument('--compare-month', help='Optional comparison month in YYYY-MM format') 
    
    args = parser.parse_args()

    # load and filter data
    df = utils.load_data(DATA_PATH)
    config = filters.load_filter_config(args.filter)
    df = filters.apply_filters(df, config) 
    
    # create output directories
    for directory in [HTML_OUTPUT_DIR, CSV_OUTPUT_DIR]:
        os.makedirs(directory, exist_ok=True)

    # handle custom bracket columns, if needed
    error_msg = (
        f"For the filters 'income-brackets' or 'age-brackets', only the metrics "
        f"'reach_imp' and 'grp_imp' are allowed, not '{args.metric}'."
    )
    
    if args.filter == 'income-brackets':
        if args.metric not in ['reach_imp', 'grp_imp']:
            raise ValueError(error_msg)
        df = filters.create_income_brackets(df, args.metric)
    
    elif args.filter == 'age-brackets':
        if args.metric not in ['reach_imp', 'grp_imp']:
            raise ValueError(error_msg)
        df = filters.create_age_brackets(df, args.metric)
        
    df.to_csv(os.path.join(CSV_OUTPUT_DIR, 'working-data.csv'), index=False)  

    # set group column/s
    group_cols = ['month']
    group_col = filters.get_group_column(config) # column name, or None   
    if group_col: group_cols.append(group_col)    
    
    # plot
    output_html = os.path.join(HTML_OUTPUT_DIR, f'{args.plot}_{args.filter}_{args.metric}.html')
    title = f'{plotting.clean(args.metric)} for {config["title"]}'

    if args.plot == 'timeline':
        # aggregate trend, and set legend order for plot if applicable 
        trend = df.groupby(group_cols, as_index=False)[args.metric].sum()
        trend = filters.set_ordered_categories(trend, group_col, config)        
        
        plotting.plot_timeline(
            trend, 
            x='month', 
            y=args.metric, 
            color=group_col,
            title=title, 
            output_file=output_html, 
            config=config)
        
    if args.plot == 'bar':
        # filter by months
        months = [args.month or df['month'].max().strftime('%Y-%m')]        
        if args.compare_month: months.append(args.compare_month)    
        try: months = pd.to_datetime(months, format='%Y-%m') 
        except ValueError as e: raise ValueError('Month format must be YYYY-MM, e.g., 2025-03') from e
        df = df[df['month'].isin(months)]
        
        # aggregate by month/s and any categories, and format month
        bar_df = df.groupby(group_cols, as_index=False)[args.metric].sum()
        bar_df['month'] = bar_df['month'].dt.strftime('%b %Y')
    
        # force category order for grouping column
        bar_df = filters.set_ordered_categories(bar_df, group_col, config)
    
        # append title
        month_label = months[0].strftime('%b %Y')
        comparison = f"{months[1].strftime('%b %Y')} vs. " if len(months) > 1 else ""
        title += f" - {comparison}{month_label}"
    
        plotting.plot_bar(
            bar_df,
            x=group_col if group_col else 'month',
            y=args.metric,
            color='month' if group_col and len(months) > 1 else None,
            title=title,
            output_file=output_html, 
        )
        
    webbrowser.open(output_html)     

# only run when this script is executed directly
if __name__ == '__main__':
    main()
