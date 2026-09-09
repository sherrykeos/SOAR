"""
SOAR Manual Model Routing & Classification Benchmark.
Tests task classification, model routing, direct answer, coding, and fallback behavior
across sample queries against local Ollama models.
100% on-premise, offline, and air-gapped.
"""

import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.orchestrator.orchestrator import Orchestrator


def run_benchmark():
    print("=" * 75)
    print("SOAR TASK CLASSIFIER & ADAPTIVE MODEL ROUTING BENCHMARK")
    print("=" * 75)

    orchestrator = Orchestrator()

    benchmark_tasks = [
        "What is 2 + 2?",
        "Write a Python function to sum three numbers.",
        "Explain why a pressure vessel might experience abnormal pressure.",
        "What does this image show?",
        "What is the pressure limit for Boiler B-4?",
        "Read inputs/inspection_report.pdf and create outputs/approval_note.docx",
    ]

    for idx, task in enumerate(benchmark_tasks, 1):
        print(f"\n[{idx}/{len(benchmark_tasks)}] TASK: \"{task}\"")
        start_time = time.perf_counter()
        try:
            result = orchestrator.process_task(task)
            latency = time.perf_counter() - start_time

            profile = result.get("task_profile", {})
            model_info = result.get("model", {})

            print(f"  - Classified Task Type: {profile.get('task_type')}")
            print(f"  - Complexity:          {profile.get('complexity')}")
            print(f"  - Execution Mode:      {result.get('execution_mode')}")
            print(f"  - Requires RAG:        {profile.get('requires_rag')}")
            print(f"  - Requires Vision:     {profile.get('requires_vision')}")
            print(f"  - Requires Coding:     {profile.get('requires_coding')}")
            print(f"  - Requested Model:     {model_info.get('requested')}")
            print(f"  - Actual Model:        {model_info.get('actual')}")
            print(f"  - Fallback Used:       {model_info.get('fallback_used')}")
            if model_info.get("fallback_reason"):
                print(f"  - Fallback Reason:     {model_info.get('fallback_reason')}")
            print(f"  - Latency:             {latency:.3f}s")
            resp_snippet = result.get('response', '')[:120].replace('\n', ' ')
            print(f"  - Response Preview:    {resp_snippet}...")
        except Exception as e:
            latency = time.perf_counter() - start_time
            print(f"  - Execution Failed:    {e} (after {latency:.3f}s)")

    print("\n" + "=" * 75)
    print("MODEL ROUTING BENCHMARK COMPLETED")
    print("=" * 75)


if __name__ == "__main__":
    run_benchmark()
