#!/usr/bin/env python3
"""Slack 영단어 퀴즈

매일 10개의 단어를 선정하고 뜻 맞추기 퀴즈를 제공합니다.
날짜 기반 시드를 사용해 같은 날에는 항상 동일한 단어가 출제됩니다.

단어 출처:
  - words.py        : 기본 큐레이션 단어
  - words_slack.json: slack_words.py 로 자동 수집한 단어
"""

import json
import random
from datetime import date
from pathlib import Path

from words import WORDS

WORDS_PER_DAY = 10
OPTIONS_PER_QUESTION = 4
WORDS_SLACK_PATH = Path(__file__).parent / "words_slack.json"


def load_all_words() -> list[dict]:
    """words.py와 words_slack.json의 단어를 합쳐서 반환합니다."""
    all_words = list(WORDS)
    if WORDS_SLACK_PATH.exists():
        with open(WORDS_SLACK_PATH, encoding="utf-8") as f:
            slack_words = json.load(f)
        all_words.extend(slack_words)
    return all_words


def get_daily_words(all_words: list[dict]) -> list[dict]:
    """오늘 날짜를 시드로 사용해 매일 다른 10개의 단어를 선정합니다."""
    today = date.today()
    seed = today.year * 10000 + today.month * 100 + today.day
    rng = random.Random(seed)
    return rng.sample(all_words, min(WORDS_PER_DAY, len(all_words)))


def show_word_list(words: list[dict], all_words: list[dict]) -> None:
    """오늘의 단어 목록을 출력합니다."""
    today = date.today()
    slack_count = len(all_words) - len(WORDS)
    print(f"\n{'=' * 54}")
    print(f"  {today.strftime('%Y년 %m월 %d일')} 오늘의 단어 {len(words)}개")
    print(f"  (전체 {len(all_words)}개 / 기본 {len(WORDS)}개 + Slack {slack_count}개)")
    print(f"{'=' * 54}")
    for i, entry in enumerate(words, 1):
        print(f"  {i:2d}. {entry['word']:<20} {entry['meaning']}")
    print(f"{'=' * 54}\n")


def build_options(correct_meaning: str, all_words: list[dict]) -> list[str]:
    """정답 1개 + 오답 3개로 구성된 보기를 만듭니다."""
    all_meanings = [w["meaning"] for w in all_words if w["meaning"] != correct_meaning]
    wrong = random.sample(all_meanings, OPTIONS_PER_QUESTION - 1)
    options = wrong + [correct_meaning]
    random.shuffle(options)
    return options


def ask_question(index: int, entry: dict, all_words: list[dict]) -> bool:
    """한 문제를 출제하고 정오 여부를 반환합니다."""
    correct = entry["meaning"]
    options = build_options(correct, all_words)
    correct_idx = options.index(correct) + 1

    print(f"[{index}/{WORDS_PER_DAY}] '{entry['word']}'의 뜻은?")
    for j, option in enumerate(options, 1):
        print(f"  {j}. {option}")

    while True:
        try:
            answer = input("정답 번호 입력 (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n퀴즈를 종료합니다.")
            raise

        if answer in ("1", "2", "3", "4"):
            break
        print("  1~4 사이의 숫자를 입력하세요.")

    if int(answer) == correct_idx:
        print("  정답!\n")
        if "example" in entry:
            print(f"  예문: {entry['example']}\n")
        return True
    else:
        print(f"  오답. 정답은 {correct_idx}번: {correct}\n")
        if "example" in entry:
            print(f"  예문: {entry['example']}\n")
        return False


def run_quiz(words: list[dict], all_words: list[dict]) -> None:
    """단어 뜻 맞추기 퀴즈를 실행합니다."""
    print("\n퀴즈를 시작합니다! 각 단어의 올바른 뜻을 고르세요.\n")
    score = 0
    total = len(words)

    try:
        for i, entry in enumerate(words, 1):
            if ask_question(i, entry, all_words):
                score += 1
    except KeyboardInterrupt:
        return

    print(f"{'=' * 54}")
    print(f"  퀴즈 완료!  점수: {score} / {total}")
    if score == WORDS_PER_DAY:
        print("  완벽합니다! 모두 맞췄어요!")
    elif score >= 7:
        print("  잘했어요!")
    elif score >= 4:
        print("  조금 더 공부해봐요!")
    else:
        print("  다시 한 번 도전해보세요!")
    print(f"{'=' * 54}\n")


def main():
    print("\n Slack 영단어 퀴즈에 오신 것을 환영합니다!")
    all_words = load_all_words()
    daily_words = get_daily_words(all_words)

    while True:
        print("메뉴를 선택하세요:")
        print("  1. 오늘의 단어 보기")
        print("  2. 퀴즈 시작")
        print("  3. 종료")

        try:
            choice = input("선택 (1-3): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다. 안녕히 가세요!")
            break

        if choice == "1":
            show_word_list(daily_words, all_words)
        elif choice == "2":
            run_quiz(daily_words, all_words)
        elif choice == "3":
            print("\n종료합니다. 안녕히 가세요!\n")
            break
        else:
            print("1~3 사이의 숫자를 입력하세요.\n")


if __name__ == "__main__":
    main()
