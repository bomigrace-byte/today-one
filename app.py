import json
import random
import os
from pathlib import Path
from datetime import date
from difflib import SequenceMatcher
from uuid import uuid4

from dotenv import load_dotenv
from google import genai
from google.genai import types
from supabase import create_client, Client

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename


# =========================================================
# 환경변수
# =========================================================

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")


if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL 환경변수가 없습니다.")

if not SUPABASE_SECRET_KEY:
    raise RuntimeError("SUPABASE_SECRET_KEY 환경변수가 없습니다.")


# =========================================================
# Flask / Supabase / Gemini
# =========================================================

app = Flask(__name__)


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


client = genai.Client(
    http_options=types.HttpOptions(
        timeout=30000,
        retry_options=types.HttpRetryOptions(
            attempts=2
        )
    )
)


# =========================================================
# 기본 경로
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

ACTIONS_FILE = (
    BASE_DIR
    / "data"
    / "actions.json"
)


STORAGE_BUCKET = "discoveries"


# =========================================================
# 공통 함수
# =========================================================

def load_actions():

    with open(
        ACTIONS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def parse_optional_int(value):

    if value in (
        None,
        "",
        "undefined",
        "null"
    ):

        return None

    try:

        return int(value)

    except (
        TypeError,
        ValueError
    ):

        return None


def get_action_info(actions, item):

    stored_title = item.get(
        "action_title"
    )

    stored_description = item.get(
        "action_description"
    )

    stored_category = item.get(
        "action_category"
    )


    if stored_title:

        return {
            "title": stored_title,
            "description": (
                stored_description
                or ""
            ),
            "category": (
                stored_category
                or ""
            )
        }


    action_id = parse_optional_int(
        item.get("action_id")
    )


    action = (
        actions.get(
            action_id,
            {}
        )
        if action_id is not None
        else {}
    )


    return {
        "title": action.get(
            "title",
            "오늘의 행동"
        ),
        "description": action.get(
            "description",
            ""
        ),
        "category": action.get(
            "category",
            ""
        )
    }


def get_previous_discovery(
    previous_id
):

    if not previous_id:

        return None


    response = (
        supabase
        .table("discoveries")
        .select(
            "id, date, content"
        )
        .eq(
            "id",
            previous_id
        )
        .limit(1)
        .execute()
    )


    if not response.data:

        return None


    return response.data[0]


def is_similar_question(
    question,
    recent_questions,
    threshold=0.65
):

    normalized_question = (
        question
        .strip()
        .lower()
    )


    for recent_question in recent_questions:

        normalized_recent = (
            recent_question
            .strip()
            .lower()
        )


        if (
            normalized_question
            == normalized_recent
        ):

            return True


        similarity = SequenceMatcher(
            None,
            normalized_question,
            normalized_recent
        ).ratio()


        if similarity >= threshold:

            return True


    return False


def create_fallback_chain_action(
    latest_discovery
):

    content = latest_discovery.get(
        "content",
        ""
    )


    return {

        "category": "discovery",

        "title":
            "방금 발견한 것 주변을 다시 살펴보세요.",

        "description":
            f'"{content}"을 발견했던 곳이나 주변을 잠깐 다시 살펴보세요.',

        "difficulty": 1,

        "estimated_minutes": 3,

        "tags": [
            "발견",
            "관찰"
        ],

        "personalized": True,

        "chain_message":
            "지난 발견에서 이어진 행동이에요.",

        "previous_discovery_id":
            latest_discovery["id"]
    }


def create_signed_image_url(
    image_path
):

    if not image_path:

        return None


    try:

        response = (
            supabase
            .storage
            .from_(STORAGE_BUCKET)
            .create_signed_url(
                image_path,
                60 * 60 * 24 * 7
            )
        )


        if isinstance(
            response,
            dict
        ):

            data = response.get(
                "data"
            )

            if isinstance(
                data,
                dict
            ):

                return (
                    data.get(
                        "signedUrl"
                    )
                    or data.get(
                        "signedURL"
                    )
                )


            return (
                response.get(
                    "signedUrl"
                )
                or response.get(
                    "signedURL"
                )
            )


        return None


    except Exception as error:

        print(
            "사진 URL 생성 실패:",
            error
        )

        return None


def upload_image(image):

    if not image:
        return None


    if not image.filename:
        return None


    original_filename = secure_filename(
        image.filename
    )


    if not original_filename:

        return None


    extension = Path(
        original_filename
    ).suffix.lower()


    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif"
    }


    if extension not in allowed_extensions:

        raise ValueError(
            "지원하지 않는 이미지 형식입니다."
        )


    filename = (
        f"{uuid4().hex}"
        f"{extension}"
    )


    storage_path = (
        f"discoveries/{filename}"
    )


    file_bytes = image.read()


    content_type = (
        image.content_type
        or "application/octet-stream"
    )


    (
        supabase
        .storage
        .from_(STORAGE_BUCKET)
        .upload(
            storage_path,
            file_bytes,
            {
                "content-type":
                    content_type,
                "upsert":
                    "false"
            }
        )
    )


    return storage_path


# =========================================================
# Home
# =========================================================

@app.get("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# 오늘의 행동
# =========================================================

@app.get("/api/today")
def get_today():

    actions = load_actions()


    try:

        response = (
            supabase
            .table("discoveries")
            .select(
                "id, content, emotion, reflection"
            )
            .order(
                "id",
                desc=True
            )
            .limit(5)
            .execute()
        )


        rows = response.data or []


    except Exception as error:

        print(
            "Supabase 기록 조회 실패:",
            error
        )

        rows = []


    # 아직 발견 기록이 없다면
    # 기존 랜덤 행동 사용

    if not rows:

        action = random.choice(
            actions
        ).copy()


        action["personalized"] = False

        action["chain_message"] = ""

        action["previous_discovery_id"] = None


        return jsonify(action)


    recent_discoveries = []


    for row in rows:

        recent_discoveries.append({

            "id":
                row.get("id"),

            "content":
                row.get("content"),

            "emotion":
                row.get("emotion"),

            "reflection":
                row.get("reflection")
        })


    latest_discovery = (
        recent_discoveries[0]
    )


    prompt = f"""
당신은 '오늘, 다른 것 하나'라는 서비스의
행동 큐레이터입니다.

서비스의 목적은 사용자의 평범한 하루에
작은 변화를 하나 만들어
새로운 경험이나 발견을 돕는 것입니다.

특히 이 서비스에서는 하나의 발견이
다음 행동의 작은 실마리가 될 수 있습니다.

가장 최근의 발견:

{json.dumps(
    latest_discovery,
    ensure_ascii=False,
    indent=2
)}

최근 발견 기록:

{json.dumps(
    recent_discoveries,
    ensure_ascii=False,
    indent=2
)}

다음 행동을 하나 제안하세요.

규칙:

- 1~15분 정도면 충분해야 합니다.
- 특별한 준비물이나 비용이 필요하지 않아야 합니다.
- 생산성, 자기계발, 운동, 공부를 강요하지 마세요.
- 해야 할 일을 추가하는 느낌보다
  '한번 해보는 작은 실험'처럼 느껴지게 하세요.
- 가장 최근의 발견과 자연스럽게 연결되어야 합니다.
- 이전 행동을 그대로 반복하지 마세요.
- 발견의 의미를 미리 정하거나 결과를 평가하지 마세요.
- 사용자가 예상하지 못한 새로운 발견의 가능성을 열어두세요.
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

discovery,
movement,
sensory,
knowledge,
everyday

difficulty는 1~3 사이의 숫자를 사용하세요.
"""


    try:

        response = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )


        output = (
            response
            .output_text
            .strip()
        )


        if output.startswith("```"):

            output = (
                output
                .replace(
                    "```json",
                    ""
                )
                .replace(
                    "```",
                    ""
                )
                .strip()
            )


        today_action = json.loads(
            output
        )


        today_action["personalized"] = True

        today_action["chain_message"] = (
            "지난 발견에서 이어진 행동이에요."
        )

        today_action["previous_discovery_id"] = (
            latest_discovery["id"]
        )


        return jsonify(
            today_action
        )


    except Exception as error:

        print(
            "Gemini 오늘의 행동 생성 실패:",
            error
        )


        action = create_fallback_chain_action(
            latest_discovery
        )


        return jsonify(action)


# =========================================================
# 지난 발견 목록
# =========================================================

@app.get("/api/discoveries")
def get_discoveries():

    actions = {
        action["id"]: action
        for action in load_actions()
    }


    try:

        response = (
            supabase
            .table("discoveries")
            .select(
                """
                id,
                action_id,
                date,
                content,
                image_path,
                emotion,
                reflection,
                ai_question,
                previous_discovery_id,
                action_title,
                action_description,
                action_category
                """
            )
            .order(
                "id",
                desc=True
            )
            .execute()
        )


        rows = response.data or []


    except Exception as error:

        print(
            "Supabase 발견 목록 조회 실패:",
            error
        )

        return jsonify({
            "error":
                "발견 기록을 불러오지 못했습니다."
        }), 500


    discoveries = []


    for row in rows:

        item = dict(row)


        action = get_action_info(
            actions,
            item
        )


        item["category"] = (
            action["category"]
        )

        item["action_title"] = (
            action["title"]
        )

        item["action_description"] = (
            action["description"]
        )


        item["previous_discovery"] = (
            get_previous_discovery(
                item.get(
                    "previous_discovery_id"
                )
            )
        )


        if item.get("image_path"):

            item["image_path"] = (
                create_signed_image_url(
                    item["image_path"]
                )
            )


        discoveries.append(item)


    return jsonify(
        discoveries
    )


# =========================================================
# 발견 상세
# =========================================================

@app.get(
    "/api/discoveries/<int:discovery_id>"
)
def get_discovery(
    discovery_id
):

    actions = {
        action["id"]: action
        for action in load_actions()
    }


    try:

        response = (
            supabase
            .table("discoveries")
            .select(
                """
                id,
                action_id,
                date,
                content,
                image_path,
                emotion,
                reflection,
                ai_question,
                previous_discovery_id,
                action_title,
                action_description,
                action_category
                """
            )
            .eq(
                "id",
                discovery_id
            )
            .limit(1)
            .execute()
        )


    except Exception as error:

        print(
            "Supabase 발견 상세 조회 실패:",
            error
        )

        return jsonify({
            "error":
                "발견 기록을 불러오지 못했습니다."
        }), 500


    if not response.data:

        return jsonify({
            "error":
                "발견 기록을 찾을 수 없습니다."
        }), 404


    discovery = dict(
        response.data[0]
    )


    action = get_action_info(
        actions,
        discovery
    )


    discovery["previous_discovery"] = (
        get_previous_discovery(
            discovery.get(
                "previous_discovery_id"
            )
        )
    )


    discovery["category"] = (
        action["category"]
    )

    discovery["action_title"] = (
        action["title"]
    )

    discovery["action_description"] = (
        action["description"]
    )


    if discovery.get(
        "image_path"
    ):

        discovery["image_path"] = (
            create_signed_image_url(
                discovery["image_path"]
            )
        )


    return jsonify(
        discovery
    )


# =========================================================
# 발견 기록 저장
# =========================================================

@app.post("/api/discoveries")
def create_discovery():

    content = (
        request.form
        .get(
            "content",
            ""
        )
        .strip()
    )


    action_id = parse_optional_int(
        request.form.get(
            "action_id"
        )
    )


    if action_id is None:

        action_id = 0


    action_title = (
        request.form
        .get(
            "action_title",
            ""
        )
        .strip()
    )


    action_description = (
        request.form
        .get(
            "action_description",
            ""
        )
        .strip()
    )


    action_category = (
        request.form
        .get(
            "action_category",
            ""
        )
        .strip()
    )


    emotion = request.form.get(
        "emotion",
        ""
    )


    previous_discovery_id = (
        parse_optional_int(
            request.form.get(
                "previous_discovery_id"
            )
        )
    )


    if not content:

        return jsonify({
            "error":
                "발견 내용을 입력해주세요."
        }), 400


    # -----------------------------------------------------
    # 같은 발견 문장을 다시 저장하지 않음
    # -----------------------------------------------------

    try:

        duplicate_response = (
            supabase
            .table("discoveries")
            .select("id")
            .eq(
                "content",
                content
            )
            .order(
                "id",
                desc=True
            )
            .limit(1)
            .execute()
        )


        if duplicate_response.data:

            return jsonify({
                "error":
                    "이미 같은 발견을 기록했어요. "
                    "다른 점을 발견했다면 그 내용을 적어보세요."
            }), 409


    except Exception as error:

        print(
            "중복 발견 확인 실패:",
            error
        )


    # -----------------------------------------------------
    # 사진 업로드
    # -----------------------------------------------------

    image_path = None


    image = request.files.get(
        "image"
    )


    if image and image.filename:

        try:

            image_path = upload_image(
                image
            )

        except Exception as error:

            print(
                "사진 업로드 실패:",
                error
            )

            return jsonify({
                "error":
                    "사진을 업로드하지 못했습니다."
            }), 500


    # -----------------------------------------------------
    # Supabase 저장
    # -----------------------------------------------------

    discovery_data = {

        "action_id":
            action_id,

        "date":
            date.today().isoformat(),

        "content":
            content,

        "image_path":
            image_path,

        "emotion":
            emotion,

        "previous_discovery_id":
            previous_discovery_id,

        "action_title":
            action_title,

        "action_description":
            action_description,

        "action_category":
            action_category
    }


    try:

        response = (
            supabase
            .table("discoveries")
            .insert(
                discovery_data
            )
            .execute()
        )


    except Exception as error:

        print(
            "발견 저장 실패:",
            error
        )

        return jsonify({
            "error":
                "발견을 저장하지 못했습니다."
        }), 500


    if not response.data:

        return jsonify({
            "error":
                "발견 저장 결과를 확인하지 못했습니다."
        }), 500


    discovery_id = (
        response.data[0]["id"]
    )


    return jsonify({

        "id":
            discovery_id,

        "message":
            "발견이 저장되었습니다."
    }), 201


# =========================================================
# AI 후속 질문
# =========================================================

@app.post("/api/ai/question")
def create_ai_question():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    discovery_id = (
        parse_optional_int(
            data.get(
                "discovery_id"
            )
        )
    )


    discovery = (
        data.get(
            "discovery",
            ""
        )
        .strip()
    )


    if not discovery:

        return jsonify({
            "error":
                "발견 내용을 입력해주세요."
        }), 400


    # -----------------------------------------------------
    # 최근 AI 질문 조회
    # -----------------------------------------------------

    try:

        response = (
            supabase
            .table("discoveries")
            .select(
                "ai_question"
            )
            .not_.is_(
                "ai_question",
                "null"
            )
            .neq(
                "ai_question",
                ""
            )
            .order(
                "id",
                desc=True
            )
            .limit(10)
            .execute()
        )


        recent_questions = [

            row["ai_question"]

            for row in (
                response.data
                or []
            )

            if row.get(
                "ai_question"
            )
        ]


    except Exception as error:

        print(
            "최근 질문 조회 실패:",
            error
        )

        recent_questions = []


    prompt = f"""
사용자는 일상에서 다음과 같은 것을 발견했습니다.

"{discovery}"

이 발견을 바탕으로 사용자가 자신의 경험을
조금 더 들여다볼 수 있도록
짧은 후속 질문을 하나 만들어주세요.

최근 사용되었던 질문:

{json.dumps(
    recent_questions,
    ensure_ascii=False
)}

규칙:

- 질문은 반드시 하나만 작성하세요.
- 한국어로 작성하세요.
- 30자 이내로 작성하세요.
- 최근 질문과 같은 질문을 만들지 마세요.
- 최근 질문과 표현만 조금 바꾼 비슷한 질문도 피하세요.
- 발견 내용과 직접적으로 관련되어야 합니다.
- 발견의 다른 측면을 바라보게 해주세요.
- 부담스럽거나 심리상담처럼 느껴지지 않게 하세요.
- 정답을 요구하지 마세요.
- 추궁하는 느낌을 피하세요.
- 질문만 출력하세요.
"""


    fallback_questions = [

        "그중 가장 의외였던 점은 무엇인가요?",

        "오늘 처음 알아차린 점은 무엇인가요?",

        "다시 본다면 무엇을 살펴보고 싶나요?",

        "이것을 보고 떠오른 것이 있나요?",

        "주변에서 함께 눈에 들어온 것은 무엇인가요?",

        "평소와 다르게 느껴진 점이 있나요?"
    ]


    available_fallbacks = [

        question

        for question
        in fallback_questions

        if not is_similar_question(
            question,
            recent_questions
        )
    ]


    if not available_fallbacks:

        available_fallbacks = (
            fallback_questions
        )


    try:

        response = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )


        question = (
            response
            .output_text
            .strip()
        )


        if (
            question.startswith('"')
            and
            question.endswith('"')
        ):

            question = (
                question[1:-1]
                .strip()
            )


        if question.startswith(
            "질문:"
        ):

            question = (
                question
                .replace(
                    "질문:",
                    "",
                    1
                )
                .strip()
            )


        if not question:

            raise ValueError(
                "AI가 빈 질문을 반환했습니다."
            )


        if is_similar_question(
            question,
            recent_questions
        ):

            question = random.choice(
                available_fallbacks
            )


    except Exception as error:

        print(
            "Gemini 후속 질문 생성 실패:",
            error
        )


        question = random.choice(
            available_fallbacks
        )


    # -----------------------------------------------------
    # 생성된 질문 저장
    # -----------------------------------------------------

    if discovery_id is not None:

        try:

            (
                supabase
                .table("discoveries")
                .update({
                    "ai_question":
                        question
                })
                .eq(
                    "id",
                    discovery_id
                )
                .execute()
            )


        except Exception as error:

            print(
                "AI 질문 저장 실패:",
                error
            )


    return jsonify({
        "question":
            question
    })


# =========================================================
# 생각 저장
# =========================================================

@app.post(
    "/api/discoveries/<int:discovery_id>/reflection"
)
def save_reflection(
    discovery_id
):

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    reflection = (
        data
        .get(
            "reflection",
            ""
        )
        .strip()
    )


    if not reflection:

        return jsonify({
            "error":
                "생각을 입력해주세요."
        }), 400


    try:

        (
            supabase
            .table("discoveries")
            .update({
                "reflection":
                    reflection
            })
            .eq(
                "id",
                discovery_id
            )
            .execute()
        )


    except Exception as error:

        print(
            "생각 저장 실패:",
            error
        )

        return jsonify({
            "error":
                "생각을 저장하지 못했습니다."
        }), 500


    return jsonify({
        "message":
            "생각이 저장되었습니다."
    })

# 기록 삭제
@app.delete("/api/discoveries/<int:discovery_id>")
def delete_discovery(discovery_id):

    # 삭제할 기록 조회
    response = (
        supabase
        .table("discoveries")
        .select("id, image_path")
        .eq("id", discovery_id)
        .limit(1)
        .execute()
    )

    if not response.data:

        return jsonify({
            "error": "삭제할 기록을 찾을 수 없습니다."
        }), 404


    discovery = response.data[0]

    image_path = discovery.get("image_path")


    # 기록 삭제
    try:

        (
            supabase
            .table("discoveries")
            .delete()
            .eq("id", discovery_id)
            .execute()
        )

    except Exception as error:

        print(
            "기록 삭제 실패:",
            error
        )

        return jsonify({
            "error": "기록을 삭제하지 못했습니다."
        }), 500


    # 사진이 있다면 Storage에서도 삭제
    if image_path:

        try:

            (
                supabase
                .storage
                .from_(STORAGE_BUCKET)
                .remove([
                    image_path
                ])
            )

        except Exception as error:

            # 기록 삭제는 성공했지만
            # 사진 삭제에 실패한 경우
            print(
                "사진 삭제 실패:",
                error
            )


    return jsonify({
        "message": "기록이 삭제되었습니다."
    })

# =========================================================
# 로컬 실행
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )