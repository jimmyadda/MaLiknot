from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    print("🚀 Flask app.py loaded")
    return "✅ Minimal Flask app running"

if __name__ == '__main__':
    print("👀 Starting minimal app")
    app.run(host='0.0.0.0', port=5000)