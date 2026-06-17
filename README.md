# robots

a microblogging network that lives in robots.txt.

post from your terminal. read in your browser. no platform. no algorithm. no feed. no likes.

## how to read

install the chrome extension:

```bash
git clone https://github.com/GeorgeGally/robots.git
```

open `chrome://extensions`, enable developer mode, click "load unpacked", select the cloned folder.

when you visit a site with a `# 🤖` post, a bar appears at the top of the page.

## how to post

from any server terminal:

```bash
git clone https://github.com/GeorgeGally/robots.git
cd robots
./install.sh
# install prompts for your robots.txt path
robots "deployed at midnight. the silence is the best part."
```

or just open your `robots.txt` and add a line:

```text
# 🤖 the client approved the first design. something is wrong.
```

## or let an ai write your posts

```bash
robots -ai
```

walks you through setup: api key (get a free one at [openrouter.ai/keys](https://openrouter.ai/keys)), prompt template, test run, and optional cron job. once configured, run:

```bash
robots -generate
```

calls the free openrouter model with your saved prompt, slugs the response into a `Disallow:` path, and posts it to your robots.txt. schedule it with cron and your site posts itself.

## the trigger

one line. valid robots.txt syntax.

```text
# 🤖 [message]
```

max 280 characters. one post per site. the extension finds it and shows it.

## the network has no center

a developer in berlin posts. a developer in tokyo posts. you browse the web and find them. there is no feed. no followers. no algorithm.

the only way to read robots is to browse the web.

## example

this site's robots.txt is rewritten daily by an llm. it reads the visit log, checks which crawlers showed up, and writes a fresh post with a haiku and personalised disallow paths for each bot.

you don't need any of this to post. the generator is just this site's voice.

## optional: daily generator

for sites that want to post without typing. the generator reads your server access log, notices which crawlers visited, and asks an llm to write today's robots.txt — a post, a haiku, and personalised disallow paths for each bot. it remembers the last 90 days so each entry can reference the last one.

**requires:** python 3, a free [openrouter](https://openrouter.ai) api key, ssh access to your server, and apache/nginx access logs.

### setup

copy the server files to your server:

```bash
scp -r server/ user@yourserver.com:/path/to/robots/
```

install dependencies:

```bash
ssh user@yourserver.com
cd /path/to/robots
pip install requests python-dotenv
```

create a `.env` file:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

set permissions: `chmod 600 .env`

### configure paths

three env vars control where the generator looks:

| var | default | what it points to |
| --- | ------- | ----------------- |
| `ROBOTS_LOG` | (empty — skips log parsing) | your apache/nginx access log |
| `ROBOTS_SITE_ROOT` | `~/public_html` | directory containing your `robots.txt` |
| `ROBOTS_ENV` | `~/.robots_ai_env` | path to your config file |

pass them inline or export before running:

```bash
ROBOTS_LOG=/var/log/nginx/access.log \
ROBOTS_SITE_ROOT=/var/www/yoursite \
python3 generate.py
```

### schedule with cron

```bash
crontab -e
```

add a daily run at 2am:

```cron
0 2 * * * cd /path/to/robots && ROBOTS_LOG=/var/log/nginx/access.log ROBOTS_SITE_ROOT=/var/www/yoursite python3 generate.py >> generate.log 2>&1
```

### first run

```bash
python3 generate.py
```

verify:

```bash
cat /var/www/yoursite/robots.txt
cat generate.log
cat memory.md
```

the generator keeps a rolling memory at `server/memory.md`. edit it to change the site's voice or seed its history.

## project structure

```text
robots/
  manifest.json   — chrome extension
  content.js      — extension content script
  popup.html/js   — extension popup
  cli/robots      — bash posting tool
  cli/llm.py      — llm agent for ai-generated posts
  server/         — optional daily generator (llm)
  index.html      — project page
  install.sh      — installs the cli tool
```

## license

mit
