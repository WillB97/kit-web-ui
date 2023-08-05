from __future__ import annotations

from pathlib import Path
from secrets import choice
from string import ascii_letters, digits


def generate_wordlist(word_file: str | Path) -> list[str]:
    with open(word_file) as wordlist:
        return [
            clean_word.lower()
            for word in wordlist
            if len(clean_word := word.strip()) > 4
            and len(clean_word) < 10
            and clean_word.isalpha()
        ]


def generate_password(wordlist: list[str] | None = None) -> str:
    if wordlist:
        return '-'.join(choice(wordlist) for _ in range(2))
    else:
        return ''.join(choice(ascii_letters + digits) for _ in range(12))
