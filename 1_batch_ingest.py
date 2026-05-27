"""
Pathway 1: Offline Ingestion Layer (Batch API + gemini-embedding-2)

This script demonstrates how to upload a manifest of student assignments to the File API,
trigger an offline batch embedding job with gemini-embedding-2 at a 50% cost reduction,
and retrieve the resulting vector dimensions.
"""

import os
import sys
import json
import time
from google import genai
from google.genai import types

# Rich CLI and shared telemetry from local utilities
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
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
        "CAMPFIRE OPTIMIZATION PIPELINE: PATHWAY 1",
        "Offline Ingestion Layer via Batch API & gemini-embedding-2 (50% Billed Rate)"
    )
    
    jsonl_filename = "assignments_batch.jsonl"
    if not os.path.exists(jsonl_filename):
        print_error(f"Pre-generated manifest '{jsonl_filename}' not found in workspace root.")
        sys.exit(1)
        
    console.print(f"[bold]Step 1:[/bold] Loading pre-generated student homework assignments from [green]{jsonl_filename}[/green]...")
    
    table = Table(show_header=True, header_style="bold gold1", border_style="bright_black")
    table.add_column("Assignment Key", style="gold1", width=15)
    table.add_column("Document Text Summary", style="dim", width=70)
    
    total_characters = 0
    try:
        with open(jsonl_filename, "r") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    key = record.get("key")
                    parts = record.get("request", {}).get("content", {}).get("parts", [])
                    content_text = parts[0].get("text", "") if parts else ""
                    total_characters += len(content_text)
                    table.add_row(key, content_text)
    except Exception as parse_err:
        print_error(f"Parsing pre-generated '{jsonl_filename}' failed: {parse_err}")
        sys.exit(1)
        
    console.print(table)
    console.print("\n")
            
    client = genai.Client()
    uploaded_file = None
    batch_job = None

    try:
        with Progress(
            SpinnerColumn(spinner_name="dots", style="bold gold1"),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            # 2. Upload file to File API
            task1 = progress.add_task(description="Uploading JSONL file to Gemini File API...", total=None)
            uploaded_file = client.files.upload(
                file=jsonl_filename,
                config=types.UploadFileConfig(
                    display_name="student_assignments_batch_upload",
                    mime_type="jsonl"
                )
            )
            progress.update(task1, completed=True, description=f"[bold green]✓[/bold green] Upload complete: [cyan]{uploaded_file.name}[/cyan]")
            
            # 3. Create Batch Embedding Job
            task2 = progress.add_task(description="Submitting Batch Embedding Job (gemini-embedding-2)...", total=None)
            batch_job = client.batches.create_embeddings(
                model="gemini-embedding-2",
                src={'file_name': uploaded_file.name},
                config={'display_name': "EdTech Student Embeddings Batch"}
            )
            progress.update(task2, completed=True, description=f"[bold green]✓[/bold green] Batch job submitted: [cyan]{batch_job.name}[/cyan]")
            
            # 4. Poll job status
            task3 = progress.add_task(description="Polling Batch Job state...", total=None)
            completed_states = {'JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED', 'JOB_STATE_EXPIRED'}
            
            while True:
                current_job = client.batches.get(name=batch_job.name)
                state_name = current_job.state.name if hasattr(current_job.state, 'name') else current_job.state
                progress.update(task3, description=f"Polling Batch Job state... (Current: [bold gold1]{state_name}[/bold gold1])")
                
                if state_name in completed_states:
                    break
                time.sleep(10)
                
            if state_name == 'JOB_STATE_SUCCEEDED':
                progress.update(task3, completed=True, description=f"[bold green]✓[/bold green] Batch job completed successfully!")
            else:
                progress.update(task3, completed=True, description=f"[bold red]✗[/bold red] Batch job finished with error state: {state_name}")
                if hasattr(current_job, 'error') and current_job.error:
                    console.print(f"[bold red]Error details:[/bold red] {current_job.error}")
                return

        # 5. Download and Retrieve Results
        console.print("\n[bold]Step 2:[/bold] Downloading and printing embedding vector indices...")
        result_file_name = current_job.dest.file_name
        
        with console.status("[bold gold1]Downloading output result manifest...", spinner="earth") as status:
            file_content_bytes = client.files.download(file=result_file_name)
            file_content = file_content_bytes.decode('utf-8')
            
        result_table = Table(show_header=True, header_style="bold gold1", border_style="bright_black")
        result_table.add_column("Key", style="gold1", width=15)
        result_table.add_column("First 5 Dimension Values (Truncated 768)", style="dim")
        
        lines = file_content.splitlines()
        embeddings_export = []
        for line in lines:
            if line.strip():
                row_data = json.loads(line)
                row_key = row_data.get("key")
                response_obj = row_data.get("response", {})
                
                if "embeddings" in response_obj:
                    vectors = response_obj["embeddings"][0]["values"]
                elif "embeddings" in response_obj.get("embedding", {}):
                    vectors = response_obj["embedding"]["embeddings"][0]["values"]
                else:
                    vectors = response_obj.get("embedding", {}).get("values", [])
                
                embeddings_export.append({
                    "key": row_key,
                    "embedding": vectors
                })
                
                vector_str = ", ".join([f"{x:.6f}" for x in vectors[:5]]) + " ..."
                result_table.add_row(row_key, f"[ {vector_str} ]")
                
        console.print(result_table)
        
        # Save results to local JSON file
        export_filename = "assignments_embeddings.json"
        with open(export_filename, "w") as out_f:
            json.dump(embeddings_export, out_f, indent=2)
            
        # 6. Pricing Telemetry
        estimated_tokens, std_cost, billed_cost, saved_cost_1m = utilities.calculate_embedding_pricing(
            total_characters, is_batch=True
        )
        
        console.print("\n")
        console.print(Panel(
            "[bold green]✓ Pipeline Completed Successfully![/bold green]\n\n"
            f"  • Source manifest uploaded: [cyan]{uploaded_file.name}[/cyan]\n"
            f"  • Batch Job completed: [cyan]{batch_job.name}[/cyan]\n"
            f"  • Output results retrieved: [cyan]{result_file_name}[/cyan]\n"
            f"  • Local results exported: [cyan]{export_filename}[/cyan]\n"
            f"  • Total Estimated Input: [cyan]{estimated_tokens:.1f} tokens[/cyan] (text input)\n"
            f"  • Standard Baseline Cost: [cyan]${std_cost:.6f}[/cyan]\n"
            f"  • Actual Billed Cost: [bold green]${billed_cost:.6f}[/bold green] (Routing: [bold gold1]BATCH API[/bold gold1] - [bold green]50% Off[/bold green])\n"
            f"  • Net Cost Saved (per 1M requests): [bold green]${saved_cost_1m:.2f}[/bold green]",
            title="[bold green]Execution Report[/bold green]",
            border_style="green",
            expand=False
        ))
        console.print("\n")

    except Exception as e:
        print_error(str(e))
        console.print("\n")
    finally:
        # Remote Cleanup only
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
            except:
                pass

if __name__ == "__main__":
    main()
