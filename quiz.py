#!/usr/bin/env python3
"""Slack 영단어 퀴즈

매일 10개의 단어를 선정하고 뜻 맞추기 퀴즈를 제공합니다.
날짜 기반 시드를 사용해 같은 날에는 항상 동일한 단어가 출제됩니다.
"""

import random
from datetime import date

from words import WORDS

WORDS_PER_DAY = 10
OPTIONS_PER_QUESTION = 4


def get_daily_words():
    """오늘 날짜를 시드로 사용해 매일 다른 10개의 단어를 선정합니다."""
    today = date.today()
    seed = today.year * 10000 + today.month * 100 + today.day
    rng = random.Random(seed)
    return rng.sample(WORDS, WORDS_PER_DAY)


def show_word_list(words):
    """오늘의 단어 목록을 출력합니다."""
    today = date.today()
    print(f"\n{'=' * 54}")
    print(f"  {today.strftime('%Y년 %m월 %d일')} 오늘의 단어 {WORDS_PER_DAY}개")
    print(f"{'=' * 54}")
    for i, entry in enumerate(words, 1):
        print(f"  {i:2d}. {entry['word']:<20} {entry['meaning']}")
    print(f"{'=' * 54}\n")


def build_options(correct_meaning):
    """정답 1개 + 오답 3개로 구성된 보기를 만듭니다."""
    all_meanings = [w["meaning"] for w in WORDS if w["meaning"] != correct_meaning]
    wrong = random.sample(all_meanings, OPTIONS_PER_QUESTION - 1)
    options = wrong + [correct_meaning]
    random.shuffle(options)
    return options


def ask_question(index, entry):
    """한 문제를 출제하고 정오 여부를 반환합니다."""
    correct = entry["meaning"]
    options = build_options(correct)
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


def run_quiz(words):
    """단어 뜻 맞추기 퀴즈를 실행합니다."""
    print("\n퀴즈를 시작합니다! 각 단어의 올바른 뜻을 고르세요.\n")
    score = 0

    try:
        for i, entry in enumerate(words, 1):
            if ask_question(i, entry):
                score += 1
    except KeyboardInterrupt:
        return

    print(f"{'=' * 54}")
    print(f"  퀴즈 완료!  점수: {score} / {WORDS_PER_DAY}")
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
    daily_words = get_daily_words()

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
            show_word_list(daily_words)
        elif choice == "2":
            run_quiz(daily_words)
        elif choice == "3":
            print("\n종료합니다. 안녕히 가세요!\n")
            break
        else:
            print("1~3 사이의 숫자를 입력하세요.\n")


if __name__ == "__main__":
    main()
