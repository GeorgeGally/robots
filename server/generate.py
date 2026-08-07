import os
import re
import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path):
        pass

from prompts import USER_PROMPT_TEMPLATE

MAX_SLUG_LENGTH = 70
SLUG_BAD_PATTERNS = [
    re.compile(r'^your[- ]sentence[- ]with[- ]spaces$', re.I),
    re.compile(r'^user[- ]safety', re.I),
    re.compile(r'we[- ]need[- ]to[- ]produce', re.I),
    re.compile(r'write[- ]a[- ]short[- ]funny[- ]sentence', re.I),
    re.compile(r'cron', re.I),
    re.compile(r'generate', re.I),
]

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

    text = path.read_text(encoding='utf-8')
    lines = text.strip().split("\n")
    posts = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("/") and stripped.endswith("/"):
            posts.append(stripped)
    return posts[-10:]


def call_llm(api_key, user_prompt):
    models = ["openrouter/free"]
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
            except Exception as e:
                print(f"  model {model} attempt {attempt+1}: {e}", file=sys.stderr)
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
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text


def update_robots_txt(post, haiku):
    slug = slugify(post)
    robots_path = Path(SITE_ROOT) / "robots.txt"
    robots_path.parent.mkdir(parents=True, exist_ok=True)

    if robots_path.exists():
        content = robots_path.read_text(encoding='utf-8')
    else:
        content = ""

    existing = []
    match = re.search(r'(?im)^User-agent:\s*Robots\n((?:Disallow:[^\n]*\n)*)', content)
    if match:
        for line in match.group(1).strip().split('\n'):
            m = re.match(r'(?i)Disallow:\s*(.*)', line.strip())
            if m:
                existing.append(m.group(1).strip())

    all_posts = [f"/{slug}/"] + existing
    all_posts = all_posts[:10]

    new_block = "User-agent: robots\n" + "\n".join(f"Disallow: {p}" for p in all_posts) + "\n"

    if content.strip():
        content_cleaned = re.sub(
            r'(?im)^User-agent:\s*Robots\n(?:Disallow:[^\n]*\n)*\n?',
            '', content
        ).lstrip('\n')
        result = new_block + "\n" + content_cleaned
    else:
        result = new_block + "\nUser-agent: *\nDisallow: /\n"

    if haiku:
        result += "\n" + "\n".join(f"# {h}" for h in haiku) + "\n"

    result = re.sub(r'\n(?!\n)(?=User-agent:\s*\*)', '\n\n', result)

    fd, tmp_path = tempfile.mkstemp(dir=robots_path.parent, prefix="robots.tmp.")
    try:
        with os.fdopen(fd, "w", encoding='utf-8') as f:
            f.write(result)
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

    with open(MEMORY_PATH, "a", encoding='utf-8') as f:
        f.write(entry)
        f.write("\n---\n")


def trim_memory(max_entries=90):
    if not MEMORY_PATH.exists():
        return

    text = MEMORY_PATH.read_text(encoding='utf-8')
    entries = text.strip().split("\n---\n")
    if len(entries) <= max_entries:
        return

    kept = entries[-max_entries:]
    MEMORY_PATH.write_text("\n---\n".join(kept) + "\n", encoding='utf-8')


def log_result(post_line, success=True):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "OK" if success else "FAIL"
    line = f"[{timestamp}] {status} | post: {post_line}\n"

    with open(GENERATE_LOG, "a", encoding='utf-8') as f:
        f.write(line)

    if GENERATE_LOG.exists() and GENERATE_LOG.stat().st_size > 1024 * 1024:
        log_path = GENERATE_LOG
        rotated = log_path.with_suffix(".log.1")
        shutil.move(log_path, rotated)


def main():
    api_key = load_env()

    previous = read_memory()
    previous_text = "\n".join(previous) if previous else "(none yet)"
    user_prompt = USER_PROMPT_TEMPLATE.format(previous_paths=previous_text)

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
    if len(slug) > MAX_SLUG_LENGTH:
        log_result(f"slug too long ({len(slug)}): {slug}", success=False)
        print("ERROR: Generated post too long — likely prompt leakage", file=sys.stderr)
        sys.exit(1)
    for pat in SLUG_BAD_PATTERNS:
        if pat.search(slug):
            log_result(f"bad pattern match: {slug}", success=False)
            print(f"ERROR: Generated post matched blocked pattern: {pat.pattern}", file=sys.stderr)
        sys.exit(1)

    update_robots_txt(post, haiku)
    append_to_memory(post, [], [f"/{slug}/"])
    trim_memory()

    log_result(post)
    print(f"🤖 {post}")


if __name__ == "__main__":
    main()
