"""Visualization module for RTEC-LLM results.

Provides charts and plots for analyzing rule generation results.
Supports both presentation (dark theme) and LaTeX (academic) modes.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from src.core.models import FinalResult


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy types."""
    
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


# Style configurations
STYLE_CONFIGS = {
    "dark": {
        "figure.facecolor": "#1a1a2e",
        "axes.facecolor": "#16213e",
        "axes.edgecolor": "#e94560",
        "axes.labelcolor": "#eaeaea",
        "text.color": "#eaeaea",
        "xtick.color": "#eaeaea",
        "ytick.color": "#eaeaea",
        "grid.color": "#0f3460",
        "legend.facecolor": "#16213e",
        "legend.edgecolor": "#e94560",
        "font.family": "monospace",
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
    },
    "latex": {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "black",
        "axes.labelcolor": "black",
        "text.color": "black",
        "xtick.color": "black",
        "ytick.color": "black",
        "grid.color": "#cccccc",
        "grid.alpha": 0.5,
        "legend.facecolor": "white",
        "legend.edgecolor": "black",
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman", "Times New Roman", "DejaVu Serif"],
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.linewidth": 0.8,
        "grid.linewidth": 0.5,
        "lines.linewidth": 1.5,
        "lines.markersize": 5,
    },
}

# Color palettes
COLOR_PALETTES = {
    "dark": {
        "primary": sns.color_palette("husl", 10),
        "converged": "#00d9ff",
        "not_converged": "#e94560",
        "threshold": "#e94560",
        "initial": "#4a5568",
        "improvement": "#48bb78",
    },
    "latex": {
        "primary": sns.color_palette("colorblind", 10),  # Colorblind-friendly
        "converged": "#2ecc71",
        "not_converged": "#e74c3c",
        "threshold": "#3498db",
        "initial": "#7f8c8d",
        "improvement": "#27ae60",
    },
}


def set_style(style: Literal["dark", "latex"] = "dark") -> None:
    """Set the matplotlib style for plots.
    
    Args:
        style: "dark" for presentation, "latex" for academic papers
    """
    if style == "latex":
        # Try to enable LaTeX rendering if available
        try:
            plt.rcParams["text.usetex"] = True
            plt.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
        except Exception:
            # LaTeX not available, use mathtext
            plt.rcParams["text.usetex"] = False
            plt.rcParams["mathtext.fontset"] = "cm"  # Computer Modern
        
        sns.set_theme(style="whitegrid", palette="colorblind")
    else:
        plt.rcParams["text.usetex"] = False
        sns.set_theme(style="darkgrid", palette="husl")
    
    # Apply style-specific settings
    for key, value in STYLE_CONFIGS[style].items():
        plt.rcParams[key] = value


def get_colors(style: Literal["dark", "latex"] = "dark") -> dict:
    """Get color palette for the specified style."""
    return COLOR_PALETTES[style]


def plot_iteration_progress(
    results: List[FinalResult],
    output_path: Optional[Path] = None,
    show: bool = True,
    style: Literal["dark", "latex"] = "dark",
) -> None:
    """Plot score progression across iterations for each fluent.
    
    Args:
        results: List of FinalResult from orchestrator
        output_path: Path to save the figure (optional)
        show: Whether to display the plot
        style: "dark" for presentation, "latex" for academic papers
    """
    set_style(style)
    colors = get_colors(style)
    
    # Figure size: smaller for LaTeX (fits column width ~3.5in)
    figsize = (5.5, 4) if style == "latex" else (12, 7)
    fig, ax = plt.subplots(figsize=figsize)
    
    palette = colors["primary"]
    
    for i, result in enumerate(results):
        iterations = [it.iteration for it in result.iterations]
        scores = [it.similarity_score for it in result.iterations]
        
        ax.plot(
            iterations,
            scores,
            marker='o',
            label=result.fluent_name,
            color=palette[i % len(palette)],
            alpha=0.9,
        )
        
        # Mark the best iteration
        best_idx = result.best_iteration - 1
        if 0 <= best_idx < len(scores):
            edge_color = "black" if style == "latex" else "white"
            ax.scatter(
                [result.best_iteration],
                [result.best_score],
                s=80 if style == "latex" else 200,
                color=palette[i % len(palette)],
                edgecolor=edge_color,
                linewidth=1.5,
                zorder=5,
            )
    
    # Add convergence threshold line
    if results:
        threshold = results[0].convergence_threshold
        ax.axhline(
            y=threshold,
            color=colors["threshold"],
            linestyle='--',
            linewidth=1.5,
            label=f'Threshold ($\\tau={threshold}$)' if style == "latex" else f'Threshold ({threshold})',
            alpha=0.8,
        )
    
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Similarity Score')
    if style != "latex":
        ax.set_title('Score Progression Across Iterations', fontweight='bold', pad=20)
    ax.set_ylim(0, 1.05)
    ax.legend(loc='lower right')
    
    plt.tight_layout()
    
    if output_path:
        dpi = 300 if style == "latex" else 150
        facecolor = "white" if style == "latex" else fig.get_facecolor()
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor=facecolor)
    
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_summary_bars(
    results: List[FinalResult],
    output_path: Optional[Path] = None,
    show: bool = True,
    style: Literal["dark", "latex"] = "dark",
) -> None:
    """Plot summary bar chart of final scores per fluent.
    
    Args:
        results: List of FinalResult from orchestrator
        output_path: Path to save the figure (optional)
        show: Whether to display the plot
        style: "dark" for presentation, "latex" for academic papers
    """
    set_style(style)
    colors = get_colors(style)
    
    figsize = (5.5, 4) if style == "latex" else (12, 7)
    fig, ax = plt.subplots(figsize=figsize)
    
    fluent_names = [r.fluent_name for r in results]
    best_scores = [r.best_score for r in results]
    converged = [r.converged for r in results]
    
    # Color bars based on convergence
    bar_colors = [colors["converged"] if c else colors["not_converged"] for c in converged]
    edge_color = "black" if style == "latex" else "white"
    
    bars = ax.barh(fluent_names, best_scores, color=bar_colors, edgecolor=edge_color, linewidth=0.8)
    
    # Add score labels on bars
    text_color = "black" if style == "latex" else "#eaeaea"
    for bar, score in zip(bars, best_scores):
        width = bar.get_width()
        ax.text(
            width + 0.02,
            bar.get_y() + bar.get_height() / 2,
            f'{score:.3f}',
            ha='left',
            va='center',
            fontsize=8 if style == "latex" else 10,
            color=text_color,
        )
    
    # Add convergence threshold line
    if results:
        threshold = results[0].convergence_threshold
        ax.axvline(
            x=threshold,
            color=colors["threshold"],
            linestyle='--',
            linewidth=1.5,
            label=f'$\\tau={threshold}$' if style == "latex" else f'Threshold ({threshold})',
        )
    
    ax.set_xlabel('Best Similarity Score')
    ax.set_ylabel('Fluent')
    if style != "latex":
        ax.set_title('Best Scores by Fluent', fontweight='bold', pad=20)
    ax.set_xlim(0, 1.15)
    
    # Add legend for colors
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=colors["converged"], edgecolor=edge_color, label='Converged'),
        Patch(facecolor=colors["not_converged"], edgecolor=edge_color, label='Not Converged'),
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    
    if output_path:
        dpi = 300 if style == "latex" else 150
        facecolor = "white" if style == "latex" else fig.get_facecolor()
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor=facecolor)
    
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_improvement_waterfall(
    results: List[FinalResult],
    output_path: Optional[Path] = None,
    show: bool = True,
    style: Literal["dark", "latex"] = "dark",
) -> None:
    """Plot improvement from initial to best score for each fluent.
    
    Args:
        results: List of FinalResult from orchestrator
        output_path: Path to save the figure (optional)
        show: Whether to display the plot
        style: "dark" for presentation, "latex" for academic papers
    """
    set_style(style)
    colors = get_colors(style)
    
    figsize = (5.5, 4) if style == "latex" else (12, 7)
    fig, ax = plt.subplots(figsize=figsize)
    
    fluent_names = [r.fluent_name for r in results]
    initial_scores = [r.statistics.initial_score for r in results]
    improvements = [r.statistics.improvement for r in results]
    
    x = np.arange(len(fluent_names))
    width = 0.6
    edge_color = "black" if style == "latex" else "white"
    
    # Stack: initial score (base) + improvement (on top)
    ax.bar(x, initial_scores, width, label='Initial Score', color=colors["initial"], edgecolor=edge_color, linewidth=0.8)
    ax.bar(x, improvements, width, bottom=initial_scores, label='Improvement', color=colors["improvement"], edgecolor=edge_color, linewidth=0.8)
    
    # Add final score labels
    text_color = "black" if style == "latex" else "#eaeaea"
    for i, (init, imp) in enumerate(zip(initial_scores, improvements)):
        final = init + imp
        ax.text(
            i,
            final + 0.03,
            f'{final:.3f}',
            ha='center',
            va='bottom',
            fontsize=8 if style == "latex" else 9,
            color=text_color,
        )
    
    ax.set_xlabel('Fluent')
    ax.set_ylabel('Score')
    if style != "latex":
        ax.set_title('Score Improvement: Initial → Best', fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(fluent_names, rotation=45, ha='right')
    ax.set_ylim(0, 1.15)
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    
    if output_path:
        dpi = 300 if style == "latex" else 150
        facecolor = "white" if style == "latex" else fig.get_facecolor()
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor=facecolor)
    
    if show:
        plt.show()
    else:
        plt.close(fig)


def generate_all_plots(
    results: List[FinalResult],
    output_dir: Path,
    show: bool = False,
) -> List[Path]:
    """Generate all visualization plots and save to output directory.
    
    Args:
        results: List of FinalResult from orchestrator
        output_dir: Directory to save plots
        show: Whether to display plots interactively
        
    Returns:
        List of paths to generated plot files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    # Progress plot
    progress_path = output_dir / "iteration_progress.png"
    plot_iteration_progress(results, progress_path, show=show)
    generated_files.append(progress_path)
    
    # Summary bars
    summary_path = output_dir / "summary_scores.png"
    plot_summary_bars(results, summary_path, show=show)
    generated_files.append(summary_path)
    
    # Improvement waterfall
    improvement_path = output_dir / "improvement.png"
    plot_improvement_waterfall(results, improvement_path, show=show)
    generated_files.append(improvement_path)
    
    return generated_files


def save_results_json(
    results: List[FinalResult],
    output_path: Path,
    metadata: Optional[dict] = None,
) -> None:
    """Save results to JSON file for later analysis.
    
    Args:
        results: List of FinalResult from orchestrator
        output_path: Path to save JSON file
        metadata: Optional metadata to include (config, etc.)
    """
    data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "total_fluents": len(results),
            "converged_count": sum(1 for r in results if r.converged),
            **(metadata or {}),
        },
        "summary": {
            "average_score": sum(r.best_score for r in results) / len(results) if results else 0,
            "average_iterations": sum(r.statistics.total_iterations for r in results) / len(results) if results else 0,
            "total_duration_seconds": sum(r.duration_seconds for r in results),
        },
        "results": [
            {
                "fluent_name": r.fluent_name,
                "domain": r.domain,
                "best_score": r.best_score,
                "best_iteration": r.best_iteration,
                "converged": r.converged,
                "convergence_threshold": r.convergence_threshold,
                "total_iterations": r.statistics.total_iterations,
                "initial_score": r.statistics.initial_score,
                "final_score": r.statistics.final_score,
                "improvement": r.statistics.improvement,
                "duration_seconds": r.duration_seconds,
                "best_rules": r.best_rules,
                "iteration_history": [
                    {
                        "iteration": it.iteration,
                        "score": it.similarity_score,
                    }
                    for it in r.iterations
                ],
            }
            for r in results
        ],
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, cls=NumpyEncoder)

