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
    challenge_accuracy: tuple[int, int] | None = None,
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

    _learning_effectiveness(story, styles, body, quiz_attempts, challenge_accuracy, capstone_status)

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


def _learning_effectiveness(story, styles, body, quiz_attempts, challenge_accuracy, capstone_status) -> None:
    """Objective 4, capstone model. The headline measure is guided-challenge
    accuracy vs. UNGUIDED capstone accuracy (does the learning transfer when
    the help is removed?); the pre-session quiz is shown only as a knowledge
    baseline. There is no post-quiz here by design."""
    by_phase = {q.phase: q for q in (quiz_attempts or [])}
    pre = by_phase.get("pre")
    capstone = by_phase.get("capstone")
    ch_done, ch_total = challenge_accuracy or (0, 0)

    rows = []
    if pre and pre.total:
        rows.append(("Pre-session knowledge quiz (baseline)", pre.score, pre.total))
    if ch_total:
        rows.append(("Guided challenges (with guidance)", ch_done, ch_total))
    if capstone and capstone.total:
        rows.append(("Unguided capstone challenge", capstone.score, capstone.total))
    if not rows:
        return

    story.append(Paragraph("Learning Effectiveness", styles["Heading2"]))
    table_data = [["Phase", "Score", "Total", "Percentage"]]
    for label, score, total in rows:
        pct = f"{score / total * 100:.0f}%" if total else "n/a"
        table_data.append([label, str(score), str(total), pct])
    table = Table(table_data, colWidths=[7 * cm, 2.5 * cm, 2.5 * cm, 3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.2 * cm))

    # The actual learning-effectiveness signal: how well guided performance
    # held up once guidance was removed in the capstone.
    if ch_total and capstone and capstone.total:
        ch_pct = ch_done / ch_total * 100
        cap_pct = capstone.score / capstone.total * 100
        delta = cap_pct - ch_pct
        if delta >= -10:
            verdict = (
                "the student sustained their performance without guidance - strong evidence the concepts "
                "transferred into independent, hands-on skill."
            )
        elif delta >= -35:
            verdict = (
                "performance dropped moderately without guidance, indicating partial transfer from guided "
                "learning to independent practice."
            )
        else:
            verdict = (
                "performance dropped sharply once guidance was removed, suggesting the student leaned on the "
                "step-by-step help and should revisit the concepts."
            )
        qualifier = {
            "gave_up": " (the capstone was ended early; this reflects partial progress)",
            "skipped": " (the capstone was skipped)",
        }.get(capstone_status or "", "")
        story.append(
            Paragraph(
                f"<b>Guided vs. unguided:</b> the student completed {ch_pct:.0f}% of the challenges with "
                f"step-by-step guidance and {cap_pct:.0f}% of the capstone unaided{qualifier} - {verdict}",
                body,
            )
        )
    story.append(Spacer(1, 0.6 * cm))


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
