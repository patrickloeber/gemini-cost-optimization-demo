"""
CAMPFIRE CLI Optimization Pipeline: Shared Utilities & Telemetry Engine

This module centralizes CLI formatting, authentication checks, and precise
pricing calculations for Caching, Batch API, and Flex Tier operations.
"""

import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

# Global shared Rich Console
console = Console()

# ==========================================================================
# 1. Security & Guardrails
# ==========================================================================

def check_api_key():
    """Verifies the GEMINI_API_KEY environment variable is present; exits otherwise."""
    if "GEMINI_API_KEY" not in os.environ:
        console.print("\n")
        console.print(Panel(
            "[bold red]Error: GEMINI_API_KEY Environment Variable Missing[/bold red]\n\n"
            "To run this production script, you must set your Gemini API Key:\n"
            "[bold green]export GEMINI_API_KEY=\"your-actual-api-key\"[/bold green]\n\n"
            "Please obtain a key from [underline]https://aistudio.google.com/[/underline]",
            title="[bold red]API Authentication Error[/bold red]",
            border_style="red",
            expand=False
        ))
        console.print("\n")
        sys.exit(1)

# ==========================================================================
# 2. Telemetry & Pricing Calculations
# ==========================================================================

# -- PATHWAY 1: Embeddings Pricing --
def calculate_embedding_pricing(total_characters, is_batch=True):
    """
    Calculates pricing for gemini-embedding-2 on Paid Tier:
    - Text input price: $0.20 / 1M tokens
    - Batch API offers a 50% discount ($0.10 / 1M tokens)
    Returns: (estimated_tokens, std_cost, billed_cost, saved_cost_1m)
    """
    estimated_tokens = total_characters / 4.0
    std_cost = (estimated_tokens * 0.20) / 1000000
    
    discount_multiplier = 0.50 if is_batch else 1.00
    billed_cost = std_cost * discount_multiplier
    saved_cost_1m = (std_cost - billed_cost) * 1000000
    
    return estimated_tokens, std_cost, billed_cost, saved_cost_1m

# -- PATHWAY 2: Context Caching Pricing --
def calculate_caching_pricing(prompt_tokens, cached_tokens, output_tokens, elapsed_seconds):
    """
    Calculates pricing for gemini-3.5-flash with Caching on Paid Tier:
    - Standard Input: $1.50 / 1M tokens
    - Standard Output: $9.00 / 1M tokens
    - Cached Read: $0.15 / 1M tokens (90% off standard input)
    - Cache Storage: $1.00 / 1M tokens per hour
    Returns: (hit_rate, total_cost_std, total_cost_opt, financial_savings)
    """
    hit_rate = (cached_tokens / prompt_tokens) * 100 if prompt_tokens > 0 else 0
    
    # Standard cost (Without Caching)
    input_cost_std = prompt_tokens * 1.50 / 1000000
    output_cost_std = output_tokens * 9.00 / 1000000
    total_cost_std = input_cost_std + output_cost_std
    
    # Optimized cost (With Caching)
    cached_input_cost = cached_tokens * 0.15 / 1000000
    dynamic_input_cost = (prompt_tokens - cached_tokens) * 1.50 / 1000000
    output_cost_opt = output_tokens * 9.00 / 1000000
    
    # Storage pro-rated
    elapsed_hours = elapsed_seconds / 3600.0
    storage_fee = cached_tokens * 1.00 * elapsed_hours / 1000000
    
    total_cost_opt = cached_input_cost + dynamic_input_cost + output_cost_opt + storage_fee
    financial_savings = (1 - (total_cost_opt / total_cost_std)) * 100 if total_cost_std > 0 else 0
    
    return hit_rate, total_cost_std, total_cost_opt, financial_savings

# -- PATHWAY 3: Flex Tier Pricing --
def calculate_flex_pricing(prompt_tokens, output_tokens, is_flex=True):
    """
    Calculates pricing for gemini-3.5-flash on Flex vs Standard Tiers:
    - Standard Input: $1.50 / 1M tokens
    - Standard Output: $9.00 / 1M tokens
    - Flex Synchronous Tier applies flat 50% off both rates
    Returns: (total_cost_std, total_cost_billed, saved_cost_1k)
    """
    std_input_cost = prompt_tokens * 1.50 / 1000000
    std_output_cost = output_tokens * 9.00 / 1000000
    total_cost_std = std_input_cost + std_output_cost
    
    discount_multiplier = 0.50 if is_flex else 1.00
    billed_input_cost = std_input_cost * discount_multiplier
    billed_output_cost = std_output_cost * discount_multiplier
    total_cost_billed = billed_input_cost + billed_output_cost
    
    saved_cost = total_cost_std - total_cost_billed
    saved_cost_1k = saved_cost * 1000
    
    return total_cost_std, total_cost_billed, saved_cost_1k
