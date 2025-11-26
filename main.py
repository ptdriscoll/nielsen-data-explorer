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
import argparse
import pandas as pd
from src import utils, filters, plotting, update_dashboard

# custom values
DATA_FILE = '2023-01_2025-09.csv'
OUTPUT_DIR = 'output'

DATA_PATH = os.path.join('data', DATA_FILE)
HTML_OUTPUT_DIR = os.path.join(OUTPUT_DIR, 'html')
CSV_OUTPUT_DIR = os.path.join(OUTPUT_DIR, 'csv')

ALL_METRICS = [     
    'avg_freq', 
    'reach%',
    'grp_imp',
    'reach_imp'
]
ALL_FILTERS = [
    'age-brackets',
    'age-levels',
    'dayparts',
    'income-brackets',
    'income-levels',
    'race',
    'totals'
]
ALL_PLOTS = ['bar', 'timeline']

def make_plot(df: pd.DataFrame, metric: str, filter: str, plot: str, 
              month_dt: pd.Timestamp, compare_dt: pd.Timestamp) -> None:
    # filter data
    config = filters.load_filter_config(filter)
    df = filters.apply_filters(df, config)     

    # handle custom bracket columns, if needed
    error_msg = (
        f'For the filters "income-brackets" or "age-brackets", only the metrics '
        f'"reach_imp" and "grp_imp" are allowed, not "{metric}".'
    )
    
    if filter == 'income-brackets':
        if metric not in ['reach_imp', 'grp_imp']: raise ValueError(error_msg)
        df = filters.create_income_brackets(df, metric)
    
    elif filter == 'age-brackets':
        if metric not in ['reach_imp', 'grp_imp']: raise ValueError(error_msg)
        df = filters.create_age_brackets(df, metric)
        
    df.to_csv(os.path.join(CSV_OUTPUT_DIR, 'working-data.csv'), index=False)  

    # set group column/s
    group_cols = ['month']
    group_col = filters.get_group_column(config) # column name, or None   
    if group_col: group_cols.append(group_col)    
    
    # plot
    metric_filename = metric.replace('_', '-')
    output_html = os.path.join(HTML_OUTPUT_DIR, f'{plot}_{filter}_{metric_filename}.html')
    title = f'{plotting.clean(metric)} for {config["title"]}'

    if plot == 'timeline':
        # filter range of months (inclusive)
        df_timeline = df[(df['month'] >= compare_dt) & (df['month'] <= month_dt)]

        # aggregate trend, and set legend order for plot if applicable 
        trend = df_timeline.groupby(group_cols, as_index=False)[metric].sum()
        trend = filters.set_ordered_categories(trend, group_col, config)        
        
        plotting.plot_timeline(
            trend, 
            x='month', 
            y=metric, 
            color=group_col,
            title=title, 
            output_file=output_html, 
            config=config)
        
    if plot == 'bar':
        # keep only selected months
        months = [month_dt]
        if compare_dt: months.append(compare_dt)
        df_bar = df[df['month'].isin(months)]
 
        # aggregate by month/s and any categories, and format month
        bar = df_bar.groupby(group_cols, as_index=False)[metric].sum()
        bar['month'] = bar['month'].dt.strftime('%b %Y')
    
        # force category order for grouping column
        bar = filters.set_ordered_categories(bar, group_col, config)
    
        # append title
        month_label = month_dt.strftime('%b %Y')
        comparison = f'{compare_dt.strftime("%b %Y")} vs. ' if compare_dt else ''
        title += f' - {comparison}{month_label}'
    
        plotting.plot_bar(
            bar,
            x=group_col if group_col else 'month',
            y=metric,
            color='month' if group_col and len(months) > 1 else None,
            title=title,
            output_file=output_html, 
        )    
    

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--metric', default='reach_imp',
                        help=('metric to plot (e.g., reach_imp, grp_imp, "reach%%", avg_freq), but for the '
                              'filters income-brackets and age-brackets, only reach_imp and grp_imp apply'))
    parser.add_argument('-f', '--filter', default='totals', 
                        help='name of JSON filter (without file extension) in config/')
    parser.add_argument('-p', '--plot', choices=['timeline', 'bar'], default='timeline')
    parser.add_argument('--month', help='Month to plot for bar chart, or timeline\'s end month, in YYYY-MM format')
    parser.add_argument('--compare-month', help='Optional comparison month for bar chart, or timeline\'s start month, in YYYY-MM format') 
    parser.add_argument('-a', '--run-all', action='store_true', help='Run plots for all filters and metrics')
    parser.add_argument('-d', '--dashboard', action='store_true', help='Update and open local index.html dashboard')
    
    args = parser.parse_args()

    print()
    print(args)

    # if command calls for updating and opening dashboard, do that and exit early
    if args.dashboard:
        update_dashboard.run(open_webbrowser=True)
        return

    # load data
    df = utils.load_data(DATA_PATH)
    month_dt, compare_dt = utils.get_selected_months(df, args)
    
    # create output directories
    for directory in [HTML_OUTPUT_DIR, CSV_OUTPUT_DIR]:
        os.makedirs(directory, exist_ok=True)

    # run all plots
    if args.run_all:
        for filter in ALL_FILTERS:
            print()
            for metric in ALL_METRICS:                
                for plot in ALL_PLOTS:
                    if filter in ['age-brackets', 'income-brackets'] and metric not in ['reach_imp', 'grp_imp']:
                        print(f'Skipping {plot} for {filter} / {metric}: invalid combination.')
                        continue
                    print(f'Running {plot} for {filter} / {metric}')
                    try:
                        make_plot(df, metric, filter, plot, month_dt, compare_dt)
                    except Exception as e:
                        print(f'Skipped {plot} for {filter} / {metric}: {e}')

        update_dashboard.run()
        return    

    # run just one plot
    make_plot(df, args.metric, args.filter, args.plot, month_dt, compare_dt)    
    update_dashboard.run()     

# only run when this script is executed directly
if __name__ == '__main__':
    main()
