"""
create_sample_data.py – Generate sample files for testing.

Creates minimal-but-valid files in the data/sample_files/ directory tree.
Formats:
  - .txt   plain text (built-in)
  - .pdf   minimal valid PDF (hand-crafted bytes, no external dep)
  - .docx  minimal valid OOXML document (zipfile + hand-crafted XML)
  - .xlsx  minimal valid OOXML spreadsheet (zipfile + hand-crafted XML)
  - .jpg   minimal valid JPEG (raw JFIF header bytes)

Run from the project root::

    python scripts/create_sample_data.py
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent  # project root
DATA_DIR = ROOT / "data" / "sample_files"


# ---------------------------------------------------------------------------
# Minimal binary generators
# ---------------------------------------------------------------------------


def _minimal_pdf(title: str) -> bytes:
    """Return the bytes of a syntactically valid single-page PDF."""
    content_stream = f"BT /F1 12 Tf 72 720 Td ({title}) Tj ET".encode()
    content_len = len(content_stream)

    body = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
        b"   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n\n"
        + f"4 0 obj\n<< /Length {content_len} >>\nstream\n".encode()
        + content_stream
        + b"\nendstream\nendobj\n\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    # Compute cross-reference table offsets
    offsets: list[int] = []
    pos = 0
    for line in body.split(b"\n"):
        if line.endswith(b"obj"):
            offsets.append(pos)
        pos += len(line) + 1  # +1 for the newline

    xref_offset = len(body)
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets[:5]:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        + f"startxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return body + xref + trailer


def _minimal_docx(text: str) -> bytes:
    """Return the bytes of a minimal valid .docx (OOXML) file."""
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
        ' Target="word/document.xml"/>'
        "</Relationships>"
    )
    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>"
        + text
        + "</w:t></w:r></w:p></w:body>"
        "</w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", doc_xml)
    return buf.getvalue()


def _minimal_xlsx(cell_text: str) -> bytes:
    """Return the bytes of a minimal valid .xlsx (OOXML) file."""
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
        ' Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>"
        '<sheet name="Sheet1" sheetId="1" r:id="rId1"/>'
        "</sheets>"
        "</workbook>"
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"'
        ' Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData><row r=\"1\"><c r=\"A1\" t=\"inlineStr\">"
        f"<is><t>{cell_text}</t></is>"
        "</c></row></sheetData>"
        "</worksheet>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue()


def _minimal_jpeg() -> bytes:
    """Return the bytes of a tiny but structurally valid JPEG image."""
    # A 1×1 white pixel JPEG (48 bytes, no external dependencies)
    return bytes(
        [
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00,
            0xFF, 0xDB, 0x00, 0x43, 0x00,
            *([0x08] * 64),
            0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x11, 0x00,
            0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01, 0x01, 0x01,
            0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02,
            0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B,
            0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
            0xF8, 0xFF, 0xD9,
        ]
    )


# ---------------------------------------------------------------------------
# File creation table
# ---------------------------------------------------------------------------

SAMPLE_FILES: list[tuple[str, bytes | str]] = [
    # Zoology
    (
        "zoology/amphibian_lifecycle_notes.pdf",
        _minimal_pdf("Amphibian Lifecycle Notes"),
    ),
    (
        "zoology/mammal_habitat_summary.docx",
        _minimal_docx("Mammal Habitat Summary – A survey of terrestrial mammal habitats."),
    ),
    (
        "zoology/bird_migration_observations.txt",
        (
            "Bird Migration Observations\n"
            "===========================\n\n"
            "Observed species: Arctic Tern, Barn Swallow, European Robin\n"
            "Season: Autumn\n"
            "Notes: Flocks travelling south-west along the coastal ridge.\n"
        ),
    ),
    # Biology
    (
        "biology/cell_structure_reference.xlsx",
        _minimal_xlsx("Cell Structure Reference Data"),
    ),
    (
        "biology/plant_growth_stages.txt",
        (
            "Plant Growth Stages\n"
            "===================\n\n"
            "Stage 1 – Germination\n"
            "Stage 2 – Seedling\n"
            "Stage 3 – Vegetative growth\n"
            "Stage 4 – Flowering\n"
            "Stage 5 – Fruiting and seed dispersal\n"
        ),
    ),
    # Ecology
    (
        "ecology/wetland_food_chain.jpg",
        _minimal_jpeg(),
    ),
    (
        "ecology/forest_biodiversity_inventory.pdf",
        _minimal_pdf("Forest Biodiversity Inventory"),
    ),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def create_all() -> None:
    """Create (or overwrite) all sample files under *DATA_DIR*."""
    for rel_path, content in SAMPLE_FILES:
        full_path = DATA_DIR / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, str):
            full_path.write_text(content, encoding="utf-8")
        else:
            full_path.write_bytes(content)

        print(f"  Created  {full_path.relative_to(ROOT)}")

    print(f"\nDone – {len(SAMPLE_FILES)} sample files created under {DATA_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    print("Creating sample data files…\n")
    create_all()
