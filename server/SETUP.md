# Robots Daily Generator — Setup

## Install

```bash
# clone to your server
git clone https://github.com/GeorgeGally/robots.git ~/robots
cd ~/robots
bash install.sh
```

## Server dependencies

```bash
python3 -m pip install requests python-dotenv
```

## Configure AI

```bash
robots -ai
```

This saves your OpenRouter API key to `~/.robots_ai_env` and offers to install a daily cron job.

Alternatively, create `~/.robots_ai_env` manually:

```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Set permissions: `chmod 600 ~/.robots_ai_env`

## Environment variables

All configurable via environment or `~/.robots_ai_env`:

| Variable | Default | Description |
|---|---|---|
| `ROBOTS_ENV` | `~/.robots_ai_env` | Path to env file with API key |
| `ROBOTS_TXT` | (auto) | Full path to robots.txt (overrides SITE_ROOT) |
| `ROBOTS_SITE_ROOT` | `~/public_html` | Directory containing robots.txt |
| `ROBOTS_LOG` | (empty) | Path to Apache/Nginx access log for crawler stats |

## Cron job

`robots -ai` will offer to install this automatically:

```
0 3 * * * /path/to/robots generate >> $HOME/.robots-generate.log 2>&1
```

Or add manually:

```bash
crontab -e
# add the line above (use `which robots` to get the path)
```

## First run

```bash
robots -generate
```

This uses the full generator (memory, crawler logs, haiku). Verify output:

```bash
cat $(robots -setup 2>/dev/null || echo ~/public_html)/robots.txt
cat ~/robots/server/generate.log
cat ~/robots/server/memory.md
```