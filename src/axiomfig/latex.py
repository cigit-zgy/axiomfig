from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from axiomfig.validation import extract_pdf_text


class LatexProbeError(RuntimeError):
    """Raised when the standalone scientific LaTeX probe cannot be verified."""


@dataclass(frozen=True)
class LatexProbeResult:
    pdf: Path
    tex: Path
    style: Path
    colors: Path
    log: Path
    extracted_text: str
    fonts: tuple[str, ...]
    tectonic_command: tuple[str, ...]


_PROBE_SOURCE = r"""\documentclass{article}
\usepackage{axiomfig}
\pagestyle{empty}
\begin{document}
\noindent Units marker: \qty{10}{\milli\gram\per\litre}.\par
Chemistry markers: \ce{NH4+}; \ce{NO3-}; \ce{PO4^3-}.\par
Math marker: $\mu_{\max}$, $\alpha$, $\beta$.
\end{document}
"""


def _executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise LatexProbeError(f"Required executable is unavailable: {name}")
    return executable


def _run(command: list[str], *, cwd: Path, label: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise LatexProbeError(
            f"{label} failed with exit code {completed.returncode}\n"
            f"Command: {' '.join(command)}\n{completed.stdout}"
        )
    return completed


def _font_rows(pdf: Path) -> tuple[str, ...]:
    completed = _run([_executable("pdffonts"), str(pdf)], cwd=pdf.parent, label="pdffonts")
    lines = completed.stdout.splitlines()
    divider = next(
        (index for index, line in enumerate(lines) if line.startswith("----------------")),
        None,
    )
    if divider is None:
        raise LatexProbeError(f"Cannot parse pdffonts output for {pdf}:\n{completed.stdout}")
    rows = tuple(line for line in lines[divider + 1 :] if line.strip())
    if not rows:
        raise LatexProbeError(f"pdffonts reported no fonts for {pdf}")
    for row in rows:
        columns = row.split()
        if len(columns) < 5 or columns[-5:-3] != ["yes", "yes"] or "Type 3" in row:
            raise LatexProbeError(f"Font is not embedded and subset in {pdf}: {row}")
    return rows


def compile_latex_probe(output_dir: Path) -> LatexProbeResult:
    """Compile and inspect standalone unit, chemistry, and mathematics semantics."""
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_latex = Path(__file__).resolve().parents[2] / "latex"
    style = output_dir / "axiomfig.sty"
    colors = output_dir / "axiomfig-colors.tex"
    shutil.copy2(source_latex / style.name, style)
    shutil.copy2(source_latex / colors.name, colors)

    tex = output_dir / "probe.tex"
    tex.write_text(_PROBE_SOURCE, encoding="utf-8")
    tectonic_command = (
        _executable("tectonic"),
        "--outdir",
        str(output_dir),
        "--keep-logs",
        "--keep-intermediates",
        tex.name,
    )
    completed = _run(list(tectonic_command), cwd=output_dir, label="Tectonic LaTeX probe")

    pdf = output_dir / "probe.pdf"
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise LatexProbeError(f"Tectonic did not create a non-empty PDF: {pdf}")
    log = output_dir / "probe.log"
    if not log.is_file():
        log.write_text(completed.stdout, encoding="utf-8")

    return LatexProbeResult(
        pdf=pdf,
        tex=tex,
        style=style,
        colors=colors,
        log=log,
        extracted_text=extract_pdf_text(pdf),
        fonts=_font_rows(pdf),
        tectonic_command=tectonic_command,
    )
