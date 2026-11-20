"""Render a merged report (llm-stream-check report ... --json) as docs/results.md.

Usage: python tools/results_md.py report.json docs/results.md
"""

from __future__ import annotations

import collections
import json
import sys


def main(src: str, out: str) -> None:
    with open(src, encoding="utf-8") as fh:
        rep = json.load(fh)
    rows = rep["rows"]
    lines = [
        "# Results",
        "",
        f"Generated {rep['generated']} by {rep['tool']} from the bundled corpus "
        f"({len({r['case'] for r in rows})} recorded streams). Every row below is a recorded provider response "
        "replayed byte for byte through the framework's own streaming code, compared with what the stream said.",
        "",
        "| adapter | versions | streams | lossy | losses |",
        "|---|---|---:|---:|---|",
    ]
    for name, s in sorted(rep["adapters"].items()):
        v = ", ".join(f"{k} {x}" for k, x in s["versions"].items())
        ls = ", ".join(f"{k} {n}" for k, n in sorted(s["losses"].items())) or "none"
        lines.append(f"| `{name}` | {v} | {s['cases']} | {s['cases_with_loss']} | {ls} |")
    lines += [
        "",
        "## Every loss",
        "",
        "Grouped by the recorded stream that caused it. The source link is the recording at a pinned commit.",
        "",
    ]
    by_case: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        if r["losses"]:
            by_case[r["case"]].append(r)
    for case, rs in sorted(by_case.items(), key=lambda kv: -len(kv[1])):
        r0 = rs[0]
        lines.append(f"### `{case}`")
        lines.append("")
        lines.append(f"Provider: {r0['provider']}. Shapes: {', '.join(r0['features'])}. Recording: {r0['source']}")
        lines.append("")
        for r in sorted(rs, key=lambda x: x["adapter"]):
            for x in r["losses"]:
                detail = x["detail"].replace("\n", " ").replace("|", "\\|")[:300]
                lines.append(f"- `{r['adapter']}`: **{x['kind']}**: {detail}")
        lines.append("")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
