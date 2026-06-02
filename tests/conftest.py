"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers to create minimal valid binary files in tmp directories
# ---------------------------------------------------------------------------


def _minimal_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"


def _minimal_docx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<w:document/>")
    return buf.getvalue()


def _minimal_xlsx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("xl/workbook.xml", "<workbook/>")
    return buf.getvalue()


def _minimal_jpg_bytes() -> bytes:
    # Minimal JFIF JPEG header + EOI marker
    return bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46,
                  0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xD9])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def temp_file_root(tmp_path: Path) -> Path:
    """
    Create a temporary directory tree that mimics the real sample-data layout.

    Structure::

        <tmp>/
        ├── zoology/
        │   ├── amphibian_notes.txt        (text)
        │   ├── bird_migration.pdf         (pdf bytes)
        │   └── mammal_summary.docx        (docx bytes)
        ├── biology/
        │   ├── plant_growth.txt           (text)
        │   └── cell_structure.xlsx        (xlsx bytes)
        └── ecology/
            ├── wetland_food_chain.jpg     (jpg bytes)
            └── forest_inventory.pdf       (pdf bytes)
    """
    zoology = tmp_path / "zoology"
    biology = tmp_path / "biology"
    ecology = tmp_path / "ecology"
    for folder in (zoology, biology, ecology):
        folder.mkdir()

    # Zoology
    (zoology / "amphibian_notes.txt").write_text("Amphibian lifecycle notes.", encoding="utf-8")
    (zoology / "bird_migration.pdf").write_bytes(_minimal_pdf_bytes())
    (zoology / "mammal_summary.docx").write_bytes(_minimal_docx_bytes())

    # Biology
    (biology / "plant_growth.txt").write_text("Plant growth stages overview.", encoding="utf-8")
    (biology / "cell_structure.xlsx").write_bytes(_minimal_xlsx_bytes())

    # Ecology
    (ecology / "wetland_food_chain.jpg").write_bytes(_minimal_jpg_bytes())
    (ecology / "forest_inventory.pdf").write_bytes(_minimal_pdf_bytes())

    return tmp_path


@pytest.fixture()
def empty_root(tmp_path: Path) -> Path:
    """Return an empty temporary directory (no files)."""
    return tmp_path
