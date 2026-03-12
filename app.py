#!/usr/bin/env python3
"""Slack 영단어 퀴즈 - 웹 인터페이스

실행:
    python3 app.py
    브라우저에서 http://localhost:5000 접속
"""

import json
import os
import time
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

from quiz import build_options, get_daily_words, load_all_words
from slack_words import extract_candidate_words, fetch_definition, load_existing_words, load_slack_words, save_slack_words
from words import WORDS

app = Flask(__name__)
app.secret_key = "slack-word-quiz-secret"

WORDS_SLACK_PATH = Path(__file__).parent / "words_slack.json"
SLACK_CACHE_PATH = Path(__file__).parent / "slack_messages_cache.json"
DEFINITION_API_DELAY = 0.3
TARGET_NEW_WORDS = 10


def get_word_pool():
    all_words = load_all_words()
    return all_words, get_daily_words(all_words)


def load_cached_messages():
    """slack_messages_cache.json에서 메시지와 수집 시각을 읽습니다."""
    if not SLACK_CACHE_PATH.exists():
        return [], None
    with open(SLACK_CACHE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    fetched_at = data.get("fetched_at")
    messages = data.get("messages", [])
    return messages, fetched_at


# ── 라우트 ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    all_words, daily_words = get_word_pool()
    today = date.today().strftime("%Y년 %m월 %d일")
    return render_template(
        "index.html",
        today=today,
        daily_words=daily_words,
        total=len(all_words),
        quiz_count=len(daily_words),
    )


@app.route("/api/slack-fetch", methods=["POST"])
def slack_fetch():
    messages, fetched_at = load_cached_messages()

    if not messages:
        msg = "최근 7일간 #announcements에 새 메시지가 없습니다."
        if fetched_at:
            msg += f" (마지막 수집: {fetched_at[:10]})"
        return jsonify({"status": "no_messages", "message": msg})

    existing = load_existing_words()
    candidates = extract_candidate_words(messages, existing)
    if not candidates:
        return jsonify({"status": "no_words", "message": "메시지에서 추가할 새 단어를 찾지 못했습니다."})

    slack_words = load_slack_words()
    added_words = []
    for word in candidates:
        if len(added_words) >= TARGET_NEW_WORDS:
            break
        entry = fetch_definition(word)
        if entry:
            slack_words.append(entry)
            existing.add(word)
            added_words.append(entry["word"])
            time.sleep(DEFINITION_API_DELAY)

    if not added_words:
        return jsonify({"status": "no_words", "message": "사전에서 정의를 찾을 수 있는 새 단어가 없습니다."})

    save_slack_words(slack_words)
    return jsonify({
        "status": "added",
        "count": len(added_words),
        "words": added_words,
        "message": f"{len(added_words)}개 단어가 추가됐습니다: {', '.join(added_words)}",
    })


@app.route("/quiz")
def quiz_page():
    all_words, daily_words = get_word_pool()
    session["quiz_words"] = [w["word"] for w in daily_words]
    session["score"] = 0
    session["current"] = 0
    today = date.today().strftime("%Y년 %m월 %d일")
    return render_template("quiz.html", today=today, total=len(daily_words))


@app.route("/api/question")
def get_question():
    all_words, daily_words = get_word_pool()
    idx = session.get("current", 0)

    if idx >= len(daily_words):
        return jsonify({"done": True, "score": session.get("score", 0), "total": len(daily_words)})

    entry = daily_words[idx]
    options = build_options(entry["meaning"], all_words)
    correct_idx = options.index(entry["meaning"])

    # 보기 순서를 세션에 저장해 답안 제출 시 일관성 유지
    session["current_options"] = options
    session["current_correct_idx"] = correct_idx

    return jsonify({
        "done": False,
        "index": idx + 1,
        "total": len(daily_words),
        "word": entry["word"],
        "options": options,
        "correct_idx": correct_idx,
        "example": entry.get("example", ""),
    })


@app.route("/api/answer", methods=["POST"])
def submit_answer():
    data = request.get_json()
    all_words, daily_words = get_word_pool()
    idx = session.get("current", 0)

    if idx >= len(daily_words):
        return jsonify({"error": "quiz finished"}), 400

    entry = daily_words[idx]
    correct_idx = session.get("current_correct_idx")
    is_correct = data.get("answer") == correct_idx

    if is_correct:
        session["score"] = session.get("score", 0) + 1

    session["current"] = idx + 1

    return jsonify({
        "correct": is_correct,
        "correct_idx": correct_idx,
        "meaning": entry["meaning"],
        "example": entry.get("example", ""),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
