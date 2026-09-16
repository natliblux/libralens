from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from .constants import PLOT_RESOLUTION

def create_results_plot(results: list[dict], methods: list[str], overall_score: float | None, output_path: str | Path) -> None:

    results = results * 50
    output_path = Path(output_path)

    if not results or not methods:
        return

    if len(results) <= PLOT_RESOLUTION:
        _create_document_heatmap(results=results, methods=methods, overall_score=overall_score, output_path=output_path)
    else:
        _create_distribution_heatmap(results=results, methods=methods, overall_score=overall_score, output_path=output_path)

def _add_title(fig, overall_score: float | None) -> None:

    if overall_score is not None:
        fig.suptitle(f"dataset score: {overall_score:.3f}", fontsize=10)

def _create_document_heatmap(results: list[dict], methods: list[str], overall_score: float | None, output_path: Path) -> None:

    values = np.full(
        (len(results), len(methods)),
        np.nan,
        dtype=float,
    )

    for row, result in enumerate(results):
        for column, method in enumerate(methods):
            score = result["methods"][method]["score"]

            if score is not None:
                values[row, column] = score

    figure_width = max(8, len(methods) * 1.8)
    figure_height = max(4, len(results) * 0.55 + 2)

    fig, ax = plt.subplots(figsize=(figure_width, figure_height))

    cmap = plt.get_cmap("RdYlGn").copy()
    cmap.set_bad("lightgrey")

    image = ax.imshow(values, cmap=cmap, vmin=0, vmax=1, aspect="auto")

    _add_title(fig=fig, overall_score=overall_score)

    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=30, ha="right")

    ax.set_yticks(range(len(results)))
    ax.set_yticklabels([f"doc {result['id']}" for result in results])

    for row in range(len(results)):
        for column in range(len(methods)):
            value = values[row, column]

            if np.isnan(value):
                text = "n/a"
            else:
                text = f"{value:.2f}"

            ax.text(column, row, text, ha="center", va="center")

    colorbar = fig.colorbar(image, ax=ax, fraction=0.03, pad=0.04)
    colorbar.set_label("score")

    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

def _create_distribution_heatmap(results: list[dict], methods: list[str], overall_score: float | None, output_path: Path) -> None:

    bin_edges = np.linspace(0, 1, PLOT_RESOLUTION + 1)
    values = np.zeros((PLOT_RESOLUTION, len(methods)), dtype=float)
    applicable_counts = {}

    for column, method in enumerate(methods):

        scores = [
            result["methods"][method]["score"]
            for result in results
            if result["methods"][method]["score"] is not None
        ]

        applicable_counts[method] = len(scores)

        if not scores:
            values[:, column] = np.nan
            continue

        counts, _ = np.histogram(scores, bins=bin_edges)
        percentages = counts / len(scores)

        # Reverse so highest scores appear at the top.
        values[:, column] = percentages[::-1]

    figure_width = max(8, len(methods) * 1.8)
    figure_height = 11

    fig, ax = plt.subplots(figsize=(figure_width, figure_height))

    cmap = plt.get_cmap("Blues").copy()
    cmap.set_bad("lightgrey")

    valid_values = values[~np.isnan(values)]
    max_percentage = valid_values.max() if valid_values.size else 1

    image = ax.imshow(values, cmap=cmap, vmin=0, vmax=max_percentage, aspect="auto")

    _add_title(fig=fig, overall_score=overall_score)

    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=30, ha="right")

    labels = []

    for i in reversed(range(PLOT_RESOLUTION)):
        lower = bin_edges[i]
        upper = bin_edges[i + 1]
        labels.append(f"{lower:.2f}–{upper:.2f}")

    ax.set_yticks(range(PLOT_RESOLUTION))
    ax.set_yticklabels(labels)

    for row in range(PLOT_RESOLUTION):
        for column in range(len(methods)):
            value = values[row, column]

            if np.isnan(value):
                text = "n/a"
            else:
                text = f"{value * 100:.0f}%"

            ax.text(column, row, text, ha="center", va="center")

    colorbar = fig.colorbar(image, ax=ax, fraction=0.03, pad=0.04)
    colorbar.set_label("percentage of applicable documents")
    colorbar.ax.yaxis.set_major_formatter(lambda value, _: f"{value * 100:.0f}%")

    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)