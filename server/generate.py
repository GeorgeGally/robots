import os
import re
import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from prompts import USER_PROMPT_TEMPLATE

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
        return []

    text = path.read_text()
    lines = text.strip().split("\n")
    posts = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("/") and stripped.endswith("/"):
            posts.append(stripped)
    return posts[-5:]


def call_llm(api_key, user_prompt):
    models = ["openai/gpt-oss-120b:free", "openrouter/free"]
    retries = 2
    for model in models:
        for attempt in range(retries):
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
                        "model": model,
                        "messages": [
                            {"role": "user", "content": user_prompt},
                        ],
                    "temperature": 0.8,
                    "max_tokens": 800,
                    },
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                if "choices" not in data or not data["choices"]:
                    continue
                message = data["choices"][0]["message"]
                content = message.get("content") or ""
                if content and content.strip():
                    return content.strip()
            except Exception:
                pass
    raise RuntimeError("LLM returned empty content")


def parse_llm_response(content):
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
    post = ""
    haiku = []
    for line in content.strip().split("\n"):
        stripped = line.strip()
        if stripped.upper().startswith("POST:"):
            post = stripped.split(":", 1)[1].strip()
        elif stripped.upper().startswith("HAIKU:"):
            haiku.append(stripped.split(":", 1)[1].strip())
    if not post:
        for line in content.strip().split("\n"):
            stripped = line.strip()
            if stripped and not re.match(r'(?i)^(?:let me|i need|i should|the task|from the last|current|i have|actually|or more|let\'s|welcome|here|okay|now|first|note:)', stripped):
                post = stripped
                break
    return post, haiku[:3]


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text


def assemble_robots_txt(post, haiku, previous_posts):
    slug = slugify(post)
    all_posts = previous_posts + [f"/{slug}/"]
    all_posts = all_posts[-5:]
    lines = []
    lines.append("User-agent: robots")
    for p in all_posts:
        lines.append(f"Disallow: {p}")
    lines.append("")
    lines.append("User-agent: *")
    lines.append("Disallow: /")
    if haiku:
        lines.append("")
        for h in haiku:
            lines.append(f"# {h}")
    return "\n".join(lines)



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



def append_to_memory(post, haiku, paths, notes=""):
    entry = f"\n## {TODAY}\n\n"
    entry += f"### post\n{post}\n\n"
    entry += f"### disallows\n"
    for path in paths:
        entry += f"{path}\n"
    entry += "\n"

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


def log_result(post_line, success=True):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "OK" if success else "FAIL"
    line = f"[{timestamp}] {status} | post: {post_line}\n"

    with open(GENERATE_LOG, "a") as f:
        f.write(line)

    if GENERATE_LOG.exists() and GENERATE_LOG.stat().st_size > 1024 * 1024:
        log_path = GENERATE_LOG
        rotated = log_path.with_suffix(".log.1")
        shutil.move(log_path, rotated)


def main():
    api_key = load_env()

    user_prompt = USER_PROMPT_TEMPLATE

    try:
        raw_response = call_llm(api_key, user_prompt)
    except Exception as e:
        post_line = f"LLM call failed: {e}"
        log_result(post_line, success=False)
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    post, haiku = parse_llm_response(raw_response)

    if not post:
        log_result(f"validation failed — {post or '(empty)'}", success=False)
        print("ERROR: Generated content failed validation", file=sys.stderr)
        sys.exit(1)

    slug = slugify(post)
    if not slug:
        log_result(f"empty slug from post: {post!r}", success=False)
        print("ERROR: Post text produced an empty slug", file=sys.stderr)
        sys.exit(1)

    previous = read_memory()
    robots_txt = assemble_robots_txt(post, haiku, previous)
    write_robots_txt(robots_txt)
    append_to_memory(post, [], [f"/{slug}/"])
    trim_memory()

    log_result(post)
    print(f"🤖 {post}")


if __name__ == "__main__":
    main()
