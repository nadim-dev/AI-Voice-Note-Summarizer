from io import BytesIO

from pypdf import PdfReader


class DocumentReader:
    def read_uploaded_file(self, uploaded_file):
        extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

        if extension == "txt":
            return uploaded_file.getvalue().decode("utf-8", errors="ignore").strip()

        if extension == "pdf":
            pdf_reader = PdfReader(BytesIO(uploaded_file.getvalue()))
            pages = [page.extract_text() or "" for page in pdf_reader.pages]
            return "\n".join(page.strip() for page in pages if page.strip()).strip()

        raise ValueError("Unsupported document type. Please upload a TXT or PDF file.")
