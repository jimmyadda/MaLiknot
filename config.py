import os

# Detect if running on PythonAnywhere or locally
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    DATABASE_PATH = "/home/maliknot1bot/mysite/grocery_list.db"
else:
    # Local development path (relative or absolute)
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), "grocery_list.db")