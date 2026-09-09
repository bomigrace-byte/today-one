import json
import random
import sqlite3
from pathlib import Path
from datetime import date

from dotenv import load_dotenv
from google import genai
from google.genai import types

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
client = genai.Client(
    http_options=types.HttpOptions(
        timeout=8000,
        retry_options=types.HttpRetryOptions(
            attempts=1
        )
    )
)

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
            ai_question TEXT,
            previous_discovery_id INTEGER
        )
    """)

    # 기존 DB에 새 컬럼이 없는 경우 추가
    columns = connection.execute(
        "PRAGMA table_info(discoveries)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "previous_discovery_id" not in column_names:
        connection.execute("""
            ALTER TABLE discoveries
            ADD COLUMN previous_discovery_id INTEGER
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

    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT id, content, emotion, reflection
        FROM discoveries
        ORDER BY id DESC
        LIMIT 5
        """
    ).fetchall()

    connection.close()

    # 발견 기록이 아직 없다면 기존 랜덤 방식 사용
    if not rows:
        action = random.choice(actions)

        action["personalized"] = False
        action["chain_message"] = ""
        action["previous_discovery_id"] = None

        return jsonify(action)

    recent_discoveries = []

    for row in rows:
        recent_discoveries.append({
            "id": row["id"],
            "content": row["content"],
            "emotion": row["emotion"],
            "reflection": row["reflection"]
        })

    latest_discovery = recent_discoveries[0]

    prompt = f"""
당신은 '오늘, 다른 것 하나'라는 서비스의 행동 큐레이터입니다.

서비스의 목적은 사용자의 평범한 하루에
작은 변화를 하나 만들어 새로운 경험이나 발견을 돕는 것입니다.

특히 이 서비스에서는 하나의 발견이
다음 행동의 작은 실마리가 될 수 있습니다.

사용자의 가장 최근 발견:
{latest_discovery}

사용자의 최근 발견 기록:
{recent_discoveries}

가장 최근의 발견을 출발점으로 삼아
오늘 해볼 새로운 작은 행동 하나를 만들어주세요.

중요한 것은 '연쇄 사건'처럼 느껴지는 것입니다.

예를 들어 사용자가 어떤 물건을 발견했다면
그 물건과 관련된 다른 장소나 물건을 살펴보거나,
그 발견에서 자연스럽게 이어지는 새로운 행동을 제안할 수 있습니다.

하지만 단순히 같은 행동을 반복해서는 안 됩니다.

행동을 만들 때 다음 규칙을 반드시 지켜주세요.

- 집이나 일상에서 쉽게 할 수 있는 행동이어야 합니다.
- 1~15분 정도면 충분해야 합니다.
- 특별한 준비물이나 비용이 필요하지 않아야 합니다.
- 생산성, 자기계발, 운동, 공부를 강요하지 마세요.
- 해야 할 일을 추가하는 느낌보다 '한번 해보는 작은 실험'처럼 느껴지게 하세요.
- 가장 최근의 발견과 자연스럽게 연결되어야 합니다.
- 이전 행동을 그대로 반복하지 마세요.
- 발견의 의미를 미리 정하거나 결과를 평가하지 마세요.
- 사용자가 예상하지 못한 새로운 발견을 할 가능성을 열어두세요.
- 행동 자체가 재미있거나 가벼운 호기심을 유발해야 합니다.
- 설명이나 인사말을 추가하지 마세요.

반드시 아래 JSON 형식 하나만 출력하세요.

{{
    "category": "discovery",
    "title": "오늘 해볼 행동",
    "description": "행동에 대한 짧은 설명",
    "difficulty": 1,
    "estimated_minutes": 5,
    "tags": ["태그1", "태그2"]
}}

category는 다음 중 하나만 사용하세요:
discovery, movement, sensory, knowledge, everyday

difficulty는 1~3 사이의 숫자를 사용하세요.
"""

    try:
        response = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )

        output = response.output_text.strip()

        # Gemini가 ```json ... ``` 형태로 응답하는 경우 제거
        if output.startswith("```"):
            output = output.replace("```json", "")
            output = output.replace("```", "")
            output = output.strip()

        today_action = json.loads(output)

        # 연쇄 사건임을 프론트에 알려줌
        today_action["personalized"] = True
        today_action["chain_message"] = "지난 발견에서 이어진 행동이에요."
        today_action["previous_discovery_id"] = latest_discovery["id"]

        return jsonify(today_action)

    except Exception as error:
        print("Gemini 오늘의 행동 생성 실패:", error)

        # Gemini에 문제가 있어도 기존 서비스는 계속 작동
        action = random.choice(actions)

        action["personalized"] = False
        action["chain_message"] = ""
        action["previous_discovery_id"] = None

        return jsonify(action)


@app.get("/api/discoveries")
def get_discoveries():
    actions = {
        action["id"]: action
        for action in load_actions()
    }

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
            ai_question,
            previous_discovery_id
        FROM discoveries
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    discoveries = []

    for row in rows:
        item = dict(row)

        action = actions.get(int(item["action_id"]), {})

        item["category"] = action.get("category", "")
        item["action_title"] = action.get("title", "")

        discoveries.append(item)

    return jsonify(discoveries)


@app.post("/api/discoveries")
def create_discovery():
    content = request.form.get("content", "").strip()
    action_id = request.form.get("action_id")
    emotion = request.form.get("emotion", "")
    previous_discovery_id = request.form.get("previous_discovery_id")

    if not content:
        return jsonify({
            "error": "발견 내용을 입력해주세요."
        }), 400

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
        (
            action_id,
            date,
            content,
            image_path,
            emotion,
            previous_discovery_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            action_id,
            date.today().isoformat(),
            content,
            image_path,
            emotion,
            previous_discovery_id
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
def create_ai_question():
    data = request.get_json()

    discovery_id = data.get("discovery_id")
    discovery = data.get("discovery", "").strip()

    if not discovery:
        return jsonify({
            "error": "발견 내용을 입력해주세요."
        }), 400

    prompt = f"""
사용자는 일상에서 다음과 같은 것을 발견했습니다.

"{discovery}"

이 발견을 바탕으로 사용자가 자신의 경험이나 생각을
조금 더 들여다볼 수 있도록 짧은 후속 질문을 하나 만들어주세요.

규칙:
- 질문은 반드시 하나만 작성하세요.
- 한국어로 작성하세요.
- 30자 이내로 작성하세요.
- 부담스럽거나 심리상담처럼 느껴지지 않게 하세요.
- 정답을 요구하지 마세요.
- 발견 내용과 직접적으로 관련된 질문을 하세요.
- "왜 그랬나요?"처럼 추궁하는 느낌의 질문은 피하세요.
- 질문만 출력하세요.
"""

    try:
        response = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )

        question = response.output_text.strip()

    except Exception as error:
        print("Gemini 후속 질문 생성 실패:", error)

        question = "이 발견에서 가장 눈에 들어온 것은 무엇이었나요?"

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE discoveries
        SET ai_question = ?
        WHERE id = ?
        """,
        (
            question,
            discovery_id
        )
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
        return jsonify({
            "error": "생각을 입력해주세요."
        }), 400

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE discoveries
        SET reflection = ?
        WHERE id = ?
        """,
        (
            reflection,
            discovery_id
        )
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "생각이 저장되었습니다."
    })


@app.get("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)