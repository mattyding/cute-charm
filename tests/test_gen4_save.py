"""Tests for core/gen4_save.py"""

import struct
import pytest
from core.gen4_save import (
    crc16_ccitt, patch_save, GAME_CONFIGS, _BACKUP_OFFSET, verify_game,
)


# ---------------------------------------------------------------------------
# CRC-16 CCITT
# ---------------------------------------------------------------------------

class TestCrc16:
    def test_empty(self):
        # Known CRC for empty input: 0xFFFF (init state with no data)
        assert crc16_ccitt(b"") == 0xFFFF

    def test_single_zero_byte(self):
        # Sanity: result changes with data
        result = crc16_ccitt(b"\x00")
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF

    def test_deterministic(self):
        data = b"hello world"
        assert crc16_ccitt(data) == crc16_ccitt(data)

    def test_different_data_different_crc(self):
        assert crc16_ccitt(b"\x01") != crc16_ccitt(b"\x02")

    def test_accepts_bytearray(self):
        data = bytearray(b"test")
        result = crc16_ccitt(data)
        assert isinstance(result, int)

    def test_result_fits_in_16_bits(self):
        for data in [b"", b"\xFF" * 100, b"\x00\x01\x02"]:
            assert crc16_ccitt(data) <= 0xFFFF


# ---------------------------------------------------------------------------
# patch_save
# ---------------------------------------------------------------------------

def _make_fake_save(game: str) -> bytes:
    """Build a zeroed save buffer with valid CRCs for both partitions."""
    cfg = GAME_CONFIGS[game]
    size = _BACKUP_OFFSET + cfg.general_block_size
    save = bytearray(size)
    for base in (0, _BACKUP_OFFSET):
        data_end = base + cfg.general_block_size - cfg.footer_size
        crc = crc16_ccitt(save[base:data_end])
        struct.pack_into("<H", save, base + cfg.general_block_size - 2, crc)
    return bytes(save)


class TestPatchSave:
    @pytest.mark.parametrize("game", list(GAME_CONFIGS.keys()))
    def test_output_same_size_as_input(self, game):
        original = _make_fake_save(game)
        patched = patch_save(original, game, "RED", 0, 12345, 23456)
        assert len(patched) == len(original)

    @pytest.mark.parametrize("game", list(GAME_CONFIGS.keys()))
    def test_tid_sid_written_correctly(self, game):
        patched = patch_save(_make_fake_save(game), game, "RED", 0, 12345, 23456)
        cfg = GAME_CONFIGS[game]
        t1 = cfg.trainer1_offset
        tid = struct.unpack_from("<H", patched, t1 + 0x10)[0]
        sid = struct.unpack_from("<H", patched, t1 + 0x12)[0]
        assert tid == 12345
        assert sid == 23456

    @pytest.mark.parametrize("game", list(GAME_CONFIGS.keys()))
    def test_gender_written_correctly(self, game):
        for gender in (0, 1):
            patched = patch_save(_make_fake_save(game), game, "A", gender, 0, 0)
            cfg = GAME_CONFIGS[game]
            t1 = cfg.trainer1_offset
            assert patched[t1 + 0x18] == gender

    @pytest.mark.parametrize("game", list(GAME_CONFIGS.keys()))
    def test_both_partitions_patched(self, game):
        patched = patch_save(_make_fake_save(game), game, "RED", 0, 1111, 2222)
        cfg = GAME_CONFIGS[game]

        for base in (0, _BACKUP_OFFSET):
            t1 = base + cfg.trainer1_offset
            tid = struct.unpack_from("<H", patched, t1 + 0x10)[0]
            sid = struct.unpack_from("<H", patched, t1 + 0x12)[0]
            assert tid == 1111, f"Primary/backup TID mismatch at base={base:#x}"
            assert sid == 2222, f"Primary/backup SID mismatch at base={base:#x}"

    @pytest.mark.parametrize("game", list(GAME_CONFIGS.keys()))
    def test_crc_stored_little_endian(self, game):
        """CRC must be stored LE; verify the last 2 bytes equal crc16 of block data."""
        patched = patch_save(_make_fake_save(game), game, "RED", 0, 1, 2)
        cfg = GAME_CONFIGS[game]
        # Check primary partition
        block_end = cfg.general_block_size
        data_end = block_end - cfg.footer_size
        expected_crc = crc16_ccitt(patched[:data_end])
        stored_crc = struct.unpack_from("<H", patched, block_end - 2)[0]
        assert stored_crc == expected_crc, (
            f"{game}: CRC mismatch — stored {stored_crc:#06x}, expected {expected_crc:#06x}"
        )

    def test_wrong_game_raises(self):
        # HGSS save is large enough to pass the size check for Diamond,
        # but its CRC is at a different offset so Diamond validation fails.
        hgss_save = _make_fake_save("HeartGold")
        with pytest.raises(ValueError, match="checksum"):
            patch_save(hgss_save, "Diamond", "RED", 0, 0, 0)

    def test_verify_game_correct(self):
        for game in GAME_CONFIGS:
            assert verify_game(_make_fake_save(game), game)

    def test_verify_game_wrong(self):
        diamond_save = _make_fake_save("Diamond")
        assert not verify_game(diamond_save, "Platinum")

    def test_too_small_save_raises(self):
        with pytest.raises(ValueError, match="bytes"):
            patch_save(b"\x00" * 10, "Diamond", "RED", 0, 0, 0)

    def test_unknown_game_raises(self):
        with pytest.raises(KeyError):
            patch_save(bytes(0x80000), "FireRed", "RED", 0, 0, 0)

    def test_original_not_mutated(self):
        original = _make_fake_save("Diamond")
        original_copy = bytes(original)
        patch_save(original, "Diamond", "RED", 0, 9999, 8888)
        assert original == original_copy


# ---------------------------------------------------------------------------
# GameConfig sanity
# ---------------------------------------------------------------------------

class TestGameConfig:
    def test_all_five_games_present(self):
        assert set(GAME_CONFIGS.keys()) == {
            "Diamond", "Pearl", "Platinum", "HeartGold", "SoulSilver"
        }

    def test_trainer1_offset_within_block(self):
        for name, cfg in GAME_CONFIGS.items():
            assert cfg.trainer1_offset < cfg.general_block_size, name

    def test_footer_size_less_than_block_size(self):
        for name, cfg in GAME_CONFIGS.items():
            assert cfg.footer_size < cfg.general_block_size, name
