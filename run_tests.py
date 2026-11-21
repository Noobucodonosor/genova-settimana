#!/usr/bin/env python3
"""Zero-dependency Test Runner for Genova Weekly Informal Outings.

Executes all 4 E2E testing tiers per TEST_INFRA.md:
- Tier 1: Feature Coverage (test_e2e_tier1_features.py)
- Tier 2: Boundary & Corner Cases (test_e2e_tier2_boundaries.py)
- Tier 3: Pairwise Interactions (test_e2e_tier3_pairwise.py)
- Tier 4: Real-World Scenarios (test_e2e_tier4_scenarios.py)

Usage:
    python3 run_tests.py
    python3 run_tests.py -v
    python3 run_tests.py --tier 1
"""

import argparse
import os
import sys
import time
import unittest

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

TIER_MODULES = [
    ("Tier 1: Feature Coverage", "tests.test_e2e_tier1_features"),
    ("Tier 2: Boundary & Corner Cases", "tests.test_e2e_tier2_boundaries"),
    ("Tier 3: Pairwise Interactions", "tests.test_e2e_tier3_pairwise"),
    ("Tier 4: Realistic Scenarios", "tests.test_e2e_tier4_scenarios"),
]


def run_tier_suite(name: str, module_name: str, verbosity: int = 1) -> unittest.TestResult:
    """Runs a single test tier and returns its TestResult."""
    suite = unittest.defaultTestLoader.loadTestsFromName(module_name)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    print(f"\n{'='*72}")
    print(f"RUNNING {name.upper()} ({module_name})")
    print(f"{'='*72}")
    result = runner.run(suite)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Genova Outings E2E Test Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose test execution")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], help="Run only a specific tier (1-4)")
    args = parser.parse_args()

    verbosity = 2 if args.verbose else 1

    selected_tiers = TIER_MODULES
    if args.tier:
        selected_tiers = [TIER_MODULES[args.tier - 1]]

    total_run = 0
    total_passed = 0
    total_skipped = 0
    total_failed = 0
    total_errors = 0

    tier_stats = []

    start_time = time.time()

    for name, module in selected_tiers:
        result = run_tier_suite(name, module, verbosity=verbosity)
        run_count = result.testsRun
        fail_count = len(result.failures)
        error_count = len(result.errors)
        skip_count = len(result.skipped)
        pass_count = run_count - fail_count - error_count - skip_count

        total_run += run_count
        total_passed += pass_count
        total_skipped += skip_count
        total_failed += fail_count
        total_errors += error_count

        tier_stats.append({
            "name": name,
            "run": run_count,
            "passed": pass_count,
            "skipped": skip_count,
            "failed": fail_count,
            "errors": error_count,
            "ok": (fail_count == 0 and error_count == 0),
        })

    elapsed = time.time() - start_time

    # Print summary table
    print("\n" + "=" * 72)
    print("GENOVA OUTINGS E2E TEST EXECUTION SUMMARY")
    print("=" * 72)
    print(f"{'Tier Name':<38} | {'Run':<5} | {'Pass':<5} | {'Skip':<5} | {'Fail':<5}")
    print("-" * 72)
    for s in tier_stats:
        status_flag = "PASS" if s["ok"] else "FAIL"
        print(f"{s['name']:<38} | {s['run']:<5} | {s['passed']:<5} | {s['skipped']:<5} | {s['failed'] + s['errors']:<5}")
    print("-" * 72)
    print(f"{'TOTAL ACROSS ALL TIERS':<38} | {total_run:<5} | {total_passed:<5} | {total_skipped:<5} | {total_failed + total_errors:<5}")
    print("=" * 72)
    print(f"Elapsed Time: {elapsed:.2f}s | Minimum Requirement: >= 82 tests | Total Tests: {total_run}")

    if total_failed > 0 or total_errors > 0:
        print("\n❌ OVERALL RESULT: FAILED (one or more test assertions failed)")
        return 1

    print("\n✅ OVERALL RESULT: PASSED (all executed tests succeeded with zero errors)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
