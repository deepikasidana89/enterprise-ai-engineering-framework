from __future__ import annotations

from pathlib import Path
from typing import cast

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .builder import format_timestamp
from .models import ReadinessReport


class PdfReporter:
    """Render a polished, shareable EARF readiness report as PDF."""

    def write(self, report: ReadinessReport, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.55 * inch,
            leftMargin=0.55 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.55 * inch,
            title=f"EARF Readiness Report - {report.repository_name}",
            author="Enterprise AI Readiness Framework",
        )

        styles = getSampleStyleSheet()
        brand = colors.HexColor("#1F3A5F")
        accent = colors.HexColor("#3A7CA5")
        light = colors.HexColor("#EEF4F8")
        pale = colors.HexColor("#F7F9FB")
        muted = colors.HexColor("#5F6B76")
        good = colors.HexColor("#2E7D32")
        warn = colors.HexColor("#B26A00")
        bad = colors.HexColor("#B3261E")

        title_style = ParagraphStyle(
            "EARFTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=brand,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
        subtitle_style = ParagraphStyle(
            "EARFSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=muted,
            alignment=TA_CENTER,
            spaceAfter=14,
        )
        h1 = ParagraphStyle(
            "EARFH1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=brand,
            spaceBefore=10,
            spaceAfter=8,
        )
        h2 = ParagraphStyle(
            "EARFH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=brand,
            spaceBefore=7,
            spaceAfter=5,
        )
        body = ParagraphStyle(
            "EARFBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#20252B"),
            spaceAfter=4,
        )
        small = ParagraphStyle(
            "EARFSmall",
            parent=body,
            fontSize=7.8,
            leading=10,
            textColor=muted,
        )
        score_style = ParagraphStyle(
            "EARFScore",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=31,
            textColor=brand,
            alignment=TA_CENTER,
        )
        metric_label = ParagraphStyle(
            "EARFMetricLabel",
            parent=small,
            alignment=TA_CENTER,
        )

        score = report.readiness_score
        coverage = score.assessment_coverage
        rule_details = cast(list[dict[str, object]], report.metadata.get("rule_details", []))
        core_gaps = cast(list[dict[str, object]], report.metadata.get("core_gaps", []))
        advanced = cast(list[dict[str, object]], report.metadata.get("advanced_opportunities", []))
        recommendations = cast(list[dict[str, str]], report.metadata.get("recommendations", []))
        passed_controls = cast(list[dict[str, object]], report.metadata.get("passed_controls", []))
        manual_review = cast(list[dict[str, object]], report.metadata.get("manual_review_required", []))
        semantic_review = cast(list[dict[str, object]], report.metadata.get("semantic_review_required", []))

        critical = [x for x in core_gaps if str(x.get("severity", "")).upper() == "CRITICAL"]
        high = [x for x in core_gaps if str(x.get("severity", "")).upper() == "HIGH"]

        story: list[object] = []
        story.append(Paragraph("EARF Enterprise AI Readiness Report", title_style))
        story.append(
            Paragraph(
                f"Repository: <b>{self._esc(report.repository_name)}</b><br/>"
                f"Generated: {self._esc(format_timestamp(report.generated_at))} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"EARF Version: {self._esc(report.earf_version)}",
                subtitle_style,
            )
        )

        status = score.production_readiness.value
        status_color = good if "READY" in status and "NOT" not in status else (warn if "WARNING" in status else bad)
        dashboard = Table(
            [
                [Paragraph(f"{score.core_readiness_score:.1f}", score_style), Paragraph(f"{score.advanced_controls_score:.1f}", score_style), Paragraph(f"{coverage.percentage:.1f}%", score_style)],
                [Paragraph("Core Readiness / 100", metric_label), Paragraph("Advanced Controls / 100", metric_label), Paragraph("Automated Coverage", metric_label)],
            ],
            colWidths=[2.25 * inch] * 3,
        )
        dashboard.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), light),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7E0E7")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7E0E7")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
                ]
            )
        )
        story.append(dashboard)
        story.append(Spacer(1, 10))

        status_table = Table(
            [[Paragraph("Production Status", h2), Paragraph(f"<b>{self._esc(status)}</b>", body)]],
            colWidths=[1.7 * inch, 5.05 * inch],
        )
        status_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), brand),
                    ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FFF8E8") if status_color == warn else pale),
                    ("BOX", (0, 0), (-1, -1), 0.7, status_color),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(status_table)

        story.append(Paragraph("Executive Summary", h1))
        summary_rows = [
            ["Critical blockers", str(len(critical))],
            ["High-priority core gaps", str(len(high))],
            ["Passed controls", str(score.passed_rules)],
            ["Failed controls", str(score.failed_rules)],
            ["Manual review", str(score.manual_review_rules)],
            ["Needs semantic review", str(score.needs_semantic_review_rules)],
            ["Evidence collected", str(report.total_evidence)],
        ]
        story.append(self._simple_table(summary_rows, brand, light))

        story.append(Paragraph("Category Scores", h1))
        category_rows: list[list[object]] = [["Category", "Score", "Passed", "Failed", "Coverage"]]
        for category, detail in sorted(score.category_details.items(), key=lambda item: item[0].lower()):
            tracked = (
                detail.passed_rules
                + detail.failed_rules
                + detail.manual_review_rules
                + detail.needs_semantic_review_rules
                + detail.not_applicable_rules
                + detail.disabled_rules
                + detail.error_rules
            )
            scored = detail.passed_rules + detail.failed_rules
            category_rows.append(
                [
                    category.replace("_", " ").title(),
                    f"{detail.score:.1f}" if detail.score is not None else "N/A",
                    str(detail.passed_rules),
                    str(detail.failed_rules),
                    f"{scored}/{tracked}",
                ]
            )
        story.append(self._data_table(category_rows, brand, light, [2.45 * inch, 0.85 * inch, 0.8 * inch, 0.8 * inch, 1.0 * inch]))

        self._append_findings_section(story, "Critical Blockers", critical, h1, h2, body, bad, pale)
        self._append_findings_section(story, "Top Core Gaps", [x for x in core_gaps if x not in critical], h1, h2, body, warn, pale)
        self._append_findings_section(story, "Advanced Opportunities", advanced, h1, h2, body, accent, pale)
        self._append_findings_section(story, "Manual Review Required", manual_review, h1, h2, body, warn, pale)
        self._append_findings_section(story, "Needs Semantic Review", semantic_review, h1, h2, body, accent, pale)

        story.append(PageBreak())
        story.append(Paragraph("Recommended Next Actions", h1))
        if recommendations:
            for index, item in enumerate(recommendations, start=1):
                title = self._esc(item.get("title", "Recommendation"))
                action = self._esc(item.get("recommendation", item.get("action", "")))
                story.append(KeepTogether([Paragraph(f"{index}. {title}", h2), Paragraph(action or "Review this item with the responsible engineering team.", body), Spacer(1, 3)]))
        else:
            story.append(Paragraph("No explicit recommendations were generated for this assessment.", body))

        story.append(Paragraph("Passed Controls", h1))
        if passed_controls:
            passed_rows: list[list[object]] = [["Rule", "Control"]]
            for item in passed_controls:
                passed_rows.append([str(item.get("rule_id", "")), Paragraph(self._esc(item.get("title", "")), small)])
            story.append(self._data_table(passed_rows, good, colors.HexColor("#EDF7ED"), [1.0 * inch, 5.75 * inch]))
        else:
            story.append(Paragraph("None detected.", body))

        story.append(Paragraph("Assessment Notes", h1))
        story.append(
            Paragraph(
                "EARF evaluates engineering evidence present in the repository. A PASS means supported evidence was detected; it does not certify that a control is complete, secure, effective, or correctly configured in production. Findings should be validated with the responsible engineers and combined with runtime testing, threat modeling, telemetry, operational evidence, and human review.",
                body,
            )
        )
        story.append(Paragraph(f"Total rule results evaluated: {len(rule_details)}", small))

        def footer(canvas, doc_obj):
            canvas.saveState()
            canvas.setStrokeColor(colors.HexColor("#D9E1E7"))
            canvas.line(doc_obj.leftMargin, 0.42 * inch, letter[0] - doc_obj.rightMargin, 0.42 * inch)
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(muted)
            canvas.drawString(doc_obj.leftMargin, 0.27 * inch, "Enterprise AI Readiness Framework (EARF)")
            canvas.drawRightString(letter[0] - doc_obj.rightMargin, 0.27 * inch, f"Page {doc_obj.page}")
            canvas.restoreState()

        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        return output_path

    @staticmethod
    def _esc(value: object) -> str:
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _append_findings_section(self, story, heading, findings, h1, h2, body, accent_color, background):
        story.append(Paragraph(heading, h1))
        if not findings:
            story.append(Paragraph("None.", body))
            return
        for item in findings:
            rule_id = self._esc(item.get("rule_id", ""))
            title = self._esc(item.get("title", "Finding"))
            severity = self._esc(item.get("severity", ""))
            rationale = self._esc(item.get("rationale", item.get("reason", "")))
            recommendation = self._esc(item.get("recommendation", item.get("action", "")))
            content = [Paragraph(f"{rule_id} - {title}", h2)]
            if severity:
                content.append(Paragraph(f"<b>Severity:</b> {severity}", body))
            if rationale:
                content.append(Paragraph(f"<b>Why it matters:</b> {rationale}", body))
            if recommendation:
                content.append(Paragraph(f"<b>Recommended action:</b> {recommendation}", body))
            box = Table([[content]], colWidths=[6.75 * inch])
            box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), background), ("BOX", (0, 0), (-1, -1), 0.7, accent_color), ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
            story.append(box)
            story.append(Spacer(1, 6))

    @staticmethod
    def _simple_table(rows, brand, light):
        table = Table(rows, colWidths=[4.9 * inch, 1.3 * inch], hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), light), ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7E0E7")), ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D7E0E7")), ("FONTNAME", (0, 0), (0, -1), "Helvetica"), ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"), ("TEXTCOLOR", (1, 0), (1, -1), brand), ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        return table

    @staticmethod
    def _data_table(rows, header_color, stripe_color, widths):
        table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), header_color), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 7.5), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D5DDE3")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, stripe_color]), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        return table
