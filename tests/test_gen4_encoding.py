"""Tests for core/gen4_encoding.py"""

import struct
import pytest
from core.gen4_encoding import (
    encode_name, decode_name, validate_name,
    TERMINATOR, MAX_NAME_LEN, _CHAR_TO_GEN4,
)


class TestEncodeName:
    def test_output_always_16_bytes(self):
        for name in ["A", "AB", "ABCDEFG", " "]:
            assert len(encode_name(name)) == 16

    def test_terminator_written_after_last_char(self):
        for name in ["A", "ABC", "ABCDEFG"]:
            data = encode_name(name)
            term_offset = len(name) * 2
            val = struct.unpack_from("<H", data, term_offset)[0]
            assert val == TERMINATOR, (
                f"Expected terminator at slot {len(name)}, got 0x{val:04X}"
            )

    def test_7_char_name_terminator_in_slot_7(self):
        # This was the original bug — 7-char names got 0x0000 not 0xFFFF at slot 7
        data = encode_name("ABCDEFG")
        val = struct.unpack_from("<H", data, 14)[0]
        assert val == TERMINATOR

    def test_chars_encoded_correctly(self):
        data = encode_name("A")
        val = struct.unpack_from("<H", data, 0)[0]
        assert val == _CHAR_TO_GEN4["A"]

    def test_lowercase_encoded(self):
        data = encode_name("a")
        val = struct.unpack_from("<H", data, 0)[0]
        assert val == _CHAR_TO_GEN4["a"]

    def test_space_encoded(self):
        data = encode_name(" ")
        val = struct.unpack_from("<H", data, 0)[0]
        assert val == _CHAR_TO_GEN4[" "]

    def test_unsupported_char_raises(self):
        with pytest.raises(ValueError, match="not supported"):
            encode_name("@")

    def test_roundtrip(self):
        for name in ["RED", "Blue", "ASH", "a b c", "ABCDEFG"]:
            assert decode_name(encode_name(name)) == name


class TestDecodeName:
    def test_stops_at_terminator(self):
        data = encode_name("Hi")
        assert decode_name(data) == "Hi"

    def test_empty_if_first_slot_terminator(self):
        data = bytes([0xFF, 0xFF] + [0x00] * 14)
        assert decode_name(data) == ""

    def test_unknown_code_replaced_with_question_mark(self):
        # code 0x0000 is not in the table
        data = bytes([0x00, 0x00, 0xFF, 0xFF] + [0x00] * 12)
        result = decode_name(data)
        assert result == "?"


class TestValidateName:
    def test_valid_names_return_no_errors(self):
        for name in ["RED", "blue", "ash", "A B", "ABCDEFG"]:
            assert validate_name(name) == []

    def test_empty_name_is_invalid(self):
        assert validate_name("") != []

    def test_too_long_is_invalid(self):
        errors = validate_name("ABCDEFGH")  # 8 chars
        assert any("too long" in e for e in errors)

    def test_unsupported_char_reported(self):
        errors = validate_name("A@B")
        assert any("@" in e for e in errors)

    def test_exactly_7_chars_valid(self):
        assert validate_name("ABCDEFG") == []
