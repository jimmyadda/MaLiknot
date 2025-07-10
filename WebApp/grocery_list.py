import sqlite3
import os

from config import DATABASE_PATH as db_name

def create_db():    
    if os.path.exists(db_name):
        print("Database already exists!")
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # יצירת טבלאות
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                chat_id TEXT UNIQUE,
                archived INTEGER DEFAULT 0
            );
    ''')
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
    conn.close()
    print("Database created successfully!")

""" def create_PostgreSQLdb():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
            CREATE TABLE "lists" (
                id	INTEGER,
                name	TEXT,
                archived	INTEGER DEFAULT 0,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            unit TEXT,
            price REAL,
            category_id INTEGER REFERENCES categories(id)
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_in_list (
            id SERIAL PRIMARY KEY,
            list_id INTEGER REFERENCES lists(id),
            product_id INTEGER REFERENCES products(id),
            collected INTEGER DEFAULT 0,
            notes TEXT,
            quantity INTEGER
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            userid TEXT PRIMARY KEY,
            password TEXT,
            salt TEXT,
            email TEXT,
            name TEXT
        );
    ''')

    # Categories in Hebrew
    categories = [
        "ירקות ופירות", "שימורים", "מוצרי חלב", "סלטים, שמנים, רטבים ותוספות", "קפואים",
        "בשר, עוף ודגים", "יבשים", "תבלינים", "שתייה", "ניקיון וחד פעמי", "טיפוח"
    ]

    for category in categories:
        cursor.execute(
            "INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;",
            (category,)
        )

    # Products in each category
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

    for category, items in products.items():
        cursor.execute("SELECT id FROM categories WHERE name = %s", (category,))
        result = cursor.fetchone()
        if result:
            category_id = result[0]
            for item in items:
                cursor.execute(
                    "INSERT INTO products (name, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                    (item, category_id)
                )

    conn.commit()
    cursor.close()
    conn.close()
    print("PostgreSQL database created successfully!")
 """

if __name__ == "__main__":
    create_db()
