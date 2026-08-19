from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_report_pdf(record):
    """Generate a styled PDF report for a chest X-ray dose calculation."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=colors.HexColor("#06204a"),
        spaceAfter=8,
        alignment=1,
    )
    brand_style = ParagraphStyle(
        "Brand",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor("#06204a"),
        spaceAfter=0,
    )
    sub_brand_style = ParagraphStyle(
        "SubBrand",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.HexColor("#ffd21f"),
        leading=10,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#06204a"),
        spaceBefore=12,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#101827"),
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor("#06204a"),
    )

    status_color = colors.HexColor("#087443") if record["status"] == "PASS" else colors.HexColor("#b42318")

    story = []
    logo_path = Path(__file__).resolve().parent / "frontend" / "static" / "radioactive-icon.jpg"
    if logo_path.exists():
        logo = Image(str(logo_path), width=20 * mm, height=20 * mm)
        logo_table = Table(
            [[logo, Paragraph("Chest X-Ray Dose Calculator", brand_style),]],
            colWidths=[24 * mm, 120 * mm],
            vAlign="MIDDLE",
        )
        logo_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(logo_table)
        story.append(Paragraph("Estimate · Analyze · Protect", sub_brand_style))
    else:
        story.append(Paragraph("Chest X-Ray Dose Calculator", title_style))
    story.append(Spacer(1, 6 * mm))

    summary_table = Table(
        [
            [Paragraph("Estimated Dose", label_style), Paragraph(f"{record['esd_mgy']} mGy", body_style)],
            [Paragraph("Status", label_style), Paragraph(record["status"], ParagraphStyle("Status", parent=body_style, textColor=status_color, fontName="Helvetica-Bold"))],
            [Paragraph("Projection", label_style), Paragraph(record["xray_type"], body_style)],
            [Paragraph("DRL Reference", label_style), Paragraph(f"{record['drl_limit']} mGy", body_style)],
        ],
        colWidths=[65 * mm, 80 * mm],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ffd21f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#06204a")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.8, colors.HexColor("#d9e2ef")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f7fb")]),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("Patient and Exposure Details", heading_style))
    detail_rows = [
        [Paragraph("Patient Name", label_style), Paragraph(record["patient_name"], body_style)],
        [Paragraph("Patient ID", label_style), Paragraph(record["patient_id"], body_style)],
        [Paragraph("Age", label_style), Paragraph(str(record["age"]), body_style)],
        [Paragraph("Sex", label_style), Paragraph(record["sex"], body_style)],
        [Paragraph("Projection", label_style), Paragraph(record["xray_type"], body_style)],
        [Paragraph("kVp", label_style), Paragraph(str(record["kvp"]), body_style)],
        [Paragraph("mAs", label_style), Paragraph(str(record["mas"]), body_style)],
        [Paragraph("FSD", label_style), Paragraph(f"{record['fsd']} cm", body_style)],
        [Paragraph("Machine Output", label_style), Paragraph(f"{record['machine_output']} mGy/mAs", body_style)],
        [Paragraph("BSF", label_style), Paragraph(str(record["bsf"]), body_style)],
        [Paragraph("Generated", label_style), Paragraph(record["created_at"], body_style)],
    ]

    detail_table = Table(detail_rows, colWidths=[65 * mm, 80 * mm])
    detail_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.8, colors.HexColor("#d9e2ef")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(detail_table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
