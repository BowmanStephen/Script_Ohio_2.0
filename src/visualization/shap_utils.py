"""
SHAP Visualization Utilities.
"""
import shap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Any, Optional, List, Union

def generate_beeswarm_plot(explainer: Any, shap_values: Any, features: pd.DataFrame, max_display: int = 20, show: bool = False):
    """
    Generate SHAP beeswarm plot.
    
    Args:
        explainer: SHAP explainer object
        shap_values: SHAP values
        features: Feature DataFrame
        max_display: Max features to display
        show: Whether to show the plot
        
    Returns:
        matplotlib figure
    """
    plt.figure()
    shap.plots.beeswarm(shap_values, max_display=max_display, show=False)
    fig = plt.gcf()
    if show:
        plt.show()
    return fig

def generate_force_plot(explainer: Any, shap_values: Any, features: pd.DataFrame, index: int = 0, matplotlib: bool = False):
    """
    Generate SHAP force plot for a single instance.
    
    Args:
        explainer: SHAP explainer
        shap_values: SHAP values
        features: Feature DataFrame
        index: Index of the instance to plot
        matplotlib: Whether to return matplotlib figure (True) or HTML/JS (False)
    """
    # Force plot is usually interactive (JS)
    try:
        return shap.plots.force(explainer.expected_value, shap_values[index], features.iloc[index], matplotlib=matplotlib)
    except Exception as e:
        print(f"Error generating force plot: {e}")
        return None

def generate_waterfall_plot(explainer: Any, shap_values: Any, features: pd.DataFrame, index: int = 0, max_display: int = 10, show: bool = False):
    """
    Generate SHAP waterfall plot.
    """
    plt.figure()
    # shap_values[index] is an Explanation object in newer SHAP versions
    # If shap_values is numpy array, we might need to construct Explanation
    try:
        shap.plots.waterfall(shap_values[index], max_display=max_display, show=False)
        fig = plt.gcf()
        if show:
            plt.show()
        return fig
    except Exception as e:
        print(f"Error generating waterfall plot: {e}")
        return None

