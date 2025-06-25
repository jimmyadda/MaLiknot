from flask import Flask, request
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Flask app is running!"

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    print(">>> /telegram hit")
    print(">>> Incoming update:", request.get_json(force=True))
    return '', 200

if __name__ == '__main__':
    print(f"🔍 Python version on Railway: {sys.version}")
    app.run(host='0.0.0.0', port=5000)