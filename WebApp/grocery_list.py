import gzip
import sqlite3
import os
import xml.etree.ElementTree as ET
from HandelDB import create_account, database_read
from config import DATABASE_PATH as db_name

def create_db(): 

    if os.path.exists(db_name):
        print("Database already exists!")
        conn = sqlite3.connect(db_name)
        import_supermarket_data(conn, "ProductPrices.gz")
        #Create Default user
        exists = database_read("SELECT * FROM accounts WHERE userid = 'admin'")
        print(exists)
        if not exists:
                print("creating user")
                create_account({
                    "userid": "admin",
                    "email": "admin@example.com",
                    "name": "Admin",
                    "password": "pass"
                })
        return
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # יצירת טבלאות
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                chat_id TEXT,
                archived INTEGER DEFAULT 0
            );
    ''')
    
    # Ensure created_at exists (for upgrades)
    cursor.execute("PRAGMA table_info(lists);")
    columns = [col[1] for col in cursor.fetchall()]
    if "created_at" not in columns:
        cursor.execute("ALTER TABLE lists ADD COLUMN created_at TEXT;")
        cursor.execute("UPDATE lists SET created_at = datetime('now');")

        
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        unit TEXT ,
        price REAL,
        category_id INTEGER,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_in_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER,
    product_id INTEGER,
    collected INTEGER DEFAULT 0,
    notes TEXT,
    quantity INTEGER,
    FOREIGN KEY (list_id) REFERENCES lists(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)''')
    #Acc
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
	"userid"	TEXT,
	"password"	TEXT,
	"salt"	TEXT,
	"email"	TEXT,
	"name"	TEXT,
	PRIMARY KEY("userid")
)    ''')
    
    cursor.execute(''' CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    list_id INTEGER,
    total_amount REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP) ''')

    cursor.execute(''' CREATE TABLE IF NOT EXISTS user_settings (
    chat_id TEXT PRIMARY KEY,
    lang TEXT); ''')

    cursor.execute(''' CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id, product_id)); ''')

     
    # הוספת קטגוריות
    categories = [
        "ירקות ופירות", "שימורים", "מוצרי חלב", "סלטים, שמנים, רטבים ותוספות", "קפואים",
        "בשר, עוף ודגים", "יבשים", "תבלינים", "שתייה", "ניקיון וחד פעמי", "טיפוח"
    ]
    
    for category in categories:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category,))
    
    # מילון מוצרים לפי קטגוריות
    products = {
        "ירקות ופירות": ["אגס", "אפרסק", "שזיף", "תפוח", "בננה", "אבטיח", "מלון", "אננס","מלפפון","עגבנייה","לימון","ענבים"],
        "שימורים": ["רסק עגבניות", "תירס", "תירס גמדי", "שעועית", "זיתים", "טונה","מלפפון חמוץ"],
        "מוצרי חלב": ["חלב", "קוטג'", "גבינה צהובה", "גבינה לבנה","מעדנים"],
        "סלטים, שמנים, רטבים ותוספות": ["חומוס", "טחינה", "חרדל", "קטשופ", "מיונז"],
        "קפואים": ["בורקסים", "ג'חנון", "פיצות קפואות", "תירס", "אפונה"],
        "בשר, עוף ודגים": ["חזה עוף", "פרגיות", "שוקיים", "ירכיים","אסאדו","סינטה"],
        "יבשים": ["פסטה", "אורז", "פתיתים", "איטריות", "בורגול"],
        "תבלינים": ["פפריקה", "פלפל שחור", "גריל עוף", "פלפל לבן"],
        "שתייה": ["מים מינרליים", "קולה זירו", "דיאט קולה", "ספרייט","קולה"],
        "ניקיון וחד פעמי": ["אקונומיקה", "סבון לרצפה", "סמרטוט רצפה", "נייר טואלט"],
        "טיפוח": ["דאודורנט", "מקלוני אוזניים", "סבון רחצה", "שמפו"]
    }
    
    # הוספת מוצרים
    for category, items in products.items():
        cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
        category_id = cursor.fetchone()[0]
        for item in items:
            cursor.execute("INSERT INTO products (name, category_id) VALUES (?, ?)", (item, category_id))
    
    
    #cursor.execute("ALTER TABLE lists ADD COLUMN archived INTEGER DEFAULT 0;")

    conn.commit()

    #Create Default user
    exists = database_read("SELECT * FROM accounts WHERE userid = 'admin'")
    if not exists:
                print("creating default user")
                create_account({
                    "userid": "admin",
                    "email": "admin@example.com",
                    "name": "Admin",
                    "password": "pass"
                })

                    # ===== Import supermarket data =====
    import_supermarket_data(conn, "ProductPrices.gz")
    conn.close()
    print("Database created successfully!")



def detect_category(name: str) -> str:
    name = (name or "").strip().lower()

    rules = {
        "ירקות ופירות": ["תפוח", "בננה", "עגבנ", "מלפפון", "ענב", "תפוז", "מלון", "אבטיח", "שום", "בצל", "אגס", "שזיף", "אפרסק"],
        "שתייה": ["קולה", "ספרייט", "מים", "בירה", "יין", "שתייה", "משקה", "דיאט"],
        "שימורים": ["טונה", "תירס", "שעועית", "זיתים", "רסק", "קטניות", "מלפפון חמוץ", "חומוס"],
        "מוצרי חלב": ["חלב", "גבינה", "קוטג", "שמנת", "מעדן", "יוגורט"],
        "קפואים": ["קפוא", "פיצה", "ג'חנון", "בורקס", "שניצל"],
        "בשר, עוף ודגים": ["עוף", "דג", "בשר", "פרגית", "כבש", "קציצה", "סלמון"],
        "יבשים": ["אורז", "פסטה", "אטריות", "קוסקוס", "סוכר", "קמח", "קוואקר"],
        "תבלינים": ["מלח", "פלפל", "פפריקה", "גריל", "תבלין", "כורכום"],
        "ניקיון וחד פעמי": ["אקונומיקה", "נייר", "סבון", "שקית", "חד פעמי", "מטלית", "מגב"],
        "טיפוח": ["דאודורנט", "שמפו", "מגבונים", "קרם", "שפתון", "מסכה", "שיער"]
    }

    for cat, words in rules.items():
        for w in words:
            if w in name:
                return cat

    return "שונות"


def import_supermarket_data(conn, gz_path):
    if not os.path.exists(gz_path):
        print(f"⚠️  File not found: {gz_path}")
        return

    cursor = conn.cursor()
    print(f"📦 Importing supermarket data from {gz_path} ...")

    try:
        with gzip.open(gz_path, "rt", encoding="utf-8", errors="ignore") as f:
            tree = ET.parse(f)
        root = tree.getroot()
        items_inserted = 0

        count = 0
        for item in root.findall(".//Item"):
            item_code = item.findtext("ItemCode")
            name = item.findtext("ItemName")
            price = item.findtext("ItemPrice")
            unit = item.findtext("UnitQty")

            if not name or not price:
                continue

            try:
                price = float(price)
            except ValueError:
                continue

            # Detect category from product name
            category_name = detect_category(name)
            cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category_name,))
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
            category_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT OR IGNORE INTO products (id,name, unit, price, category_id)
                VALUES (?,?, ?, ?, ?)
            """, (item_code,name.strip(), unit, price, category_id)) 
            if cursor.rowcount > 0:
                 items_inserted+=1                             
            count += 1                                         
        conn.commit()
        if items_inserted == 0 :
             print("all items already exests in DB , no insert needed!!")
        print(f"✅ Imported {count} products with auto-categories.")
    except Exception as e:
        print(f"❌ Error importing supermarket data: {e}")

        
if __name__ == "__main__":
    create_db()

        
