import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
GROUP_ID: int = int(os.environ["GROUP_ID"])

_topic_raw = os.getenv("TOPIC_ID", "").strip()
TOPIC_ID: int | None = int(_topic_raw) if _topic_raw else None
