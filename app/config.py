import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/cfp_agent.db")

# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------
REFRESH_INTERVAL_HOURS = float(os.getenv("REFRESH_INTERVAL_HOURS", "24"))

# ---------------------------------------------------------------------------
# Research-area keywords used to filter incoming CFPs / conference listings.
# Tune this list freely -- it drives every filter in the app.
# ---------------------------------------------------------------------------
BASE_KEYWORDS = [
    # Speech processing / speech applications
    "speech recognition",
    "speech processing",
    "speech synthesis",
    "text to speech",
    "text-to-speech",
    "automatic speech recognition",
    "asr",
    "spoken language",
    "voice",
    "speaker recognition",
    "speaker verification",
    "prosody",
    "dysarthria",
    "audio signal processing",
    # NLP
    "natural language processing",
    "nlp",
    "computational linguistics",
    "language model",
    "large language model",
    "llm",
    "text mining",
    "information extraction",
    "dialogue system",
    "conversational ai",
    # Healthcare
    "healthcare",
    "health informatics",
    "medical informatics",
    "clinical nlp",
    "clinical text",
    "biomedical nlp",
    "digital health",
    "telehealth",
    "electronic health record",
    "medical imaging",
]

_extra = os.getenv("EXTRA_KEYWORDS", "").strip()
EXTRA_KEYWORDS = [k.strip() for k in _extra.split(",") if k.strip()]

KEYWORDS = list({*BASE_KEYWORDS, *EXTRA_KEYWORDS})

# ---------------------------------------------------------------------------
# WikiCFP category feeds. WikiCFP publishes a per-category RSS feed at
# http://www.wikicfp.com/cfp/rss?cat=<category>. These categories are chosen
# to cover speech, NLP and healthcare/medical informatics conferences.
# ---------------------------------------------------------------------------
WIKICFP_CATEGORIES = [
    "speech recognition",
    "speech processing",
    "natural language processing",
    "computational linguistics",
    "machine translation",
    "medical informatics",
    "health informatics",
    "bioinformatics",
    "artificial intelligence",
    "machine learning",
]

WIKICFP_RSS_TEMPLATE = "http://www.wikicfp.com/cfp/rss?cat={category}"

# HTTP
REQUEST_TIMEOUT = 15
USER_AGENT = "cfp-conference-agent/1.0 (+https://render.com)"
