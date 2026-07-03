import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.langchain_agents import (
    run_monitoring_agent,
    run_margin_agent,
    run_execution_agent,
)


def run_repricer_chain():
    print("=" * 60)
    print("REPRICER AGENT — LANGGRAPH PIPELINE")
    print("=" * 60)
    print()

    # Phase 1
    print(">>> PHASE 1: Monitoring Agent (Scraping)")
    print("-" * 40)
    monitoring_result = run_monitoring_agent()
    print("\nResult:", monitoring_result)
    print()

    # Phase 2
    print(">>> PHASE 2: Margin Agent (Pricing Analysis)")
    print("-" * 40)
    margin_result = run_margin_agent()
    print("\nResult:", margin_result)
    print()

    # Phase 3 — receives margin agent's output as context
    print(">>> PHASE 3: Execution Agent (DB Write)")
    print("-" * 40)
    execution_result = run_execution_agent(margin_result)
    print("\nResult:", execution_result)
    print()

    print("=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_repricer_chain()