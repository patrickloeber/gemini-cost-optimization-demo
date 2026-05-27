"""
Pathway 3: Custom Study Planner (Flex Inference Tier + gemini-3.5-flash)

This script demonstrates how to route non-urgent background tasks (like study planner compiling)
to the sheddable "Flex" inference tier synchronous endpoint with a 50% cost discount.
It includes advanced, production-grade exponential backoff retries inside a background thread.
"""

import os
import sys
import time
import threading
from google import genai
from google.genai import types

# Rich CLI and shared utilities
from rich.panel import Panel
from rich.markdown import Markdown
import utilities
from utilities import console

def print_header(title, description):
    """Prints a beautiful standardized Panel header for each pipeline pathway."""
    console.print("\n")
    console.print(Panel(
        f"[bold gold1]{title}[/bold gold1]\n"
        f"[italic sand]{description}[/italic sand]",
        border_style="bright_black",
        expand=False
    ))
    console.print("\n")

def print_error(message):
    """Prints a standardized red error panel."""
    console.print(Panel(
        f"[bold red]✗ Error: {message}[/bold red]",
        title="[bold red]Pipeline Failure[/bold red]",
        border_style="red",
        expand=False
    ))

PLANNER_PROMPT = """
You are an advanced academic study advisor. 
Compile a highly customized 7-day study timeline for a student failing 'Cellular Respiration':
1. Identify 3 major weak areas based on student scoring: Glycolysis regulatory enzymes, Krebs Cycle intermediates, and active proton transport across inner mitochondrial membranes.
2. Provide a custom high-impact active-recall task for each day.
3. Recommend short, concrete diagnostic milestones (e.g., 'Explain PFK inhibition in 2 sentences' to double check standards).
Keep responses structured, professional, and highly actionable. Use markdown headers.
"""

def run_flex_inference_with_retry(client, model_name, max_retries=3, base_delay=5):
    for attempt in range(max_retries):
        try:
            console.print(f"  • [bold]Attempt {attempt + 1}/{max_retries}[/bold]: Submitting request to [bold gold1]Flex Tier[/bold gold1] synchronous queue...")
            
            response = client.models.generate_content(
                model=model_name,
                contents=PLANNER_PROMPT,
                config={
                    "service_tier": "flex",
                    "http_options": {"timeout": 600000}
                }
            )
            return response, "flex"
            
        except Exception as e:
            console.print(f"    [bold red]✗ Flex Tier capacity unavailable or congested:[/bold red] {e}")
            
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                console.print(f"      [dim]Congestion preemption handled. Applying backoff... retrying in {delay}s.[/dim]")
                time.sleep(delay)
            else:
                console.print(f"\n    [bold orange3]⚠ Flex capacity retries exhausted. Routing fallback to Standard Tier...[/bold orange3]")
                
                # Fallback to standard (Full price billing, non-sheddable)
                with console.status("[bold orange3]Executing standard fallback request...", spinner="dots2") as status:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=PLANNER_PROMPT
                    )
                return response, "standard"

def main():
    # 1. Authentication Guard & Header
    utilities.check_api_key()
    print_header(
        "CAMPFIRE OPTIMIZATION PIPELINE: PATHWAY 3",
        "Synchronous Study Planner via Flex Inference Tier (50% Billed Rate with preemption handling)"
    )
    
    client = genai.Client()
    model_name = "gemini-3.5-flash"
    
    console.print(f"📝 [bold]Creating non-blocking Study Plan request in background thread...[/bold]")
    console.print(f"  • Planner prompt length: [cyan]{len(PLANNER_PROMPT)} characters[/cyan]")
    console.print(f"  • Configured Timeout limits: [cyan]600,000 ms (10 mins)[/cyan]")
    console.print(f"  • Maximum Congestion retries: [cyan]3 attempts[/cyan]\n")
    
    result_holder = {}
    error_holder = []
    
    def thread_worker():
        try:
            res, tier = run_flex_inference_with_retry(client, model_name)
            result_holder["response"] = res
            result_holder["tier"] = tier
        except Exception as ex:
            error_holder.append(ex)
            
    # Spin up background thread
    worker_thread = threading.Thread(target=thread_worker, name="FlexPlannerWorker")
    worker_thread.start()
    
    # The main thread continues executing and remains unblocked!
    # We showcase this by running a live ticking spinner in the foreground.
    with console.status("[bold cyan]Background thread spawned...", spinner="arc") as status:
        elapsed = 0.0
        while worker_thread.is_alive():
            time.sleep(0.1)
            elapsed += 0.1
            status.update(
                f"[bold cyan]Active Foreground Monitor:[/bold cyan] "
                f"Background thread '[bold yellow]FlexPlannerWorker[/bold yellow]' is running... "
                f"([bold gold1]{elapsed:.1f}s elapsed[/bold gold1])"
            )
            
    worker_thread.join()
    
    # Handle any errors from the worker thread
    if error_holder:
        raise error_holder[0]
        
    response = result_holder["response"]
    tier_used = result_holder["tier"]
    
    # Display Output Plan
    console.print("\n")
    console.print(Panel(
        Markdown(response.text),
        title=f"[bold gold1]Generated Study Plan ({tier_used.upper()} TIER)[/bold gold1]",
        border_style="gold1"
    ))
    console.print("\n")
    
    # 2. Billing Telemetry & Pricing Calculations
    meta = response.usage_metadata
    prompt_tokens = meta.prompt_token_count
    output_tokens = meta.candidates_token_count
    
    total_cost_std, total_cost_billed, saved_cost_1k = utilities.calculate_flex_pricing(
        prompt_tokens, output_tokens, is_flex=(tier_used == "flex")
    )
    
    discount_lbl = "50% Off" if tier_used == "flex" else "0% (Standard Rate)"
    border_style = "green" if tier_used == "flex" else "orange3"
    
    console.print(Panel(
        f"  • Model utilised: [cyan]{model_name}[/cyan]\n"
        f"  • Prompt / Input tokens: [cyan]{prompt_tokens} tokens[/cyan]\n"
        f"  • Generated / Output tokens: [cyan]{output_tokens} tokens[/cyan]\n"
        f"  • Standard Baseline Cost: [cyan]${total_cost_std:.6f}[/cyan]\n"
        f"  • Actual Billed Cost: [bold green]${total_cost_billed:.6f}[/bold green] (Routing: [bold gold1]{tier_used.upper()}[/bold gold1] - [bold green]{discount_lbl}[/bold green])\n"
        f"  • Net Cost Saved (per 1k requests): [bold green]${saved_cost_1k:.2f}[/bold green]",
        title="[bold green]Post-Flight Optimization Summary[/bold green]",
        border_style=border_style,
        expand=False
    ))
    console.print("\n")

if __name__ == "__main__":
    main()
