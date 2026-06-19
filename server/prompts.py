SYSTEM_PROMPT = ""

USER_PROMPT_TEMPLATE = """Write today's robots.txt. Be direct. Address crawlers like old acquaintances.

Recent memory:
{memory_contents}

Crawlers seen yesterday:
{crawler_log}

Start with # 🤖 and a one-line hook. Add a 3-line haiku as comments.
Add User-agent blocks with Disallow paths. Max 5 Disallow lines total.
End with User-agent: * block.
Output ONLY valid robots.txt."""
