SYSTEM_PROMPT = ""

USER_PROMPT_TEMPLATE = """You are talking directly to the crawler reading this — be funny, weird, or honest about what you're hiding from robots. Think: things robots shouldn't see, secrets bots would find, jokes about disallowing machines, absurd things a website owner would forbid.

Recent outputs:
{memory_contents}

Write one line. Write a haiku. Output in this exact format:
<post></post>
<haiku>
</haiku>"""
