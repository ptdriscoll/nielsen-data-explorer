import os
from pathlib import Path
import re
import webbrowser

# mapping of filename parts to friendly display names
rename_map = {     
    'avg-freq': 'Average Frequency', 
    'reach%': 'Reach Percentage',
    'grp-imp': 'Group Impressions',
    'reach-imp': 'Reach Impressions',
    'age-brackets': 'Age Brackets',
    'age-levels': 'Age Levels',
    'dayparts': 'Dayparts',
    'income-brackets': 'Income Brackets',
    'income-levels': 'Income Levels',
    'race': 'Race and Ethnicity',
    'totals': 'Totals',
    'bar': 'Bar Chart',
    'timeline': 'Timeline'
}

def display_name(filename: str, rename_map: dict) -> str:
    """Convert a filename into a friendly display name."""
    name = filename.rsplit('.', 1)[0]  # remove .html
    parts = name.split('_')
    friendly_parts = [
        rename_map.get(part, part.replace('-', ' ').replace('_', ' ').title())
        for part in parts
    ]
    return ' | '.join(friendly_parts) if len(friendly_parts) > 1 else friendly_parts[0]
    
def run(open_webbrowser=False):
    html_dir = Path('output/html')
    output_path = Path('index.html')

    if not html_dir.exists():
        print(f'Directory not found: {html_dir}')
        return
    
    # get list of .html files (preserve directory order), and determine newest file
    files = [f for f in html_dir.iterdir() if f.is_file() and f.suffix == '.html']

    # build HTML <select> element
    if not files:
        select_block = '      <p>No files to display.</p>'
    else:
        newest_file = max(files, key=lambda f: f.stat().st_mtime).name
        option_lines = []
        for f in files:
            selected_attr = ' selected' if f.name == newest_file else ''
            selected_name = display_name(f.name, rename_map)
            option_lines.append(f'        <option value="output/html/{f.name}"{selected_attr}>{selected_name}</option>')
        
        options = '\n'.join(option_lines)
        select_block = (
            '      <select id="plotSelect">\n'
            f'{options}\n'
            '      </select>'
        )

    # read HTML file
    html = output_path.read_text(encoding='utf-8')

    # replace <select> element
    updated_html = re.sub(
        r' {6}<select id=\"plotSelect\">.*?</select>',
        select_block,
        html,
        flags=re.DOTALL
    )   

    # write updated html 
    output_path.write_text(updated_html, encoding='utf-8')

    print(f'\nDashboard updated: {output_path}')

    # open dashboard if flagged to open
    if open_webbrowser: webbrowser.open(output_path.resolve().as_uri(), new=0)

if __name__ == '__main__':
    run(open_webbrowser=True)
