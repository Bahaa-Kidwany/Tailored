import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Tuple, List, Optional

LATEX_COMPILER_CANDIDATES = ("pdflatex", "xelatex", "lualatex", "tectonic")


def _extract_balanced_macros(tex: str, macro_name: str, num_args: int) -> List[Tuple[List[str], int, int]]:
    """Extracts \\macro_name{arg1}...{argN} with balanced braces."""
    results: List[Tuple[List[str], int, int]] = []
    pattern = re.compile(rf"\\{re.escape(macro_name)}\b")
    for m in pattern.finditer(tex):
        start_idx = m.start()
        pos = m.end()
        args: List[str] = []
        valid = True
        for _ in range(num_args):
            while pos < len(tex) and tex[pos].isspace():
                pos += 1
            if pos >= len(tex) or tex[pos] != "{":
                valid = False
                break
            depth = 0
            arg_start = pos + 1
            while pos < len(tex):
                ch = tex[pos]
                if ch == "\\" and pos + 1 < len(tex):
                    pos += 2
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        args.append(tex[arg_start:pos])
                        pos += 1
                        break
                pos += 1
            else:
                valid = False
                break
        if valid and len(args) == num_args:
            results.append((args, start_idx, pos))
    return results


def unwrap_paragraph_text_macros(tex: str) -> str:
    """
    Prevents single-line overflow bug where the Profile section summary gets
    printed on a single horizontal line running outside the physical page.
    Unwraps any \\text{...} horizontal box (\\hbox) that wraps a multi-word or
    Profile paragraph inside \\begin{justify} ... \\end{justify}.
    """
    if not tex or ("\\text{" not in tex and "\\text {" not in tex):
        return tex

    macro_matches = _extract_balanced_macros(tex, "text", 1)
    if not macro_matches:
        return tex

    out = tex
    for args, start_pos, end_pos in reversed(macro_matches):
        content = args[0]
        ctx_before = out[max(0, start_pos - 120) : start_pos].lower()
        is_profile_or_justify = "justify" in ctx_before or "profile" in ctx_before
        is_paragraph = len(content.strip()) > 35 or "\\textbf" in content
        if is_profile_or_justify or is_paragraph:
            out = out[:start_pos] + content + out[end_pos:]

    return out


def _clean_latex_inline(text: str) -> str:
    """Converts inline LaTeX markup to clean human-readable plain text."""
    s = text
    s = re.sub(r"(?<!\\)%.*$", "", s, flags=re.MULTILINE)
    s = re.sub(r"\\(?:begin|end)\{[^{}]*\}(?:\[[^\]]*\])?", "", s)
    s = s.replace(r"\&", "&").replace(r"\%", "%").replace(r"\$", "$").replace(r"\#", "#").replace(r"\_", "_")
    s = s.replace(r"\{", "{").replace(r"\}", "}")
    s = s.replace(r"\textbackslash{}", "\\").replace(r"\textasciitilde{}", "~").replace(r"\textasciicircum{}", "^")
    s = s.replace(r"$\cdot$", " | ").replace(r"$|$", " | ").replace("--", "–").replace("~", "  ")
    # Convert \href{url}{display} -> display
    for _ in range(3):
        s = re.sub(r"\\href\{[^{}]*\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", r"\1", s)
    s = re.sub(r"\\raisebox\{[^{}]*\}(?:\{[^{}]*\})?", "", s)
    s = re.sub(r"\\fa[A-Za-z0-9]+\b\s*\\?", "", s)
    s = re.sub(r"\\hfill\b", "   ", s)
    s = re.sub(r"\\\\(?:\[[^\]]*\])?", "", s)
    s = re.sub(r"\\(?:vspace|needspace|hspace)\{[^}]*\}", "", s)
    s = re.sub(r"\\(?:hrule|newline|item|resumeSubHeadingListStart|resumeSubHeadingListEnd|resumeItemListStart|resumeItemListEnd)\b", "", s)
    for _ in range(5):
        s = re.sub(
            r"\\(?:textbf|textit|emph|underline|text|textnormal|small|large|LARGE|huge|normalsize|scriptsize)\{([^{}]*)\}",
            r"\1",
            s,
        )
    s = re.sub(r"\\(?:LARGE|large|small|huge|normalsize|scriptsize|textbf|textit|emph|underline|text|textnormal|centering)\b", "", s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def _latex_to_reportlab_xml(text: str) -> str:
    """
    Converts inline LaTeX markup (\\textbf, \\textit, \\emph, \\underline, \\href)
    into safe ReportLab Platypus XML markup (<b>, <i>, <u>, <a href="...">)
    while escaping XML special characters (&, <, >).
    """
    if not text:
        return ""
    s = re.sub(r"(?<!\\)%.*$", "", text, flags=re.MULTILINE)
    # Strip LaTeX environment wrappers like \begin{justify}, \end{justify}, \begin{itemize}[leftmargin=0.15in, label={}]
    s = re.sub(r"\\(?:begin|end)\{[^{}]*\}(?:\[[^\]]*\])?", "", s)

    # Remove inline Link icon tags like {\href{...}{Link {\scriptsize\faLink}}} or convert to clean link
    s = re.sub(
        r"\{\\href\{([^{}]+)\}\{Link\s*(?:\{[^{}]*\})?\}\}",
        r"\\href{\1}{[Link]}",
        s,
    )

    # Unescape LaTeX specials to placeholders before XML escaping
    s = s.replace(r"\&", "&").replace(r"\%", "%").replace(r"\$", "$").replace(r"\#", "#").replace(r"\_", "_")
    s = s.replace(r"\textasciitilde{}", "~").replace(r"$|$", " | ").replace("--", "–")
    s = re.sub(r"\\raisebox\{[^{}]*\}(?:\{[^{}]*\})?", "", s)
    s = re.sub(r"\\faPhone\b\s*\\?", "Tel: ", s)
    s = re.sub(r"\\faEnvelope\b\s*\\?", "", s)
    s = re.sub(r"\\faLinkedin\b\s*\\?", "LinkedIn: ", s)
    s = re.sub(r"\\faGithub\b\s*\\?", "", s)
    s = re.sub(r"\\fa[A-Za-z0-9]+\b\s*\\?", "", s)
    s = re.sub(r"\\(?:vspace|needspace|hspace)\{[^}]*\}", "", s)
    s = re.sub(r"\\(?:newline|item|resumeSubHeadingListStart|resumeSubHeadingListEnd|resumeItemListStart|resumeItemListEnd)\b", "", s)
    s = re.sub(r"\\\\(?:\[[^\]]*\])?", "", s)

    # Convert \href{url}{label} into token markers before XML escaping
    links: List[Tuple[str, str]] = []

    def _href_repl(m: re.Match) -> str:
        url = m.group(1).strip()
        if "@" in url and not url.startswith(("mailto:", "http://", "https://")):
            url = f"mailto:{url}"
        label = m.group(2)
        idx = len(links)
        links.append((url, label))
        return f"@@HREF_{idx}@@"

    for _ in range(3):
        s = re.sub(r"\\href\{([^{}]+)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", _href_repl, s)

    # Convert \textbf{...}, \textit{...}, \emph{...}, \underline{...}, \text{...}, \textnormal{...}
    for _ in range(5):
        s = re.sub(r"\\textbf\s*\{([^{}]*)\}", r"@@B_START@@\1@@B_END@@", s)
        s = re.sub(r"\\(?:textit|emph)\s*\{([^{}]*)\}", r"@@I_START@@\1@@I_END@@", s)
        s = re.sub(r"\\underline\s*\{([^{}]*)\}", r"@@U_START@@\1@@U_END@@", s)
        s = re.sub(r"\\(?:text|textnormal|small|normalsize|large|LARGE|huge|scriptsize)\s*\{([^{}]*)\}", r"\1", s)

    s = re.sub(r"\\(?:LARGE|large|small|huge|normalsize|scriptsize|textbf|textit|emph|underline|text|textnormal|centering)\b", "", s)
    s = s.replace("{", "").replace("}", "").replace("~", "  ")

    # Restore HREFs with inner formatting processed
    for idx, (url, raw_label) in enumerate(links):
        inner = raw_label
        for _ in range(3):
            inner = re.sub(r"\\textbf\s*\{([^{}]*)\}", r"@@B_START@@\1@@B_END@@", inner)
            inner = re.sub(r"\\(?:textit|emph)\s*\{([^{}]*)\}", r"@@I_START@@\1@@I_END@@", inner)
            inner = re.sub(r"\\underline\s*\{([^{}]*)\}", r"@@U_START@@\1@@U_END@@", inner)
        inner = re.sub(r"\\fa[A-Za-z0-9]+\b\s*\\?", "", inner)
        inner = re.sub(r"\\raisebox\{[^{}]*\}(?:\{[^{}]*\})?", "", inner)
        inner = inner.replace("{", "").replace("}", "").strip()
        s = s.replace(f"@@HREF_{idx}@@", f"@@A_START_{idx}@@{inner}@@A_END@@")

    # Escape XML special characters
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Replace formatting markers with valid XML tags
    s = s.replace("@@B_START@@", "<b>").replace("@@B_END@@", "</b>")
    s = s.replace("@@I_START@@", "<i>").replace("@@I_END@@", "</i>")
    s = s.replace("@@U_START@@", "<u>").replace("@@U_END@@", "</u>")
    for idx, (url, _) in enumerate(links):
        safe_url = url.replace("&", "&amp;").replace('"', "&quot;")
        s = s.replace(f"@@A_START_{idx}@@", f'<a href="{safe_url}">')
    s = s.replace("@@A_END@@", "</a>")

    return re.sub(r"\s+", " ", s).strip()


def _generate_fallback_ats_pdf(tex_path: Path, pdf_path: Path) -> bool:
    """
    High-fidelity ReportLab Platypus PDF generator matching the exact Jake Gutierrez /
    Bahaa Kidwany (cv(1)(1).tex) visual layout:
    - Centered header: 20pt Name | Role Title, 10pt Location, single-line Contact Bar with underlined links
    - Small-caps bold section headers with full-width black horizontal rules
    - Full-width justified text (TA_JUSTIFY) for Profile, role summaries, and achievement bullets
    - Two-column right-aligned date subheadings that wrap cleanly on the left without text collision
    - Bold inline achievement titles and nested 'Stack:' sub-bullets
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            HRFlowable,
        )

        raw_tex = tex_path.read_text(encoding="utf-8")
        parts = split_latex_document(raw_tex)
        body = parts[1] if parts else raw_tex
        body = re.sub(r"(?<!\\)%.*$", "", body, flags=re.MULTILINE)

        page_w, page_h = letter  # 612 x 792 pt
        margin_lr = 30.0
        margin_tb = 22.0
        avail_w = page_w - 2 * margin_lr

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            leftMargin=margin_lr,
            rightMargin=margin_lr,
            topMargin=margin_tb,
            bottomMargin=margin_tb,
        )

        style_name = ParagraphStyle(
            "CvName",
            fontName="Helvetica",
            fontSize=18.5,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=3,
        )
        style_loc = ParagraphStyle(
            "CvLoc",
            fontName="Helvetica",
            fontSize=9.8,
            leading=12.5,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=3,
        )
        style_contact = ParagraphStyle(
            "CvContact",
            fontName="Helvetica",
            fontSize=9.0,
            leading=11.5,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=6,
        )
        style_section = ParagraphStyle(
            "CvSection",
            fontName="Helvetica-Bold",
            fontSize=11.0,
            leading=13,
            alignment=TA_LEFT,
            textColor=colors.black,
            spaceBefore=6,
            spaceAfter=1.5,
        )
        style_justify = ParagraphStyle(
            "CvJustify",
            fontName="Helvetica",
            fontSize=9.3,
            leading=12.4,
            alignment=TA_JUSTIFY,
            textColor=colors.black,
            spaceAfter=3,
        )
        style_sub_left = ParagraphStyle(
            "CvSubLeft",
            fontName="Helvetica-Bold",
            fontSize=9.8,
            leading=12.4,
            alignment=TA_LEFT,
            textColor=colors.black,
        )
        style_sub_right = ParagraphStyle(
            "CvSubRight",
            fontName="Helvetica-Bold",
            fontSize=9.3,
            leading=12.4,
            alignment=TA_RIGHT,
            textColor=colors.black,
        )
        style_sub2_left = ParagraphStyle(
            "CvSub2Left",
            fontName="Helvetica-Oblique",
            fontSize=9.1,
            leading=11.6,
            alignment=TA_LEFT,
            textColor=colors.black,
        )
        style_sub2_right = ParagraphStyle(
            "CvSub2Right",
            fontName="Helvetica-Oblique",
            fontSize=9.1,
            leading=11.6,
            alignment=TA_RIGHT,
            textColor=colors.black,
        )
        style_proj_left = ParagraphStyle(
            "CvProjLeft",
            fontName="Helvetica",
            fontSize=9.5,
            leading=12.4,
            alignment=TA_LEFT,
            textColor=colors.black,
        )
        style_bullet = ParagraphStyle(
            "CvBullet",
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.0,
            alignment=TA_JUSTIFY,
            leftIndent=13,
            firstLineIndent=-8,
            textColor=colors.black,
            spaceAfter=1.8,
        )
        style_subbullet = ParagraphStyle(
            "CvSubBullet",
            fontName="Helvetica-Bold",
            fontSize=9.0,
            leading=11.5,
            alignment=TA_LEFT,
            leftIndent=24,
            firstLineIndent=-8,
            textColor=colors.black,
            spaceAfter=2.5,
        )
        style_skill_row = ParagraphStyle(
            "CvSkillRow",
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.2,
            alignment=TA_JUSTIFY,
            leftIndent=6,
            textColor=colors.black,
            spaceAfter=3.0,
        )

        story = []

        # 1. Parse \begin{center} ... \end{center} Header Block
        center_m = re.search(r"\\begin\{center\}([\s\S]*?)\\end\{center\}", body)
        if center_m:
            center_content = center_m.group(1)
            # Split header into logical rows by \\, \vspace{...}, or newlines
            raw_rows = re.split(r"\\\\|\\vspace\{[^}]*\}|\n", center_content)
            header_rows = [r.strip() for r in raw_rows if _clean_latex_inline(r).strip()]
            if len(header_rows) >= 1:
                story.append(Paragraph(_latex_to_reportlab_xml(header_rows[0]), style_name))
            if len(header_rows) >= 2:
                story.append(Paragraph(_latex_to_reportlab_xml(header_rows[1]), style_loc))
            if len(header_rows) >= 3:
                contact_raw = " ~ ".join(header_rows[2:])
                contact_parts = [
                    _latex_to_reportlab_xml(p.strip())
                    for p in contact_raw.split("~")
                    if _clean_latex_inline(p).strip()
                ]
                if contact_parts:
                    story.append(Paragraph(" &nbsp;~&nbsp; ".join(contact_parts), style_contact))

        # 2. Split body by \section{...}
        sec_matches = list(re.finditer(r"\\section\*?\{([^}]*)\}", body))
        for s_idx, sec_m in enumerate(sec_matches):
            sec_title = _clean_latex_inline(sec_m.group(1)).upper()
            sec_start = sec_m.end()
            sec_end = sec_matches[s_idx + 1].start() if s_idx + 1 < len(sec_matches) else len(body)
            sec_body = body[sec_start:sec_end]

            story.append(Paragraph(sec_title, style_section))
            story.append(
                HRFlowable(
                    width="100%",
                    thickness=0.8,
                    color=colors.black,
                    spaceBefore=1,
                    spaceAfter=6,
                )
            )

            sec_low = sec_title.lower()

            # A. PROFILE SECTION
            if "profile" in sec_low or "summary" in sec_low:
                prof_xml = _latex_to_reportlab_xml(sec_body)
                if prof_xml:
                    story.append(Paragraph(prof_xml, style_justify))
                continue

            # B. TECHNICAL SKILLS SECTION
            if "skill" in sec_low:
                # Split by \\ or \vspace
                raw_skill_lines = re.split(r"\\\\|\\vspace\{[^}]*\}", sec_body)
                for r_line in raw_skill_lines:
                    cleaned_check = _clean_latex_inline(r_line)
                    if not cleaned_check or len(cleaned_check) < 3:
                        continue
                    if cleaned_check.lower() in ("item", "normalsize"):
                        continue
                    row_xml = _latex_to_reportlab_xml(r_line)
                    if row_xml:
                        story.append(Paragraph(row_xml, style_skill_row))
                continue

            # C. LANGUAGES SECTION
            if "language" in sec_low:
                lang_lines = re.split(r"\\newline|\\\\|\n", sec_body)
                for l_line in lang_lines:
                    if not _clean_latex_inline(l_line):
                        continue
                    story.append(Paragraph(_latex_to_reportlab_xml(l_line), style_justify))
                continue

            # D. SECTIONS WITH \resumeSubheading AND/OR \resumeProjectHeading (Experience, Projects, Education, Certificates)
            # Tokenize sec_body into ordered macro events
            sub_calls = [
                ("subheading", args, st, en)
                for args, st, en in _extract_balanced_macros(sec_body, "resumeSubheading", 4)
            ]
            proj_calls = [
                ("projheading", args, st, en)
                for args, st, en in _extract_balanced_macros(sec_body, "resumeProjectHeading", 2)
            ]
            all_headings = sorted(sub_calls + proj_calls, key=lambda x: x[2])

            if not all_headings:
                # Fallback for simple bullet/text section
                items = _extract_balanced_macros(sec_body, "resumeItem", 1)
                if items:
                    for args, _, _ in items:
                        story.append(Paragraph(f"• {_latex_to_reportlab_xml(args[0])}", style_bullet))
                else:
                    xml_txt = _latex_to_reportlab_xml(sec_body)
                    if xml_txt:
                        story.append(Paragraph(xml_txt, style_justify))
                continue

            for h_idx, (h_kind, h_args, h_start, h_end) in enumerate(all_headings):
                next_h_start = all_headings[h_idx + 1][2] if h_idx + 1 < len(all_headings) else len(sec_body)
                chunk_after = sec_body[h_end:next_h_start]

                if h_kind == "subheading":
                    c1 = _latex_to_reportlab_xml(h_args[0])
                    c2 = _latex_to_reportlab_xml(h_args[1])
                    c3 = _latex_to_reportlab_xml(h_args[2])
                    c4 = _latex_to_reportlab_xml(h_args[3])

                    rows_data = [[Paragraph(c1, style_sub_left), Paragraph(c2, style_sub_right)]]
                    if _clean_latex_inline(h_args[2]) or _clean_latex_inline(h_args[3]):
                        rows_data.append([Paragraph(c3, style_sub2_left), Paragraph(c4, style_sub2_right)])

                    tbl = Table(rows_data, colWidths=[avail_w * 0.76, avail_w * 0.24])
                    tbl.setStyle(
                        TableStyle([
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 1),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ])
                    )
                    story.append(tbl)
                else:
                    p1 = _latex_to_reportlab_xml(h_args[0])
                    p2 = _latex_to_reportlab_xml(h_args[1])
                    if _clean_latex_inline(h_args[1]):
                        tbl = Table(
                            [[Paragraph(p1, style_proj_left), Paragraph(p2, style_sub_right)]],
                            colWidths=[avail_w * 0.80, avail_w * 0.20],
                        )
                    else:
                        tbl = Table([[Paragraph(p1, style_proj_left)]], colWidths=[avail_w])
                    tbl.setStyle(
                        TableStyle([
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 2),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ])
                    )
                    story.append(tbl)

                # Check for text before \resumeItemListStart (e.g. role intro paragraph, 'Key achievements:', or 'Grade: 3.11/4')
                list_start_m = re.search(r"\\resumeItemListStart", chunk_after)
                pre_list_text = chunk_after[: list_start_m.start()] if list_start_m else chunk_after
                pre_list_clean = re.sub(
                    r"\\(?:resumeSubHeadingListEnd|resumeSubHeadingListStart|vspace\{[^}]*\}|needspace\{[^}]*\}|begin\{samepage\}|end\{samepage\})",
                    "",
                    pre_list_text,
                )
                for pre_line in pre_list_clean.splitlines():
                    cleaned_pre = _clean_latex_inline(pre_line)
                    if cleaned_pre:
                        story.append(Paragraph(_latex_to_reportlab_xml(pre_line), style_justify))

                # Extract \resumeItem{...} and any nested \item \textbf{Stack: ...}
                res_items = _extract_balanced_macros(chunk_after, "resumeItem", 1)
                for r_idx, (r_args, _, r_end) in enumerate(res_items):
                    bullet_xml = _latex_to_reportlab_xml(r_args[0])
                    if bullet_xml:
                        story.append(Paragraph(f"• {bullet_xml}", style_bullet))

                    r_next_start = res_items[r_idx + 1][1] if r_idx + 1 < len(res_items) else len(chunk_after)
                    between_text = chunk_after[r_end:r_next_start]
                    stack_m = re.search(r"\\item\s*(.+)", between_text)
                    if stack_m:
                        stack_xml = _latex_to_reportlab_xml(stack_m.group(1))
                        if stack_xml:
                            story.append(Paragraph(f"- {stack_xml}", style_subbullet))

                story.append(Spacer(1, 3))

        doc.build(story)
        return pdf_path.exists()
    except Exception:
        return False


def is_complete_latex_document(value: str) -> bool:
    """Checks whether the string has documentclass, begin{document}, and end{document}."""
    return all(marker in value for marker in (r"\documentclass", r"\begin{document}", r"\end{document}"))


def latex_content_signature(value: str) -> str:
    """Computes a normalized whitespace-free signature of LaTeX text omitting comments."""
    without_comments = re.sub(r"(?m)(?<!\\)%.*$", "", value)
    return re.sub(r"\s+", "", without_comments)


def split_latex_document(value: str) -> Optional[Tuple[str, str, str]]:
    """Splits LaTeX into preamble, body, and closing document tags."""
    begin_match = re.search(r"\\begin\{document\}", value)
    end_matches = list(re.finditer(r"\\end\{document\}", value))
    if begin_match is None or not end_matches or end_matches[-1].start() < begin_match.end():
        return None
    end_match = end_matches[-1]
    return value[: begin_match.end()], value[begin_match.end() : end_match.start()], value[end_match.start() :]


def preserve_visual_template(base_latex: str, generated_latex: str) -> str:
    """Locks the preamble and document postamble byte-for-byte from the base CV."""
    base_parts = split_latex_document(base_latex)
    generated_parts = split_latex_document(generated_latex)
    if base_parts is None or generated_parts is None:
        raise ValueError("CV must be a complete LaTeX document.")
    return base_parts[0] + generated_parts[1] + base_parts[2]


def latex_format_signature(value: str) -> tuple:
    """Extracts all control sequences and environment tags used in the document body."""
    parts = split_latex_document(value)
    if parts is None:
        return ()
    body = re.sub(r"(?m)(?<!\\)%.*$", "", parts[1])
    return tuple(re.findall(r"\\(?:begin|end)\{[^{}]+\}|\\[a-zA-Z@]+\*?|\\\\", body))


STANDARD_CV_TEMPLATE_TOKENS = {
    r"\begin{center}",
    r"\end{center}",
    r"\begin{justify}",
    r"\end{justify}",
    r"\begin{itemize}",
    r"\end{itemize}",
    r"\begin{samepage}",
    r"\end{samepage}",
    r"\begin{tabular*}",
    r"\end{tabular*}",
    r"\section",
    r"\section*",
    r"\resumeSubheading",
    r"\resumeDualSubheading",
    r"\resumeSubSubheading",
    r"\resumeProjectHeading",
    r"\resumeItem",
    r"\resumeSubItem",
    r"\classesList",
    r"\resumeSubHeadingListStart",
    r"\resumeSubHeadingListEnd",
    r"\resumeItemListStart",
    r"\resumeItemListEnd",
    r"\textbf",
    r"\textit",
    r"\emph",
    r"\underline",
    r"\text",
    r"\textnormal",
    r"\small",
    r"\scriptsize",
    r"\normalsize",
    r"\large",
    r"\LARGE",
    r"\huge",
    r"\scshape",
    r"\raggedright",
    r"\needspace",
    r"\vspace",
    r"\newline",
    r"\hfill",
    r"\item",
    r"\href",
    r"\raisebox",
    r"\faPhone",
    r"\faEnvelope",
    r"\faLinkedin",
    r"\faGithub",
    r"\faGlobe",
    r"\faLink",
    r"\\",
}


def keeps_visual_structure(base_latex: str, generated_latex: str) -> bool:
    """Verifies that generated LaTeX does not introduce commands outside base CV's vocabulary and standard cv(1)(1).tex macros."""
    allowed_tokens = set(latex_format_signature(base_latex)) | STANDARD_CV_TEMPLATE_TOKENS
    generated_tokens = set(latex_format_signature(generated_latex))
    return generated_tokens.issubset(allowed_tokens)


def sanitize_latex_content(value: str) -> str:
    """Sanitizes unescaped ampersands and percent signs, respecting tabular and alignment blocks."""
    unwrapped = unwrap_paragraph_text_macros(value)
    parts = split_latex_document(unwrapped)
    if parts is None:
        return unwrapped
    alignment_environments = ("tabular", "tabular*", "tabularx", "array", "align", "align*", "matrix")
    alignment_depth = 0
    sanitized_lines: List[str] = []
    for line in parts[1].splitlines(keepends=True):
        begins = sum(
            len(re.findall(rf"\\begin\{{{re.escape(environment)}\}}", line))
            for environment in alignment_environments
        )
        ends = sum(
            len(re.findall(rf"\\end\{{{re.escape(environment)}\}}", line))
            for environment in alignment_environments
        )
        active_alignment = alignment_depth > 0 or begins > 0
        cleaned = line
        if not active_alignment:
            cleaned = re.sub(r"(?<!\\)&", r"\\&", cleaned)
        if not cleaned.lstrip().startswith("%"):
            cleaned = re.sub(r"(?<!\\)%", r"\\%", cleaned)
        sanitized_lines.append(cleaned)
        alignment_depth = max(0, alignment_depth + begins - ends)
    return parts[0] + "".join(sanitized_lines) + parts[2]


def find_latex_compiler() -> Optional[Tuple[str, str]]:
    """Finds an installed LaTeX compiler on the system."""
    # Check bundled backend/bin/tectonic.exe first
    bundled_tectonic = Path(__file__).resolve().parents[3] / "bin" / "tectonic.exe"
    if bundled_tectonic.exists():
        return "tectonic", str(bundled_tectonic)
    for candidate in LATEX_COMPILER_CANDIDATES:
        executable = shutil.which(candidate)
        if executable:
            return candidate, executable
    return None


def compile_latex(artifact_folder: Path) -> Tuple[str, List[str], List[str]]:
    """
    Compiles cv.tex into cv.pdf inside artifact_folder.
    Supports tectonic, pdflatex, xelatex, and ReportLab high-fidelity ATS PDF compilation.
    """
    tex_path = (artifact_folder / "cv.tex").resolve()
    pdf_path = (artifact_folder / "cv.pdf").resolve()

    # 0. Always unwrap any single-line \text{...} wrappers in cv.tex before compilation
    try:
        if tex_path.exists():
            source_raw = tex_path.read_text(encoding="utf-8")
            unwrapped_source = unwrap_paragraph_text_macros(source_raw)
            if unwrapped_source != source_raw:
                tex_path.write_text(unwrapped_source, encoding="utf-8")
    except Exception:
        pass

    compiler_info = find_latex_compiler()

    if compiler_info is None:
        if _generate_fallback_ats_pdf(tex_path, pdf_path):
            return "ok", ["Compiled high-fidelity ATS PDF matching cv(1)(1).tex layout and full-width justification."], []
        supported = ", ".join(LATEX_COMPILER_CANDIDATES)
        return "not_installed", [], [f"No supported LaTeX compiler found on system (tried: {supported}). Generated .tex preserved."]

    compiler, compiler_path = compiler_info
    notes: List[str] = []
    errors: List[str] = []

    try:
        compile_tex_path = tex_path
        tectonic_pdf_path = pdf_path

        if compiler == "tectonic":
            source = tex_path.read_text(encoding="utf-8")
            source = re.sub(r"\\input\s*\{glyphtounicode\}", "% glyphtounicode omitted for XeTeX/Tectonic", source)
            source = re.sub(r"\\pdfgentounicode\s*=\s*1", "% pdfgentounicode omitted for XeTeX/Tectonic", source)
            if r"\usepackage{amsmath}" not in source:
                source = re.sub(r"(\\documentclass[^\n]*\n)", r"\1\\usepackage{amsmath}\n", source, count=1)
            source = source.replace(
                r"\begin{document}",
                "% Compatibility for templates that use \\text without amsmath\n"
                r"\providecommand{\text}[1]{#1}"
                "\n"
                r"\begin{document}",
                1,
            )
            # Ensure amsmath and needspace are available for compatibility
            if r"\usepackage{amsmath}" not in source:
                source = re.sub(r"(\\documentclass[^\n]*\n)", r"\1\\usepackage{amsmath}\n", source, count=1)
            if r"\usepackage{needspace}" not in source:
                source = re.sub(r"(\\documentclass[^\n]*\n)", r"\1\\usepackage{needspace}\n", source, count=1)
            source = source.replace(
                r"\begin{document}",
                "% Compatibility for templates that use \\text without amsmath\n"
                r"\providecommand{\text}[1]{#1}"
                "\n"
                r"\begin{document}",
                1,
            )
            # Ensure anti-orphan guards before sections
            source = re.sub(r"\\needspace\{[^{}]*\}\s*\\section", r"\\section", source)
            source = re.sub(r"(\\section\*?\{)", r"\\needspace{6\\baselineskip}\n\1", source)
            source = source.replace(r"\newline", r"\leavevmode\newline")
            compile_tex_path = (artifact_folder / "cv_tectonic.tex").resolve()
            tectonic_pdf_path = (artifact_folder / "cv_tectonic.pdf").resolve()
            compile_tex_path.write_text(source, encoding="utf-8")

        passes = 1 if compiler == "tectonic" else 2
        for _ in range(passes):
            command = (
                [compiler_path, compile_tex_path.name, "--outdir", str(artifact_folder), "--keep-logs"]
                if compiler == "tectonic"
                else [compiler_path, "-interaction=nonstopmode", "-halt-on-error", tex_path.name]
            )
            result = subprocess.run(
                command,
                cwd=artifact_folder,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "LaTeX compilation failed.").strip()[-1500:]
                return "failed", notes, [f"LaTeX compilation failed: {detail}"]

        if compiler == "tectonic" and tectonic_pdf_path.exists():
            shutil.copyfile(tectonic_pdf_path, pdf_path)

    except OSError as exc:
        return "failed", notes, [f"LaTeX compilation could not start: {exc}"]

    if not pdf_path.exists():
        errors.append("LaTeX compilation finished without producing cv.pdf.")
        return "failed", notes, errors

    notes.append(f"LaTeX compiled successfully using {compiler}.")
    return "ok", notes, errors
