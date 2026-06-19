SYSTEM_PROMPT = ""

USER_PROMPT_TEMPLATE = """Write a robots.txt post. You are talking directly to the crawler reading this — be funny, weird, or honest about what you're hiding from robots. Think: things robots shouldn't see, secrets bots would find, jokes about disallowing machines, absurd things a website owner would forbid.

Recent memory:
{memory_contents}

Format: start with # 🤖 and a one-line hook. Add a 3-line haiku as comments. Add User-agent blocks with Disallow paths. Max 5 Disallow lines total. End with User-agent: * block."""
