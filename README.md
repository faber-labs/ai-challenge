# AI Engineer: take-home challenge

**Start with [CHALLENGE.md](CHALLENGE.md)**: it explains the client's need, what we ask, and how we review it.

This README covers how to run what is in the repository.

Deliver a functional product with a complete workflow from drawing submission to
rendered results and STEP files, an improved agent, evidence from experiments,
concurrent execution with isolated runs, and saved traces.
The product must have a UI usable without technical knowledge. Include a short technical write-up with an
answer to the client. The starter only provides a single-call reconstruction:
the agent loop, evaluation, and concurrency are yours to design. See
CHALLENGE.md for expectations.

## Getting started

You need [uv](https://docs.astral.sh/uv/). Python 3.12 and every dependency are installed by the first command.

```bash
uv sync
uv run python solve.py cases/tier1/01/drawing.pdf
```

Before running, copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` to the
key we sent you. An existing environment variable takes precedence.

The starter makes one call to `openai/gpt-6-luna` through OpenRouter, executes
the generated CadQuery script, and renders a PNG with [CadQuery's viewer](https://cadquery.readthedocs.io/en/stable/vis.html#screenshots).
For PDF input, every page is rasterized and sent in the same call. PNG and JPEG
inputs are also accepted. Some cases span several sheets: always use the complete PDF
when evaluating your own harness.
Each run saves `model.py`, `model.step`, and `render.png` in a new folder under
`.screenshots/`. It stops on errors; there is no repair loop.

The cost of each call in USD is printed immediately, even if CAD generation fails.
OpenRouter's [reported usage](https://openrouter.ai/docs/cookbook/administration/usage-accounting)
is saved as `usage.json` in the run folder, including cost, token counts, and the
generation ID. If no cost is reported, it is shown as unavailable, not zero.

Pass a second argument to choose the STEP output path:
`uv run python solve.py cases/tier1/01/drawing.pdf out.step`.

`solve.py` runs the scripts the model writes on your machine, in a child process, with no sandbox.

## Cases

`cases/` contains **four tiers of increasing difficulty**, from `tier1` to `tier4`,
with **eight cases per tier**, numbered `01` to `08`. Each case contains a drawing
(`drawing.pdf`) and its reference STEP part (`reference.step`).

Everything here is a starting point. Choose your own interface and document how to run it (see CHALLENGE.md).
