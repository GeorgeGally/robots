SYSTEM_PROMPT = ""

USER_PROMPT_TEMPLATE = """Write a short funny sentence about what you're hiding. Use spaces. Be creative and varied — different topics each time. No prefix like "no-robots-allowed". Just a natural sentence. Never mention bots, robots, or crawlers. No personal pronouns like "I'm" or "my" — just the thing being hidden.

Recently used paths (don't reuse):
{previous_paths}

And write a 3-line haiku about it.

Output exactly this format:
POST: your sentence with spaces
HAIKU: line 1
HAIKU: line 2
HAIKU: line 3"""