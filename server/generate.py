import os
import re
import sys
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

BASE_DIR = Path(__file__).parent.resolve()

ENV_PATH = os.environ.get("ROBOTS_ENV", str(Path.home() / ".robots_ai_env"))
_robots_txt = os.environ.get("ROBOTS_TXT", "")
if _robots_txt:
    SITE_ROOT = str(Path(_robots_txt).resolve().parent)
else:
    _site_root = os.environ.get("ROBOTS_SITE_ROOT", "")
    SITE_ROOT = _site_root or str(Path.home() / "public_html")
MEMORY_PATH = BASE_DIR / "memory.md"
GENERATE_LOG = BASE_DIR / "generate.log"
TODAY = datetime.now().strftime("%Y-%m-%d")


def load_env():
    load_dotenv(ENV_PATH)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY not found in config")
    return api_key


def read_memory():
    path = MEMORY_PATH
    if not path.exists():
        return ""

    text = path.read_text()
    entries = text.strip().split("\n---\n")
    last_30 = entries[-30:]
    return "\n---\n".join(last_30)


def call_llm(api_key, user_prompt):
    for attempt in range(3):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/GeorgeGally/robots",
                    "X-Title": "Robots",
                },
                json={
                    "model": "openrouter/free",
                    "messages": [
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.8,
                    "max_tokens": 600,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            if "choices" not in data or not data["choices"]:
                if attempt < 2:
                    continue
                raise RuntimeError(f"LLM returned no choices")
            message = data["choices"][0]["message"]
            content = message.get("content") or ""
            if content and content.strip():
                return extract_robots_txt(content.strip())
        except Exception:
            if attempt == 2:
                raise
    raise RuntimeError("LLM returned empty content")


def extract_robots_txt(content):
    import re
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
    lines = content.strip().split("\n")
    result_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'(?i)^(?:let me|i need to|i should|the task|from the last|current|i have \d|actually|or more|let\'s)', stripped):
            continue
        result_lines.append(stripped)
    return "\n".join(result_lines[:10]).strip() if result_lines else content


def validate_output(content):
    return bool(content and content.strip())


def write_robots_txt(content):
    robots_path = Path(SITE_ROOT) / "robots.txt"
    robots_path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=robots_path.parent, prefix="robots.tmp.")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.chmod(tmp_path, 0o644)
        shutil.move(tmp_path, robots_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def parse_generated_content(content):
    lines = content.strip().split("\n")

    bar = ""
    haiku = []
    disallows = []
    crawlers_seen = set()
    state = "bar"

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("#"):
            text = stripped.lstrip("#").strip()
            if not text:
                continue
            if state == "bar":
                bar = text
                state = "haiku"
            elif state == "haiku" and len(haiku) < 3:
                haiku.append(text)
                if len(haiku) == 3:
                    state = "directives"

        elif stripped.startswith("User-agent:"):
            agent = stripped.split(":", 1)[1].strip()
            if agent != "*":
                crawlers_seen.add(agent)

        elif stripped.startswith("Disallow:"):
            path = stripped.split(":", 1)[1].strip()
            if path:
                disallows.append(path)

    return bar, haiku, disallows, crawlers_seen


def append_to_memory(bar, haiku, disallows, crawlers_seen, notes=""):
    entry = f"\n## {TODAY}\n\n"
    entry += f"### bar\n{bar}\n\n"
    entry += f"### haiku\n"
    for line in haiku:
        entry += f"{line}\n"
    entry += "\n"
    entry += f"### disallows\n"
    for path in disallows:
        entry += f"{path}\n"
    entry += "\n"
    entry += f"### crawlers seen\n{', '.join(sorted(crawlers_seen))}\n\n"
    entry += f"### notes\n{notes}\n"

    with open(MEMORY_PATH, "a") as f:
        f.write(entry)
        f.write("\n---\n")


def trim_memory(max_entries=90):
    if not MEMORY_PATH.exists():
        return

    text = MEMORY_PATH.read_text()
    entries = text.strip().split("\n---\n")
    if len(entries) <= max_entries:
        return

    kept = entries[-max_entries:]
    MEMORY_PATH.write_text("\n---\n".join(kept) + "\n")


def log_result(crawlers_seen, bar_line, success=True):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    crawlers = ", ".join(sorted(crawlers_seen)) if crawlers_seen else "none"
    status = "OK" if success else "FAIL"
    line = f"[{timestamp}] {status} | crawlers: {crawlers} | bar: {bar_line}\n"

    with open(GENERATE_LOG, "a") as f:
        f.write(line)

    if GENERATE_LOG.exists() and GENERATE_LOG.stat().st_size > 1024 * 1024:
        log_path = GENERATE_LOG
        rotated = log_path.with_suffix(".log.1")
        shutil.move(log_path, rotated)


def main():
    api_key = load_env()
    memory = read_memory()

    user_prompt = USER_PROMPT_TEMPLATE.format(
        memory_contents=memory or "",
    )

    try:
        content = call_llm(api_key, user_prompt)
    except Exception as e:
        bar_line = f"LLM call failed: {e}"
        log_result(set(), bar_line, success=False)
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not validate_output(content):
        bar_line = content.split("\n")[0].lstrip("#").strip() if content else "(empty)"
        log_result(set(), f"validation failed — {bar_line}", success=False)
        first_line = content.split("\n")[0] if content else ""
        print("ERROR: Generated content failed validation", file=sys.stderr)
        print(f"First line: {first_line}", file=sys.stderr)
        print("The LLM may have returned thinking/explanation instead of robots.txt.", file=sys.stderr)
        print("Try: robots -ai  (to reconfigure with a different prompt)", file=sys.stderr)
        sys.exit(1)

    write_robots_txt(content)

    bar, haiku, disallows, crawlers_seen = parse_generated_content(content)
    append_to_memory(bar, haiku, disallows, crawlers_seen)
    trim_memory()

    log_result(crawlers_seen, bar)
    print(f"OK | {TODAY} | {bar}")


if __name__ == "__main__":
    main()
