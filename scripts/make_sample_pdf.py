"""Generate the demo PDF `data/documents/sample/travel_policy.pdf`.

A tiny PDF writer without extra dependencies (Helvetica, one text block per page).
It is also used by the tests to create PDFs on the fly.

Usage:  python -m scripts.make_sample_pdf
"""

from __future__ import annotations

from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "documents" / "sample" / "travel_policy.pdf"


def _escape(line: str) -> str:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(pages: list[list[str]]) -> bytes:
    """Build a valid PDF; each inner list holds the text lines of one page (ASCII only)."""
    objects: list[bytes] = []
    page_ids = [4 + 2 * i for i in range(len(pages))]
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for page_id, lines in zip(page_ids, pages, strict=True):
        text = "BT /F1 11 Tf 15 TL 60 780 Td\n"
        text += "".join(f"({_escape(line)}) Tj T*\n" for line in lines)
        text += "ET"
        stream = text.encode("latin-1")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {page_id + 1} 0 R >>".encode()
        )
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
        )

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{offset:010d} 00000 n \n" for offset in offsets).encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    ).encode()
    return bytes(out)


TRAVEL_POLICY = [
    [
        "Northwind Labs GmbH - Business Travel Policy",
        "Version 2.1, valid from 1 March 2026",
        "",
        "1. Approval",
        "Every business trip must be approved by your team lead before booking.",
        "Trips outside Europe also need approval from the Head of Finance.",
        "Submit the travel request in the TravelDesk tool at least 14 days in advance.",
        "",
        "2. Transport",
        "Train is the default for trips under 600 km. Book second class.",
        "First class is allowed for train rides longer than 4 hours.",
        "Flights are allowed for distances over 600 km. Always book economy class.",
        "Business class is only allowed for flights longer than 8 hours.",
        "Taxis are reimbursed up to 50 EUR per ride. Use public transport when possible.",
    ],
    [
        "3. Hotels",
        "The hotel budget is 140 EUR per night in Germany.",
        "In London, Paris and Zurich the hotel budget is 220 EUR per night.",
        "Book hotels through TravelDesk to get the company rate.",
        "",
        "4. Meals and per diem",
        "Employees receive a per diem of 28 EUR for each full travel day in Germany.",
        "For trips abroad the per diem is 40 EUR per full day.",
        "Client dinners must be approved by your team lead and need a receipt.",
        "",
        "5. Expense reports",
        "Submit your expense report within 30 days after the trip.",
        "Upload all receipts as PDF or photo in the ExpenseHub app.",
        "Reimbursement is paid with the next monthly salary.",
        "Questions about travel: write to travel@northwind-labs.example.",
    ],
]


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(build_pdf(TRAVEL_POLICY))
    print(f"Wrote {OUTPUT}")
