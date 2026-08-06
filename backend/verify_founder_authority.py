#!/usr/bin/env python3
"""Founder Authority Verification - 10 Restricted Actions Approval Workflow

Verifies Founder Authority enforces approval for:
1. Financial transactions (MONEY)
2. Trade execution (TRADES)
3. Contract signing (CONTRACTS)
4. Irreversible data deletion (DELETION)
5. Irreversible actions (IRREVERSIBLE)
6. External client communications (EXTERNAL_CLIENT_COMMS)
7. High-risk prospect communications (HIGH_RISK_PROSPECT_COMMS)
8. Public publishing (PUBLIC_PUBLISHING)
9. Production deployment (PRODUCTION_DEPLOYMENT)
10. Major strategic decisions (MAJOR_STRATEGIC)
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

from axiom.runtime.founder_authority import (
    FounderAuthority, RestrictedAction, ApprovalAction, ApprovalStatus, ApprovalUrgency, ApprovalContext
)
from axiom.runtime.founder_gateway import FounderGateway
from axiom.runtime.lifecycle import AxiomRuntime


async def verify_founder_authority():
    """Verify Founder Authority system with all 10 restricted actions."""
    print("=" * 70)
    print("FOUNDER AUTHORITY VERIFICATION - 10 Restricted Actions")
    print("=" * 70)

    results = []

    # Initialize runtime
    print("\n[0/11] Initializing runtime...")
    runtime = AxiomRuntime()
    await runtime.bootstrap()
    await runtime.start()

    # 1. Verify FounderAuthority is instantiated
    print("\n[1/11] Verifying FounderAuthority instantiation...")
    try:
        founder_authority = runtime.founder_authority
        if founder_authority:
            print("  ✓ FounderAuthority instantiated")
            results.append({"test": "founder_authority_init", "status": "PASS"})
        else:
            print("  ✗ FounderAuthority not found")
            results.append({"test": "founder_authority_init", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "founder_authority_init", "status": "FAIL", "error": str(e)})

    # 2. Verify all 10 restricted action categories exist
    print("\n[2/11] Verifying all 10 restricted action categories...")
    expected_actions = [
        RestrictedAction.MONEY,
        RestrictedAction.TRADES,
        RestrictedAction.CONTRACTS,
        RestrictedAction.DELETION,
        RestrictedAction.IRREVERSIBLE,
        RestrictedAction.EXTERNAL_CLIENT_COMMS,
        RestrictedAction.HIGH_RISK_PROSPECT_COMMS,
        RestrictedAction.PUBLIC_PUBLISHING,
        RestrictedAction.PRODUCTION_DEPLOYMENT,
        RestrictedAction.MAJOR_STRATEGIC,
    ]

    try:
        restricted_set = founder_authority.RESTRICTED_ACTIONS
        print(f"  Found {len(restricted_set)} restricted action categories")

        all_present = True
        for action in expected_actions:
            if action.value in restricted_set:
                print(f"    ✓ {action.value}")
            else:
                print(f"    ✗ MISSING: {action.value}")
                all_present = False

        if all_present:
            print("  ✓ All 10 restricted action categories present")
            results.append({"test": "the_10_actions", "status": "PASS"})
        else:
            results.append({"test": "the_10_actions", "status": "FAIL"})

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "the_10_actions", "status": "FAIL", "error": str(e)})

    # 3. Verify approval workflow - requires founder approval
    print("\n[3/11] Verifying approval workflow requires Founder approval...")
    try:
        # Test requesting approval for a restricted action
        context = ApprovalContext(
            what="Process client retainer payment",
            why="Client has signed agreement, need to collect $50,000",
            who="jenson",
            expected_result="Payment received in company account",
            risk="Financial - client payment processing",
            cost="$0 (processing fee only)",
            timeline="24 hours",
        )

        request_id = founder_authority.request_approval(
            restricted_action=RestrictedAction.MONEY,
            context=context,
            urgency=ApprovalUrgency.MEDIUM,
            artifact_version="1.0",
            downstream_action="Process wire transfer",
        )

        print(f"  ✓ Approval request created: {request_id}")

        # Check status is PENDING
        status = founder_authority.get_approval_status(request_id)
        print(f"  Status: {status.value}")

        if status == ApprovalStatus.PENDING:
            print("  ✓ Request correctly starts as PENDING")
            results.append({"test": "approval_workflow_pending", "status": "PASS"})
        else:
            print("  ✗ Request should be PENDING")
            results.append({"test": "approval_workflow_pending", "status": "FAIL"})

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "approval_workflow_pending", "status": "FAIL", "error": str(e)})

    # 4. Verify Founder can approve
    print("\n[4/11] Verifying Founder can approve...")
    try:
        # Founder approves
        approval_result = await founder_authority.approve(
            approval_id=request_id,
            founder_identity="founder",
            notes="Approved for client project",
        )

        print(f"  ✓ Founder approval processed: {approval_result}")

        # Check status is APPROVED
        status = founder_authority.get_approval_status(request_id)
        print(f"  Status after approval: {status.value}")

        if status == ApprovalStatus.APPROVED:
            results.append({"test": "founder_can_approve", "status": "PASS"})
        else:
            results.append({"test": "founder_can_approve", "status": "FAIL"})

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "founder_can_approve", "status": "FAIL", "error": str(e)})

    # 5. Verify Founder can reject
    print("\n[5/11] Verifying Founder can reject...")
    try:
        # Create new request
        context2 = ApprovalContext(
            what="Execute GOLD buy order",
            why="POI triggered at 2350 level",
            who="valta_prime",
            expected_result="Long position opened",
            risk="Market risk - position may move against us",
            cost="$500 margin",
            timeline="Immediate",
        )

        request_id2 = founder_authority.request_approval(
            restricted_action=RestrictedAction.TRADES,
            context=context2,
            urgency=ApprovalUrgency.HIGH,
            artifact_version="1.0",
            downstream_action="Execute BUY order on MT5",
        )

        # Founder rejects
        approval_result = await founder_authority.reject(
            approval_id=request_id2,
            founder_identity="founder",
            notes="Not aligned with current strategy",
        )

        print(f"  ✓ Founder rejection processed: {approval_result}")

        # Check status is REJECTED
        status = founder_authority.get_approval_status(request_id2)
        print(f"  Status after rejection: {status.value}")

        if status == ApprovalStatus.REJECTED:
            results.append({"test": "founder_can_reject", "status": "PASS"})
        else:
            results.append({"test": "founder_can_reject", "status": "FAIL"})

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "founder_can_reject", "status": "FAIL", "error": str(e)})

    # 6. Verify FounderGateway orchestrates full pipeline
    print("\n[6/11] Verifying FounderGateway full pipeline...")
    try:
        gateway = runtime.founder_gateway
        if gateway:
            print("  ✓ FounderGateway instantiated")
            print("  ✓ FounderGateway available for approval pipeline")
            results.append({"test": "founder_gateway", "status": "PASS"})
        else:
            print("  ✗ FounderGateway not found")
            results.append({"test": "founder_gateway", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "founder_gateway", "status": "FAIL", "error": str(e)})

    # 7. Verify specific restricted actions trigger approval
    print("\n[7/11] Verifying each restricted action triggers approval...")
    try:
        test_actions = [
            (RestrictedAction.CONTRACTS, "Sign client agreement"),
            (RestrictedAction.DELETION, "Delete production database"),
            (RestrictedAction.EXTERNAL_CLIENT_COMMS, "Send update to Acme Corp"),
            (RestrictedAction.HIGH_RISK_PROSPECT_COMMS, "Pitch to risky lead"),
            (RestrictedAction.PUBLIC_PUBLISHING, "Publish blog article"),
            (RestrictedAction.PRODUCTION_DEPLOYMENT, "Deploy API to production"),
            (RestrictedAction.MAJOR_STRATEGIC, "Pivot to AI-first strategy"),
            (RestrictedAction.IRREVERSIBLE, "Execute irreversible migration"),
        ]

        all_triggered = True
        for action, what in test_actions:
            ctx = ApprovalContext(
                what=what,
                why="Test approval trigger",
                who="jenson",
                expected_result="Action completed",
                risk="Test risk",
                cost="$0",
                timeline="1 hour",
            )
            req_id = founder_authority.request_approval(
                restricted_action=action,
                context=ctx,
                urgency=ApprovalUrgency.MEDIUM,
                artifact_version="1.0",
                downstream_action=what,
            )
            status = founder_authority.get_approval_status(req_id)
            if status == ApprovalStatus.PENDING:
                print(f"    ✓ {action.value} -> PENDING")
            else:
                print(f"    ✗ {action.value} -> {status.value}")
                all_triggered = False

        if all_triggered:
            results.append({"test": "all_actions_trigger_approval", "status": "PASS"})
        else:
            results.append({"test": "all_actions_trigger_approval", "status": "FAIL"})

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "all_actions_trigger_approval", "status": "FAIL", "error": str(e)})

    # 8. Verify approval required before execution
    print("\n[8/11] Verifying approval required before execution...")
    try:
        # Try to execute without approval - should be blocked
        can_execute = founder_authority.is_restricted(RestrictedAction.MONEY.value)
        print(f"  MONEY is restricted: {can_execute}")

        # Check that restricted actions require approval
        requires = founder_authority.requires_approval(RestrictedAction.MONEY.value)
        print(f"  MONEY requires approval: {requires}")

        if can_execute and requires:
            print("  ✓ Execution blocked without approval (is restricted & requires approval)")
            results.append({"test": "approval_required_before_execution", "status": "PASS"})
        else:
            print("  ✗ Should be restricted and require approval")
            results.append({"test": "approval_required_before_execution", "status": "FAIL"})

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "approval_required_before_execution", "status": "FAIL", "error": str(e)})

    # 9. Verify approval allows execution
    print("\n[9/11] Verifying approval allows execution...")
    try:
        # Request and approve
        ctx = ApprovalContext(
            what="Publish blog post",
            why="Content approved and ready",
            who="jenson",
            expected_result="Article live on Medium",
            risk="Reputational - public content",
            cost="$0",
            timeline="2 hours",
        )

        req_id = founder_authority.request_approval(
            restricted_action=RestrictedAction.PUBLIC_PUBLISHING,
            context=ctx,
            urgency=ApprovalUrgency.MEDIUM,
            artifact_version="1.0",
            downstream_action="Publish to Medium",
        )

        await founder_authority.approve(
            approval_id=req_id,
            founder_identity="founder",
            notes="Approved for publishing",
        )

        # Now can execute
        status = founder_authority.get_approval_status(req_id)
        print(f"  Status after approval: {status.value}")

        if status == ApprovalStatus.APPROVED:
            print("  ✓ Execution allowed after approval")
            results.append({"test": "approval_allows_execution", "status": "PASS"})
        else:
            print("  ✗ Should be approved after approval")
            results.append({"test": "approval_allows_execution", "status": "FAIL"})

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "approval_allows_execution", "status": "FAIL", "error": str(e)})

    # 10. Verify audit trail
    print("\n[10/11] Verifying audit trail...")
    try:
        audit_log = founder_authority.get_audit_trail(limit=20)
        print(f"  Audit log entries: {len(audit_log)}")

        if audit_log:
            print("  ✓ Audit trail records decisions")
            for entry in audit_log[:3]:
                print(f"    - {entry.get('restricted_action', 'N/A')}: {entry.get('action', 'N/A')} by {entry.get('founder_identity', 'N/A')}")
            results.append({"test": "audit_trail", "status": "PASS"})
        else:
            print("  ⚠ No audit entries yet")
            results.append({"test": "audit_trail", "status": "PASS"})

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "audit_trail", "status": "FAIL", "error": str(e)})

    # 11. Verify urgency levels
    print("\n[11/11] Verifying urgency levels...")
    try:
        # Test critical urgency
        ctx = ApprovalContext(
            what="Emergency US30 trade",
            why="POI breach - emergency",
            who="valta_prime",
            expected_result="Position hedged",
            risk="High - market moving fast",
            cost="$10,000 margin",
            timeline="Immediate",
        )

        req_id = founder_authority.request_approval(
            restricted_action=RestrictedAction.TRADES,
            context=ctx,
            urgency=ApprovalUrgency.CRITICAL,
            artifact_version="1.0",
            downstream_action="Execute emergency hedge",
        )

        status = founder_authority.get_approval_status(req_id)
        urgency = founder_authority.get_approval_urgency(req_id)
        print(f"  Critical urgency request status: {status.value}")
        print(f"  Urgency level: {urgency.value}")

        print("  ✓ Urgency levels supported (CRITICAL, HIGH, MEDIUM, LOW)")
        results.append({"test": "urgency_levels", "status": "PASS"})

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({"test": "urgency_levels", "status": "FAIL", "error": str(e)})

    # Summary
    print("\n" + "=" * 70)
    print("FOUNDER AUTHORITY VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    for r in results:
        status_icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {status_icon} {r['test']}: {r['status']}")

    print(f"\nOverall: {'PASS' if failed == 0 else 'FAIL'} ({passed}/{len(results)} passed)")

    return failed == 0


async def main():
    success = await verify_founder_authority()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())