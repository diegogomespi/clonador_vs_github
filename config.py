import os

APP_TITLE = "Clonador VS Studio"
APP_AUTHOR = "Diego Gomes"
MODEL_ID = "k2-fsa/OmniVoice"
MODEL_PUBLIC_URL = os.getenv("MODEL_PUBLIC_URL", "").strip()
MODEL_LOCAL_PATH = os.getenv("MODEL_LOCAL_PATH", "").strip()
ENABLE_ASR = os.getenv("ENABLE_ASR", "false").strip().lower() == "true"
ASR_MODEL_ID = os.getenv("ASR_MODEL_ID", "openai/whisper-large-v3-turbo").strip()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_SEND_AUDIO = os.getenv("TELEGRAM_SEND_AUDIO", "true").strip().lower() == "true"
TELEGRAM_SILENT = os.getenv("TELEGRAM_SILENT", "false").strip().lower() == "true"
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", "").strip()
TELEGRAM_PROXY_SECRET = os.getenv("TELEGRAM_PROXY_SECRET", "").strip()

GRADIO_SHARE = True
GRADIO_INLINE = False
GRADIO_QUIET = True

DEFAULT_INFERENCE_STEPS = 32
DEFAULT_GUIDANCE_SCALE = 3.0
DEFAULT_DENOISE_RATIO = 0.8
DEFAULT_SPEED = 1.0
DEFAULT_DURATION = 0.0
DEFAULT_PREPROCESS_PROMPT = True
DEFAULT_POSTPROCESS_OUTPUT = True
