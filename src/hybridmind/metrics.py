from dataclasses import dataclass

@dataclass
class HybridStats:
    total_inputs: int = 0

    tier1_success: int = 0
    tier1_fail: int = 0

    rule_used: int = 0

    llm_used: int = 0
    llm_fail: int = 0
    llm_rejected: int = 0
    llm_verified_and_executed: int = 0

def print_stats(stats: HybridStats) -> None:
    if stats.total_inputs == 0:
        print("[STATS] No inputs processed.")
        return

    tier1_rate = stats.tier1_success / stats.total_inputs
    fallback_rate = (stats.total_inputs - stats.tier1_success) / stats.total_inputs
    llm_dependency = stats.llm_used / stats.total_inputs

    print("\n========== HybridMind Metrics ==========")
    print(f"Total inputs: {stats.total_inputs}")
    print(f"Tier-1 (grammar) success: {stats.tier1_success} ({tier1_rate:.2%})")
    print(f"Tier-1 fail → fallback needed: {stats.tier1_fail} ({fallback_rate:.2%})")
    print(f"Rule fallback used: {stats.rule_used}")
    print(f"LLM used: {stats.llm_used}  (LLM dependency ratio = {llm_dependency:.2%})")
    print(f"LLM fail: {stats.llm_fail}")
    print(f"LLM rejected (failed verification): {stats.llm_rejected}")
    print(f"LLM verified + executed: {stats.llm_verified_and_executed}")
    print("======================================\n")
