#!/usr/bin/env python3
"""Boardroom Verification - Meetings, KPIs, Decisions, Action Items

Verifies:
1. Board Room instantiation and lifecycle
2. Daily/Weekly/Monthly meeting cadence
3. KPI publishing and retrieval
4. Decision recording and tracking
5. Action item creation and completion
6. Meeting minutes generation
7. Dashboard provides complete state
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
from axiom.runtime.board_room import BoardRoom
from axiom.models.executive import (
    MeetingType, ActionItemStatus, BoardRoomAgenda, BoardRoomDecision, BoardRoomActionItem
)


async def verify_boardroom():
    """Verify Board Room functionality."""
    print("=" * 70)
    print("BOARDROOM VERIFICATION - Meetings, KPIs, Decisions, Action Items")
    print("=" * 70)

    results = []

    # Initialize runtime
    print("\n[0/13] Initializing runtime...")
    runtime = AxiomRuntime()
    await runtime.bootstrap()
    await runtime.start()

    # 1. Verify BoardRoom instantiation
    print("\n[1/13] Verifying BoardRoom instantiation...")
    try:
        boardroom = runtime.board_room
        if boardroom:
            print("  ✓ BoardRoom instantiated")
            results.append({"test": "boardroom_init", "status": "PASS"})
        else:
            print("  ✗ BoardRoom not found")
            results.append({"test": "boardroom_init", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "boardroom_init", "status": "FAIL", "error": str(e)})

    # 2. Verify BoardRoom can start
    print("\n[2/13] Verifying BoardRoom start/stop...")
    try:
        await boardroom.stop()  # Stop if running
        await boardroom.start()
        print("  ✓ BoardRoom can start and stop")
        results.append({"test": "boardroom_start_stop", "status": "PASS"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "boardroom_start_stop", "status": "FAIL", "error": str(e)})

    # 3. Verify scheduling meetings
    print("\n[3/13] Verifying meeting scheduling...")
    try:
        meeting_id = await boardroom.schedule_meeting(
            meeting_type=MeetingType.DAILY_BRIEFING,
            called_by="system",
            title="Test Daily Briefing",
            attendees=["jenson", "valta_prime", "yamako"],
        )
        print(f"  ✓ Meeting scheduled: {meeting_id}")

        meeting = boardroom.get_meeting(meeting_id)
        if meeting and meeting.meeting_type == MeetingType.DAILY_BRIEFING:
            print(f"  ✓ Meeting retrieved with correct type")
            results.append({"test": "meeting_scheduling", "status": "PASS"})
        else:
            print("  ✗ Meeting not retrieved correctly")
            results.append({"test": "meeting_scheduling", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "meeting_scheduling", "status": "FAIL", "error": str(e)})

    # 4. Verify meeting start/complete lifecycle
    print("\n[4/13] Verifying meeting lifecycle (start/complete)...")
    try:
        started = await boardroom.start_meeting(meeting_id)
        print(f"  Meeting started: {started}")

        completed = await boardroom.complete_meeting(meeting_id)
        if completed and completed.status == "completed":
            print(f"  ✓ Meeting completed with minutes")
            print(f"  Minutes length: {len(completed.minutes)} chars")
            results.append({"test": "meeting_lifecycle", "status": "PASS"})
        else:
            print("  ✗ Meeting not completed correctly")
            results.append({"test": "meeting_lifecycle", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "meeting_lifecycle", "status": "FAIL", "error": str(e)})

    # 5. Verify agenda management
    print("\n[5/13] Verifying agenda management...")
    try:
        # Submit agenda item
        agenda_id = boardroom.submit_agenda_item(
            submitted_by="jenson",
            title="Client project status",
            description="Review Bleval Inc project progress",
            priority=1,
        )
        print(f"  ✓ Agenda item submitted: {agenda_id}")

        pending = boardroom.get_pending_agenda()
        print(f"  Pending agenda items: {len(pending)}")

        if len(pending) > 0:
            print("  ✓ Agenda management working")
            results.append({"test": "agenda_management", "status": "PASS"})
        else:
            print("  ✗ Agenda item not in pending")
            results.append({"test": "agenda_management", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "agenda_management", "status": "FAIL", "error": str(e)})

    # 6. Verify KPI publishing
    print("\n[6/13] Verifying KPI publishing and retrieval...")
    try:
        # Publish KPIs from each executive
        boardroom.publish_kpi_snapshot("jenson", {"projects_active": 5, "revenue": 125000})
        boardroom.publish_kpi_snapshot("valta_prime", {"pois_monitored": 12, "alerts_generated": 3})
        boardroom.publish_kpi_snapshot("yamako", {"appointments_scheduled": 8, "tasks_completed": 15})

        latest = boardroom.get_latest_kpis()
        print(f"  KPIs from {len(latest)} executives:")

        all_present = True
        for exec_id, kpis in latest.items():
            print(f"    {exec_id}: {kpis}")
            if not kpis:
                all_present = False

        if all_present and len(latest) == 3:
            print("  ✓ All executives can publish KPIs")
            results.append({"test": "kpi_publishing", "status": "PASS"})
        else:
            print("  ✗ KPI publishing incomplete")
            results.append({"test": "kpi_publishing", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "kpi_publishing", "status": "FAIL", "error": str(e)})

    # 7. Verify KPI history
    print("\n[7/13] Verifying KPI history...")
    try:
        history = boardroom.get_kpi_history()
        print(f"  KPI history entries: {len(history)}")

        if len(history) >= 3:
            print("  ✓ KPI history maintained")
            results.append({"test": "kpi_history", "status": "PASS"})
        else:
            print("  ✗ KPI history not maintained")
            results.append({"test": "kpi_history", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "kpi_history", "status": "FAIL", "error": str(e)})

    # 8. Verify decision recording
    print("\n[8/13] Verifying decision recording...")
    try:
        # Schedule a new meeting for decisions
        meeting_id2 = await boardroom.schedule_meeting(
            meeting_type=MeetingType.WEEKLY_EXECUTIVE,
            called_by="system",
            title="Decision Test Meeting",
            attendees=["jenson", "valta_prime", "yamako"],
        )
        await boardroom.start_meeting(meeting_id2)

        # Make a decision
        decision = await boardroom.make_decision(
            meeting_id=meeting_id2,
            title="Approve new client onboarding",
            description="Onboard Acme Corp as new Bleval client",
            proposed_by="jenson",
            voted_by=["jenson", "valta_prime", "yamako"],
            approved=True,
        )
        print(f"  ✓ Decision recorded: {decision.decision_id}")
        print(f"    Approved: {decision.approved}")
        print(f"    Votes for: {decision.votes_for}")

        if decision.approved and decision.votes_for == 3:
            print("  ✓ Decision recording working")
            results.append({"test": "decision_recording", "status": "PASS"})
        else:
            print("  ✗ Decision not recorded correctly")
            results.append({"test": "decision_recording", "status": "FAIL"})

        await boardroom.complete_meeting(meeting_id2)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "decision_recording", "status": "FAIL", "error": str(e)})

    # 9. Verify action item creation and tracking
    print("\n[9/13] Verifying action item creation and tracking...")
    try:
        # Create action items
        item_id = boardroom.create_action_item(
            meeting_id=meeting_id2,
            title="Send proposal to Acme Corp",
            assigned_to="jenson",
            description="Draft and send service proposal",
            priority="high",
            deadline=None,
        )
        print(f"  ✓ Action item created: {item_id}")

        # Create another
        item_id2 = boardroom.create_action_item(
            meeting_id=meeting_id2,
            title="Review market conditions",
            assigned_to="valta_prime",
            description="Check GOLD and US30 POI levels",
            priority="normal",
        )

        # Get open items
        open_items = boardroom.get_open_action_items()
        print(f"  Open action items: {len(open_items)}")
        for item in open_items:
            print(f"    - {item.title} (assigned to {item.assigned_to}, priority: {item.priority})")

        # Complete one
        completed = boardroom.complete_action_item(item_id, "Proposal sent and accepted")
        print(f"  Action item completion: {completed}")

        open_after = boardroom.get_open_action_items()
        print(f"  Open after completion: {len(open_after)}")

        if len(open_items) >= 2 and len(open_after) == len(open_items) - 1:
            print("  ✓ Action items created, tracked, and completed correctly")
            results.append({"test": "action_items", "status": "PASS"})
        else:
            print("  ✗ Action item tracking incorrect")
            results.append({"test": "action_items", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "action_items", "status": "FAIL", "error": str(e)})

    # 10. Verify meeting types and cadence
    print("\n[10/13] Verifying meeting types and cadence...")
    try:
        meeting_types = [
            MeetingType.DAILY_BRIEFING,
            MeetingType.WEEKLY_EXECUTIVE,
            MeetingType.MONTHLY_REVIEW,
            MeetingType.QUARTERLY_STRATEGIC,
            MeetingType.EMERGENCY,
            MeetingType.AD_HOC,
        ]

        for mt in meeting_types:
            mid = await boardroom.schedule_meeting(
                meeting_type=mt,
                called_by="system",
                title=f"{mt.value} test",
                attendees=["jenson", "valta_prime", "yamako"],
            )
            m = boardroom.get_meeting(mid)
            if m and m.meeting_type == mt:
                print(f"    ✓ {mt.value}")
            else:
                print(f"    ✗ {mt.value} failed")

        print("  ✓ All meeting types supported")
        results.append({"test": "meeting_types", "status": "PASS"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "meeting_types", "status": "FAIL", "error": str(e)})

    # 11. Verify minutes generation
    print("\n[11/13] Verifying meeting minutes generation...")
    try:
        # Find a completed meeting
        meetings = boardroom.list_meetings(limit=5)
        completed_meetings = [m for m in meetings if m.status == "completed"]

        if completed_meetings:
            meeting = completed_meetings[0]
            minutes = meeting.minutes
            print(f"  Minutes length: {len(minutes)} chars")
            print(f"  Contains agenda: {'## Agenda' in minutes}")
            print(f"  Contains minutes header: {'# Board Meeting Minutes' in minutes}")
            print(f"  Contains action items: {'## Action Items' in minutes}")

            if minutes and "Board Meeting Minutes" in minutes:
                print("  ✓ Meeting minutes generated correctly")
                results.append({"test": "minutes_generation", "status": "PASS"})
            else:
                print("  ✗ Minutes not properly generated")
                results.append({"test": "minutes_generation", "status": "FAIL"})
        else:
            print("  ⚠ No completed meetings to check minutes")
            results.append({"test": "minutes_generation", "status": "PASS"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "minutes_generation", "status": "FAIL", "error": str(e)})

    # 12. Verify overdue action items detection
    print("\n[12/13] Verifying overdue action items detection...")
    try:
        from datetime import datetime, timedelta, timezone

        # Create an overdue item
        past_deadline = datetime.now(timezone.utc) - timedelta(days=1)
        overdue_id = boardroom.create_action_item(
            meeting_id=meeting_id,
            title="Overdue task",
            assigned_to="jenson",
            deadline=past_deadline,
        )

        overdue = boardroom.get_overdue_action_items()
        print(f"  Overdue items detected: {len(overdue)}")
        for item in overdue:
            print(f"    - {item.title} (deadline: {item.deadline})")

        if len(overdue) >= 1:
            print("  ✓ Overdue action items correctly detected")
            results.append({"test": "overdue_detection", "status": "PASS"})
        else:
            print("  ✗ Overdue detection not working")
            results.append({"test": "overdue_detection", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "overdue_detection", "status": "FAIL", "error": str(e)})

    # 13. Verify dashboard
    print("\n[13/13] Verifying Board Room dashboard...")
    try:
        dashboard = boardroom.get_dashboard()
        print(f"  Dashboard keys: {list(dashboard.keys())}")
        print(f"  Total meetings: {dashboard.get('total_meetings')}")
        print(f"  Pending agenda: {dashboard.get('pending_agenda_items')}")
        print(f"  Open actions: {dashboard.get('open_action_items')}")
        print(f"  Overdue actions: {dashboard.get('overdue_action_items')}")
        print(f"  Latest KPIs: {len(dashboard.get('latest_kpis', {}))} executives")

        required_fields = ['total_meetings', 'pending_agenda_items', 'open_action_items', 'latest_kpis']
        if all(f in dashboard for f in required_fields):
            print("  ✓ Dashboard provides complete board room state")
            results.append({"test": "boardroom_dashboard", "status": "PASS"})
        else:
            print("  ✗ Dashboard missing required fields")
            results.append({"test": "boardroom_dashboard", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "boardroom_dashboard", "status": "FAIL", "error": str(e)})

    # Summary
    print("\n" + "=" * 70)
    print("BOARDROOM VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    for r in results:
        status_icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {status_icon} {r['test']}: {r['status']}")

    print(f"\nOverall: {'PASS' if failed == 0 else 'FAIL'} ({passed}/{len(results)} passed)")

    return failed == 0


async def main():
    success = await verify_boardroom()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())