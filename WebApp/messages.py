import json
import os

# Load messages from JSON files
def load_translations(base_path="./messages"):
    languages = ["he", "en", "fr"]
    messages = {}
    for lang in languages:
        path = os.path.join(base_path, f"messages_{lang}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                messages[lang] = json.load(f)
    return messages

# Load once on import
TRANSLATIONS = load_translations("./messages")  

# Function to access messages
def get_message(key: str, lang: str = "en", **kwargs) -> str:
    lang = lang[:2] if lang else "en"
    fallback_lang = "en"
    message_template = (
        TRANSLATIONS.get(lang, {}).get(key)
        or TRANSLATIONS.get(fallback_lang, {}).get(key, "")
    )
    return message_template.format(**kwargs)
