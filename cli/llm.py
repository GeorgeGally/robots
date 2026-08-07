#!/usr/bin/env python3
import os, sys, re

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

CONFIG_PATH = os.environ.get("ROBOTS_AI_ENV", os.path.expanduser("~/.robots_ai_env"))


def read_config():
    config = {}
    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    config[key.strip()] = val.strip()
    except FileNotFoundError:
        pass
    return config


def clean_output(content):
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
    lines = content.strip().split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'(?i)^(?:let me|i need to|i should|the task|from the last|current|i have \d|actually|or more|let\'s)', stripped):
            continue
        if stripped.startswith("#") or stripped.lower().startswith("disallow:"):
            return stripped
    first = content.strip().split("\n")[0].strip()
    return first


def call_llm(api_key, prompt):
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
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 300,
                    },
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                if "choices" not in data or not data["choices"]:
                    continue
                message = data["choices"][0]["message"]
                content = message.get("content") or ""
                if content and content.strip():
                    return clean_output(content)
            except (requests.exceptions.HTTPError, requests.exceptions.Timeout) as e:
                print(f"  model {model} attempt {attempt+1}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"  model {model} attempt {attempt+1}: {e}", file=sys.stderr)
    raise RuntimeError("LLM returned empty content")


def main():
    config = read_config()
    api_key = config.get("OPENROUTER_API_KEY", "")
    prompt = config.get("PROMPT_TEMPLATE", "")

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", help="API key override")
    parser.add_argument("--prompt", help="Prompt override")
    args = parser.parse_args()

    if args.key:
        api_key = args.key
    if args.prompt:
        prompt = args.prompt

    if not api_key:
        print("Error: OPENROUTER_API_KEY not configured", file=sys.stderr)
        print("Run: robots ai", file=sys.stderr)
        sys.exit(1)
    if not prompt:
        print("Error: PROMPT_TEMPLATE not configured", file=sys.stderr)
        print("Run: robots ai", file=sys.stderr)
        sys.exit(1)

    try:
        result = call_llm(api_key, prompt)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()
