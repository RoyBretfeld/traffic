from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generate_pdf_from_text(text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    # Start a text object to handle line breaks and positioning
    text_object = c.beginText()
    text_object.setTextOrigin(40, height - 40)
    text_object.setFont("Helvetica", 11)

    for line in text.splitlines():
        # Fallback for potential non-ASCII characters; ReportLab's Helvetica can handle Latin-1 reasonably
        try:
            text_object.textLine(line)
        except Exception:
            # Replace characters that cannot be encoded, to avoid failing the sample generation
            safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
            text_object.textLine(safe_line)

    c.drawText(text_object)
    c.showPage()
    c.save()


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    input_txt = project_root / "tests" / "test_data" / "Fake_teha_content.txt"
    output_pdf = project_root / "tests" / "test_data" / "teha_sample.pdf"

    if not input_txt.exists():
        raise FileNotFoundError(f"Eingabedatei nicht gefunden: {input_txt}")

    text = input_txt.read_text(encoding="utf-8")
    generate_pdf_from_text(text, output_pdf)
    print(f"Beispiel-PDF erzeugt: {output_pdf}")


if __name__ == "__main__":
    main()
