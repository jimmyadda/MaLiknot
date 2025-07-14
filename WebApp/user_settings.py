from HandelDB import database_read, database_write

def save_user_language(chat_id, lang):
    database_write("""
        INSERT INTO user_settings (chat_id, lang)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET lang = excluded.lang
    """, (chat_id, lang))

def get_user_language(chat_id):
    rows = database_read("SELECT lang FROM user_settings WHERE chat_id = ?", (chat_id,))
    return rows[0]["lang"] if rows else None