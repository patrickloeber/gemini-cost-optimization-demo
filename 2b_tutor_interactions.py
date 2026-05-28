"""
Pathway 2b: Stateful Interactive Tutoring (Interactions API + gemini-3.5-flash)

This script demonstrates how to implement a stateful multi-turn tutoring session
using the new Interactions API with implicit server-side context caching.
"""

import os
import sys
import time
from google import genai
from google.genai import types

# Rich CLI and shared utilities
from rich.table import Table
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

def main():
    # 1. Authentication Guard & Header
    utilities.check_api_key()
    print_header(
        "CAMPFIRE OPTIMIZATION PIPELINE: PATHWAY 2B",
        "Stateful Interactive Tutoring via Interactions API & gemini-3.5-flash (Implicit Caching)"
    )
    
    client = genai.Client()
    model_name = "gemini-3.5-flash"
    
    # 2. Read the entire book.txt file into memory
    book_text = ""
    book_filename = "book.txt"
    if not os.path.exists(book_filename):
        print_error(f"Reference book file '{book_filename}' not found in workspace root.")
        sys.exit(1)
        
    try:
        with console.status("[bold gold1]Reading entire local reference book 'Mysteries of Bee-keeping Explained'...", spinner="earth") as status:
            with open(book_filename, "r") as f:
                book_text = f.read().strip()
                
    except Exception as e:
        print_error(f"Failed to read local book.txt: {e}")
        sys.exit(1)
        
    estimated_tokens = len(book_text) // 4
    console.print(f"📖 [bold]Loading entire reference book 'Mysteries of Bee-keeping Explained' into Context Cache...[/bold]")
    console.print(f"  • Document Size: [bold cyan]{len(book_text)} characters[/bold cyan]")
    console.print(f"  • Estimated Token Volume: [bold cyan]~{estimated_tokens} tokens[/bold cyan]\n")
    
    # Prepare system instruction containing the full book
    system_instruction = (
        "You are an expert apiarian scholar and biology tutor. Answer student questions based "
        "strictly on the provided book: M. Quinby's Mysteries of Bee-keeping Explained (1853). "
        "Adopt a helpful, scientific tone, cite specific chapters and page details from the text, and use bullet points for lists."
    )
    
    # Combine instructions with book content
    full_system_instruction = f"{system_instruction}\n\n--- REFERENCE BOOK ---\n{book_text}"
    
    # Prepare multi-turn student conversation queries
    student_turns = [
        "Why does Quinby say that using drums, tin pans, and bells to make 'a horrible din' during swarming is mostly a useless whim, and what does he recommend doing instead?",
        "What are the principal causes of bees freezing or dying in the winter when left in the open air, and what is Quinby's unique solution of inverting the hives?"
    ]
    
    telemetry_records = []
    start_time = time.time()
    previous_interaction_id = None
    
    try:
        # 3. Conduct QA turns using the stateful Interactions API
        for idx, question in enumerate(student_turns, start=1):
            console.print(Panel(f"[bold cyan]Student Query (Turn {idx}):[/bold cyan] [italic]{question}[/italic]", border_style="cyan", expand=False))
            
            with console.status(f"[bold gold1]Querying apiarian tutor via Interactions API (Server-side state)...", spinner="arc") as status:
                # Standard or stateful interaction creation
                if previous_interaction_id is None:
                    interaction = client.interactions.create(
                        model=model_name,
                        system_instruction=full_system_instruction,
                        input=question
                    )
                else:
                    # System instructions are interaction-scoped and must be re-specified on each turn
                    interaction = client.interactions.create(
                        model=model_name,
                        system_instruction=full_system_instruction,
                        input=question,
                        previous_interaction_id=previous_interaction_id
                    )
            
            # Render the tutor output
            response_text = interaction.output_text
            console.print(Panel(
                Markdown(response_text),
                title=f"[bold gold1]Tutor Response (Turn {idx})[/bold gold1]",
                border_style="gold1"
            ))
            
            # Extract usage tokens
            usage = interaction.usage
            prompt_tokens = usage.total_input_tokens
            cached_tokens = usage.total_cached_tokens
            output_tokens = usage.total_output_tokens
            
            telemetry_records.append({
                "turn": f"Turn {idx}",
                "prompt": prompt_tokens,
                "cached": cached_tokens,
                "output": output_tokens,
                "elapsed": time.time() - start_time
            })
            
            # Save current interaction ID for the next turn's history link
            previous_interaction_id = interaction.id
            console.print("\n")
            
        # 4. Telemetry Audit Report
        console.print("[bold]Step 3:[/bold] Post-Flight Billing & Cache Telemetry Audit (Interactions API):")
        
        telemetry_table = Table(show_header=True, header_style="bold gold1", border_style="bright_black")
        telemetry_table.add_column("Conversation Turn", style="gold1", width=18)
        telemetry_table.add_column("Input Tokens", justify="right")
        telemetry_table.add_column("Cached Tokens", justify="right", style="green")
        telemetry_table.add_column("Cached Input", justify="center", style="cyan")
        telemetry_table.add_column("Output Tokens", justify="right")
        telemetry_table.add_column("Cost Savings", justify="center", style="bold green")
        
        for row in telemetry_records:
            # Calculate detailed pricing telemetry using shared engine
            hit_rate, total_cost_std, total_cost_opt, financial_savings = utilities.calculate_caching_pricing(
                prompt_tokens=row["prompt"],
                cached_tokens=row["cached"],
                output_tokens=row["output"],
                elapsed_seconds=row["elapsed"]
            )
            
            telemetry_table.add_row(
                row["turn"],
                f"{row['prompt']}",
                f"{row['cached']}",
                f"{hit_rate:.2f}%",
                f"{row['output']}",
                f"{financial_savings:.1f}% Off"
            )
        console.print(telemetry_table)
        console.print("\n")

    except Exception as e:
        print_error(str(e))
        console.print("\n")

if __name__ == "__main__":
    main()
