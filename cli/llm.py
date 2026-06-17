#!/usr/bin/env python3
import os, sys, json
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

CONFIG_PATH = os.environ.get("ROBOTS_AI_ENV", os.path.expanduser("~/.robots_ai_env"))


def read_config():
    config = {}
    try:
        with open(CONFIG_PATH) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    config[key.strip()] = val.strip()
    except FileNotFoundError:
        pass
    return config


def call_llm(api_key, prompt):
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
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            if "choices" not in data or not data["choices"]:
                if attempt < 2:
                    continue
                raise RuntimeError(f"LLM returned no choices: {json.dumps(data)}")
            content = data["choices"][0]["message"]["content"]
            if content and content.strip():
                return content.strip()
            if attempt < 2:
                continue
            raise RuntimeError(f"LLM returned empty content: {json.dumps(data)}")
        except requests.exceptions.HTTPError:
            if attempt == 2:
                raise
        except requests.exceptions.Timeout:
            if attempt == 2:
                raise RuntimeError("LLM request timed out after 3 attempts")
    raise RuntimeError("LLM returned empty content after 3 attempts")


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
