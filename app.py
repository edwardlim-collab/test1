#!/usr/bin/env python3
"""Slack 영단어 퀴즈 - 웹 인터페이스

실행:
    python3 app.py
    브라우저에서 http://localhost:5000 접속
"""

import json
import random
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

from quiz import build_options, get_daily_words, load_all_words
from words import WORDS

app = Flask(__name__)
app.secret_key = "slack-word-quiz-secret"

WORDS_SLACK_PATH = Path(__file__).parent / "words_slack.json"


def get_word_pool():
    all_words = load_all_words()
    return all_words, get_daily_words(all_words)


# ── 라우트 ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    all_words, daily_words = get_word_pool()
    slack_count = len(all_words) - len(WORDS)
    today = date.today().strftime("%Y년 %m월 %d일")
    return render_template(
        "index.html",
        today=today,
        daily_words=daily_words,
        total=len(all_words),
        base_count=len(WORDS),
        slack_count=slack_count,
    )


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
    app.run(debug=True, port=5000)
