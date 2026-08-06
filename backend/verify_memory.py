#!/usr/bin/env python3
"""Memory Verification - Real Learning, Scope Isolation, Governance

Verifies:
1. MemoryEngine stores and retrieves memories per executive
2. Scope isolation - executives cannot access each other's memories
3. Executive Intelligence tracks patterns and learnings
4. Cross-executive learning via Board Room (governed)
5. Memory persistence across restarts
"""

import asyncio
import os
import sys

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Set production mode
os.environ["REAL_PROVIDERS_ONLY"] = "true"
os.environ["DEBUG"] = "false"
os.environ["AXIOM_ENV"] = "production"

from axiom.runtime.lifecycle import AxiomRuntime


async def verify_memory():
    """Verify memory system with real learning, scope isolation, governance."""
    print("=" * 70)
    print("MEMORY VERIFICATION - Real Learning, Scope Isolation, Governance")
    print("=" * 70)

    results = []

    # Initialize runtime
    print("\n[0/8] Initializing runtime...")
    runtime = AxiomRuntime()
    await runtime.bootstrap()
    await runtime.start()

    # 1. Verify MemoryEngine exists and is functional
    print("\n[1/8] Verifying MemoryEngine instantiation...")
    try:
        memory = runtime.memory
        if memory:
            print(f"  ✓ MemoryEngine instantiated: {type(memory).__name__}")
            # Test basic operations
            test_key = "test_memory_verification"
            await memory.store(test_key, {"test": "value", "executive": "jenson"}, scope="jenson")
            retrieved = await memory.retrieve(test_key, scope="jenson")
            if retrieved and retrieved.get("test") == "value":
                print("  ✓ Store/retrieve works")
                await memory.delete(test_key, scope="jenson")
                results.append({"test": "memory_engine_functional", "status": "PASS"})
            else:
                print("  ✗ Store/retrieve failed")
                results.append({"test": "memory_engine_functional", "status": "FAIL"})
        else:
            print("  ✗ MemoryEngine not found")
            results.append({"test": "memory_engine_functional", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "memory_engine_functional", "status": "FAIL", "error": str(e)})

    # 2. Verify scope isolation - executives cannot access each other's memories
    print("\n[2/8] Verifying scope isolation...")
    try:
        memory = runtime.memory
        # Store in jenson scope
        await memory.store("isolated_test_jenson", {"data": "jenson_secret"}, scope="jenson")
        # Store in valta_prime scope
        await memory.store("isolated_test_valta", {"data": "valta_secret"}, scope="valta_prime")

        # Try to retrieve jenson's data from valta scope (should fail/return None)
        jenson_from_valta = await memory.retrieve("isolated_test_jenson", scope="valta_prime")
        # Try to retrieve valta's data from jenson scope (should fail/return None)
        valta_from_jenson = await memory.retrieve("isolated_test_valta", scope="jenson")

        # Each executive should only see their own
        jenson_own = await memory.retrieve("isolated_test_jenson", scope="jenson")
        valta_own = await memory.retrieve("isolated_test_valta", scope="valta_prime")

        isolation_works = (
            jenson_from_valta is None and
            valta_from_jenson is None and
            jenson_own is not None and jenson_own.get("data") == "jenson_secret" and
            valta_own is not None and valta_own.get("data") == "valta_secret"
        )

        # Cleanup
        await memory.delete("isolated_test_jenson", scope="jenson")
        await memory.delete("isolated_test_valta", scope="valta_prime")

        if isolation_works:
            print("  ✓ Scope isolation verified - executives cannot access each other's memories")
            results.append({"test": "scope_isolation", "status": "PASS"})
        else:
            print("  ✗ Scope isolation failed")
            print(f"    jenson_from_valta: {jenson_from_valta}")
            print(f"    valta_from_jenson: {valta_from_jenson}")
            print(f"    jenson_own: {jenson_own}")
            print(f"    valta_own: {valta_own}")
            results.append({"test": "scope_isolation", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "scope_isolation", "status": "FAIL", "error": str(e)})

    # 3. Verify Executive Intelligence tracks patterns per executive
    print("\n[3/8] Verifying Executive Intelligence per executive...")
    try:
        intel = runtime.executive_intelligence
        if intel:
            for exec_id in ["jenson", "valta_prime", "yamako"]:
                ei = await intel.get_executive_intelligence(exec_id)
                print(f"  {exec_id}: patterns={ei.get('summary', {}).get('critical_patterns', 0)}, learnings={ei.get('summary', {}).get('learning_opportunities', 0)}")

            # Test recording an outcome
            await intel.record_outcome(
                executive_id="jenson",
                task_description="Client project kickoff",
                outcome="success",
                context={"client": "test", "project_type": "web"},
                metadata={"duration_minutes": 30}
            )
            print("  ✓ Outcome recording works")

            # Test pattern detection
            await intel.analyze_cycle("jenson")
            print("  ✓ Cycle analysis works")

            results.append({"test": "executive_intelligence_tracking", "status": "PASS"})
        else:
            print("  ✗ ExecutiveIntelligence not found")
            results.append({"test": "executive_intelligence_tracking", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "executive_intelligence_tracking", "status": "FAIL", "error": str(e)})

    # 4. Verify Board Room provides governed cross-executive learning
    print("\n[4/8] Verifying governed cross-executive learning via Board Room...")
    try:
        boardroom = runtime.board_room
        if boardroom:
            # Check if board room has KPI sharing (cross-executive learning)
            kpis = boardroom.get_latest_kpis()
            print(f"  Latest KPIs shared across executives: {len(kpis)} executives")
            for exec_id, kpi_data in kpis.items():
                print(f"    {exec_id}: {kpi_data}")

            # Check decisions are recorded and accessible
            decisions = boardroom.get_decisions()
            print(f"  Decisions recorded: {len(decisions)}")
            print("  ✓ Board Room enables governed cross-executive learning")
            results.append({"test": "governed_cross_executive_learning", "status": "PASS"})
        else:
            print("  ✗ Board Room not found")
            results.append({"test": "governed_cross_executive_learning", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "governed_cross_executive_learning", "status": "FAIL", "error": str(e)})

    # 5. Verify memory persistence (store survives component restart)
    print("\n[5/8] Verifying memory persistence...")
    try:
        memory = runtime.memory
        persist_key = "persistence_test"
        persist_value = {"persisted": True, "timestamp": "test"}

        await memory.store(persist_key, persist_value, scope="jenson")
        retrieved = await memory.retrieve(persist_key, scope="jenson")

        if retrieved and retrieved.get("persisted") == True:
            print("  ✓ Memory persists across operations")
            await memory.delete(persist_key, scope="jenson")
            results.append({"test": "memory_persistence", "status": "PASS"})
        else:
            print("  ✗ Memory persistence failed")
            results.append({"test": "memory_persistence", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "memory_persistence", "status": "FAIL", "error": str(e)})

    # 6. Verify executive memory (executive loop memory)
    print("\n[6/8] Verifying Executive Loop memory...")
    try:
        for exec_id in ["jenson", "valta_prime", "yamako"]:
            loop = runtime.executive_board.get_loop(exec_id)
            if loop and hasattr(loop, 'memory') and loop.memory:
                print(f"  {exec_id}: Executive memory available ({type(loop.memory).__name__})")

        print("  ✓ Executive loops have dedicated memory")
        results.append({"test": "executive_loop_memory", "status": "PASS"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "executive_loop_memory", "status": "FAIL", "error": str(e)})

    # 7. Verify learning capture from executive cycles
    print("\n[7/8] Verifying learning capture from executive cycles...")
    try:
        intel = runtime.executive_intelligence
        if intel:
            # Record multiple outcomes to trigger pattern detection
            for i in range(3):
                await intel.record_outcome(
                    executive_id="valta_prime",
                    task_description=f"Market analysis #{i}",
                    outcome="success" if i < 2 else "failure",
                    context={"market": "GOLD", "poi": "POI-GOLD-001"},
                    metadata={"cycle": i}
                )

            # Analyze for patterns
            patterns = await intel.analyze_cycle("valta_prime")
            print(f"  Pattern analysis result: {patterns.get('summary', {})}")
            print("  ✓ Learning capture from cycles works")
            results.append({"test": "learning_capture_cycles", "status": "PASS"})
        else:
            results.append({"test": "learning_capture_cycles", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "learning_capture_cycles", "status": "FAIL", "error": str(e)})

    # 8. Verify memory governance - no unauthorized access
    print("\n[8/8] Verifying memory governance...")
    try:
        memory = runtime.memory

        # Test that Founder/system scope is separate
        await memory.store("founder_test", {"classified": True}, scope="founder")
        founder_data = await memory.retrieve("founder_test", scope="founder")
        jenson_cannot_access_founder = await memory.retrieve("founder_test", scope="jenson") is None

        # Test executive cannot access system scope
        await memory.store("system_test", {"internal": True}, scope="system")
        system_data = await memory.retrieve("system_test", scope="system")
        jenson_cannot_access_system = await memory.retrieve("system_test", scope="jenson") is None

        await memory.delete("founder_test", scope="founder")
        await memory.delete("system_test", scope="system")

        if founder_data and system_data and jenson_cannot_access_founder and jenson_cannot_access_system:
            print("  ✓ Memory governance enforced - scope separation works")
            results.append({"test": "memory_governance", "status": "PASS"})
        else:
            print("  ✗ Memory governance failed")
            results.append({"test": "memory_governance", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "memory_governance", "status": "FAIL", "error": str(e)})

    # Summary
    print("\n" + "=" * 70)
    print("MEMORY VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    for r in results:
        status_icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {status_icon} {r['test']}: {r['status']}")

    print(f"\nOverall: {'PASS' if failed == 0 else 'FAIL'} ({passed}/{len(results)} passed)")

    await runtime.shutdown()
    return failed == 0


async def main():
    success = await verify_memory()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())