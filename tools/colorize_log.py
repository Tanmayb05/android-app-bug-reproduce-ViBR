#!/usr/bin/env python3
"""Render structured run logs as color-coded HTML files."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


LINE_RE = re.compile(
    r"^\[(?P<time>[^\]]+)\] \[(?P<level>[A-Z]+)\] \[(?P<logger>[^\]]+)\] (?P<msg>.*)$"
)

KEYWORD_CLASSES = [
    (re.compile(r"\b(successful|completed|same_state\"\s*:\s*\"yes)\b", re.I), "ok"),
    (re.compile(r"\b(WARNING|warn|mismatch|Skipping action|Attempting to align state)\b", re.I), "warn"),
    (re.compile(r"\b(ERROR|failed|failure|Exception|Traceback|timeout|impossible)\b", re.I), "err"),
    (re.compile(r"\b(404 Not Found|EntryNotFound|no action)\b", re.I), "bad"),
    (re.compile(r"\b(tap|input_text|swipe|long_press|predicted_action|execute_action)\b", re.I), "action"),
    (re.compile(r"\b(Processing segment \d+|RUN CONFIGURATION|RUN SUMMARY)\b", re.I), "section"),
]

HTTP_RE = re.compile(r"(HTTP/1\.1\s+)([1-5]\d\d)(\s+[A-Za-z ]+)")
STATUS_RE = re.compile(r"Status:\s*(?P<status>\S+)")


def span(class_name: str, text: str) -> str:
    return f'<span class="{class_name}">{text}</span>'


def highlight_message(raw_message: str) -> str:
    escaped = html.escape(raw_message)

    def http_repl(match: re.Match[str]) -> str:
        prefix, code, suffix = match.groups()
        status_class = {
            "1": "http-info",
            "2": "http-ok",
            "3": "http-redirect",
            "4": "http-bad",
            "5": "http-err",
        }[code[0]]
        return f"{prefix}{span(status_class, code)}{suffix}"

    escaped = HTTP_RE.sub(http_repl, escaped)
    for pattern, class_name in KEYWORD_CLASSES:
        escaped = pattern.sub(lambda m: span(class_name, m.group(0)), escaped)
    return escaped


def render_line(line_number: int, line: str) -> str:
    line = line.rstrip("\n")
    match = LINE_RE.match(line)
    if not match:
        return (
            f'<div class="line raw" id="L{line_number}">'
            f'<a class="ln" href="#L{line_number}">{line_number}</a>'
            f'<span class="content">{highlight_message(line)}</span></div>'
        )

    parts = match.groupdict()
    level = parts["level"].lower()
    logger = html.escape(parts["logger"])
    message = highlight_message(parts["msg"])
    return (
        f'<div class="line level-{level}" id="L{line_number}">'
        f'<a class="ln" href="#L{line_number}">{line_number}</a>'
        f'<span class="time">[{html.escape(parts["time"])}]</span> '
        f'<span class="level">[{html.escape(parts["level"])}]</span> '
        f'<span class="logger">[{logger}]</span> '
        f'<span class="message">{message}</span></div>'
    )


def output_name_for(source: Path) -> str:
    return f"{source.parent.name}-{source.stem}.html"


def summarize(source: Path, lines: list[str], output: Path) -> dict[str, str | int]:
    text = "".join(lines)
    status_match = STATUS_RE.search(text)
    return {
        "app": source.parent.name,
        "name": source.stem,
        "source": str(source),
        "file": output.name,
        "lines": len(lines),
        "warnings": len(re.findall(r"\[WARNING\]|\bWARNING\b", text)),
        "errors": len(re.findall(r"\[ERROR\]|\[CRITICAL\]|\bException\b|\bTraceback\b", text)),
        "http_bad": len(re.findall(r"HTTP/1\.1 [45]\d\d", text)),
        "status": status_match.group("status") if status_match else "unknown",
    }


def render_html(source: Path) -> tuple[str, dict[str, str | int]]:
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines(True)
    rendered_lines = "\n".join(render_line(index, line) for index, line in enumerate(lines, 1))
    title = html.escape(f"{source.parent.name} / {source.name}")
    metadata = summarize(source, lines, Path(output_name_for(source)))
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b0f14;
      --panel: #111821;
      --text: #d7dde5;
      --muted: #7f8b99;
      --line: #1e2a36;
      --debug: #8091a7;
      --info: #8ccdf6;
      --warn: #ffd166;
      --err: #ff6b6b;
      --ok: #57d68d;
      --action: #c4a7ff;
      --section: #f7c59f;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 13px/1.5 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }}

    header {{
      position: sticky;
      top: 0;
      z-index: 2;
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 14px 18px;
      border-bottom: 1px solid #263443;
      background: rgba(11, 15, 20, 0.96);
      backdrop-filter: blur(8px);
    }}

    h1 {{
      margin: 0;
      font-size: 15px;
      font-weight: 700;
      color: #f2f5f8;
    }}

    .meta, .legend {{ color: var(--muted); }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 10px; margin-left: auto; }}
    .chip {{ padding: 2px 7px; border: 1px solid #324457; border-radius: 999px; }}

    main {{
      min-width: max-content;
      padding: 12px 0 36px;
    }}

    .line {{
      display: grid;
      grid-template-columns: 58px max-content max-content max-content 1fr;
      gap: 7px;
      padding: 1px 16px 1px 0;
      border-left: 4px solid transparent;
      white-space: pre;
    }}

    .line:hover {{ background: #17212c; }}
    .ln {{
      padding-right: 10px;
      color: #586678;
      text-align: right;
      text-decoration: none;
      user-select: none;
    }}
    .time {{ color: #7c8da1; }}
    .level {{ font-weight: 700; }}
    .logger {{ color: #aab4c0; }}

    .level-debug {{ color: var(--debug); }}
    .level-debug .level {{ color: #6f8198; }}
    .level-info .level {{ color: var(--info); }}
    .level-warning {{
      background: rgba(255, 209, 102, 0.08);
      border-left-color: var(--warn);
    }}
    .level-warning .level, .warn {{ color: var(--warn); font-weight: 700; }}
    .level-error, .level-critical {{
      background: rgba(255, 107, 107, 0.12);
      border-left-color: var(--err);
    }}
    .level-error .level, .level-critical .level, .err, .bad {{ color: var(--err); font-weight: 700; }}

    .ok, .http-ok {{ color: var(--ok); font-weight: 700; }}
    .http-info {{ color: #9ecbff; font-weight: 700; }}
    .http-redirect {{ color: #f7c59f; font-weight: 700; }}
    .http-bad, .http-err {{ color: var(--err); font-weight: 700; }}
    .action {{ color: var(--action); font-weight: 700; }}
    .section {{ color: var(--section); font-weight: 800; }}

    .raw {{
      grid-template-columns: 58px 1fr;
      color: #d6d3bd;
    }}

    @media (max-width: 900px) {{
      header {{ align-items: flex-start; flex-direction: column; gap: 8px; }}
      .legend {{ margin-left: 0; }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>{title}</h1>
      <div class="meta">{len(lines)} lines · source: {html.escape(str(source))}</div>
    </div>
    <div class="legend">
      <span class="chip" style="color: var(--info)">INFO</span>
      <span class="chip" style="color: var(--warn)">WARNING</span>
      <span class="chip" style="color: var(--err)">ERROR / 404</span>
      <span class="chip" style="color: var(--action)">actions</span>
      <span class="chip" style="color: var(--ok)">success</span>
    </div>
  </header>
  <main>
{rendered_lines}
  </main>
</body>
</html>
"""
    return document, metadata


def render_index(items: list[dict[str, str | int]]) -> str:
    options = "\n".join(
        f'        <option value="{html.escape(str(item["file"]))}">'
        f'{html.escape(str(item["app"]))} / {html.escape(str(item["name"]))}'
        f' · {item["lines"]} lines · {item["warnings"]} warnings · {item["http_bad"]} HTTP 4xx/5xx'
        f'</option>'
        for item in items
    )
    rows = "\n".join(
        f"""      <tr>
        <td>{html.escape(str(item["app"]))}</td>
        <td><a href="{html.escape(str(item["file"]))}" target="log-frame">{html.escape(str(item["name"]))}</a></td>
        <td>{item["lines"]}</td>
        <td>{item["warnings"]}</td>
        <td>{item["errors"]}</td>
        <td>{item["http_bad"]}</td>
        <td>{html.escape(str(item["status"]))}</td>
      </tr>"""
        for item in items
    )
    first = html.escape(str(items[0]["file"])) if items else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Run Logs</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b0f14;
      --panel: #111821;
      --text: #d7dde5;
      --muted: #8492a3;
      --line: #263443;
      --accent: #8ccdf6;
      --warn: #ffd166;
      --err: #ff6b6b;
      --ok: #57d68d;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    header {{
      display: grid;
      grid-template-columns: minmax(260px, 1fr) auto;
      gap: 16px;
      align-items: end;
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
      background: #0e141b;
    }}

    h1 {{
      margin: 0 0 4px;
      font-size: 20px;
      letter-spacing: 0;
    }}

    .meta {{ color: var(--muted); }}

    label {{
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}

    select {{
      width: min(760px, 80vw);
      padding: 9px 12px;
      border: 1px solid #385066;
      border-radius: 6px;
      background: #151f2a;
      color: var(--text);
      font: inherit;
    }}

    .content {{
      display: grid;
      grid-template-columns: 420px 1fr;
      min-height: calc(100vh - 86px);
    }}

    aside {{
      overflow: auto;
      border-right: 1px solid var(--line);
      background: var(--panel);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}

    th, td {{
      padding: 8px 10px;
      border-bottom: 1px solid #1f2b37;
      text-align: left;
      white-space: nowrap;
    }}

    th {{
      position: sticky;
      top: 0;
      background: #141d27;
      color: var(--muted);
      z-index: 1;
    }}

    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    iframe {{
      width: 100%;
      height: calc(100vh - 86px);
      border: 0;
      background: #0b0f14;
    }}

    @media (max-width: 1000px) {{
      header {{ grid-template-columns: 1fr; align-items: start; }}
      select {{ width: 100%; }}
      .content {{ grid-template-columns: 1fr; }}
      aside {{ max-height: 280px; border-right: 0; border-bottom: 1px solid var(--line); }}
      iframe {{ height: calc(100vh - 360px); min-height: 520px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Run Logs</h1>
      <div class="meta">{len(items)} colorized logs generated from <code>apps/</code></div>
    </div>
    <div>
      <label for="log-select">Select log</label>
      <select id="log-select">
{options}
      </select>
    </div>
  </header>
  <div class="content">
    <aside>
      <table>
        <thead>
          <tr>
            <th>App</th>
            <th>Log</th>
            <th>Lines</th>
            <th>Warn</th>
            <th>Err</th>
            <th>HTTP</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </aside>
    <iframe id="log-frame" name="log-frame" src="{first}" title="Selected log"></iframe>
  </div>
  <script>
    const select = document.getElementById("log-select");
    const frame = document.getElementById("log-frame");

    select.addEventListener("change", () => {{
      frame.src = select.value;
      history.replaceState(null, "", `#${{select.value}}`);
    }});

    const initial = location.hash.slice(1);
    if (initial) {{
      const option = Array.from(select.options).find((item) => item.value === initial);
      if (option) {{
        select.value = initial;
        frame.src = initial;
      }}
    }}
  </script>
</body>
</html>
"""


def write_log_html(source: Path, output: Path) -> dict[str, str | int]:
    document, metadata = render_html(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    metadata["file"] = output.name
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--index", action="store_true", help="write index.html in the output directory")
    args = parser.parse_args()

    if args.output and len(args.source) > 1:
        parser.error("--output can only be used with one source")
    if args.index and not args.output_dir:
        parser.error("--index requires --output-dir")

    items: list[dict[str, str | int]] = []
    for source in args.source:
        if args.output:
            output = args.output
        elif args.output_dir:
            output = args.output_dir / output_name_for(source)
        else:
            output = source.with_suffix(".html")
        items.append(write_log_html(source, output))
        print(output)

    if args.index and args.output_dir:
        items.sort(key=lambda item: (str(item["app"]), str(item["name"])))
        index = args.output_dir / "index.html"
        index.write_text(render_index(items), encoding="utf-8")
        print(index)


if __name__ == "__main__":
    main()
