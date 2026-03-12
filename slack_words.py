#!/usr/bin/env python3
"""슬랙 채널 메시지에서 새 영단어를 추출해 words_slack.json에 매일 10개씩 추가합니다.

필요한 환경 변수:
    SLACK_BOT_TOKEN   - Slack Bot OAuth 토큰 (xoxb-...)
    SLACK_CHANNEL_ID  - 메시지를 가져올 채널 ID (예: C0123ABCDEF)

Slack 앱 권한 (OAuth Scopes):
    channels:history  - 공개 채널 메시지 읽기
    groups:history    - 비공개 채널 메시지 읽기 (비공개 채널인 경우)

사용법:
    python3 slack_words.py

cron 예시 (매일 오전 9시 실행):
    0 9 * * * cd /path/to/project && python3 slack_words.py
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from words import WORDS

WORDS_SLACK_PATH = Path(__file__).parent / "words_slack.json"
TARGET_NEW_WORDS = 10
MIN_WORD_LENGTH = 5          # 너무 짧은 단어 제외
FETCH_HOURS = 48             # 최근 N시간 메시지 분석 (단어가 적을 경우 범위 확대)
DEFINITION_API_DELAY = 0.4   # Free Dictionary API rate limit 준수 (초)

# 제외할 일반 영단어 (학습 가치가 낮은 단어)
STOP_WORDS = {
    "the", "and", "for", "are", "was", "were", "been", "have", "has", "had",
    "will", "would", "could", "should", "shall", "might", "must", "that",
    "this", "with", "from", "they", "their", "them", "then", "than", "when",
    "what", "which", "who", "how", "where", "there", "here", "into", "onto",
    "over", "under", "about", "above", "after", "before", "between", "through",
    "during", "also", "just", "even", "still", "only", "very", "much", "more",
    "most", "some", "other", "each", "every", "both", "either", "neither",
    "because", "while", "since", "although", "though", "unless", "until",
    "being", "doing", "going", "using", "making", "having", "getting",
    "your", "mine", "ours", "them", "these", "those", "such", "same",
    "back", "down", "away", "well", "good", "great", "nice", "okay",
    "thanks", "thank", "sorry", "please", "right", "sure", "yeah", "nope",
    "hello", "today", "tomorrow", "yesterday", "week", "month", "year",
    "time", "work", "think", "know", "want", "need", "make", "take",
    "come", "look", "send", "check", "keep", "feel", "help", "call",
    "said", "says", "made", "goes", "came", "took", "gave", "left",
    "team", "meet", "next", "last", "first", "again", "might", "else",
    "does", "didn", "isn", "aren", "won", "can", "cannot", "would",
    "things", "something", "anything", "everything", "nothing", "someone",
    "anyone", "everyone", "somewhere", "anywhere", "everywhere",
    "like", "just", "then", "when", "really", "actually", "basically",
    "probably", "definitely", "absolutely", "maybe", "perhaps",
}


# ── Slack API ────────────────────────────────────────────────────────────────

def fetch_slack_messages(token: str, channel_id: str, hours: int = FETCH_HOURS) -> list[str]:
    """Slack 채널에서 최근 N시간의 메시지 텍스트 목록을 반환합니다."""
    oldest = (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp()
    params = urllib.parse.urlencode({
        "channel": channel_id,
        "oldest": str(oldest),
        "limit": 1000,
    })
    url = f"https://slack.com/api/conversations.history?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.URLError as e:
        raise RuntimeError(f"Slack API 연결 실패: {e}") from e

    if not data.get("ok"):
        error = data.get("error", "unknown")
        hint = {
            "not_in_channel": "봇을 채널에 초대해 주세요: /invite @your-bot",
            "missing_scope": "Slack 앱에 channels:history 권한을 추가해 주세요.",
            "invalid_auth": "SLACK_BOT_TOKEN 값을 확인해 주세요.",
            "channel_not_found": "SLACK_CHANNEL_ID 값을 확인해 주세요.",
        }.get(error, "")
        raise RuntimeError(f"Slack API 오류: {error}" + (f"\n  힌트: {hint}" if hint else ""))

    messages = data.get("messages", [])
    # 봇 메시지 제외, 실제 사용자 메시지만
    return [m.get("text", "") for m in messages if m.get("subtype") is None]


# ── 단어 추출 ────────────────────────────────────────────────────────────────

def extract_candidate_words(messages: list[str], existing_words: set[str]) -> list[str]:
    """
    메시지에서 후보 영단어를 추출합니다.
    - Slack 마크업(<@U...>, <http...>, *bold* 등) 제거
    - 알파벳만 포함, 최소 길이 이상
    - stop words 및 기존 단어 제외
    - 등장 빈도 내림차순 정렬
    """
    slack_markup = re.compile(r"<[^>]+>|:[a-z_]+:|```[\s\S]*?```|`[^`]+`|\*[^*]+\*|_[^_]+_")
    word_pattern = re.compile(rf"\b[a-zA-Z]{{{MIN_WORD_LENGTH},}}\b")

    freq: dict[str, int] = {}
    for msg in messages:
        clean = slack_markup.sub(" ", msg)
        for match in word_pattern.finditer(clean):
            word = match.group().lower()
            if word not in STOP_WORDS and word not in existing_words:
                freq[word] = freq.get(word, 0) + 1

    # 2회 이상 등장한 단어만 후보로 (1회짜리는 오타/고유명사 가능성 높음)
    candidates = [w for w, cnt in freq.items() if cnt >= 2]
    return sorted(candidates, key=lambda w: freq[w], reverse=True)


# ── 사전 조회 ────────────────────────────────────────────────────────────────

def fetch_definition(word: str) -> dict | None:
    """
    Free Dictionary API(https://api.dictionaryapi.dev)에서 단어 정보를 조회합니다.
    성공하면 {"word", "meaning", "example"} 딕셔너리를 반환하고,
    단어가 없거나 요청 실패 시 None을 반환합니다.
    """
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
    req = urllib.request.Request(url, headers={"User-Agent": "SlackWordQuiz/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # 사전에 없는 단어
        return None
    except urllib.error.URLError:
        return None

    if not isinstance(data, list) or not data:
        return None

    meaning, example = "", ""
    for m in data[0].get("meanings", []):
        for d in m.get("definitions", []):
            if not meaning and d.get("definition"):
                meaning = d["definition"]
            if not example and d.get("example"):
                example = d["example"]
        if meaning and example:
            break

    if not meaning:
        return None

    # 너무 긴 경우 말줄임 처리
    if len(meaning) > 100:
        meaning = meaning[:97] + "..."
    if len(example) > 120:
        example = example[:117] + "..."

    return {"word": word, "meaning": meaning, "example": example}


# ── 저장/로드 ─────────────────────────────────────────────────────────────────

def load_existing_words() -> set[str]:
    """words.py + words_slack.json에 등록된 단어 집합을 반환합니다."""
    existing = {w["word"].lower() for w in WORDS}
    if WORDS_SLACK_PATH.exists():
        with open(WORDS_SLACK_PATH, encoding="utf-8") as f:
            existing.update(w["word"].lower() for w in json.load(f))
    return existing


def load_slack_words() -> list[dict]:
    """words_slack.json의 현재 단어 목록을 반환합니다."""
    if WORDS_SLACK_PATH.exists():
        with open(WORDS_SLACK_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_slack_words(words_list: list[dict]) -> None:
    """단어 목록을 words_slack.json에 저장합니다."""
    with open(WORDS_SLACK_PATH, "w", encoding="utf-8") as f:
        json.dump(words_list, f, ensure_ascii=False, indent=4)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel_id = os.environ.get("SLACK_CHANNEL_ID")

    if not token or not channel_id:
        print("오류: 환경 변수를 설정해 주세요.\n")
        print("  export SLACK_BOT_TOKEN=xoxb-...")
        print("  export SLACK_CHANNEL_ID=C0123ABCDEF")
        raise SystemExit(1)

    # 1. Slack 메시지 수집
    print(f"Slack 채널({channel_id}) 메시지 가져오는 중 (최근 {FETCH_HOURS}시간)...")
    messages = fetch_slack_messages(token, channel_id)
    print(f"  {len(messages)}개 메시지 수집 완료")

    # 2. 기존 단어 목록 로드
    existing = load_existing_words()
    print(f"  기존 등록 단어: {len(existing)}개")

    # 3. 후보 단어 추출
    candidates = extract_candidate_words(messages, existing)
    print(f"  신규 후보 단어: {len(candidates)}개")

    if not candidates:
        print("\n메시지에서 새 단어를 찾지 못했습니다.")
        print("  - 채널에 충분한 영어 메시지가 있는지 확인해 주세요.")
        print(f"  - 필요 시 FETCH_HOURS 값({FETCH_HOURS})을 늘려 더 넓은 범위를 분석할 수 있습니다.")
        return

    # 4. 사전 조회 및 신규 단어 추가
    slack_words = load_slack_words()
    added = 0

    print(f"\n사전 조회 중 (목표: {TARGET_NEW_WORDS}개)...")
    for word in candidates:
        if added >= TARGET_NEW_WORDS:
            break

        entry = fetch_definition(word)
        if not entry:
            continue

        slack_words.append(entry)
        existing.add(word)
        added += 1
        print(f"  [{added:2d}] {word:<20} {entry['meaning'][:50]}")
        time.sleep(DEFINITION_API_DELAY)

    # 5. 저장
    if added == 0:
        print("\n추가할 새 단어를 찾지 못했습니다.")
        print("  사전에 없는 단어이거나, 모두 기존에 등록된 단어일 수 있습니다.")
    else:
        save_slack_words(slack_words)
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"\n{today} 기준으로 {added}개 단어가 words_slack.json에 추가되었습니다.")
        print(f"누적 Slack 단어 수: {len(slack_words)}개 / 전체 단어 수: {len(WORDS) + len(slack_words)}개")


if __name__ == "__main__":
    main()
