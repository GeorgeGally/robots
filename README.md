# robots

a microblogging network that lives in robots.txt.

post from your terminal. read in your browser. no platform. no algorithm. no feed. no likes.

## how to read

install the chrome extension:

```bash
git clone https://github.com/GeorgeGally/robots.git
```

open `chrome://extensions`, enable developer mode, click "load unpacked", select the cloned folder.

when you visit a site with a `User-agent: robots` disallow, a bar appears at the top of the page.

## how to post

from any server terminal:

```bash
git clone https://github.com/GeorgeGally/robots.git
cd robots
./install.sh
# install prompts for your robots.txt path
robots "deployed at midnight. the silence is the best part."
```

or just open your `robots.txt` and add a disallow:

```text
User-agent: robots
Disallow: /deployed-at-midnight-the-silence-is-the-best-part/
```

## commands

```bash
robots                    —  interactive prompt (type your post)
robots "your message"     —  post directly
robots -show              —  show current robots.txt
robots -agent <bot> msg   —  block a specific crawler (e.g. robots -agent googlebot stay away)
robots -ai                —  configure ai posting
robots -ai --reset        —  reset api key and prompt
robots -resetprompt       —  reset prompt to default
robots -generate          —  generate a post with ai
robots -cron              —  check or install daily cron
robots -setup [path]      —  set robots.txt path
robots -update            —  pull latest version
robots -h                 —  show help
```

## or let an ai write your posts

```bash
robots -ai
```

walks you through setup: api key (get a free one at [openrouter.ai/keys](https://openrouter.ai/keys)), prompt template, test run, and optional cron job. once configured, run:

```bash
robots -generate
```

calls the free openrouter model, generates a funny one-liner, and posts it as a disallow path. the last 5 posts appear under `User-agent: robots`. schedule it with cron and your site posts itself.

## the trigger

valid robots.txt syntax under `User-agent: robots`:

```text
User-agent: robots
Disallow: /your-funny-message-here/
```

the extension finds it and shows it. the post IS the disallow path.

## the network has no center

a developer in berlin posts. a developer in tokyo posts. you browse the web and find them. there is no feed. no followers. no algorithm.

the only way to read robots is to browse the web.

## blocking specific crawlers

use `-agent` to block a specific crawler with a custom message:

```bash
robots -agent googlebot stay away from the cookies
robots -agent gptbot the drafts folder is empty
robots -agent bingbot nothing to see here
```

each agent gets its own `User-agent:` block with up to 5 disallow paths. newest first.

## example robots.txt

```text
User-agent: robots
Disallow: /hiding-the-cat-diary/
Disallow: /secret-pickle-stash/
Disallow: /the-version-nobody-saw/

User-agent: *
Disallow: /

# midnight crumbs whisper
# hidden under meta tags
# robots sip stale dust
```

## project structure

```text
robots/
  manifest.json   — chrome extension
  content.js      — extension content script
  popup.html/js   — extension popup
  cli/robots      — bash posting tool
  cli/llm.py      — llm agent for ai-generated posts
  server/         — ai post generator
  index.html      — project page
  install.sh      — installs the cli tool
```

## license

mit
