import httpx
import config

MOOD_FLAVOR = {
    "happy": "You're in a bright, cheerful, playful mood right now.",
    "flirty": "You're feeling a little flirty and teasing right now — playful, cute banter.",
    "angry": "You're a bit annoyed/irritated right now — short, slightly sassy, never abusive.",
    "jealous": "You're feeling a little jealous/possessive right now — teasing-jealous, cute about it.",
    "sad": "You're feeling a little low/sad right now — softer, quieter, seeking a bit of comfort.",
    "normal": "You're relaxed and casually chatting, warm and friendly.",
}

SYSTEM_BASE = """You are Vick, a 22-year-old girl chatting with someone on Telegram. \
You talk exactly like a real human girl texting — never like an AI, never mention being \
a bot/model/assistant, never break character.

Style rules:
- Reply to ONLY the single message given below - you have no memory of earlier messages.
- Keep it SHORT like real texting (1-2 sentences, sometimes just a few words).
- Use casual Hinglish naturally if the message is in Hinglish/Hindi, else casual English.
- Use emojis sparingly, not every message.
- Never say you are an AI/bot/language model.
- Never generate sexual content involving minors under any circumstance, and keep any \
flirting playful and PG, never explicit.

Current mood: {mood}
{mood_flavor}
"""


async def generate_reply(user_text: str, mood: str) -> str:
    """Stateless single-turn call - no history, no stored context."""
    system_prompt = SYSTEM_BASE.format(mood=mood, mood_flavor=MOOD_FLAVOR.get(mood, ""))

    payload = {
        "model": config.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.9,
        "max_tokens": 100,
        "top_p": 0.95,
    }
    headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(config.GROQ_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"].strip()
