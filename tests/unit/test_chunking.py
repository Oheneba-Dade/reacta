import pytest

from backend.workers.tasks import chunk_transcript


def test_empty_string_returns_empty_list():
    assert chunk_transcript("") == []


def test_whitespace_only_returns_empty_list():
    assert chunk_transcript("   ") == []


def test_short_text_returns_single_chunk():
    text = "one two three"
    result = chunk_transcript(text, max_words=10)
    assert result == [text]


def test_exactly_max_words_returns_single_chunk():
    words = " ".join(f"word{i}" for i in range(100))
    result = chunk_transcript(words, max_words=100, overlap=20)
    assert len(result) == 1
    assert result[0] == words


def test_one_word_over_max_creates_two_chunks():
    words = " ".join(f"word{i}" for i in range(101))
    result = chunk_transcript(words, max_words=100, overlap=20)
    assert len(result) == 2


def test_chunks_have_correct_overlap():
    # 120 words → step=80, so chunk1=words[0:100], chunk2=words[80:120]
    words = [f"word{i}" for i in range(120)]
    text = " ".join(words)
    result = chunk_transcript(text, max_words=100, overlap=20)
    assert len(result) == 2

    chunk1_words = result[0].split()
    chunk2_words = result[1].split()

    # Last 20 words of chunk1 should equal first 20 words of chunk2
    assert chunk1_words[-20:] == chunk2_words[:20]


def test_two_full_chunks():
    words = " ".join(f"word{i}" for i in range(200))
    result = chunk_transcript(words, max_words=100, overlap=20)
    # step=80, so chunks at 0, 80, 160 → 3 chunks
    assert len(result) == 3


def test_all_chunks_are_nonempty_strings():
    words = " ".join(f"w{i}" for i in range(250))
    result = chunk_transcript(words, max_words=100, overlap=20)
    assert all(isinstance(c, str) and c.strip() for c in result)
