from __future__ import annotations

import sqlite3

from .db import reset_demo_tables, save_recap
from .models import DemoContact, DemoRecap


def synthetic_recaps() -> list[DemoRecap]:
    def contact(name: str, email: str, role: str) -> DemoContact:
        return DemoContact(name=name, email=email, role=role)

    return [
        DemoRecap(
            organization_name="Northstar Academy",
            lead_name="Diana Grant",
            demo_lead="Ava Chen",
            call_datetime="2026-04-14 10:30",
            with_text=(
                "Marta Vale | marta.vale@northstar.example | IT Operations Lead\n"
                "Diana Grant | diana.grant@northstar.example | Project sponsor"
            ),
            contacts=(
                contact("Marta Vale", "marta.vale@northstar.example", "IT Operations Lead"),
                contact("Diana Grant", "diana.grant@northstar.example", "Project sponsor"),
            ),
            location="Austin, TX",
            user_count="335 users showing in console; about 290 active staff and students",
            first_heard_of_gat=(
                "Diana Grant found GAT through Google Search after a peer recommended a lighter "
                "workflow option than a full GAM implementation."
            ),
            competition="AdminPulse for reporting; no active workflow automation tool",
            devices="Google Workspace, Chromebooks, shared Windows lab devices",
            budget="Budget owner expects approval if trial proves offboarding savings.",
            authority="Diana Grant sponsors evaluation; Marta Vale owns technical validation.",
            timeline="Trial ends in late April; likely decision in May if workflow proof succeeds.",
            organization_details=(
                "Northstar Academy is a fake K-12 school network with multiple campuses around Austin, TX."
            ),
            needs=(
                "Northstar Academy has too many manual steps to onboard and offboard employees. "
                "The Austin, TX operations team needs delegated workflows for password resets, "
                "auto-replies, email forwarding, and group cleanup without giving broad admin rights."
            ),
            demo_discussion=(
                "Marta Vale liked the Flow interface but wanted to see actions run end-to-end. "
                "Diana Grant asked whether the workflow history is clear enough for audit review."
            ),
            questions_answers=(
                "Q1: Marta Vale asked whether workflow actions overwrite existing Google policies.\n"
                "A1: Demonstrated that actions are scoped and auditable.\n\n"
                "Q2: Can alerts send to marta.vale@northstar.example when offboarding fails?\n"
                "A2: Yes, notification routing can be configured."
            ),
            requests_during_demo=(
                "Review https://northstar.example/workflows before the trial closes.\n\n"
                "Add an offboarding template that sets autoforwarding and an automatic reply.\n\n"
                "Generate and email 2FA backup codes to the end user during onboarding if possible."
            ),
            follow_up=(
                "Send Diana Grant workflow documentation and quote language. Extend trial for "
                "Northstar Academy while the Austin, TX team validates offboarding."
            ),
        ),
        DemoRecap(
            organization_name="Riverton Health Group",
            lead_name="Leo Hart",
            demo_lead="Miles Carter",
            call_datetime="2026-04-11 15:00",
            with_text=(
                "Noor Abbas | noor.abbas@riverton.example | Compliance Manager\n"
                "Leo Hart | leo.hart@riverton.example | IT Director"
            ),
            contacts=(
                contact("Noor Abbas", "noor.abbas@riverton.example", "Compliance Manager"),
                contact("Leo Hart", "leo.hart@riverton.example", "IT Director"),
            ),
            location="Dublin, Ireland",
            user_count="1,180 users; 220 shared clinical accounts need cleanup",
            first_heard_of_gat="Referral from an MSP after Leo Hart asked about Google audit reporting.",
            competition="Evaluating BetterCloud and internal scripts",
            devices="Google Workspace, Windows laptops, managed Android tablets",
            budget="Budget is available this quarter if compliance reporting is covered.",
            authority="Leo Hart can recommend; finance committee signs contract.",
            timeline="Decision target is early June before annual access review.",
            organization_details=(
                "Riverton Health Group is a fake healthcare provider with clinics in Dublin, Ireland."
            ),
            needs=(
                "Riverton Health Group needs repeatable access reviews and better evidence for audits. "
                "Noor Abbas wants exception reports for dormant users, risky forwarding rules, and "
                "shared account ownership."
            ),
            demo_discussion=(
                "Showed reporting dashboards, workflow approvals, and exporting evidence. Leo Hart "
                "wanted the Dublin, Ireland compliance team to see whether reports are understandable."
            ),
            questions_answers=(
                "Q1: Can compliance exports be scheduled monthly?\n"
                "A1: Yes, via scheduled reports.\n\n"
                "Q2: Noor Abbas asked whether evidence can be sent to noor.abbas@riverton.example.\n"
                "A2: Yes, scheduled report delivery supports email recipients."
            ),
            requests_during_demo=(
                "Provide examples from https://riverton.example/audit-program.\n"
                "Add a saved view for accounts with forwarding outside the domain.\n"
                "Template for quarterly access-review attestation."
            ),
            follow_up=(
                "Send Leo Hart compliance report examples, export documentation, and trial checklist. "
                "Schedule follow-up with Noor Abbas for the Dublin, Ireland audit workflow."
            ),
        ),
        DemoRecap(
            organization_name="Blue Finch Robotics",
            lead_name="Priya Nayar",
            demo_lead="June Park",
            call_datetime="2026-04-08 09:15",
            with_text=(
                "Priya Nayar | priya.nayar@bluefinch.example | Head of IT\n"
                "Gabe Ortiz | gabe.ortiz@bluefinch.example | Automation Engineer"
            ),
            contacts=(
                contact("Priya Nayar", "priya.nayar@bluefinch.example", "Head of IT"),
                contact("Gabe Ortiz", "gabe.ortiz@bluefinch.example", "Automation Engineer"),
            ),
            location="Toronto, ON",
            user_count="640 users including contractors; rapid hiring spikes every quarter",
            first_heard_of_gat="Webinar registration from Priya Nayar after searching for Workspace automation.",
            competition="Existing Zapier automations and manual Admin console work",
            devices="MacBooks, Linux engineering workstations, Google Workspace",
            budget="Could use automation budget if contractor onboarding time drops.",
            authority="Priya Nayar owns tool selection; CTO reviews security notes.",
            timeline="Wants pilot running within 30 days for the next contractor cohort.",
            organization_details="Blue Finch Robotics is a fake robotics company based in Toronto, ON.",
            needs=(
                "Blue Finch Robotics needs faster contractor onboarding and deprovisioning. Gabe Ortiz "
                "asked for a way to create groups, apply labels, and trigger device instructions from "
                "one checklist."
            ),
            demo_discussion=(
                "Walked through Flow actions, approval steps, and admin activity review. Priya Nayar "
                "liked that templates could be copied for engineering and operations teams."
            ),
            questions_answers=(
                "Q1: Can workflows branch based on contractor type?\n"
                "A1: Demonstrated conditional steps.\n\n"
                "Q2: Gabe Ortiz asked whether a webhook can call https://bluefinch.example/device-api.\n"
                "A2: Discussed using existing integration hooks and safer approval gates."
            ),
            requests_during_demo=(
                "Bulk clone onboarding workflows for contractor cohorts.\n"
                "Add a preview mode showing every group and label change before execution.\n"
                "Send setup notes to priya.nayar@bluefinch.example."
            ),
            follow_up=(
                "Share workflow branching documentation with Priya Nayar. Confirm Toronto, ON pilot "
                "timeline and get security notes for Gabe Ortiz."
            ),
        ),
        DemoRecap(
            organization_name="Pine Harbor District",
            lead_name="Marco Flynn",
            demo_lead="Ava Chen",
            call_datetime="2026-03-29 13:45",
            with_text=(
                "Marco Flynn | marco.flynn@pineharbor.example | Technology Coordinator\n"
                "Iris Chen | iris.chen@pineharbor.example | Help Desk Lead"
            ),
            contacts=(
                contact("Marco Flynn", "marco.flynn@pineharbor.example", "Technology Coordinator"),
                contact("Iris Chen", "iris.chen@pineharbor.example", "Help Desk Lead"),
            ),
            location="Denver, CO",
            user_count="4,800 student accounts and 520 staff accounts",
            first_heard_of_gat="Marco Flynn heard about GAT from a regional education technology forum.",
            competition="GAM scripts maintained by one administrator",
            devices="Chromebooks, Google Workspace for Education, shared lab PCs",
            budget="Needs a formal quote for the district procurement packet.",
            authority="Marco Flynn recommends; district cabinet approves purchase.",
            timeline="Procurement window opens in July; wants data before end of school year.",
            organization_details="Pine Harbor District is a fake school district serving the Denver, CO area.",
            needs=(
                "Pine Harbor District needs safer delegated admin tasks because only one person can run "
                "current scripts. Iris Chen wants help desk staff to reset passwords and suspend accounts "
                "without full super-admin access."
            ),
            demo_discussion=(
                "Reviewed role scoping, Flow approval steps, and student safety searches. Marco Flynn "
                "asked how much training help desk staff would need."
            ),
            questions_answers=(
                "Q1: Can help desk staff have limited workflow permissions?\n"
                "A1: Yes, demonstrated role-based delegation.\n\n"
                "Q2: Iris Chen asked if reports could identify risky forwarding after graduation.\n"
                "A2: Yes, using reporting and workflow cleanup."
            ),
            requests_during_demo=(
                "Formal quote for https://pineharbor.example/procurement packet.\n"
                "Checklist for graduating student account cleanup.\n"
                "Short training plan for delegated help desk workflows."
            ),
            follow_up=(
                "Send Marco Flynn quote, education references, and delegated admin guide. Book a "
                "second demo for Iris Chen and the Denver, CO cabinet team."
            ),
        ),
        DemoRecap(
            organization_name="Summit Lane Finance",
            lead_name="Elena Brooks",
            demo_lead="Miles Carter",
            call_datetime="2026-03-21 11:00",
            with_text=(
                "Elena Brooks | elena.brooks@summitlane.example | Operations VP\n"
                "Tariq Stone | tariq.stone@summitlane.example | Security Analyst"
            ),
            contacts=(
                contact("Elena Brooks", "elena.brooks@summitlane.example", "Operations VP"),
                contact("Tariq Stone", "tariq.stone@summitlane.example", "Security Analyst"),
            ),
            location="Bristol, UK",
            user_count="910 users; 75 privileged users need monthly review",
            first_heard_of_gat="Elena Brooks saw a partner newsletter about Workspace governance.",
            competition="Considering a SIEM add-on and spreadsheet-based controls",
            devices="Google Workspace, Windows laptops, Okta-managed access",
            budget="Security budget available after risk committee review.",
            authority="Elena Brooks owns operations case; CISO signs off.",
            timeline="Risk committee meeting in six weeks; proof points needed before then.",
            organization_details="Summit Lane Finance is a fake financial-services firm in Bristol, UK.",
            needs=(
                "Summit Lane Finance wants audit-ready reporting for privileged users and external "
                "sharing. Tariq Stone needs a repeatable process for reviewing forwarding, delegates, "
                "and Drive exposure."
            ),
            demo_discussion=(
                "Discussed scheduled reports, security investigation workflows, and export evidence. "
                "Elena Brooks asked how to brief non-technical risk committee members."
            ),
            questions_answers=(
                "Q1: Can reports group findings by risk category?\n"
                "A1: Demonstrated filtered report views.\n\n"
                "Q2: Can Tariq Stone export evidence to tariq.stone@summitlane.example?\n"
                "A2: Yes, export and delivery options are supported."
            ),
            requests_during_demo=(
                "Executive summary example for https://summitlane.example/risk-committee.\n"
                "Saved dashboard for privileged-user review.\n"
                "One-page explanation of external sharing risk categories."
            ),
            follow_up=(
                "Send Elena Brooks security summary template and pricing range. Confirm Bristol, UK "
                "risk committee date and include Tariq Stone in technical follow-up."
            ),
        ),
        DemoRecap(
            organization_name="MeadowByte Studios",
            lead_name="Samir Cole",
            demo_lead="June Park",
            call_datetime="2026-03-12 16:30",
            with_text=(
                "Samir Cole | samir.cole@meadowbyte.example | Studio IT Manager\n"
                "Lena Ortiz | lena.ortiz@meadowbyte.example | People Ops Lead"
            ),
            contacts=(
                contact("Samir Cole", "samir.cole@meadowbyte.example", "Studio IT Manager"),
                contact("Lena Ortiz", "lena.ortiz@meadowbyte.example", "People Ops Lead"),
            ),
            location="Warsaw, Poland",
            user_count="420 users with frequent freelancer churn",
            first_heard_of_gat="Samir Cole found a GAT article while looking for offboarding workflows.",
            competition="Manual checklists in Asana and a few Apps Script jobs",
            devices="MacBooks, Google Workspace, shared production tablets",
            budget="People Ops and IT can split cost if offboarding risk is reduced.",
            authority="Samir Cole owns technical decision; Lena Ortiz influences process fit.",
            timeline="Needs a decision before summer production hiring starts.",
            organization_details="MeadowByte Studios is a fake creative studio with an office in Warsaw, Poland.",
            needs=(
                "MeadowByte Studios needs cleaner freelancer onboarding and fast revocation when a "
                "project ends. Lena Ortiz wants People Ops to trigger a workflow without waiting for IT."
            ),
            demo_discussion=(
                "Demonstrated intake forms, approval gates, and group cleanup. Samir Cole asked about "
                "visibility into every step before it runs."
            ),
            questions_answers=(
                "Q1: Can People Ops start a workflow but require IT approval?\n"
                "A1: Yes, showed approval gates.\n\n"
                "Q2: Lena Ortiz asked whether freelancer reminders can be sent before access expires.\n"
                "A2: Discussed scheduled reminders and follow-up tasks."
            ),
            requests_during_demo=(
                "Freelancer offboarding template with approval gate.\n"
                "A report for access expiring in the next 14 days.\n"
                "Send notes to samir.cole@meadowbyte.example and review https://meadowbyte.example/ops."
            ),
            follow_up=(
                "Send Samir Cole offboarding template and approval-gate documentation. Schedule "
                "Warsaw, Poland process session with Lena Ortiz."
            ),
        ),
    ]


def seed_demo_data(conn: sqlite3.Connection, reset: bool = True) -> list[DemoRecap]:
    if reset:
        reset_demo_tables(conn)
    saved: list[DemoRecap] = []
    for recap in synthetic_recaps():
        saved.append(save_recap(conn, recap))
    return saved
