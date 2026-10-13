"""Minimal draw2cad starter: Luna -> CadQuery -> STEP and PNG.

    uv run python solve.py cases/tier1/01/drawing.pdf [out.step]

Set OPENROUTER_API_KEY in .env. Generated code runs without a sandbox.
"""
import base64
import json
import mimetypes
import os
import re
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from openai import OpenAI

MODEL = "openai/gpt-6-luna"
PROMPT = """Reconstruct the mechanical part in this dimensioned engineering drawing.
Write a self-contained Python script using CadQuery, in millimetres.
Import cadquery as cq and assign the final cq.Workplane to `result`.
Do not open a viewer or export files. Reply only with one Python code block."""


def render(script: Path, step: Path, screenshot: Path):
    import cadquery as cq
    from cadquery.vis import show

    namespace = {"__name__": "__main__", "__file__": str(script)}
    exec(compile(script.read_text(encoding="utf-8"), str(script), "exec"), namespace)
    result = namespace["result"]
    if not isinstance(result, cq.Workplane) or not result.solids().size():
        raise ValueError("The script must produce a CadQuery Workplane containing a solid")
    step.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(result, str(step))
    show(result, screenshot=str(screenshot), interact=False, width=1024,
         height=768, trihedron=False, gradient=False)
    if not screenshot.is_file():
        raise RuntimeError("No screenshot was written")


def drawing_content(drawing: Path):
    """Send every sheet of a PDF, or a single raster drawing."""
    images = []
    if drawing.suffix.lower() == ".pdf":
        import pymupdf

        with pymupdf.open(drawing) as document:
            if not len(document):
                raise ValueError("The PDF contains no pages")
            for page in document:
                pixels = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
                images.append(("image/png", pixels.tobytes("png")))
    else:
        mime = mimetypes.guess_type(drawing.name)[0]
        if mime not in ("image/png", "image/jpeg", "image/webp"):
            raise ValueError("Use a PDF, PNG, JPEG, or WebP drawing")
        images.append((mime, drawing.read_bytes()))
    content = [{"type": "text", "text": PROMPT}]
    for page, (mime, data) in enumerate(images, 1):
        image = base64.b64encode(data).decode()
        content.extend([
            {"type": "text", "text": f"Drawing sheet {page} of {len(images)}:"},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image}"}},
        ])
    return content


def solve(drawing: Path, out: Path | None = None):
    load_dotenv(Path(__file__).with_name(".env"))
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("Add OPENROUTER_API_KEY to .env or your environment")
    content = drawing_content(drawing)
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key,
                    timeout=120, max_retries=0)
    reply = client.chat.completions.create(model=MODEL, messages=[{
        "role": "user", "content": content,
    }])
    usage = reply.usage.model_dump() if reply.usage else {}
    cost = usage.get("cost")
    print(f"OpenRouter cost: ${cost:.8f} USD" if cost is not None
          else "OpenRouter cost: unavailable (not reported)", flush=True)
    run = Path(".screenshots") / f"{drawing.parent.name}-{drawing.stem}-{uuid4().hex[:8]}"
    run.mkdir(parents=True)
    (run / "usage.json").write_text(json.dumps({"id": reply.id, "model": MODEL,
                                              "usage": usage}, indent=2), encoding="utf-8")
    text = reply.choices[0].message.content or ""
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.S)
    code = match.group(1) if match else text
    if not code.strip():
        raise ValueError("The model returned no script")
    script, screenshot = run / "model.py", run / "render.png"
    step = (out or run / "model.step").resolve()
    script.write_text(code, encoding="utf-8")
    subprocess.run([sys.executable, str(Path(__file__).resolve()), "--render",
                    str(script.resolve()), str(step), str(screenshot.resolve())],
                   check=True, timeout=180)
    print(f"Script: {script}\nSTEP: {step}\nPNG: {screenshot}")


if __name__ == "__main__":
    try:
        if len(sys.argv) == 5 and sys.argv[1] == "--render":
            render(*map(Path, sys.argv[2:]))
        elif len(sys.argv) in (2, 3):
            solve(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) == 3 else None)
        else:
            sys.exit(__doc__)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
