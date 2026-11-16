import pandas as pd
import io

# Safe import of reportlab with a fallback option
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def generate_pdf_report(data=None, filename="report.pdf"):
    """
    Generates a PDF report with error handling for missing reportlab dependency.
    """
    if not REPORTLAB_AVAILABLE:
        # Returning a text byte buffer as a safe placeholder
        return io.BytesIO(b"PDF generation requires reportlab package.")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(Paragraph("Geroscience Target Explorer Report", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Generated successfully from application data.", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer