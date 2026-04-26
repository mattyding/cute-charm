"""
Gen 4 save-file patching (Diamond, Pearl, Platinum, HeartGold, SoulSilver).

Patches trainer name, TID, SID, and gender in an existing save file, then
recalculates the General block checksum so the game accepts the modified save.

Ported from PKHeX.Core:
  SAV4DP.cs   – https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Saves/SAV4DP.cs
  SAV4Pt.cs   – https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Saves/SAV4Pt.cs
  SAV4HGSS.cs – https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Saves/SAV4HGSS.cs
  Checksums.cs– https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Saves/Util/Checksums.cs
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from .gen4_encoding import encode_name


@dataclass(frozen=True)
class GameConfig:
    name: str
    general_block_size: int   # bytes including footer
    trainer1_offset: int       # offset of trainer info within the General block
    footer_size: int           # CRC covers everything before this tail


GAME_CONFIGS: dict[str, GameConfig] = {
    "Diamond":     GameConfig("Diamond",     0xC100, 0x64, 0x14),
    "Pearl":       GameConfig("Pearl",       0xC100, 0x64, 0x14),
    "Platinum":    GameConfig("Platinum",    0xCF2C, 0x68, 0x14),
    "HeartGold":   GameConfig("HeartGold",   0xF628, 0x64, 0x10),
    "SoulSilver":  GameConfig("SoulSilver",  0xF628, 0x64, 0x10),
}

_BACKUP_OFFSET = 0x40000

# Field offsets relative to trainer1_offset (identical across all Gen 4 games)
_OFF_NAME   = 0x00   # 16 bytes (8 × LE u16)
_OFF_TID    = 0x10   # u16 LE
_OFF_SID    = 0x12   # u16 LE
_OFF_GENDER = 0x18   # u8: 0=Male 1=Female


def crc16_ccitt(data: bytes | bytearray) -> int:
    """
    Ported verbatim from PKHeX Checksums.cs::CRC16_CCITT.
    https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Saves/Util/Checksums.cs
    """
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4) & 0xFF
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot


def _patch_block(
    save: bytearray,
    partition_base: int,
    cfg: GameConfig,
    name_bytes: bytes | None,
    gender: int,
    tid: int,
    sid: int,
) -> None:
    t1 = partition_base + cfg.trainer1_offset
    if name_bytes is not None:
        save[t1 + _OFF_NAME : t1 + _OFF_NAME + 16] = name_bytes
    struct.pack_into("<H", save, t1 + _OFF_TID,    tid)
    struct.pack_into("<H", save, t1 + _OFF_SID,    sid)
    save[t1 + _OFF_GENDER] = gender

    data_end = partition_base + cfg.general_block_size - cfg.footer_size
    crc = crc16_ccitt(save[partition_base:data_end])
    struct.pack_into("<H", save, partition_base + cfg.general_block_size - 2, crc)


def _block_crc_valid(save_bytes: bytes, base: int, cfg: GameConfig) -> bool:
    data_end = base + cfg.general_block_size - cfg.footer_size
    expected = crc16_ccitt(save_bytes[base:data_end])
    stored = struct.unpack_from("<H", save_bytes, base + cfg.general_block_size - 2)[0]
    return expected == stored


def verify_game(save_bytes: bytes, game: str) -> bool:
    """Return True if the primary partition CRC matches the given game's layout."""
    cfg = GAME_CONFIGS[game]
    if len(save_bytes) < cfg.general_block_size:
        return False
    return _block_crc_valid(save_bytes, 0, cfg)


def patch_save(
    save_bytes: bytes,
    game: str,
    name: str,
    gender: int,
    tid: int,
    sid: int,
    *,
    keep_name: bool = False,
) -> bytes:
    """
    Return a patched copy of save_bytes with updated trainer info and valid checksums.

    Raises KeyError  if game is unrecognised.
    Raises ValueError if the save is too small, the name contains invalid characters,
                      or the original save's checksum doesn't match the selected game.
    """
    cfg = GAME_CONFIGS[game]
    min_size = _BACKUP_OFFSET + cfg.general_block_size
    if len(save_bytes) < min_size:
        raise ValueError(
            f"Save file is only {len(save_bytes)} bytes; "
            f"{game} requires at least {min_size} bytes."
        )

    if not _block_crc_valid(save_bytes, 0, cfg):
        # Check if any other game config matches, to give a useful hint
        matches = [g for g, c in GAME_CONFIGS.items() if g != game and verify_game(save_bytes, g)]
        hint = f"  The checksum matches: {', '.join(matches)}." if matches else ""
        raise ValueError(
            f"The save file does not appear to be a valid {game} save "
            f"(primary block checksum mismatch).{hint}\n"
            f"Make sure you selected the correct game."
        )

    name_bytes = None if keep_name else encode_name(name)
    save = bytearray(save_bytes)
    for base in (0, _BACKUP_OFFSET):
        _patch_block(save, base, cfg, name_bytes, gender, tid, sid)
    return bytes(save)
