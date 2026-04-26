"""
Gen 4 trainer name encoding.

Strings are stored as arrays of little-endian 16-bit values using a proprietary
mapping.  0xFFFF terminates the string; unused slots are zeroed.

Ported from PKHeX.Core StringConverter4.cs:
  https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/PKM/Strings/StringConverter4.cs
Bulbapedia reference:
  https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_IV)
"""

from __future__ import annotations
import struct

_CHAR_TO_GEN4: dict[str, int] = {
    " ":  0x0001,
    **{chr(ord("0") + i): 0x00A2 + i for i in range(10)},
    **{chr(ord("A") + i): 0x00B3 + i for i in range(26)},
    **{chr(ord("a") + i): 0x00CD + i for i in range(26)},
    "!":  0x0002,
    "?":  0x01AC,
    ".":  0x01AF,
    ",":  0x01AE,
    "-":  0x0109,
    "'":  0x01B3,
    "/":  0x011C,
    "♂":  0x246D,
    "♀":  0x246E,
}

_GEN4_TO_CHAR: dict[int, str] = {v: k for k, v in _CHAR_TO_GEN4.items()}

TERMINATOR: int = 0xFFFF
MAX_NAME_LEN: int = 7  # 8 slots total; slot 8 holds the terminator


def encode_name(name: str) -> bytes:
    """
    Encode a trainer name to 16 bytes (8 × LE u16).
    Raises ValueError for unsupported characters or names longer than MAX_NAME_LEN.
    """
    if len(name) > MAX_NAME_LEN:
        raise ValueError(f"Name too long ({len(name)} chars; max {MAX_NAME_LEN})")
    out = bytearray(16)
    for i, ch in enumerate(name):
        code = _CHAR_TO_GEN4.get(ch)
        if code is None:
            raise ValueError(
                f"Character {ch!r} is not supported in Gen 4 names. "
                f"Supported characters: letters, digits, space, basic punctuation."
            )
        struct.pack_into("<H", out, i * 2, code)
    struct.pack_into("<H", out, len(name) * 2, TERMINATOR)
    return bytes(out)


def decode_name(data: bytes) -> str:
    """Decode 16 raw save bytes into a trainer name string."""
    chars = []
    for i in range(8):
        code = struct.unpack_from("<H", data, i * 2)[0]
        if code == TERMINATOR:
            break
        chars.append(_GEN4_TO_CHAR.get(code, "?"))
    return "".join(chars)


def validate_name(name: str) -> list[str]:
    """Return a list of human-readable error strings, empty if the name is valid."""
    errors: list[str] = []
    if not name:
        errors.append("Name cannot be empty.")
    if len(name) > MAX_NAME_LEN:
        errors.append(f"Name is too long ({len(name)} chars; max {MAX_NAME_LEN}).")
    for ch in name:
        if ch not in _CHAR_TO_GEN4:
            errors.append(f"Unsupported character: {ch!r}")
    return errors
