from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from axiomfig.validation import ValidationError, extract_pdf_text


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

_EXPECTED_TEXT = (
    "Units marker:",
    "10 mg L−1",
    "Chemistry markers:",
    "+ – 3–",
    "NH4",
    "NO3",
    "PO4",
    "Math marker:",
    "𝜇max",
    "𝛼",
    "𝛽",
)


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
        if "Type 3" in row:
            raise LatexProbeError(f"Type 3 font is forbidden in {pdf}: {row}")
        columns = row.split()
        if len(columns) < 8:
            raise LatexProbeError(f"Cannot parse pdffonts row for {pdf}: {row}")
        embedded, subset, unicode_mapping = columns[-5:-2]
        if embedded != "yes" or subset != "yes":
            raise LatexProbeError(f"Font is not embedded and subset in {pdf}: {row}")
        if unicode_mapping != "yes":
            raise LatexProbeError(f"Font has no Unicode mapping in {pdf}: {row}")
    font_names = tuple(row.split()[0] for row in rows)
    if not any("LMRoman" in name for name in font_names) or not any(
        "LatinModernMath" in name for name in font_names
    ):
        raise LatexProbeError(
            f"PDF is missing required Latin Modern fonts: {', '.join(font_names)}"
        )
    return rows


def _validate_semantics(text: str) -> None:
    normalized = " ".join(text.split())
    missing = tuple(expected for expected in _EXPECTED_TEXT if expected not in normalized)
    if missing:
        missing_text = ", ".join(repr(item) for item in missing)
        raise LatexProbeError(f"PDF is missing expected scientific semantics: {missing_text}")


def _resource_bytes(name: str) -> bytes:
    resource = files("axiomfig").joinpath("resources", "latex", name)
    try:
        return resource.read_bytes()
    except FileNotFoundError as error:
        raise LatexProbeError(f"Packaged LaTeX resource is missing: {name}") from error


def _atomic_copy(source: Path, target: Path) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            with source.open("rb") as source_file:
                shutil.copyfileobj(source_file, temporary)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def compile_latex_probe(output_dir: Path) -> LatexProbeResult:
    """Compile, verify, and atomically publish scientific LaTeX probe artifacts."""
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="axiomfig-latex-probe-", dir=output_dir.parent
    ) as temporary_directory:
        workdir = Path(temporary_directory)
        style = workdir / "axiomfig.sty"
        colors = workdir / "axiomfig-colors.tex"
        style.write_bytes(_resource_bytes(style.name))
        colors.write_bytes(_resource_bytes(colors.name))

        tex = workdir / "probe.tex"
        tex.write_text(_PROBE_SOURCE, encoding="utf-8")
        tectonic_command = (
            _executable("tectonic"),
            "--outdir",
            str(workdir),
            "--keep-logs",
            "--keep-intermediates",
            tex.name,
        )
        completed = _run(list(tectonic_command), cwd=workdir, label="Tectonic LaTeX probe")

        pdf = workdir / "probe.pdf"
        if not pdf.is_file() or pdf.stat().st_size == 0:
            raise LatexProbeError(f"Tectonic did not create a fresh non-empty PDF: {pdf}")
        log = workdir / "probe.log"
        if not log.is_file():
            log.write_text(completed.stdout, encoding="utf-8")

        try:
            extracted_text = extract_pdf_text(pdf)
        except ValidationError as error:
            raise LatexProbeError(f"Cannot extract probe PDF text: {error}") from error
        _validate_semantics(extracted_text)
        font_rows = _font_rows(pdf)

        published = {path.name: output_dir / path.name for path in (pdf, tex, style, colors, log)}
        for source_name, target in published.items():
            _atomic_copy(workdir / source_name, target)

    return LatexProbeResult(
        pdf=published["probe.pdf"],
        tex=published["probe.tex"],
        style=published["axiomfig.sty"],
        colors=published["axiomfig-colors.tex"],
        log=published["probe.log"],
        extracted_text=extracted_text,
        fonts=font_rows,
        tectonic_command=tectonic_command,
    )
