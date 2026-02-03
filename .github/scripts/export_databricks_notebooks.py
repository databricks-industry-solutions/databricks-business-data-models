#!/usr/bin/env python3
"""
Export notebooks from Databricks workspace as HTML with consistent styling.
This script fetches executed notebooks from Databricks and wraps them with
consistent branding and navigation.
"""

import os
import json
import requests
import re
import base64
import glob
from pathlib import Path

# Configuration
DATABRICKS_HOST = os.environ.get('DATABRICKS_HOST', 'https://e2-demo-field-eng.cloud.databricks.com')
DATABRICKS_TOKEN = os.environ.get('DATABRICKS_TOKEN', '')

# Databricks brand colors
COLORS = {
    'primary': '#FF3621',
    'text': '#1B3139',
    'bg': '#FFFFFF', 
    'light_bg': '#F5F5F5',
    'border': '#E3E3E3'
}

def list_workspace_notebooks():
    """List all notebooks in the workspace"""
    headers = {'Authorization': f'Bearer {DATABRICKS_TOKEN}'}
    
    # You can customize this path based on your workspace structure
    workspace_path = '/Workspace/Users'
    
    response = requests.get(
        f"{DATABRICKS_HOST}/api/2.0/workspace/list",
        headers=headers,
        params={'path': workspace_path}
    )
    
    if response.status_code == 200:
        return response.json().get('objects', [])
    return []

def export_notebook_html(notebook_path):
    """Export a single notebook as HTML"""
    headers = {'Authorization': f'Bearer {DATABRICKS_TOKEN}'}
    
    response = requests.get(
        f"{DATABRICKS_HOST}/api/2.0/workspace/export",
        headers=headers,
        params={
            'path': notebook_path,
            'format': 'HTML'
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        html_content = base64.b64decode(data['content']).decode('utf-8')
        return html_content
    else:
        print(f"Failed to export {notebook_path}: {response.status_code}")
        return None

def find_notebooks_in_workspace():
    """Find notebooks based on local notebook files"""
    # Look for notebooks in the local notebooks directory
    local_notebooks = []
    
    # Check for .py notebooks
    for py_file in glob.glob('notebooks/*.py'):
        name = os.path.splitext(os.path.basename(py_file))[0]
        local_notebooks.append(name)
    
    # Check for .ipynb notebooks
    for ipynb_file in glob.glob('notebooks/*.ipynb'):
        name = os.path.splitext(os.path.basename(ipynb_file))[0]
        local_notebooks.append(name)
    
    return local_notebooks

def create_wrapper_html(notebook_name, notebook_html, all_notebooks):
    """Create consistent wrapper for notebook HTML"""
    # Extract body content
    body_match = re.search(r'<body[^>]*>(.*?)</body>', notebook_html, re.DOTALL)
    body_content = body_match.group(1) if body_match else notebook_html
    
    # Extract styles
    style_content = ""
    style_matches = re.findall(r'<style[^>]*>(.*?)</style>', notebook_html, re.DOTALL)
    for style in style_matches:
        style_content += style + "\n"
    
    repo_name = os.environ.get('GITHUB_REPOSITORY', '').split('/')[-1]
    title = ' '.join(word.capitalize() for word in repo_name.split('-')) + ' Accelerator'
    display_name = notebook_name.replace('_', ' ').title()
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>{display_name} - {title}</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Reset and base styles */
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            margin: 0;
            padding: 0;
            background: {COLORS['bg']};
            color: {COLORS['text']};
            font-size: 14px;
            line-height: 1.6;
        }}
        
        /* Header */
        .header {{
            background: {COLORS['bg']};
            padding: 20px 40px;
            border-bottom: 1px solid {COLORS['border']};
            display: flex;
            align-items: center;
            gap: 20px;
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 1000;
        }}
        
        .logo {{ height: 24px; }}
        
        .title {{
            font-size: 24px;
            font-weight: 600;
            flex: 1;
            text-align: center;
            color: {COLORS['text']};
        }}
        
        .github-link {{
            background: {COLORS['light_bg']};
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            color: {COLORS['text']};
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .github-link:hover {{
            background: {COLORS['border']};
        }}
        
        /* Layout */
        .main-container {{
            display: flex;
            margin-top: 80px;
            min-height: calc(100vh - 80px);
        }}
        
        .sidebar {{
            width: 280px;
            background: {COLORS['light_bg']};
            padding: 30px 20px;
            position: fixed;
            left: 0;
            top: 80px;
            height: calc(100vh - 80px);
            overflow-y: auto;
        }}
        
        .sidebar h3 {{
            font-size: 16px;
            font-weight: 600;
            margin: 0 0 20px 12px;
            color: {COLORS['text']};
        }}
        
        .content {{
            flex: 1;
            padding: 20px;
            margin-left: 280px;
        }}
        
        .notebook-container {{
            background: {COLORS['bg']};
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 40px;
            margin: 0 auto;
            max-width: 1200px;
        }}
        
        /* Navigation */
        .nav-link {{
            display: block;
            padding: 10px 12px;
            margin: 4px 0;
            text-decoration: none;
            color: {COLORS['text']};
            border-radius: 4px;
            font-weight: 400;
            transition: all 0.2s;
        }}
        
        .nav-link:hover {{
            background: {COLORS['bg']};
        }}
        
        .nav-link.active {{
            background: {COLORS['primary']};
            color: {COLORS['bg']};
            font-weight: 500;
        }}
        
        /* Databricks notebook overrides */
        .notebook-container h1,
        .notebook-container h2,
        .notebook-container h3,
        .notebook-container h4,
        .notebook-container h5,
        .notebook-container h6 {{
            font-family: 'DM Sans', sans-serif !important;
            color: {COLORS['text']} !important;
            font-weight: 600 !important;
            margin-top: 24px;
            margin-bottom: 16px;
        }}
        
        .notebook-container p,
        .notebook-container div,
        .notebook-container span {{
            font-family: 'DM Sans', sans-serif !important;
        }}
        
        .notebook-container code,
        .notebook-container pre {{
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace !important;
            background-color: {COLORS['light_bg']} !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 4px !important;
        }}
        
        .notebook-container pre {{
            padding: 16px !important;
            overflow-x: auto !important;
        }}
        
        .notebook-container code {{
            padding: 2px 6px !important;
        }}
        
        /* Output areas */
        .ansiout,
        .output_area,
        div[class*="output"] {{
            font-family: 'Monaco', 'Consolas', monospace !important;
            background: {COLORS['light_bg']} !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 4px !important;
            padding: 10px !important;
            margin: 10px 0 !important;
            overflow-x: auto !important;
        }}
        
        /* Tables */
        .notebook-container table {{
            border-collapse: collapse;
            margin: 16px 0;
            font-family: 'DM Sans', sans-serif !important;
        }}
        
        .notebook-container th,
        .notebook-container td {{
            border: 1px solid {COLORS['border']};
            padding: 8px 12px;
            text-align: left;
        }}
        
        .notebook-container th {{
            background: {COLORS['light_bg']};
            font-weight: 600;
        }}
        
        /* Original Databricks styles (scoped) */
        .notebook-container {{
            {style_content}
        }}
    </style>
</head>
<body>
    <div class="header">
        <img src="https://databricks-prod-cloudfront.cloud.databricks.com/static/811f68f9f55e3a5330b6e6ae1e54c07fc5ec7224f15be529de3400226e2eca3a/db-nav-logo.svg" 
             class="logo" alt="Databricks">
        <div class="title">{title}</div>
        <a href="{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}" 
           class="github-link">View on GitHub</a>
    </div>
    <div class="main-container">
        <div class="sidebar">
            <h3>📚 Documentation</h3>
            <a href="index.html" class="nav-link">Overview</a>
            <h3 style="margin-top: 30px;">📓 Notebooks</h3>
'''
    
    # Add notebook links
    for nb in sorted(all_notebooks):
        nb_display = nb.replace('_', ' ').title()
        active = 'active' if nb == notebook_name else ''
        html += f'            <a href="{nb}.html" class="nav-link {active}">{nb_display}</a>\n'
    
    html += f'''
        </div>
        <div class="content">
            <div class="notebook-container">
                {body_content}
            </div>
        </div>
    </div>
</body>
</html>'''
    
    return html

def main():
    """Main export function"""
    os.makedirs('site', exist_ok=True)
    
    # Find notebooks to export
    notebooks = find_notebooks_in_workspace()
    print(f"Found {len(notebooks)} notebooks to export")
    
    # For now, use a mapping of local to workspace paths
    # In production, this could be automated or configured
    notebook_mappings = {
        'notebook1': '/path/to/workspace/notebook1',
        'notebook2': '/path/to/workspace/notebook2',
    }
    
    exported = []
    for notebook in notebooks:
        workspace_path = notebook_mappings.get(notebook)
        if workspace_path:
            print(f"Exporting {notebook} from {workspace_path}...")
            html = export_notebook_html(workspace_path)
            if html:
                wrapped = create_wrapper_html(notebook, html, notebooks)
                with open(f'site/{notebook}.html', 'w') as f:
                    f.write(wrapped)
                exported.append(notebook)
                print(f"Successfully exported {notebook}")
        else:
            print(f"No workspace mapping for {notebook}")
    
    # Create index.html
    import markdown
    
    readme_content = ""
    if os.path.exists('README.md'):
        with open('README.md', 'r') as f:
            readme_content = markdown.markdown(f.read())
    
    repo_name = os.environ.get('GITHUB_REPOSITORY', '').split('/')[-1]
    title = ' '.join(word.capitalize() for word in repo_name.split('-')) + ' Accelerator'
    
    index_html = f'''<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'DM Sans', sans-serif;
            margin: 0;
            padding: 0;
            background: {COLORS['bg']};
            color: {COLORS['text']};
        }}
        
        .header {{
            background: {COLORS['bg']};
            padding: 20px 40px;
            border-bottom: 1px solid {COLORS['border']};
            display: flex;
            align-items: center;
            gap: 20px;
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 1000;
            box-sizing: border-box;
        }}
        
        .logo {{ height: 24px; }}
        
        .title {{
            font-size: 24px;
            font-weight: 600;
            flex: 1;
            text-align: center;
            color: {COLORS['text']};
        }}
        
        .github-link {{
            background: {COLORS['light_bg']};
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            color: {COLORS['text']};
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .github-link:hover {{
            background: {COLORS['border']};
        }}
        
        .main-container {{
            display: flex;
            margin-top: 80px;
            min-height: calc(100vh - 80px);
        }}
        
        .sidebar {{
            width: 280px;
            background: {COLORS['light_bg']};
            padding: 30px 20px;
            position: fixed;
            left: 0;
            top: 80px;
            height: calc(100vh - 80px);
            overflow-y: auto;
            box-sizing: border-box;
        }}
        
        .sidebar h3 {{
            font-size: 16px;
            font-weight: 600;
            margin: 0 0 20px 12px;
            color: {COLORS['text']};
        }}
        
        .content {{
            flex: 1;
            padding: 20px;
            margin-left: 280px;
        }}
        
        .content-container {{
            background: {COLORS['bg']};
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin: 0 auto;
            max-width: 900px;
        }}
        
        .nav-link {{
            display: block;
            padding: 10px 12px;
            margin: 4px 0;
            text-decoration: none;
            color: {COLORS['text']};
            border-radius: 4px;
            font-weight: 400;
            transition: all 0.2s;
        }}
        
        .nav-link:hover {{
            background: {COLORS['bg']};
        }}
        
        .nav-link.active {{
            background: {COLORS['primary']};
            color: {COLORS['bg']};
            font-weight: 500;
        }}
        
        h1, h2, h3 {{
            color: {COLORS['text']};
            font-weight: 600;
        }}
        
        h1 {{ font-size: 32px; margin: 0 0 24px 0; }}
        h2 {{ font-size: 24px; margin: 32px 0 16px 0; }}
        h3 {{ font-size: 18px; margin: 24px 0 12px 0; }}
        
        p {{ line-height: 1.6; margin: 0 0 16px 0; }}
        
        code {{
            background: {COLORS['light_bg']};
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 14px;
        }}
        
        pre {{
            background: {COLORS['light_bg']};
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 16px 0;
        }}
        
        ul, ol {{
            margin: 0 0 16px 0;
            padding-left: 24px;
            line-height: 1.6;
        }}
        
        a {{
            color: {COLORS['primary']};
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="header">
        <img src="https://databricks-prod-cloudfront.cloud.databricks.com/static/811f68f9f55e3a5330b6e6ae1e54c07fc5ec7224f15be529de3400226e2eca3a/db-nav-logo.svg" 
             class="logo" alt="Databricks">
        <div class="title">{title}</div>
        <a href="{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}" 
           class="github-link">View on GitHub</a>
    </div>
    <div class="main-container">
        <div class="sidebar">
            <h3>📚 Documentation</h3>
            <a href="index.html" class="nav-link active">Overview</a>
'''
    
    if exported:
        index_html += '            <h3 style="margin-top: 30px;">📓 Notebooks</h3>\n'
        for nb in sorted(exported):
            nb_display = nb.replace('_', ' ').title()
            index_html += f'            <a href="{nb}.html" class="nav-link">{nb_display}</a>\n'
    
    index_html += f'''
        </div>
        <div class="content">
            <div class="content-container">
                {readme_content}
            </div>
        </div>
    </div>
</body>
</html>'''
    
    with open('site/index.html', 'w') as f:
        f.write(index_html)
    
    print(f"Created index.html with {len(exported)} notebooks")
    return len(exported)

if __name__ == '__main__':
    main()