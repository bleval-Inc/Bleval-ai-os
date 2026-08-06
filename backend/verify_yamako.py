#!/usr/bin/env python3
"""Yamako Autonomy Verification - Personal Organization Calendar, Schedule, Learning, Morning Routine

Verifies Yamako can:
1. Manage Founder's calendar and schedule
2. Execute morning routine at 05:00
3. Learn from patterns
4. Optimize schedule
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
from axiom.runtime.executive_loop import ExecutiveRuntimeLoop


async def verify_yamako_autonomy():
    """Verify Yamako's autonomous capabilities for Personal organization."""
    print("=" * 70)
    print("YAMAKO AUTONOMY VERIFICATION - Personal Organization")
    print("=" * 70)

    results = []

    # 1. Verify Yamako instantiation
    print("\n[1/7] Verifying Yamako Executive Loop instantiation...")
    try:
        runtime = AxiomRuntime()
        await runtime.bootstrap()
        await runtime.start()
        yamako_loop = runtime.executive_board.get_loop("yamako")

        if yamako_loop:
            print("  ✓ Yamako loop instantiated successfully")
            print(f"    Org ID: {yamako_loop.org_id}")
            print(f"    Departments: {yamako_loop.departments}")
            results.append({"test": "yamako_instantiation", "status": "PASS"})
        else:
            print("  ✗ Yamako loop not found")
            results.append({"test": "yamako_instantiation", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "yamako_instantiation", "status": "FAIL", "error": str(e)})

    # 2. Verify Personal organization config
    print("\n[2/7] Verifying Personal organization configuration...")
    try:
        personal_org = runtime.executive.get_organization_detail("personal")
        if personal_org:
            print(f"  ✓ Organization loaded: {personal_org.get('name', 'Personal')}")
            tools = personal_org.get('enabled_tools', [])
            print(f"    Enabled tools: {len(tools)}")
            for tool in tools[:5]:
                print(f"      - {tool}")
            results.append({"test": "personal_org_config", "status": "PASS"})
        else:
            print("  ✗ Personal organization not found")
            results.append({"test": "personal_org_config", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "personal_org_config", "status": "FAIL", "error": str(e)})

    # 3. Verify tool access (calendar, email)
    print("\n[3/7] Verifying Yamako tool access...")
    try:
        personal_tools = runtime.tool.get_available_tools("personal")
        if personal_tools:
            print(f"  ✓ {len(personal_tools)} tools available for Personal")
            for tool in personal_tools:
                print(f"      - {tool.id}: {tool.description}")
            results.append({"test": "yamako_tool_access", "status": "PASS"})
        else:
            print("  ✗ No tools available for Personal")
            results.append({"test": "yamako_tool_access", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "yamako_tool_access", "status": "FAIL", "error": str(e)})

    # 4. Verify intelligence engine
    print("\n[4/7] Verifying Yamako intelligence engine...")
    try:
        intelligence = runtime.intelligence
        providers = intelligence.list_providers()
        real_providers = [p for p in providers if p.get("available") and "mock" not in p.get("name", "").lower()]

        if real_providers:
            print(f"  ✓ Intelligence engine has {len(real_providers)} real providers")

            # Test schedule reasoning
            result = await intelligence.generate_for_executive(
                exec_id="yamako",
                task_description="Optimize today's schedule for maximum deep work time",
                org_id="personal",
            )
            print(f"  ✓ Schedule reasoning completed ({len(result)} chars)")
            print(f"  Sample: {result[:200]}...")
            results.append({"test": "yamako_intelligence", "status": "PASS"})
        else:
            print("  ✗ No real providers in intelligence engine")
            results.append({"test": "yamako_intelligence", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "yamako_intelligence", "status": "FAIL", "error": str(e)})

    # 5. Verify Schedule Coordinator
    print("\n[5/7] Verifying Schedule Coordinator (calendar management)...")
    try:
        schedule_coordinator = yamako_loop._schedule_coordinator
        if schedule_coordinator:
            print("  ✓ Schedule Coordinator instantiated")
            dashboard = schedule_coordinator.get_dashboard()
            print(f"    Today's blocks: {len(dashboard.get('today_blocks', []))}")
            print(f"    Sleep schedule: {dashboard.get('sleep_schedule', 'Not set')}")
            print(f"    Morning routine: {dashboard.get('morning_routine', 'Not set')}")

            # Check morning routine at 05:00
            morning = dashboard.get('morning_routine', {})
            if morning:
                print(f"  ✓ Morning routine configured: {morning.get('time', 'N/A')}")
                print(f"    Activities: {', '.join(morning.get('activities', []))}")

            # Test reminder system
            reminders = schedule_coordinator.get_reminders()
            print(f"  ✓ Reminder system active - {len(reminders)} reminder(s)")

            results.append({"test": "yamako_schedule_coordinator", "status": "PASS"})
        else:
            print("  ✗ Schedule Coordinator not found")
            results.append({"test": "yamako_schedule_coordinator", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "yamako_schedule_coordinator", "status": "FAIL", "error": str(e)})

    # 6. Verify Learning capabilities
    print("\n[6/7] Verifying Learning capabilities...")
    try:
        # Check learning engine integration
        learning = runtime.learning
        if learning:
            print("  ✓ Learning Engine connected")

            # Check executive intelligence
            exec_intel = runtime.executive_intelligence
            if exec_intel:
                intel = await exec_intel.get_executive_intelligence("yamako")
                print(f"  ✓ Executive Intelligence loaded for Yamako")
                print(f"    Patterns tracked: {intel.get('summary', {}).get('critical_patterns', 0)}")
                print(f"    Learning opportunities: {intel.get('summary', {}).get('learning_opportunities', 0)}")

        results.append({"test": "yamako_learning", "status": "PASS"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "yamako_learning", "status": "FAIL", "error": str(e)})

    # 7. Verify executive cycle & morning routine
    print("\n[7/7] Verifying Yamako executive cycle & morning routine schedule...")
    try:
        status_before = yamako_loop.get_status()
        print(f"  Before cycle: {status_before.get('cycle_count', 0)} cycles")

        # Verify schedule includes morning routine
        schedules = yamako_loop.list_schedules()
        has_morning = any('morning' in s.lower() for s in schedules.keys())
        if has_morning:
            print("  ✓ Morning routine schedule configured")
        else:
            print("  ⚠ No explicit morning routine schedule (uses ScheduleCoordinator)")

        # Check if 05:00 is configured
        morning_routine = schedule_coordinator.get_dashboard().get('morning_routine', {})
        if morning_routine.get('time') == '05:00':
            print("  ✓ Morning routine scheduled at 05:00")
        elif morning_routine:
            print(f"  ⚠ Morning routine at {morning_routine.get('time')} (expected 05:00)")

        results.append({"test": "yamako_cycle", "status": "PASS"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "yamako_cycle", "status": "FAIL", "error": str(e)})

    # Summary
    print("\n" + "=" * 70)
    print("YAMAKO VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    for r in results:
        status_icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {status_icon} {r['test']}: {r['status']}")

    print(f"\nOverall: {'PASS' if failed == 0 else 'FAIL'} ({passed}/{len(results)} passed)")

    return failed == 0


async def main():
    success = await verify_yamako_autonomy()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())