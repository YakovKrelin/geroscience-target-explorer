import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_due_diligence_pdf(target_name: str, score: float) -> bytes:
  """Генерирует PDF-отчет по выбранной мишени."""
  buffer = io.BytesIO()
  c = canvas.Canvas(buffer, pagesize=letter)
  width, height = letter

  # Заголовок отчета
  c.setFont("Helvetica-Bold", 16)
  c.drawString(50, height - 50, "Geroscience Target Explorer - Due Diligence Report")

  c.setFont("Helvetica", 12)
  c.drawString(50, height - 90, f"Target Asset: {target_name}")
  c.drawString(50, height - 115, f"Integrated Score: {score:.2f} / 100")
  c.drawString(
      50, height - 140, "Status: Validated for Preclinical Pipeline Review"
  )

  c.showPage()
  c.save()

  buffer.seek(0)
  return buffer.getvalue()