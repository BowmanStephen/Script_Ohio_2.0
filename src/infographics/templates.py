#!/usr/bin/env python3
"""
HTML/CSS/JS Templates for Interactive Infographics

This module provides reusable HTML templates with dark mode support,
responsive design, and accessibility features for standalone infographic components.

Author: Claude Code Assistant
Created: 2025-11-19
Version: 1.0
"""

from typing import Dict, Any, Optional


def get_base_template(title: str = "Interactive Infographic", 
                     description: Optional[str] = None,
                     include_plotly: bool = True) -> str:
    """
    Get base HTML template with Plotly.js, responsive CSS, and dark mode support.
    
    Args:
        title: Page title
        description: Optional description meta tag
        include_plotly: Whether to include Plotly.js CDN
        
    Returns:
        Complete HTML template string
    """
    description_meta = f'<meta name="description" content="{description}">' if description else ""
    plotly_script = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>' if include_plotly else ""
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {description_meta}
    {plotly_script}
    <style>
        :root {{
            --bg-color: #ffffff;
            --text-color: #212529;
            --card-bg: #ffffff;
            --border-color: #dee2e6;
            --primary-color: #0d6efd;
            --secondary-color: #6c757d;
            --hover-bg: #f8f9fa;
            --shadow: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-hover: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #1a1a1a;
                --text-color: #ffffff;
                --card-bg: #2d2d2d;
                --border-color: #495057;
                --primary-color: #4dabf7;
                --secondary-color: #adb5bd;
                --hover-bg: #3a3a3a;
                --shadow: 0 2px 4px rgba(0,0,0,0.3);
                --shadow-hover: 0 4px 8px rgba(0,0,0,0.4);
            }}
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 30px;
            box-shadow: var(--shadow);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid var(--border-color);
        }}
        
        .header h1 {{
            color: var(--primary-color);
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        
        .header p {{
            color: var(--secondary-color);
            font-size: 1rem;
        }}
        
        .component-wrapper {{
            margin: 20px 0;
            padding: 20px;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            transition: box-shadow 0.2s ease;
        }}
        
        .component-wrapper:hover {{
            box-shadow: var(--shadow-hover);
        }}
        
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 20px;
            padding: 15px;
            background-color: var(--hover-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        
        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        
        .control-group label {{
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-color);
        }}
        
        .control-group select,
        .control-group input {{
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background-color: var(--card-bg);
            color: var(--text-color);
            font-size: 0.9rem;
        }}
        
        .control-group select:focus,
        .control-group input:focus {{
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }}
        
        .plotly-container {{
            width: 100%;
            min-height: 400px;
        }}
        
        .info-panel {{
            margin-top: 20px;
            padding: 15px;
            background-color: var(--hover-bg);
            border-radius: 8px;
            border-left: 4px solid var(--primary-color);
            font-size: 0.9rem;
            color: var(--text-color);
        }}
        
        /* Accessibility */
        .sr-only {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border-width: 0;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .container {{
                padding: 15px;
            }}
            
            .header h1 {{
                font-size: 1.5rem;
            }}
            
            .controls {{
                flex-direction: column;
            }}
            
            .control-group {{
                width: 100%;
            }}
        }}
        
        /* Focus styles for keyboard navigation */
        *:focus-visible {{
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }}
        
        /* Print styles */
        @media print {{
            body {{
                background: white;
                color: black;
            }}
            
            .controls {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            {f'<p>{description}</p>' if description else ''}
        </div>
        <div id="component-content">
            <!-- Component content will be inserted here -->
        </div>
    </div>
</body>
</html>"""


def get_standalone_html(figure_html: str, 
                       title: str = "Interactive Infographic",
                       description: Optional[str] = None,
                       additional_css: Optional[str] = None,
                       additional_js: Optional[str] = None) -> str:
    """
    Wrap Plotly figure HTML in a complete standalone HTML document.
    
    Args:
        figure_html: HTML string from plotly figure.to_html(full_html=False)
        title: Page title
        description: Optional description
        additional_css: Optional additional CSS to inject
        additional_js: Optional additional JavaScript to inject
        
    Returns:
        Complete standalone HTML document
    """
    base = get_base_template(title, description, include_plotly=True)
    
    # Insert figure HTML into component-content div
    html = base.replace(
        '<div id="component-content">',
        f'<div id="component-content"><div class="component-wrapper"><div class="plotly-container">{figure_html}</div></div>'
    )
    
    # Add additional CSS before closing </head>
    if additional_css:
        html = html.replace('</head>', f'<style>{additional_css}</style></head>')
    
    # Add additional JS before closing </body>
    if additional_js:
        html = html.replace('</body>', f'<script>{additional_js}</script></body>')
    
    return html


def get_controls_html(controls: list[Dict[str, Any]]) -> str:
    """
    Generate HTML for interactive controls (filters, sliders, toggles).
    
    Args:
        controls: List of control dictionaries with keys:
            - type: 'select', 'input', 'slider', 'checkbox'
            - id: Unique ID for the control
            - label: Label text
            - options: For select type, list of {value, label} dicts
            - min/max/step: For slider type
            - default: Default value
            
    Returns:
        HTML string for controls panel
    """
    if not controls:
        return ""
    
    control_html = '<div class="controls" role="group" aria-label="Interactive controls">'
    
    for control in controls:
        control_type = control.get('type', 'input')
        control_id = control.get('id', '')
        label = control.get('label', '')
        default = control.get('default', '')
        
        control_html += '<div class="control-group">'
        control_html += f'<label for="{control_id}">{label}</label>'
        
        if control_type == 'select':
            options = control.get('options', [])
            control_html += f'<select id="{control_id}" name="{control_id}" aria-label="{label}">'
            for opt in options:
                value = opt.get('value', '')
                opt_label = opt.get('label', value)
                selected = 'selected' if value == default else ''
                control_html += f'<option value="{value}" {selected}>{opt_label}</option>'
            control_html += '</select>'
            
        elif control_type == 'slider':
            min_val = control.get('min', 0)
            max_val = control.get('max', 100)
            step = control.get('step', 1)
            control_html += f'<input type="range" id="{control_id}" name="{control_id}" '
            control_html += f'min="{min_val}" max="{max_val}" step="{step}" value="{default}" '
            control_html += f'aria-label="{label}"><span id="{control_id}-value">{default}</span>'
            
        elif control_type == 'checkbox':
            checked = 'checked' if default else ''
            control_html += f'<input type="checkbox" id="{control_id}" name="{control_id}" {checked} '
            control_html += f'aria-label="{label}">'
            
        else:  # input (text, number, etc.)
            input_type = control.get('input_type', 'text')
            placeholder = control.get('placeholder', '')
            control_html += f'<input type="{input_type}" id="{control_id}" name="{control_id}" '
            control_html += f'value="{default}" placeholder="{placeholder}" aria-label="{label}">'
        
        control_html += '</div>'
    
    control_html += '</div>'
    return control_html

