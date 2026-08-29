from __future__ import annotations

import shutil
import subprocess
import warnings
from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
from matplotlib.figure import Figure

from axiomfig.typography import apply_figure_typography, discover_fonts


class RenderError(RuntimeError):
    """Raised when the deterministic renderer cannot produce both deliverables."""


@dataclass(frozen=True)
class RenderResult:
    pdf: Path
    png: Path
    workdir: Path
    intermediate_pdf: Path
    tex: Path
    log: Path
    tectonic_command: tuple[str, ...]


def standalone_tex(intermediate_name: str) -> str:
    return (
        "\\documentclass[border=0pt]{standalone}\n"
        "\\usepackage{graphicx}\n"
        "\\begin{document}\n"
        f"\\includegraphics{{{intermediate_name}}}\n"
        "\\end{document}\n"
    )


def _resolve_executable(value: str, label: str) -> str:
    candidate = shutil.which(value)
    if candidate is None and Path(value).is_file():
        candidate = str(Path(value).resolve())
    if candidate is None:
        raise RenderError(f"{label} executable is unavailable: {value}")
    return candidate


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
        raise RenderError(
            f"{label} failed with exit code {completed.returncode}\n"
            f"Command: {' '.join(command)}\n{completed.stdout}"
        )
    return completed


def render_figure(
    figure: Figure,
    output_stem: Path,
    *,
    work_root: Path | None = None,
    tectonic: str = "tectonic",
    pdftoppm: str = "pdftoppm",
    preview_dpi: int = 300,
    typography: str = "sans",
) -> RenderResult:
    discover_fonts(mode=typography)
    tectonic_bin = _resolve_executable(tectonic, "Tectonic")
    pdftoppm_bin = _resolve_executable(pdftoppm, "pdftoppm")
    output_stem = Path(output_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)

    root = Path(work_root) if work_root is not None else output_stem.parent / "tmp"
    workdir = root / output_stem.name
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)

    intermediate_pdf = workdir / "intermediate.pdf"
    tex_path = workdir / "wrapper.tex"
    tex_path.write_text(standalone_tex(intermediate_pdf.name), encoding="utf-8")

    style_root = Path(__file__).resolve().parents[2] / "styles"
    style_path = style_root / "typography" / f"{typography}.mplstyle"
    style_params = mpl.rc_params_from_file(
        style_path, fail_on_error=True, use_default_template=False
    )
    style_params.update(
        mpl.rc_params_from_file(
            style_root / "rendering" / "vector.mplstyle",
            fail_on_error=True,
            use_default_template=False,
        )
    )
    with mpl.rc_context(rc=style_params), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        apply_figure_typography(figure, mode=typography)
        figure.savefig(intermediate_pdf, format="pdf")
    glyph_warnings = [str(item.message) for item in caught if "Glyph" in str(item.message)]
    if glyph_warnings:
        raise RenderError("Matplotlib reported missing glyphs:\n" + "\n".join(glyph_warnings))

    command = [
        tectonic_bin,
        "--outdir",
        str(workdir),
        "--keep-logs",
        "--keep-intermediates",
        tex_path.name,
    ]
    completed = _run(command, cwd=workdir, label="Tectonic")
    compiled_pdf = workdir / "wrapper.pdf"
    if not compiled_pdf.is_file() or compiled_pdf.stat().st_size == 0:
        raise RenderError(f"Tectonic did not create a non-empty PDF: {compiled_pdf}")

    final_pdf = output_stem.with_suffix(".pdf")
    final_png = output_stem.with_suffix(".png")
    shutil.copy2(compiled_pdf, final_pdf)

    preview_prefix = workdir / "preview"
    _run(
        [
            pdftoppm_bin,
            "-f",
            "1",
            "-singlefile",
            "-png",
            "-r",
            str(preview_dpi),
            str(final_pdf),
            str(preview_prefix),
        ],
        cwd=workdir,
        label="Poppler preview",
    )
    preview_path = preview_prefix.with_suffix(".png")
    if not preview_path.is_file() or preview_path.stat().st_size == 0:
        raise RenderError(f"Poppler did not create a non-empty preview: {preview_path}")
    shutil.copy2(preview_path, final_png)

    log_path = workdir / "wrapper.log"
    if not log_path.exists():
        log_path.write_text(completed.stdout, encoding="utf-8")

    return RenderResult(
        pdf=final_pdf,
        png=final_png,
        workdir=workdir,
        intermediate_pdf=intermediate_pdf,
        tex=tex_path,
        log=log_path,
        tectonic_command=tuple(command),
    )
