"""Builds the student-friendly PDF report with ReportLab."""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.config import REPORT_TITLE

_SEVERITY_COLOR = {
    "High": colors.HexColor("#c0392b"),
    "Medium": colors.HexColor("#d68910"),
    "Low": colors.HexColor("#7d8c1e"),
}


def generate_report(
    session,
    findings: list,
    quiz_attempts: list,
    not_applicable: list | None = None,
    scan: dict | None = None,
    capstone_status: str | None = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=9, leading=12)

    story = []
    story.append(Paragraph(REPORT_TITLE, styles["Title"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            f"Session: <b>{session.name}</b> &nbsp;|&nbsp; Target: <b>{session.target_ip}</b> "
            f"&nbsp;|&nbsp; Generated: {session.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            body,
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    # --- Executive summary: at-a-glance risk tally ------------------------
    counts = {"High": 0, "Medium": 0, "Low": 0}
    for f in findings:
        if f.severity in counts:
            counts[f.severity] += 1
    story.append(Paragraph("Executive Summary", styles["Heading2"]))
    story.append(
        Paragraph(
            f"This assessment recorded <b>{len(findings)}</b> confirmed finding(s) on the target: "
            f"<b>{counts['High']}</b> High, <b>{counts['Medium']}</b> Medium, and "
            f"<b>{counts['Low']}</b> Low severity, each mapped to the OWASP IoT Top 5 below.",
            body,
        )
    )
    story.append(Spacer(1, 0.6 * cm))

    _scan_section(story, styles, body, small, scan)

    story.append(Paragraph("Findings Summary", styles["Heading2"]))
    if not findings:
        story.append(Paragraph("No findings were recorded for this session.", body))
    else:
        table_data = [["Severity", "OWASP IoT", "Finding", "Evidence", "Mitigation"]]
        for f in findings:
            table_data.append(
                [
                    Paragraph(f.severity, small),
                    Paragraph(f.owasp_id, small),
                    Paragraph(f.title, small),
                    Paragraph(f.evidence, small),
                    Paragraph(f.mitigation, small),
                ]
            )
        table = Table(table_data, colWidths=[2 * cm, 2 * cm, 4 * cm, 5 * cm, 5 * cm], repeatRows=1)
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f4")]),
        ]
        for row_idx, f in enumerate(findings, start=1):
            color = _SEVERITY_COLOR.get(f.severity, colors.black)
            style_commands.append(("TEXTCOLOR", (0, row_idx), (0, row_idx), color))
        table.setStyle(TableStyle(style_commands))
        story.append(table)

    story.append(Spacer(1, 0.8 * cm))

    if not_applicable:
        story.append(Paragraph("Tested But Not Present On This Target", styles["Heading2"]))
        story.append(
            Paragraph(
                "These OWASP IoT Top 5 categories were part of this assessment's scope but were not "
                "exploitable on this specific target - either already remediated or not applicable to "
                "this device configuration.",
                body,
            )
        )
        story.append(Spacer(1, 0.2 * cm))
        na_data = [["OWASP IoT", "Weakness checked for"]]
        for item in not_applicable:
            na_data.append([Paragraph(item["owasp_id"], small), Paragraph(item["title"], small)])
        na_table = Table(na_data, colWidths=[3 * cm, 13 * cm], repeatRows=1)
        na_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef6ee")]),
                ]
            )
        )
        story.append(na_table)
        story.append(Spacer(1, 0.8 * cm))

    if quiz_attempts:
        story.append(Paragraph("Learning Effectiveness", styles["Heading2"]))
        quiz_data = [["Phase", "Score", "Total", "Percentage"]]
        for q in quiz_attempts:
            pct = f"{(q.score / q.total * 100):.0f}%" if q.total else "n/a"
            quiz_data.append([q.phase.upper(), str(q.score), str(q.total), pct])
        quiz_table = Table(quiz_data, colWidths=[3 * cm, 3 * cm, 3 * cm, 3 * cm])
        quiz_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(quiz_table)
        story.append(Spacer(1, 0.2 * cm))

        # Learning gain = the actual measurement objective 4 is about, not
        # just the two raw scores. Only meaningful once both phases exist.
        by_phase = {q.phase: q for q in quiz_attempts}
        pre, post = by_phase.get("pre"), by_phase.get("post")
        capstone = by_phase.get("capstone")
        if pre and capstone and capstone.total:
            # Objective 4, capstone model: a pre-session knowledge check
            # (multiple choice) followed by an UNGUIDED capstone where the
            # student independently exploited a second, unseen target. The two
            # measure different things - recall vs. applied competency - so
            # they're reported side by side rather than as a single delta.
            pre_pct = pre.score / pre.total * 100 if pre.total else 0
            cap_pct = capstone.score / capstone.total * 100
            _qualifier = {
                "gave_up": " (the student ended the capstone early; this is their partial progress)",
                "skipped": "",
                "completed": "",
            }.get(capstone_status or "", "")
            story.append(
                Paragraph(
                    f"<b>Applied competency:</b> starting from a pre-session knowledge score of "
                    f"{pre.score}/{pre.total} ({pre_pct:.0f}%), the student then independently completed "
                    f"{capstone.score} of {capstone.total} exploitation objective(s) ({cap_pct:.0f}%) against a "
                    f"second, unseen target with no step-by-step guidance{_qualifier} - evidence of whether the "
                    f"guided session transferred into hands-on skill.",
                    body,
                )
            )
        if pre and post and post.total:
            delta = post.score - pre.score
            pre_pct = pre.score / pre.total * 100 if pre.total else 0
            post_pct = post.score / post.total * 100
            if delta > 0:
                verdict = (
                    f"the student's score improved by {delta} question(s) "
                    f"(+{post_pct - pre_pct:.0f} percentage points), indicating a measurable learning gain."
                )
            elif delta == 0:
                verdict = "the student's score was unchanged between the pre- and post-session quiz."
            else:
                verdict = f"the student's score decreased by {abs(delta)} question(s) after the session."
            story.append(
                Paragraph(
                    f"<b>Learning gain:</b> going from {pre_pct:.0f}% to {post_pct:.0f}%, {verdict}",
                    body,
                )
            )
        story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Disclaimer", styles["Heading2"]))
    story.append(
        Paragraph(
            "This report was generated by EduVAPT-IoT for educational purposes against an "
            "authorised lab target only. Findings and mitigation guidance are simplified for "
            "learning and are not a substitute for a professional security assessment.",
            body,
        )
    )

    doc.build(story)
    return buffer.getvalue()


def _scan_section(story, styles, body, small, scan: dict | None) -> None:
    """Automated recon results (objective 1), if a scan was run for the
    session. Placed before the manual findings so the report reads in the
    order the assessment happened: automated recon first, then confirmed
    exploitation."""
    if not scan:
        return
    story.append(Paragraph("Automated Recon Scan", styles["Heading2"]))
    story.append(Paragraph(scan.get("summary", ""), body))
    story.append(Spacer(1, 0.2 * cm))

    services = scan.get("services", [])
    if services:
        scan_data = [["Port", "Protocol", "OWASP", "Observation", "Banner / Version"]]
        for svc in services:
            banner = svc.get("version") or svc.get("banner") or "-"
            scan_data.append(
                [
                    Paragraph(str(svc.get("port", "")), small),
                    Paragraph(svc.get("protocol", ""), small),
                    Paragraph(svc.get("owasp_id", ""), small),
                    Paragraph(svc.get("observation", ""), small),
                    Paragraph(banner, small),
                ]
            )
        scan_table = Table(scan_data, colWidths=[1.5 * cm, 2 * cm, 1.8 * cm, 6 * cm, 5 * cm], repeatRows=1)
        scan_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f4")]),
                ]
            )
        )
        story.append(scan_table)

    notes = scan.get("engine_notes", [])
    if notes:
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph("Scan engines: " + "; ".join(notes), small))
    story.append(Spacer(1, 0.8 * cm))
