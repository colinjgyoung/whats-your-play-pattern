#!/usr/bin/env python3
"""Generate the downloadable nnherit 12 Play Patterns field guide PDF.

This script intentionally uses only the Python standard library and the existing
`patterns.js` data file so the PDF can be regenerated without a Node package,
browser, backend, or external PDF dependency.
"""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "field-guide.pdf"
PATTERNS_JS = ROOT / "patterns.js"
NNHERIT_URL = "https://www.nnherit.com"

PAGE_W = 595
PAGE_H = 842
MARGIN = 52
BLACK = (0.067, 0.067, 0.067)
CHARCOAL = (0.20, 0.20, 0.20)
MUTED = (0.34, 0.34, 0.34)
YELLOW = (1.0, 0.82, 0.0)
WHITE = (1.0, 1.0, 1.0)
PALE_YELLOW = (1.0, 0.965, 0.72)
PALE_GRAY = (0.955, 0.955, 0.94)


def load_patterns() -> dict:
    script = (
        "global.window = global; "
        f"require({json.dumps(str(PATTERNS_JS))}); "
        "process.stdout.write(JSON.stringify(global.PATTERN_APP_DATA.patterns));"
    )
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def pdf_escape(text: str) -> bytes:
    encoded = text.encode("cp1252", errors="replace")
    return encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


class PDF:
    def __init__(self) -> None:
        self.objects: list[bytes] = []
        self.pages: list[int] = []
        self.pages_obj = self.add_object(b"")
        self.font_regular = self.add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        self.font_bold = self.add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    def add_object(self, data: bytes) -> int:
        self.objects.append(data)
        return len(self.objects)

    def set_object(self, num: int, data: bytes) -> None:
        self.objects[num - 1] = data

    def add_page(self, content: bytes, annots: list[tuple[float, float, float, float, str]] | None = None) -> None:
        stream = b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"
        content_obj = self.add_object(stream)
        annot_refs = []
        for x1, y1, x2, y2, url in annots or []:
            annot = (
                b"<< /Type /Annot /Subtype /Link /Rect [%.2f %.2f %.2f %.2f] "
                b"/Border [0 0 0] /A << /S /URI /URI (%s) >> >>"
                % (x1, y1, x2, y2, pdf_escape(url))
            )
            annot_refs.append(self.add_object(annot))
        annots_part = b""
        if annot_refs:
            annots_part = b" /Annots [" + b" ".join(f"{n} 0 R".encode() for n in annot_refs) + b"]"
        page = (
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] "
            b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> /Contents %d 0 R%s >>"
            % (self.pages_obj, PAGE_W, PAGE_H, self.font_regular, self.font_bold, content_obj, annots_part)
        )
        self.pages.append(self.add_object(page))

    def write(self, path: Path) -> None:
        kids = b" ".join(f"{page} 0 R".encode() for page in self.pages)
        self.set_object(self.pages_obj, b"<< /Type /Pages /Kids [" + kids + b"] /Count %d >>" % len(self.pages))
        catalog = self.add_object(b"<< /Type /Catalog /Pages %d 0 R >>" % self.pages_obj)

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for i, obj in enumerate(self.objects, start=1):
            offsets.append(len(out))
            out.extend(f"{i} 0 obj\n".encode())
            out.extend(obj)
            out.extend(b"\nendobj\n")
        xref = len(out)
        out.extend(f"xref\n0 {len(self.objects) + 1}\n".encode())
        out.extend(b"0000000000 65535 f\n")
        for offset in offsets[1:]:
            out.extend(f"{offset:010d} 00000 n\n".encode())
        out.extend(
            b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(self.objects) + 1, catalog, xref)
        )
        path.write_bytes(out)


class Page:
    def __init__(self) -> None:
        self.commands: list[bytes] = []
        self.links: list[tuple[float, float, float, float, str]] = []
        self.y = PAGE_H - MARGIN

    def color(self, rgb: tuple[float, float, float]) -> str:
        return "%.3f %.3f %.3f" % rgb

    def rect(self, x: float, y: float, w: float, h: float, fill: tuple[float, float, float]) -> None:
        self.commands.append(f"q {self.color(fill)} rg {x:.2f} {y:.2f} {w:.2f} {h:.2f} re f Q\n".encode())

    def text(self, x: float, y: float, text: str, size: float = 10, font: str = "F1", color: tuple[float, float, float] = BLACK) -> None:
        self.commands.append(
            b"BT "
            + f"{self.color(color)} rg /{font} {size:.2f} Tf {x:.2f} {y:.2f} Td ".encode()
            + b"(" + pdf_escape(text) + b") Tj ET\n"
        )

    def line(self, y: float, color: tuple[float, float, float] = YELLOW, x: float = MARGIN, w: float | None = None, h: float = 3) -> None:
        self.rect(x, y, PAGE_W - 2 * MARGIN if w is None else w, h, color)

    def bytes(self) -> bytes:
        return b"".join(self.commands)


class Guide:
    def __init__(self, pdf: PDF) -> None:
        self.pdf = pdf
        self.page: Page | None = None
        self.page_number = 0

    def begin_page(self, title: str | None = None) -> None:
        if self.page:
            self.finish_page()
        self.page = Page()
        self.page_number += 1
        self.page.text(MARGIN, PAGE_H - 34, "nnherit", 17, "F2", BLACK)
        self.page.rect(MARGIN, PAGE_H - 42, 74, 8, YELLOW)
        self.page.text(PAGE_W - 226, PAGE_H - 32, "The 12 Play Patterns Field Guide", 9, "F1", MUTED)
        self.page.y = PAGE_H - 74
        if title:
            self.heading(title, 18)

    def finish_page(self) -> None:
        assert self.page is not None
        self.page.text(MARGIN, 28, f"nnherit · {NNHERIT_URL}", 8.5, "F1", MUTED)
        self.page.text(PAGE_W - 80, 28, str(self.page_number), 8.5, "F1", MUTED)
        self.pdf.add_page(self.page.bytes(), self.page.links)
        self.page = None

    def ensure(self, needed: float) -> None:
        assert self.page is not None
        if self.page.y - needed < 56:
            self.begin_page()

    def heading(self, text: str, size: float = 22) -> None:
        assert self.page is not None
        self.ensure(size + 22)
        self.page.text(MARGIN, self.page.y, text, size, "F2", BLACK)
        self.page.y -= size + 12

    def subheading(self, text: str) -> None:
        assert self.page is not None
        self.ensure(34)
        self.page.text(MARGIN, self.page.y, text, 11.5, "F2", BLACK)
        self.page.y -= 15

    def text_block(self, x: float, text: str, size: float = 9.8, width: int = 92, gap: float = 9, color: tuple[float, float, float] = CHARCOAL, font: str = "F1") -> float:
        assert self.page is not None
        start_y = self.page.y
        for para in text.split("\n\n"):
            for line in textwrap.wrap(para, width=width):
                self.ensure(size + 7)
                self.page.text(x, self.page.y, line, size, font, color)
                self.page.y -= size + 3.5
            self.page.y -= gap
        return start_y - self.page.y

    def paragraph(self, text: str, size: float = 9.8, width: int = 92, gap: float = 9, color: tuple[float, float, float] = CHARCOAL) -> None:
        self.text_block(MARGIN, text, size=size, width=width, gap=gap, color=color)

    def bullet(self, text: str) -> None:
        assert self.page is not None
        for i, line in enumerate(textwrap.wrap(text, width=86)):
            self.ensure(15)
            prefix = "• " if i == 0 else "  "
            self.page.text(MARGIN + 8, self.page.y, prefix + line, 9.5, "F1", CHARCOAL)
            self.page.y -= 13

    def pattern_index(self, patterns: dict) -> None:
        assert self.page is not None
        self.ensure(476)
        col_w = 235
        gap = 21
        card_h = 68
        row_gap = 10
        start_y = self.page.y
        names = list(patterns.keys())
        for idx, name in enumerate(names, start=1):
            col = 0 if idx <= 6 else 1
            row = (idx - 1) % 6
            x = MARGIN + col * (col_w + gap)
            top = start_y - row * (card_h + row_gap)
            bottom = top - card_h
            self.page.rect(x, bottom, col_w, card_h, PALE_GRAY if row % 2 else PALE_YELLOW)
            self.page.rect(x, top - 9, 34, 9, YELLOW)
            self.page.text(x + 10, top - 25, f"{idx}.", 12.5, "F2", BLACK)
            for line_no, line in enumerate(textwrap.wrap(name, width=27)[:2]):
                self.page.text(x + 38, top - 21 - line_no * 12, line, 9.8, "F2", BLACK)
            summary_y = top - 46
            for line_no, line in enumerate(textwrap.wrap(patterns[name]["summary"], width=40)[:2]):
                self.page.text(x + 12, summary_y - line_no * 10.5, line, 8.4, "F1", CHARCOAL)
        self.page.y = start_y - 6 * (card_h + row_gap) + row_gap - 12

    def accent_rule(self) -> None:
        assert self.page is not None
        self.ensure(20)
        self.page.line(self.page.y - 2, x=MARGIN, w=150, h=5)
        self.page.y -= 22

    def pattern_section(self, label: str, text: str) -> None:
        assert self.page is not None
        self.ensure(48)
        self.page.y -= 4
        self.subheading(label)
        self.paragraph(text, width=88, gap=10)
        self.page.y -= 4

    def button_link(self, label: str, url: str) -> None:
        assert self.page is not None
        self.ensure(54)
        x, y, w, h = MARGIN, self.page.y - 30, 184, 30
        self.page.rect(x, y, w, h, YELLOW)
        self.page.text(x + 15, y + 10, label, 10.5, "F2", BLACK)
        self.page.links.append((x, y, x + w, y + h, url))
        self.page.y -= 48


def draw_cover(pdf: PDF) -> None:
    p = Page()
    p.rect(0, 0, PAGE_W, PAGE_H, BLACK)
    p.rect(0, PAGE_H - 188, PAGE_W, 188, YELLOW)
    p.text(MARGIN, PAGE_H - 94, "nnherit", 36, "F2", BLACK)
    p.text(MARGIN, PAGE_H - 139, "What’s Your", 30, "F2", BLACK)
    p.text(MARGIN, PAGE_H - 176, "Play Pattern?", 42, "F2", BLACK)
    p.text(MARGIN, PAGE_H - 250, "The 12 Play Patterns Field Guide", 22, "F2", WHITE)
    p.text(MARGIN, PAGE_H - 286, "A practical mirror for facilitators, educators, coaches,", 13, "F1", WHITE)
    p.text(MARGIN, PAGE_H - 306, "consultants, game designers, and playful learning practitioners.", 13, "F1", WHITE)
    p.rect(MARGIN, 92, 210, 34, YELLOW)
    p.text(MARGIN + 16, 104, "Explore playful tools", 12, "F2", BLACK)
    p.links.append((MARGIN, 92, MARGIN + 210, 126, NNHERIT_URL))
    p.text(MARGIN, 62, NNHERIT_URL, 11, "F1", WHITE)
    pdf.add_page(p.bytes(), p.links)


def build() -> None:
    patterns = load_patterns()
    pdf = PDF()
    draw_cover(pdf)
    guide = Guide(pdf)

    guide.begin_page("How to use this field guide")
    guide.paragraph(
        "This guide expands the What’s Your Play Pattern? profiler into a practical reference. "
        "Use it to notice how you tend to use play in group settings, where your style is strongest, "
        "and what to watch when the room needs something different.",
        size=10.5,
        width=86,
    )
    guide.subheading("This is not a personality test")
    guide.paragraph(
        "Treat each Play Pattern as a facilitation lens, not a label. Your primary pattern may describe "
        "your default move. Your secondary pattern may describe the support move you often bring with it.",
        width=88,
    )
    guide.subheading("The 12 patterns at a glance")
    guide.pattern_index(patterns)
    guide.paragraph(
        "Tip: after reading your own pattern, read the two patterns listed under Good pairings. "
        "Those combinations often reveal the next useful stretch for your practice.",
        width=88,
    )

    for i, (name, pattern) in enumerate(patterns.items(), start=1):
        guide.begin_page(f"{i}. {name}")
        guide.accent_rule()
        guide.paragraph(pattern["summary"], size=11.2, width=76, gap=14, color=BLACK)
        guide.paragraph(pattern["description"], width=88, gap=14)
        for label, key in [
            ("Your strength", "strength"),
            ("Your danger zone", "danger"),
            ("Try this next", "next"),
            ("Good pairings", "pairings"),
            ("nnherit bridge", "bridge"),
        ]:
            guide.pattern_section(label, pattern[key])

    guide.begin_page("Keep playing with purpose")
    guide.paragraph(
        "nnherit creates playful tools, prompts, and facilitation experiences for teams and groups "
        "working with complex conversations. Our playkits use structure, distance, and imagination "
        "to help people surface dynamics, explore possibilities, and move from insight to action.",
        size=11,
        width=82,
    )
    guide.subheading("Use this guide with your next group")
    guide.bullet("Name the pattern you naturally reach for when a room gets stuck.")
    guide.bullet("Choose one pattern that could balance or stretch your default style.")
    guide.bullet("Pair with someone who brings a different Play Pattern into the room.")
    guide.button_link("Visit www.nnherit.com", NNHERIT_URL)
    guide.paragraph(
        "Explore more playful tools and insights at www.nnherit.com.",
        size=10.5,
        width=80,
    )
    guide.finish_page()

    pdf.write(OUT)
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
