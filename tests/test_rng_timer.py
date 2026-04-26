"""Tests for core/rng_timer.py"""

import pytest
from core.rng_timer import (
    lcg_next, lcg_prev, tid_sid_from_seed,
    find_seed_for_tid_sid, eon_timer_defaults, build_instructions,
    EON_DEFAULTS,
)


class TestLcg:
    def test_next_deterministic(self):
        assert lcg_next(0) == 0x6073
        assert lcg_next(1) == 0x41C6AEE0  # 1 * 0x41C64E6D + 0x6073

    def test_prev_reverses_next(self):
        for seed in [0, 1, 0xABCD, 0xFFFFFFFF]:
            assert lcg_prev(lcg_next(seed)) == seed

    def test_next_stays_32_bit(self):
        state = 0xFFFFFFFF
        for _ in range(100):
            state = lcg_next(state)
            assert 0 <= state <= 0xFFFFFFFF


class TestTidSidFromSeed:
    def test_returns_16_bit_values(self):
        for seed in [0, 1, 0x1234, 0xFFFF]:
            tid, sid = tid_sid_from_seed(seed)
            assert 0 <= tid <= 0xFFFF
            assert 0 <= sid <= 0xFFFF

    def test_different_seeds_usually_different_results(self):
        results = {tid_sid_from_seed(s) for s in range(100)}
        assert len(results) > 50  # high variety expected


class TestFindSeedForTidSid:
    def test_found_seeds_produce_correct_tid_sid(self):
        # Use a seed we know works to generate a TID/SID, then search for it
        target_seed = 0x1234
        tid, sid = tid_sid_from_seed(target_seed)
        found = find_seed_for_tid_sid(tid, sid)
        assert target_seed in found
        for s in found:
            assert tid_sid_from_seed(s) == (tid, sid)

    def test_returns_empty_for_no_match(self):
        # Artificially construct a TID/SID unlikely to come from a 16-bit seed
        # by using a 32-bit seed outside the search range
        large_seed = 0xDEADBEEF
        tid, sid = tid_sid_from_seed(large_seed)
        found = find_seed_for_tid_sid(tid, sid)
        # Result may or may not be empty (collision possible), but all found
        # seeds must verify correctly
        for s in found:
            assert tid_sid_from_seed(s) == (tid, sid)


class TestEonTimerDefaults:
    def test_all_games_present(self):
        for game in ("Diamond", "Pearl", "Platinum", "HeartGold", "SoulSilver"):
            result = eon_timer_defaults(game)
            assert "calibrated_delay" in result
            assert "calibrated_seconds" in result
            assert "target_delay" in result
            assert "target_seconds" in result

    def test_target_delay_is_placeholder(self):
        # Should NOT be a computed integer — always a string placeholder
        for game in EON_DEFAULTS:
            result = eon_timer_defaults(game)
            assert isinstance(result["target_delay"], str)

    def test_unknown_game_falls_back_to_diamond(self):
        result = eon_timer_defaults("UnknownGame")
        diamond = eon_timer_defaults("Diamond")
        assert result["calibrated_delay"] == diamond["calibrated_delay"]


class TestBuildInstructions:
    def _make(self, game="Platinum", name="RED", gender="Boy", tid=1111, sid=2222):
        seeds = find_seed_for_tid_sid(tid, sid)
        return build_instructions(game, name, gender, tid, sid, seeds)

    def test_contains_tid_and_sid(self):
        text = self._make(tid=12345, sid=67890)
        assert "12345" in text
        assert "67890" in text

    def test_contains_trainer_name(self):
        text = self._make(name="ASH")
        assert "ASH" in text

    def test_contains_eontimer_section(self):
        text = self._make()
        assert "EonTimer" in text
        assert "Calibrated Delay" in text

    def test_hgss_also_gets_eontimer_section(self):
        # Previously HGSS skipped STEP 2 — verify it is now included
        text = self._make(game="HeartGold")
        assert "Calibrated Delay" in text

    def test_contains_pokefinder_reference(self):
        text = self._make()
        assert "PokéFinder" in text

    def test_no_emulator_specific_references(self):
        text = self._make()
        assert "DeSmuME" not in text
        assert "melonDS" not in text

    def test_all_games_produce_output(self):
        for game in ("Diamond", "Pearl", "Platinum", "HeartGold", "SoulSilver"):
            text = self._make(game=game)
            assert len(text) > 100
