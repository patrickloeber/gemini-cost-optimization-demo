# 🗂️ Gemini API Optimization Demo

![Optimization Demo Overview](overview.png)

A Python-only command-line repository demonstrating high-performance **Gemini API Cost-Optimization Pathways** (Context Caching, Batch API, and the Flex Inference Tier) equipped with a beautiful `rich`-styled terminal interface and real-time financial cost-accounting engines.

---

## 📁 Repository Architecture

```
/optimization-demo
├── 1_batch_ingest.py           # Pathway 1: Ingestion Layer (Batch API + gemini-embedding-2)
├── 2_tutor_cache.py            # Pathway 2: Interactive Tutoring (Context Caching + gemini-3.5-flash)
├── 2b_tutor_interactions.py    # Pathway 2b: Tutoring (Interactions API stateful chatbot)
├── 3_planner_flex.py           # Pathway 3: Study Planner (Flex Inference Tier + gemini-3.5-flash)
├── utilities.py                # Shared security checking, Rich Console styling, and Pricing engines
├── assignments_batch.jsonl     # Static manifest source containing 5 student essays
└── book.txt                    # M. Quinby - 'Mysteries of Bee-keeping Explained' (1853)
```

---

## 🧪 The Three Optimization Pathways

### 1. Ingestion Layer — [1_batch_ingest.py](1_batch_ingest.py)
* **Optimization Lever**: **Batch API** (flat **50% discount** on `gemini-embedding-2`).
* **How It Works**: Uploads the static `assignments_batch.jsonl` to the File API, runs a batch job, downloads the results, and exports the vectors to `assignments_embeddings.json`.
* **Telemetry**: Compares standard vs Batch rates, scaled per **1M requests**.

### 2. Interactive Tutoring — [2_tutor_cache.py](2_tutor_cache.py)
* **Optimization Lever**: **Explicit Context Caching** (up to **90% cheaper** input reads).
* **How It Works**: Caches the entire `book.txt` (~151,506 tokens) on the Gemini API, and runs a multi-turn Q&A chat session.
* **Telemetry**: Calculates standard vs cached rates, showing exact hit rate (**`99.98%`**) and cost savings (**up to `87% Off`**).

### 2b. Stateful Tutoring — [2b_tutor_interactions.py](2b_tutor_interactions.py)
* **Optimization Lever**: **Server-Side Stateful Interactions** (with automatic, implicit context caching).
* **How It Works**: Leverages the new stateful **Interactions API**, passing `previous_interaction_id` to link turns and maintain history on the server side without manual client history arrays.
* **Telemetry**: Displays detailed cost accounting showing the token usage from both turns.

### 3. Custom Study Planner — [3_planner_flex.py](3_planner_flex.py)
* **Optimization Lever**: **Flex Inference Tier** (flat **50% discount** on sheddable off-peak capacity).
* **How It Works**: Routes planning queries to the `flex` tier inside a non-blocking background thread with exponential backoff preemption handling.
* **Telemetry**: Compares standard vs Flex rates, scaled per **1,000 requests**.

---

## 🛠️ Shared Telemetry Engine — [utilities.py](utilities.py)

All non-visual logic is consolidated in `utilities.py` to keep the core scripts under 120 lines of code:
* **`check_api_key()`**: Verifies the environment configuration.
* **`calculate_embedding_pricing()`**: Models `gemini-embedding-2` input costs.
* **`calculate_caching_pricing()`**: Pro-rates cache storage and hit-rate savings.
* **`calculate_flex_pricing()`**: Models standard vs Flex pricing models.

## 🚀 Setup & Execution Guide

1. **Create Virtual Environment & Install Dependencies**:
   Create a Python virtual environment, activate it, and install/upgrade the required libraries:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -U google-genai rich
   ```

2. **Configure API Key**:
   Export your Gemini API Key (get one at [ai.studio](ai.studio)) as an environment variable:
   ```bash
   export GEMINI_API_KEY="your-actual-gemini-api-key"
   ```

   > [!IMPORTANT]
   > **Free Tier Compatibility**: The **Batch API (Pathway 1)** is **not available** on the Gemini API Free Tier and requires a paid billing plan. However, **all other pathways** (Context Caching, Interactions API, and Flex Inference Tier) can be followed using a **free API key**!

3. **Run Ingestion Layer (Pathway 1)**:
   ```bash
   python3 1_batch_ingest.py
   ```

4. **Run Context Caching Chatbot (Pathway 2)**:
   ```bash
   python3 2_tutor_cache.py
   ```

5. **Run Interactions API Chatbot (Pathway 2b)**:
   ```bash
   python3 2b_tutor_interactions.py
   ```

6. **Run Flex Planner Agent (Pathway 3)**:
   ```bash
   python3 3_planner_flex.py
   ```

---

## 🔗 Official Documentation & References

To learn more about the technical specifications, best practices, and API parameters for these optimization techniques, explore the official Google Gemini documentation:
* **Overview**: [Gemini API Optimization Guide](https://ai.google.dev/gemini-api/docs/optimization)
* **Pathway 1**: [Gemini Batch API Reference](https://ai.google.dev/gemini-api/docs/batch-api?batch=file)
* **Pathway 2**: [Gemini Context Caching Guide](https://ai.google.dev/gemini-api/docs/caching)
* **Pathway 2b**: [Gemini Interactions API Overview](https://ai.google.dev/gemini-api/docs/interactions/interactions-overview)
* **Pathway 3**: [Gemini Flex Inference Documentation](https://ai.google.dev/gemini-api/docs/flex-inference)

---

## 💡 Best Practices & Production Patterns

### 📦 Batch API
* **Segment Batches**: Break large datasets into smaller, manageable sub-batches to get intermediate results sooner and limit failed job risks.
* **Webhooks**: Configure webhook callback endpoints to handle job completion asynchronously instead of resource-heavy polling loops.
* **Dry-Run Schema**: Always test a single request locally first to avoid large-scale validation or processing failures.

### 💾 Context Caching (Implicit & Explicit)
* **Implicit Caching (Interactions API)**:
  * Place large, static components (e.g., system instructions, textbook PDFs) at the very beginning of your prompt structure:  
    `[System Instruction + Textbook PDF] (CACHED) ➔ [User Query] (DYNAMIC)`
  * Group/cluster requests with identical prefixes within a short timeframe to maximize cache reuse.
* **Explicit Caching**:
  * **Optimize TTL**: Tune the cache Time-To-Live (TTL) to match typical user session gaps (e.g., 15 minutes) to avoid paying for idle storage while preserving reuse windows.
* **Telemetry & Monitoring**:
  * Regularly inspect standard metric fields in `usage_metadata` (specifically cache hit rates, latency impact, and proportion of tokens read from the cache) to continuously refine your partition strategies.

### ⚡ Flex Inference Tier
* **Configure Timeouts**: Set custom client-side timeouts to proactively handle off-peak scheduling variability and avoid indefinite connection hangs.
* **Mandatory Retries**: Always design background tasks with robust exponential backoff handlers to gracefully handle capacity-based retries.
* **Dynamic Fallback Routing**: The Flex tier does not automatically fallback to the Standard tier if capacity is fully saturated; you must implement your own logic to dynamically route queries to the Standard tier when meeting capacity constraints.
* **Decoupled Task Queues**: Avoid calling the Flex tier directly from the main request-response thread. Wrap queries inside a reliable background task queue (e.g., Celery, Redis Queue) to isolate downstream processing.
