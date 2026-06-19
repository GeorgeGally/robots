import os
import re
import sys
import tempfile
import shutil
import random
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
        return ""

    text = path.read_text()
    entries = text.strip().split("\n---\n")
    posts = []
    for entry in entries[-5:]:
        post = ""
        haiku_lines = []
        in_haiku = False
        in_post = False
        for line in entry.strip().split("\n"):
            stripped = line.strip()
            if stripped.lower() == "### post":
                in_post = True
                in_haiku = False
                continue
            if stripped.lower() == "### haiku":
                in_haiku = True
                in_post = False
                continue
            if stripped.startswith("###"):
                in_post = False
                in_haiku = False
                continue
            if in_post and stripped:
                post = stripped
                in_post = False
            if in_haiku and stripped:
                haiku_lines.append(stripped)
        if post:
            posts.append(f'"{post}"')
    return "\n".join(posts) if posts else ""


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
    think_blocks = re.findall(r'<think>(.*?)</think>', content, flags=re.DOTALL)
    think_blocks += re.findall(r'<thinking>(.*?)</thinking>', content, flags=re.DOTALL)
    content_clean = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'<thinking>.*?</thinking>', '', content_clean, flags=re.DOTALL)

    for source in (content_clean, "\n".join(think_blocks)):
        if not source.strip():
            continue

        post = ""
        haiku = []
        lines = source.strip().split("\n")
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r'(?i)^(?:let me|i need to|i should|the task|from the last|current|i have|actually|or more|let\'s|welcome|here is|here\'s|i\'ll|okay|now|first|note:)', stripped):
                continue
            if stripped.startswith("#"):
                text = stripped.lstrip("#").strip()
                text = re.sub(r'[^\x20-\x7E]', '', text).strip()
                if not text:
                    continue
                if not post:
                    post = text
                elif len(haiku) < 3:
                    haiku.append(text)
            elif post and len(haiku) >= 3:
                break

        if post:
            return post, haiku

        post_match = re.search(r'<post>(.*?)</post>', source, re.DOTALL)
        if post_match:
            post = post_match.group(1).strip()
            haiku_match = re.search(r'<haiku>(.*?)</haiku>', source, re.DOTALL)
            haiku = []
            if haiku_match:
                for line in haiku_match.group(1).strip().split("\n"):
                    stripped = line.strip()
                    if stripped:
                        haiku.append(stripped)
            return post, haiku[:3]

    return "", []


PATH_TEMPLATES = [
    "/secret-{word}/",
    "/the-{word}-files/",
    "/hidden-{word}/",
    "/{word}-vault/",
    "/dont-look-at-{word}/",
    "/private-{word}/",
    "/forbidden-{word}/",
    "/robots-cant-see-{word}/",
    "/the-{word}-archives/",
    "/classified-{word}/",
]


def generate_paths(post, haiku, count=3):
    text = (post + " " + " ".join(haiku)).lower()
    words = re.findall(r'[a-z]{4,}', text)
    if not words:
        return ["/secret-corner/", "/hidden-key/", "/private-diaries/"]

    paths = []
    used_words = set()
    for i in range(count):
        available = [w for w in words if w not in used_words]
        if not available:
            available = words
        word = random.choice(available)
        used_words.add(word)
        template = random.choice(PATH_TEMPLATES)
        paths.append(template.format(word=word))

    return paths


def assemble_robots_txt(post, haiku_lines, paths):
    lines = []
    lines.append(f"# {post}")
    lines.append("#")
    for h in haiku_lines:
        lines.append(f"# {h}")
    lines.append("#")
    lines.append("User-agent: *")
    for path in paths:
        lines.append(f"Disallow: {path}")
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
    entry += f"### haiku\n"
    for line in haiku:
        entry += f"{line}\n"
    entry += "\n"
    entry += f"### disallows\n"
    for path in paths:
        entry += f"{path}\n"
    entry += "\n"
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
    memory = read_memory()

    user_prompt = USER_PROMPT_TEMPLATE.format(
        memory_contents=memory or "",
    )

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
        print(f"post={post!r} haiku={haiku!r}", file=sys.stderr)
        sys.exit(1)

    paths = generate_paths(post, haiku)
    robots_txt = assemble_robots_txt(post, haiku, paths)
    write_robots_txt(robots_txt)
    append_to_memory(post, haiku, paths)
    trim_memory()

    log_result(post)
    print(f"OK | {post}")


if __name__ == "__main__":
    main()
