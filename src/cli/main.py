"""RTEC-LLM CLI - Command-line interface for RTEC rule generation.

Usage:
    rtec-llm run --domain msa --provider openai --model gpt-4o
    rtec-llm run --domain har --provider openai --model gpt-4o --max-iterations 5
    rtec-llm run -d msa -o ./results --visualize
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core import LoopOrchestrator, OrchestratorConfig
from src.feedback.client import FeedbackClient
from src.interfaces.models import LLMConfig
from src.llm.factory import get_provider
from src.memory import RuleMemory
from src.prompts.factory import get_prompt_builder, list_available_domains

app = typer.Typer(
    name="rtec-llm",
    help="LLM-Driven Generation & Evaluation of RTEC Event Descriptions",
    add_completion=False,
)

console = Console()


def get_requests_for_domain(domain: str):
    """Get the requests list for the specified domain."""
    if domain.lower() == "msa":
        from src.prompts.msa_requests import msa_requests
        return msa_requests
    elif domain.lower() == "har":
        from src.prompts.har_requests import har_requests
        return har_requests
    else:
        raise typer.BadParameter(f"Unknown domain: {domain}")


@app.command()
def run(
    domain: str = typer.Option(
        ...,
        "--domain",
        "-d",
        help="Domain to run (e.g., 'msa', 'har')",
    ),
    provider: str = typer.Option(
        "openai",
        "--provider",
        "-p",
        help="LLM provider to use (e.g., 'openai')",
    ),
    model: str = typer.Option(
        "gpt-4o",
        "--model",
        "-m",
        help="Model to use (e.g., 'gpt-4o', 'gpt-4o-mini')",
    ),
    max_iterations: int = typer.Option(
        5,
        "--max-iterations",
        "-i",
        help="Maximum number of iterations per fluent",
        min=1,
        max=20,
    ),
    convergence_threshold: float = typer.Option(
        0.95,
        "--convergence-threshold",
        "-t",
        help="Score threshold for convergence (0.0 to 1.0)",
        min=0.0,
        max=1.0,
    ),
    api_key_name: str = typer.Option(
        "OPENAI_API_KEY",
        "--api-key-name",
        "-k",
        help="Name of the API key environment variable in .env file",
    ),
    verbose: bool = typer.Option(
        True,
        "--verbose/--quiet",
        "-v/-q",
        help="Enable verbose output",
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for results and visualizations",
    ),
    visualize: bool = typer.Option(
        False,
        "--visualize",
        help="Generate visualization plots",
    ),
    show_plots: bool = typer.Option(
        False,
        "--show-plots",
        help="Display plots interactively (requires --visualize)",
    ),
):
    """Run the RTEC rule generation feedback loop.
    
    Example:
        rtec-llm run --domain msa --provider openai --model gpt-4o
        rtec-llm run -d har -p openai -m gpt-4o-mini -i 3 -t 0.9
        rtec-llm run -d msa -o ./results --visualize
    """
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv(api_key_name)
    if not api_key:
        console.print(
            f"[bold red]Error:[/bold red] API key '{api_key_name}' not found in environment",
            style="red",
        )
        raise typer.Exit(code=1)
    
    # Display configuration
    console.print(Panel.fit(
        f"[bold cyan]RTEC-LLM Rule Generation[/bold cyan]\n\n"
        f"Domain: [green]{domain}[/green]\n"
        f"Provider: [green]{provider}[/green]\n"
        f"Model: [green]{model}[/green]\n"
        f"Max Iterations: [green]{max_iterations}[/green]\n"
        f"Convergence Threshold: [green]{convergence_threshold}[/green]\n"
        f"API Key: [green]{api_key_name}[/green]",
        title="Configuration",
        border_style="cyan",
    ))
    
    try:
        # Initialize components
        prompt_builder = get_prompt_builder(domain)
        
        llm_config = LLMConfig(
            provider=provider,
            api_key=api_key,
            extra={"model": model},
        )
        llm_provider = get_provider(provider)(llm_config)
        
        memory = RuleMemory(min_score_threshold=0.7)
        feedback_client = FeedbackClient()
        
        config = OrchestratorConfig(
            max_iterations=max_iterations,
            convergence_threshold=convergence_threshold,
            verbose=verbose,
        )
        
        orchestrator = LoopOrchestrator(
            prompt_builder=prompt_builder,
            llm_provider=llm_provider,
            memory=memory,
            feedback_client=feedback_client,
            config=config,
        )
        
        # Get requests for domain
        requests = get_requests_for_domain(domain)
        
        # Prepare fluent configs
        fluent_configs = [
            {
                "fluent_name": f["fluent_name"],
                "activity_description": f["description"],
                "ground_truth": f.get("prolog", None),
                "prerequisites": f.get("prerequisites", None),
            }
            for f in requests
        ]
        
        console.print(f"\n[bold]Running {len(fluent_configs)} fluents...[/bold]\n")
        
        # Run batch
        results = orchestrator.run_batch(fluent_configs)
        
        # Display summary table
        table = Table(title="Batch Results", show_header=True, header_style="bold magenta")
        table.add_column("Status", style="dim", width=6)
        table.add_column("Fluent", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Iterations", justify="right")
        
        for r in results:
            status = "[green]✓[/green]" if r.converged else "[red]✗[/red]"
            table.add_row(
                status,
                r.fluent_name,
                f"{r.best_score:.4f}",
                str(r.statistics.total_iterations),
            )
        
        console.print(table)
        
        # Summary stats
        converged = sum(1 for r in results if r.converged)
        avg_score = sum(r.best_score for r in results) / len(results) if results else 0
        
        console.print(f"\n[bold]Summary:[/bold] {converged}/{len(results)} converged, avg score: {avg_score:.4f}")
        
        # Handle output and visualization
        if output_dir or visualize:
            from src.cli.visualize import generate_all_plots, save_results_json
            
            # Determine output directory
            if output_dir:
                out_path = Path(output_dir)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_path = Path(f"results/{domain}_{timestamp}")
            
            out_path.mkdir(parents=True, exist_ok=True)
            
            # Save results JSON
            json_path = out_path / "results.json"
            save_results_json(
                results,
                json_path,
                metadata={
                    "domain": domain,
                    "provider": provider,
                    "model": model,
                    "max_iterations": max_iterations,
                    "convergence_threshold": convergence_threshold,
                },
            )
            console.print(f"\n[dim]Results saved to:[/dim] {json_path}")
            
            # Generate visualizations
            if visualize:
                console.print("\n[bold]Generating visualizations...[/bold]")
                plot_files = generate_all_plots(results, out_path, show=show_plots)
                for pf in plot_files:
                    console.print(f"  [green]✓[/green] {pf}")
                
                console.print(f"\n[bold green]✓[/bold green] All outputs saved to: {out_path}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        raise typer.Exit(code=1)


@app.command()
def domains():
    """List available domains."""
    available = list_available_domains()
    console.print("[bold]Available domains:[/bold]")
    for domain in available:
        console.print(f"  • {domain}")


@app.command()
def version():
    """Show version information."""
    console.print("[bold cyan]rtec-llm[/bold cyan] version 0.1.0")


if __name__ == "__main__":
    app()

