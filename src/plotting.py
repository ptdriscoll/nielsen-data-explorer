import re
import plotly.express as px
from plotly.graph_objs import Figure
import pandas as pd

def clean(s: str) -> str:
    """Replace '_' and '-' and extra spaces in string, and capitalize words."""
    if s:
        s = s.replace('_', ' ').replace('-', ' ')
        s = re.sub(r'\s+', ' ', s).strip()
        return ' '.join(word.capitalize() for word in s.split())
    return ''

def common_layout(
    fig: Figure,
    title: str,
    x: str,
    y: str,
    color: str | None = None,
    df: pd.DataFrame | None = None
) -> Figure:    
    """
    Applies common layout to a Plotly figure, including title, axis labels,
    tick formatting, and optional color legend.

    Args:
        fig (Figure): Plotly figure to format.
        title (str): Title to display at the top of chart.
        x (str): Name of column for x-axis.
        y (str): Name column for y-axis.
        color (str, optional): Column name used for color grouping, to determine legend display.
        df (pd.DataFrame, optional): DataFrame used to get max y value.

    Returns:
        Figure: The updated Plotly figure with applied layout.
    """
    font_family = '"Open Sans", verdana, arial, sans-serif'
    font_color = 'rgb(71, 71, 71)'
    y_max = df[y].max() * 1.12 if df is not None and y in df else None
    
    fig.update_layout(
        font=dict(size=16, family=font_family, color=font_color),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=100, r=50, t=90, b=60),
        showlegend=bool(color),
        title=dict(
            text=title,
            font=dict(size=22, family=font_family, color=font_color)
        ),
        xaxis_title=None,         
        xaxis=dict(
            title=clean(x),
            color=font_color,
            title_font=dict(color=font_color),
            tickfont=dict(color=font_color)
        ),
        yaxis=dict(
            title=clean(y),
            color=font_color,
            title_font=dict(color=font_color),
            tickfont=dict(color=font_color),
            range=[0, y_max] if y_max else None
        ),
        hoverlabel=dict(
            font_color='white',
            bordercolor='white'
        ),
    )
    return fig

def format_tooltip(df: pd.DataFrame, x: str, y: str, color: str | None = None) -> tuple[str, str]:
    """
    Adds formatted columns to `df` and returns hovertemplate + customdata list.

    Args:
        df (pd.DataFrame): The dataframe used in the plot.
        x (str): Column name for x-axis, expected to be a date/month or label column.
        y (str): Column name for metric to be formatted as comma-separated integer.
        color (str, optional): Column name for color grouping.

    Returns:
        tuple[str, str]: A tuple containing:
            - hovertemplate (str): A Plotly-formatted string for displaying tooltips.
            - customdata (str): A comma-separated string of column names used in customdata.
    """
    if pd.api.types.is_datetime64_any_dtype(df[x]):         
        df['x_fmt'] = pd.to_datetime(df[x]).dt.strftime('%b %Y') # like 'Apr 2025'
    else:
        df['x_fmt'] = df[x].astype(str)
        
    df['metric_fmt'] = df[y].apply(lambda x: f'{int(round(x)):,}') # like 36,720
    
    custom_cols = ['x_fmt', 'metric_fmt']
    if color: custom_cols.append(color)

    if pd.api.types.is_datetime64_any_dtype(df[x]):
        hovertemplate = (
            f'{clean(x)}: %{{customdata[0]}}<br>'
            f'{clean(y)}: %{{customdata[1]}}'
            + (f'<br>{clean(color)}: %{{customdata[2]}}' if color else '')
            + '<extra></extra>'
        )
    else:
        hovertemplate = (
            (f'{clean(color)}: %{{customdata[2]}}<br>' if color else '')
            + f'{clean(y)}: %{{customdata[1]}}<br>'
            f'{clean(x)}: %{{customdata[0]}}'
            '<extra></extra>'
        )

    return hovertemplate, custom_cols

def plot_timeline(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str,
    output_file: str,
    config: dict | None = None
) -> Figure:    
    """
    Create a line chart showing trends over time, with optional grouping.
    
    Parameters:
        df (pd.DataFrame): The input DataFrame.
        x (str): Column to use for the x-axis (datetime).
        y (str): Column to use for the y-axis (metric being measured).
        color (str): Column to group by color.
        title (str): Title for plot.        
        output_file (str): Saves HTML to this path.
        config (dict, optional): Filter configuration, including potential color column.
    
    Returns:
        plotly.graph_objs.Figure: The generated Plotly figure.
    """
    hovertemplate, custom_cols = format_tooltip(df, x, y, color)   
    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        markers=True,
        labels={x: clean(x), y: clean(y), color: clean(color) if color else None},
        category_orders={color: config[color]} if color and config and config.get(color) else {},
        custom_data=custom_cols, 
        template='simple_white',
    )
    fig = common_layout(fig, title, x, y, color, df)
    fig.update_traces(line=dict(width=4), marker=dict(size=4))
    fig.update_traces(hovertemplate=hovertemplate)    
    fig.write_html(output_file)
    return fig

def plot_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str,
    output_file: str
) -> Figure:   
    """
    Create a bar chart with optional color grouping.
    
    Parameters:
        df (pd.DataFrame): The input DataFrame.
        x (str): Column to use for x-axis (categories).
        y (str): Column to use for y-axis (metric being measured).
        color (str): Column to group by color.
        title (str): Title for plot.
        output_file (str): Saves HTML to this path.
    
    Returns:
        plotly.graph_objs.Figure: The generated Plotly figure.
    """
    hovertemplate, custom_cols = format_tooltip(df, x, y, color) 
    
    category_orders = {}
    if x in df.columns and pd.api.types.is_categorical_dtype(df[x]):
        category_orders[x] = df[x].cat.categories.tolist()   
        
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        barmode='group' if color else 'relative',
        title=title,
        labels={x: clean(x), y: clean(y), color: clean(color) if color else None},
        category_orders=category_orders,
        custom_data=custom_cols,
        template='simple_white',
    )
    fig = common_layout(fig, title, x, y, color, df)
    fig.update_traces(marker=dict(line=dict(width=2, color='white')))
    fig.update_traces(hovertemplate=hovertemplate)
    fig.write_html(output_file)
    return fig
