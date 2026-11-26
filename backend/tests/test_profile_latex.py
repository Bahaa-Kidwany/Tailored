import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.formatters.latex_template import (
    unwrap_paragraph_text_macros,
    enforce_mandatory_sections_in_latex,
    validate_mandatory_latex_sections,
)
from app.ai.formatters.latex_engine import sanitize_latex_content


def test_unwrap_profile_text_macro():
    """Verify that \\text{...} wrapping a profile paragraph inside justify is unwrapped."""
    raw_tex = (
        r"\begin{justify}" + "\n"
        r"\text{\textbf{Senior AI Engineer} Experienced in building resilient machine learning systems, "
        r"distributed training pipelines, and high-throughput microservices using PyTorch and FastAPI.}" + "\n"
        r"\end{justify}"
    )

    unwrapped = unwrap_paragraph_text_macros(raw_tex)

    assert r"\text{" not in unwrapped
    assert r"\begin{justify}" in unwrapped
    assert r"\textbf{Senior AI Engineer}" in unwrapped
    assert "Experienced in building resilient" in unwrapped
    assert unwrapped.endswith(r"\end{justify}")


def test_unwrap_nested_braces():
    r"""Verify that balanced brace counting works with nested macros like \href and \textbf."""
    nested_tex = (
        r"\section{Profile}" + "\n"
        r"\begin{justify}" + "\n"
        r"\text{\textbf{Lead Architect} Contributed to \href{https://github.com/project}{open source} "
        r"and published at \textbf{NeurIPS 2024}.}" + "\n"
        r"\end{justify}"
    )

    unwrapped = unwrap_paragraph_text_macros(nested_tex)

    assert r"\text{" not in unwrapped
    assert r"\href{https://github.com/project}{open source}" in unwrapped
    assert r"\textbf{NeurIPS 2024}" in unwrapped
    # Check brace balance: count of '{' must equal count of '}'
    assert unwrapped.count("{") == unwrapped.count("}")


def test_enforce_mandatory_sections_profile_no_text_wrapper():
    """Verify enforce_mandatory_sections_in_latex does not produce \\text{ in the injected profile."""
    minimal_latex = r"""
\documentclass[11pt]{article}
\begin{document}
\section{Education}
Cairo University
\end{document}
""".strip()

    repaired, notes = enforce_mandatory_sections_in_latex(minimal_latex, job_title="Senior ML Engineer")
    ok, missing = validate_mandatory_latex_sections(repaired)
    assert ok, f"Mandatory sections missing: {missing}"

    # Profile section must NOT wrap the paragraph in \text{
    assert r"\text{\textbf{Senior ML Engineer}" not in repaired
    assert r"\textbf{Senior ML Engineer}" in repaired


def test_sanitize_latex_unwraps_text_macro():
    """Verify sanitize_latex_content strips \\text{...} wrappers."""
    content = r"\begin{justify}\text{\textbf{Role} Bio text that is quite long and multi-sentence.}\end{justify}"
    cleaned = sanitize_latex_content(content)
    assert r"\text{" not in cleaned
    assert r"\textbf{Role}" in cleaned
