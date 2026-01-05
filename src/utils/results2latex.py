"""Generate LaTeX TikZ bar charts from RTEC-LLM results JSON files."""

import json
from pathlib import Path
from typing import Any

# Abbreviation mappings for fluent names
FLUENT_ABBREVIATIONS = {
    # MSA domain
    "gap": "GAP",
    "highSpeedNearCoast": "HSC",
    "trawlSpeed": "TRS",
    "trawlingMovement": "TRM",
    "lowSpeed": "LSP",
    "tuggingSpeed": "TGS",
    "sarSpeed": "SRS",
    "changingSpeed": "CHS",
    "movingSpeed": "MVS",
    "trawling": "TRW",
    "anchoredOrMoored": "ANM",
    "tugging": "TGN",
    "sarMovement": "SRM",
    "pilotOps": "PTS",
    "drifting": "DFG",
    "inSAR": "NSR",
    "loitering": "LTR",
    # HAR domain
    "leaving_object": "LVO",
    "moving": "MOV",
    "fighting": "FGT",
}

# Full names for the glossary
FLUENT_FULL_NAMES = {
    # MSA domain
    "gap": "Gap",
    "highSpeedNearCoast": "High Speed Near Coast",
    "trawlSpeed": "Trawl Speed",
    "trawlingMovement": "Trawling Movement",
    "lowSpeed": "Low Speed",
    "tuggingSpeed": "Tugging Speed",
    "sarSpeed": "SAR Speed",
    "changingSpeed": "Changing Speed",
    "movingSpeed": "Moving Speed",
    "trawling": "Trawling",
    "anchoredOrMoored": "Anchored or Moored",
    "tugging": "Tugging",
    "sarMovement": "SAR Movement",
    "pilotOps": "Pilot Operations",
    "drifting": "Drifting",
    "inSAR": "In SAR",
    "loitering": "Loitering",
    # HAR domain
    "leaving_object": "Leaving Object",
    "moving": "Moving",
    "fighting": "Fighting",
}


def load_results(json_path: str | Path) -> dict[str, Any]:
    """Load results from a JSON file."""
    with open(json_path) as f:
        return json.load(f)


def filter_fluents(
    results: list[dict],
    exclude_perfect_first: bool = True,
    perfect_threshold: float = 1.0,
) -> list[dict]:
    """Filter fluents based on criteria.

    Args:
        results: List of fluent result dictionaries
        exclude_perfect_first: If True, exclude fluents that got perfect score on first iteration
        perfect_threshold: Score threshold to consider as "perfect" (default 1.0)

    Returns:
        Filtered list of fluent results
    """
    if not exclude_perfect_first:
        return results

    return [
        r
        for r in results
        if r["iteration_history"][0]["score"] < perfect_threshold
    ]


def get_max_iterations(results: list[dict]) -> int:
    """Get the maximum number of iterations across all fluents."""
    return max(len(r["iteration_history"]) for r in results)


def generate_latex_bar_chart(
    json_path: str | Path,
    exclude_perfect_first: bool = True,
    caption: str | None = None,
    label: str = "fig:iteration_scores",
) -> str:
    """Generate LaTeX TikZ bar chart code from results JSON.

    Args:
        json_path: Path to the results JSON file
        exclude_perfect_first: Exclude fluents that got 1.0 on first iteration
        caption: Custom caption (auto-generated if None)
        label: LaTeX label for the figure

    Returns:
        Complete LaTeX figure code as a string
    """
    data = load_results(json_path)
    results = data["results"]
    metadata = data["metadata"]

    # Filter fluents
    filtered = filter_fluents(results, exclude_perfect_first)
    excluded = [r for r in results if r not in filtered]

    # Sort by fluent name for consistent ordering
    filtered.sort(key=lambda x: x["fluent_name"])

    max_iters = get_max_iterations(filtered)

    # Build symbolic x coords
    abbrevs = [
        FLUENT_ABBREVIATIONS.get(r["fluent_name"], r["fluent_name"][:3].upper())
        for r in filtered
    ]
    x_coords = ", ".join(abbrevs)

    # Build coordinates for each iteration
    iteration_plots = []
    for iter_num in range(1, max_iters + 1):
        coords = []
        for r in filtered:
            history = r["iteration_history"]
            if iter_num <= len(history):
                abbrev = FLUENT_ABBREVIATIONS.get(
                    r["fluent_name"], r["fluent_name"][:3].upper()
                )
                score = history[iter_num - 1]["score"]
                coords.append(f"({abbrev},{score:.2f})")

        if coords:
            coords_str = " ".join(coords)
            iteration_plots.append(
                f"      % Iteration {iter_num}\n"
                f"      \\addplot coordinates {{{coords_str}}};"
            )

    # Build legend
    legend_items = ", ".join([f"Iteration {i}" for i in range(1, max_iters + 1)])

    # Build glossary table
    items = [
        (
            FLUENT_ABBREVIATIONS.get(r["fluent_name"], r["fluent_name"][:3].upper()),
            FLUENT_FULL_NAMES.get(r["fluent_name"], r["fluent_name"]),
        )
        for r in filtered
    ]

    mid = (len(items) + 1) // 2
    left_items = items[:mid]
    right_items = items[mid:]

    glossary_rows = []
    for i in range(mid):
        left = left_items[i] if i < len(left_items) else ("", "")
        right = right_items[i] if i < len(right_items) else ("", "")
        glossary_rows.append(f"  {left[0]} & {left[1]} & {right[0]} & {right[1]} \\\\")

    glossary_table = "\n".join(glossary_rows)

    # Build excluded fluents list for caption
    excluded_names = [f"\\emph{{{r['fluent_name']}}}" for r in excluded]
    excluded_str = ", ".join(excluded_names) if excluded_names else "none"

    # Generate caption
    if caption is None:
        domain_name = metadata.get("domain", "unknown").upper()
        caption = (
            f"Similarity scores for the {domain_name} case study "
            f"across {max_iters} iterations."
        )
        if excluded_names:
            caption += (
                f"\n  Rules that reached a similarity of 1.0 on the first attempt "
                f"were excluded:\n  {excluded_str}."
            )

    # Assemble the complete LaTeX figure
    latex = f"""\\begin{{figure}}[h]
  \\centering
  \\begin{{tikzpicture}}
    \\begin{{axis}}[
        ybar,
        bar width=4pt,
        enlargelimits=0.1,
        ylabel={{Similarity score}},
        symbolic x coords={{{x_coords}}},
        xtick=data,
        x tick label style={{rotate=45, anchor=east, font=\\scriptsize}},
        nodes near coords,
        point meta=y,
        nodes near coords align={{vertical}},
        every node near coord/.append style={{font=\\scriptsize}},
        every node near coord/.append style={{
          /pgfplots/bar shift=0pt,
          shift={{(0pt,3pt)}}
        }},
        legend style={{at={{(0.5,-0.15)}}, anchor=north, legend columns=-1}}
    ]
{chr(10).join(iteration_plots)}
      \\legend{{{legend_items}}}
    \\end{{axis}}
  \\end{{tikzpicture}}

  \\caption{{{caption}}}
  \\textbf{{Abbreviations:}}
  \\caption*{{\\footnotesize
  \\begin{{tabular}}{{@{{}}ll@{{\\hspace{{1cm}}}}ll@{{}}}}
{glossary_table}
  \\end{{tabular}}
  }}

  \\label{{{label}}}
\\end{{figure}}"""

    return latex


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate LaTeX TikZ bar charts from RTEC-LLM results"
    )
    parser.add_argument("json_path", help="Path to the results JSON file")
    parser.add_argument(
        "--include-perfect",
        action="store_true",
        help="Include fluents that got 1.0 on first iteration",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (prints to stdout if not specified)",
    )
    parser.add_argument(
        "--label",
        default="fig:iteration_scores",
        help="LaTeX label for the figure",
    )

    args = parser.parse_args()

    latex = generate_latex_bar_chart(
        args.json_path,
        exclude_perfect_first=not args.include_perfect,
        label=args.label,
    )

    if args.output:
        Path(args.output).write_text(latex)
        print(f"LaTeX written to {args.output}")
    else:
        print(latex)


if __name__ == "__main__":
    main()

