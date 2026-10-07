from __future__ import annotations

import io
import zipfile
from pathlib import PurePosixPath
from xml.etree import ElementTree


class ResumeReadError(ValueError):
    """A user-facing error raised when a resume cannot be read."""


def extract_resume_text(filename: str, content: bytes) -> str:
    extension = PurePosixPath(filename).suffix.lower()

    if extension == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ResumeReadError(
                "PDF reading is not installed. Run `python -m pip install -r requirements.txt` and try again."
            ) from exc
        try:
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ResumeReadError("We couldn't read that PDF. Try exporting it again or upload a DOCX file.") from exc
    elif extension == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                xml = ElementTree.fromstring(archive.read("word/document.xml"))
            text = "\n".join(
                "".join(node.text or "" for node in paragraph.iter() if node.tag.endswith("}t"))
                for paragraph in xml.iter()
                if paragraph.tag.endswith("}p")
            )
        except (KeyError, OSError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
            raise ResumeReadError("We couldn't read that DOCX file. Try saving it again and re-uploading it.") from exc
    else:
        raise ResumeReadError("Upload a PDF or DOCX resume. Legacy DOC files aren't supported yet.")

    text = text.strip()
    if not text:
        raise ResumeReadError("No readable text was found. Try a text-based PDF or DOCX file.")
    return text
