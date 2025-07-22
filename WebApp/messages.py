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

    # Step 1: get lang dictionary
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS.get(fallback_lang, {}))

    # Step 2: get the message string
    message_template = lang_dict.get(key, TRANSLATIONS.get(fallback_lang, {}).get(key, ""))

    # Step 3: format
    if isinstance(message_template, str):
        return message_template.format(**kwargs)
    return str(message_template)
