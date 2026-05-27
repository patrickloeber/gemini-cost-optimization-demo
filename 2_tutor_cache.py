"""
Pathway 2: Interactive Tutoring (Context Caching + gemini-3.5-flash)

This script demonstrates how to cache a massive educational textbook once, and then
run multiple extremely low-cost interactive tutoring turns reading directly from the cache,
showing exact token telemetry and cost savings based on the standard pricing sheet.
"""

import os
import sys
import time
import httpx
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
        "CAMPFIRE OPTIMIZATION PIPELINE: PATHWAY 2",
        "Interactive Tutoring Layer via Context Caching & gemini-3.5-flash (90% Caching Discount)"
    )
    
    client = genai.Client()
    model_name = "gemini-3.5-flash"
    
    # 2. Read and slice Chapter III from the local book.txt file
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
    
    # Create explicit Context Cache
    cache = None
    try:
        with console.status("[bold gold1]Provisioning explicit context cache on Gemini API...", spinner="bouncingBar") as status:
            system_instruction = (
                "You are an expert apiarian scholar and biology tutor. Answer student questions based "
                "strictly on the provided book: M. Quinby's Mysteries of Bee-keeping Explained (1853). "
                "Adopt a helpful, scientific tone, cite specific chapters and page details from the text, and use bullet points for lists."
            )
            cache = client.caches.create(
                model=model_name,
                config=types.CreateCachedContentConfig(
                    display_name="quinby_beekeeping_full_book",
                    contents=[book_text],
                    system_instruction=system_instruction,
                    ttl="600s"
                )
            )
        
        console.print(f"[bold green]✓ Cache Created Successfully![/bold green]")
        console.print(f"  • Cache Key: [cyan]{cache.name}[/cyan]")
        console.print(f"  • Expiration Time: [cyan]{cache.expire_time}[/cyan]\n")
        
        # Record cache creation time
        cache_creation_time = time.time()
        
        # Prepare multi-turn student conversation logs
        student_turns = [
            "Why does Quinby say that using drums, tin pans, and bells to make 'a horrible din' during swarming is mostly a useless whim, and what does he recommend doing instead?",
            "What are the principal causes of bees freezing or dying in the winter when left in the open air, and what is Quinby's unique solution of inverting the hives?"
        ]
        
        telemetry_records = []
        
        # 3. Conduct QA turns
        for idx, question in enumerate(student_turns, start=1):
            console.print(Panel(f"[bold cyan]Student Query (Turn {idx}):[/bold cyan] [italic]{question}[/italic]", border_style="cyan", expand=False))
            
            with console.status(f"[bold gold1]Querying apiarian tutor model reading from cache...", spinner="arc") as status:
                response = client.models.generate_content(
                    model=model_name,
                    contents=question,
                    config=types.GenerateContentConfig(
                        cached_content=cache.name
                    )
                )
            
            console.print(Panel(
                Markdown(response.text),
                title=f"[bold gold1]Tutor Response (Turn {idx})[/bold gold1]",
                border_style="gold1"
            ))
            
            meta = response.usage_metadata
            prompt_tokens = meta.prompt_token_count
            cached_tokens = meta.cached_content_token_count
            output_tokens = meta.candidates_token_count
            
            telemetry_records.append({
                "turn": f"Turn {idx}",
                "prompt": prompt_tokens,
                "cached": cached_tokens,
                "output": output_tokens,
                "elapsed": time.time() - cache_creation_time
            })
            
            console.print("\n")
            
        # 3. Telemetry Audit Report
        console.print("[bold]Step 3:[/bold] Post-Flight Billing & Cache Telemetry Audit:")
        
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
    finally:
        # 4. Clean up Cache
        if cache:
            try:
                with console.status("[bold red]De-allocating explicit cache from Gemini API...", spinner="simpleDots") as status:
                    client.caches.delete(name=cache.name)
                console.print("[bold green]✓ Cache safely de-allocated.[/bold green] Stored resources released successfully.\n")
            except Exception as clean_e:
                console.print(f"[bold red]✗ Failed to delete cache: {clean_e}[/bold red]\n")

if __name__ == "__main__":
    main()
