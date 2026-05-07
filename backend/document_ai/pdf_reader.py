import pymupdf


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using PyMuPDF.
    Works for normal text-based PDFs.
    Scanned/image-only PDFs need OCR later.
    """

    document = pymupdf.open(pdf_path)

    full_text = ""

    for page_number, page in enumerate(document, start=1):
        text = page.get_text()

        if text.strip():
            full_text += f"\n\n--- Page {page_number} ---\n"
            full_text += text

    document.close()

    return full_text.strip()