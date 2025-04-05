from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

# Sample patient data
patient_data = {
    "Patient Name": "John Doe",
    "Age": 45,
    "Insurance": 1,
    "PRG": 120,
    "PL": 80,
    "PR": 72,
    "SK": 4.5,
    "TS": 98.6,
    "M11": 1.2,
    "BD2": 3.5,
}

def generate_hospital_pdf(filename="hospital_report.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("<b>HOSPITAL REPORT</b>", styles["Title"])
    elements.append(title)
    
    # Subtitle
    subtitle = Paragraph("<b>Patient Medical Report</b><br/><br/>", styles["Heading2"])
    elements.append(subtitle)

    # Create a table with patient details
    data = [["Attribute", "Value"]]
    for key, value in patient_data.items():
        data.append([key, str(value)])

    table = Table(data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    
    # Build the PDF
    doc.build(elements)
    print(f"PDF Generated: {filename}")

# Generate the PDF
generate_hospital_pdf()
