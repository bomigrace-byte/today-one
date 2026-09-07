import json
import random
import sqlite3
from pathlib import Path
from datetime import date

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

ACTIONS_FILE = BASE_DIR / "data" / "actions.json"
DATABASE_FILE = BASE_DIR / "data" / "today_one.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"

UPLOAD_FOLDER.mkdir(exist_ok=True)


def get_db_connection():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            content TEXT NOT NULL,
            image_path TEXT,
            emotion TEXT,
            reflection TEXT,
            ai_question TEXT
        )
    """)

    connection.commit()
    connection.close()


def load_actions():
    with open(ACTIONS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/today")
def get_today():
    actions = load_actions()
    today_action = random.choice(actions)

    return jsonify(today_action)


@app.post("/api/discoveries")

@app.get("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

def create_discovery():

    content = request.form.get("content", "").strip()
    action_id = request.form.get("action_id")
    emotion = request.form.get("emotion", "")

    if not content:
        return jsonify({"error": "발견 내용을 입력해주세요."}), 400

    image_path = None

    image = request.files.get("image")

    if image and image.filename:
        filename = secure_filename(image.filename)
        image.save(UPLOAD_FOLDER / filename)
        image_path = f"/uploads/{filename}"

    connection = get_db_connection()

    cursor = connection.execute(
        """
        INSERT INTO discoveries
        (action_id, date, content, image_path, emotion)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            action_id,
            date.today().isoformat(),
            content,
            image_path,
            emotion
        )
    )

    connection.commit()

    discovery_id = cursor.lastrowid

    connection.close()

    return jsonify({
        "id": discovery_id,
        "message": "발견이 저장되었습니다."
    }), 201


if __name__ == "__main__":
    init_db()
    app.run(debug=True)