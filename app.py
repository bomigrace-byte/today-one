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

@app.get("/api/discoveries")
def get_discoveries():
    actions = {action["id"]: action for action in load_actions()}

    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            action_id,
            date,
            content,
            image_path,
            emotion,
            reflection,
            ai_question
        FROM discoveries
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    discoveries = []

    for row in rows:
        item = dict(row)

        action = actions.get(item["action_id"], {})

        item["category"] = action.get("category", "")
        item["action_title"] = action.get("title", "")

        discoveries.append(item)

    return jsonify(discoveries)

@app.post("/api/discoveries")
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

@app.post("/api/ai/question")

@app.post("/api/ai/question")
def create_ai_question():

    data = request.get_json()

    discovery_id = data.get("discovery_id")
    discovery = data.get("discovery", "").strip()

    if not discovery:
        return jsonify({"error": "발견 내용을 입력해주세요."}), 400

    question = f"'{discovery}'을(를) 발견했을 때 가장 먼저 어떤 생각이 들었나요?"

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE discoveries
        SET ai_question = ?
        WHERE id = ?
        """,
        (question, discovery_id)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "question": question
    })

@app.post("/api/discoveries/<int:discovery_id>/reflection")
def save_reflection(discovery_id):

    data = request.get_json()

    reflection = data.get("reflection", "").strip()

    if not reflection:
        return jsonify({"error": "생각을 입력해주세요."}), 400

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE discoveries
        SET reflection = ?
        WHERE id = ?
        """,
        (reflection, discovery_id)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "생각이 저장되었습니다."
    })

@app.get("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)