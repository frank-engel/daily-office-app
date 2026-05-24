"""Tests for bible/reference_parser.py"""
import pytest
from app.bible.reference_parser import parse_reference, VerseRange

EN = "–"  # en-dash U+2013


def r(book, sc, sv, ec, ev):
    return VerseRange(book, sc, sv, ec, ev)


class TestSimpleRange:
    def test_simple_range(self):
        result = parse_reference(f"Isa 1:1{EN}9")
        assert result == [r("Isa", 1, 1, 1, 9)]

    def test_single_verse(self):
        result = parse_reference("John 3:16")
        assert result == [r("John", 3, 16, 3, 16)]

    def test_letter_suffix_stripped(self):
        result = parse_reference(f"2 Pet 2:1{EN}10a")
        assert result == [r("2 Pet", 2, 1, 2, 10)]

    def test_both_ends_letter_suffix(self):
        result = parse_reference(f"Isa 6:1{EN}8b")
        assert result == [r("Isa", 6, 1, 6, 8)]


class TestChapterSpanning:
    def test_cross_chapter(self):
        result = parse_reference(f"Luke 20:41{EN}21:4")
        assert result == [r("Luke", 20, 41, 21, 4)]


class TestMultiRange:
    def test_multi_range_same_chapter(self):
        result = parse_reference(f"Isa 5:8{EN}12, 18{EN}23")
        assert len(result) == 2
        assert result[0] == r("Isa", 5, 8, 5, 12)
        assert result[1] == r("Isa", 5, 18, 5, 23)

    def test_semicolon_separated(self):
        result = parse_reference(f"Gal 3:23{EN}29; 4:4{EN}7")
        assert len(result) == 2
        assert result[0] == r("Gal", 3, 23, 3, 29)
        assert result[1] == r("Gal", 4, 4, 4, 7)


class TestParenthetical:
    def test_optional_suffix_stripped(self):
        result = parse_reference(f"John 17:1{EN}11(12{EN}26)")
        assert result == [r("John", 17, 1, 17, 11)]

    def test_optional_prefix_stripped(self):
        # "Isa 42:(1–9)10–17" → Isa 42:10–17
        result = parse_reference(f"Isa 42:(1{EN}9)10{EN}17")
        assert result == [r("Isa", 42, 10, 42, 17)]


class TestKnownOverrides:
    def test_rev_override(self):
        result = parse_reference(f"Rev 21:1{EN}4,{EN}14")
        assert len(result) == 2
        assert result[0] == r("Rev", 21, 1, 21, 4)
        assert result[1] == r("Rev", 21, 9, 21, 14)


class TestEdgeCases:
    def test_empty_string(self):
        assert parse_reference("") == []

    def test_whitespace(self):
        assert parse_reference("   ") == []

    def test_two_digit_prefix_book(self):
        result = parse_reference(f"1 Sam 1:1{EN}20")
        assert result == [r("1 Sam", 1, 1, 1, 20)]

    def test_nt_book(self):
        result = parse_reference(f"Rev 4:1{EN}11")
        assert result == [r("Rev", 4, 1, 4, 11)]
