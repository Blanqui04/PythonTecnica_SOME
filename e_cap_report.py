import os
import tempfile
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle, Image, SimpleDocTemplate, Paragraph, Spacer
# ---------- funció de gràfics d'estudi de capacitat ---------- #
from e_cap import get_sample_data, analisi_mostra, index_proces
from e_cap_plots import i_chart, rm_chart, plt_sample_analysis, plt_extrapolated_sample
from e_cap_plots import main as study_charts
from translation_dict import translations
# ---------- dades necessàries, carpetes, etc. ---------- #
output_dir = r'C:\Github\PythonTecnica_SOME\estudi de capacitat'
logos_dir = r'C:\Github\PythonTecnica_SOME\ui_images'
os.makedirs(output_dir, exist_ok=True)

# --- Translation dictionaries ---
translations

def add_logo(canvas, doc):
    logo_path = os.path.join(logos_dir, 'logo_some.png')
    if os.path.exists(logo_path):
        # Desired width in points (1 cm = 28.3465 points)
        width_cm = 5.5
        width_pt = width_cm * 28.3465
        img = ImageReader(logo_path)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        height_pt = width_pt * aspect
        # Place at (left margin, top of page - height)
        x = doc.leftMargin
        y = doc.pagesize[1] - doc.topMargin - height_pt + 15  # +15 for a little padding from the top
        canvas.drawImage(
            logo_path, x, y,
            width=width_pt, height=height_pt,
            preserveAspectRatio=True, mask='auto'
        )


def add_context(canvas, doc, context_text):
    # Draw context (not a title) in the upper right
    canvas.saveState()
    canvas.setFont("Times-Roman", 12)
    text_width = canvas.stringWidth(context_text, "Times-Roman", 12)
    x = doc.pagesize[0] - doc.rightMargin - text_width
    y = doc.pagesize[1] - doc.topMargin + 10
    canvas.drawString(x, y, context_text)
    canvas.restoreState()


def build_header_table(row, tr):
    # Dummy values for now; replace with DB values later
    supplier = "Some S.A."
    part_name = "[Part Name]"
    part_no = "[Part Nº]"
    drawing_no = "[Drawing Nº]"
    item_no = str(row['Element']).replace(' ', '_')
    description = "[Description of the dimension]"
    measurement_equipment = "[Measurement Equipment]"

    header_data = [
        [f"{tr['supplier']}:", supplier, f"{tr['part_name']}:", part_name],
        [f"{tr['part_no']}:", part_no, f"{tr['drawing_no']}:", drawing_no],
        [f"{tr['item_no']}:", item_no, f"{tr['description']}:", description],
        [f"{tr['measurement_equipment']}:", measurement_equipment, "", ""]
    ]
    header_table = Table(header_data, hAlign='LEFT', colWidths=[2.5*cm, 5*cm, 2.5*cm, 5*cm])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('SPAN', (1, 3), (3, 3)),  # Span last row for measurement equipment
    ]))
    return header_table


def add_image_with_aspect(elements, img_path, width=5*inch):
    if os.path.exists(img_path):
        img = ImageReader(img_path)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        height = width * aspect
        elements.append(Image(img_path, width=width, height=height))


def add_charts(elements, element, tr):
    ichart_path = os.path.join(output_dir, f"{element}_IChart.png")
    if os.path.exists(ichart_path):
        elements.append(Paragraph(f"{tr['ichart']}:", getSampleStyleSheet()['Normal']))
        add_image_with_aspect(elements, ichart_path, width=5*inch)
        elements.append(Spacer(1, 12))

    mrchart_path = os.path.join(output_dir, f"{element}_MRChart.png")
    if os.path.exists(mrchart_path):
        elements.append(Paragraph(f"{tr['mrchart']}:", getSampleStyleSheet()['Normal']))
        add_image_with_aspect(elements, mrchart_path, width=5*inch)
        elements.append(Spacer(1, 12))

    hist_path = os.path.join(output_dir, f"{element}_normalitat.png")
    if os.path.exists(hist_path):
        elements.append(Paragraph(f"{tr['hist_kde']}:", getSampleStyleSheet()['Normal']))
        add_image_with_aspect(elements, hist_path, width=5*inch)
        elements.append(Spacer(1, 18))


def clean_up_images(df):
    for i, row in df.iterrows():
        element = str(row['Element']).replace(' ', '_')
        for suffix in ["_IChart.png", "_MRChart.png", "_normalitat.png"]:
            img_path = os.path.join(output_dir, f"{element}{suffix}")
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except Exception as e:
                    print(f"Could not delete {img_path}: {e}")


def build_report(language='en'):
    tr = translations[language]
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Header', fontName='Times-Roman', fontSize=12, leading=14, spaceAfter=8))

    # Prepare PDF
    pdf_file = "informe_ppap.pdf"
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        leftMargin=1.78 * cm,
        rightMargin=1.78 * cm,
        topMargin=1.91 * cm,
        bottomMargin=1.91 * cm
    )

    elements = []
    df = get_sample_data()  # Get data

    # Loop through each element and add its section
    for i, row in df.iterrows():
        element = str(row['Element']).replace(' ', '_')

        # Header info block
        elements.append(build_header_table(row, tr))
        elements.append(Spacer(1, 10))

        add_charts(elements, element, tr)   # Add charts

        # Page break after each element except the last
        if i < len(df) - 1:
            elements.append(Spacer(1, 24))

    # Compose onPage function to add logo and context
    def on_page(canvas, doc):
        add_logo(canvas, doc)
        add_context(canvas, doc, tr['report_context'])


    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)  # Build PDF
    clean_up_images(df) # Clean up images

    print(f"PDF report generated: {pdf_file}")


def main():
    # Generate charts for all elements (if not already done)
    df = get_sample_data()
    for i, row in df.iterrows():
        element = str(row['Element']).replace(' ', '_')
        nominal = row['Nominal']
        tolerance = [row['Tol-'], row['Tol+']]
        mostra = [float(x) for x in row['Values']]
        mu, std, is_normal, a2_stat, ad_res = analisi_mostra(mostra)
        pp, ppk = index_proces(mostra, nominal, tolerance)
        i_chart(mostra, nominal, tolerance, mu, std, element, pp, ppk, save=True, display=False)
        rm_chart(mostra, element, save=True, display=False)
        plt_sample_analysis(mostra, nominal, tolerance, element, save=True, display=False)
    # Build the report (choose language: 'en' or 'ca')
    build_report(language='en')

if __name__ == "__main__":
    main()
