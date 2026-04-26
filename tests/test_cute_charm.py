"""Tests for core/cute_charm.py"""

import pytest
from core.cute_charm import (
    NATURES, GENDER_RATIOS,
    pid_base, cute_charm_pids, calc_psv, calc_tsv,
    is_shiny, shiny_groups, find_tid_sid,
)


# ---------------------------------------------------------------------------
# PID base
# ---------------------------------------------------------------------------

class TestPidBase:
    def test_male_lead_always_zero(self):
        for ratio_name in GENDER_RATIOS:
            assert pid_base("Male", ratio_name) == 0

    def test_female_lead_50_50(self):
        # ceil(0x7F / 25) * 25 = ceil(127/25)*25 = 6*25 = 150
        assert pid_base("Female", "50/50 (Ralts, Machop…)") == 150

    def test_female_lead_875_male(self):
        # ceil(0x1F / 25) * 25 = ceil(31/25)*25 = 2*25 = 50
        assert pid_base("Female", "87.5% Male (most starters, Eevee…)") == 50

    def test_female_lead_75_male(self):
        # ceil(0x3F / 25) * 25 = ceil(63/25)*25 = 3*25 = 75
        assert pid_base("Female", "75% Male") == 75

    def test_female_lead_25_male(self):
        # ceil(0xBF / 25) * 25 = ceil(191/25)*25 = 8*25 = 200
        assert pid_base("Female", "25% Male (Clefairy, Jigglypuff…)") == 200

    def test_base_is_multiple_of_25(self):
        for lead in ("Male", "Female"):
            for ratio_name in GENDER_RATIOS:
                base = pid_base(lead, ratio_name)
                assert base % 25 == 0

    def test_female_base_satisfies_male_gender_condition(self):
        """All 25 PIDs from female-lead base must be >= the ratio byte (i.e. male)."""
        for ratio_name, ratio_byte in GENDER_RATIOS.items():
            base = pid_base("Female", ratio_name)
            for pid in range(base, base + 25):
                assert pid & 0xFF >= ratio_byte, (
                    f"PID {pid} not male for ratio {ratio_name}"
                )

    def test_male_base_satisfies_female_gender_condition(self):
        """All 25 PIDs from male-lead base (0-24) must be < any ratio byte."""
        for ratio_byte in GENDER_RATIOS.values():
            for pid in range(25):
                assert pid & 0xFF < ratio_byte, (
                    f"PID {pid} not female for ratio {ratio_byte:#x}"
                )


# ---------------------------------------------------------------------------
# cute_charm_pids
# ---------------------------------------------------------------------------

class TestCuteCharmPids:
    def test_always_25_pids(self):
        for lead in ("Male", "Female"):
            for ratio_name in GENDER_RATIOS:
                pids = cute_charm_pids(lead, ratio_name)
                assert len(pids) == 25

    def test_covers_all_25_natures(self):
        for lead in ("Male", "Female"):
            for ratio_name in GENDER_RATIOS:
                pids = cute_charm_pids(lead, ratio_name)
                natures = {p % 25 for p in pids}
                assert natures == set(range(25))

    def test_pids_are_consecutive(self):
        for lead in ("Male", "Female"):
            for ratio_name in GENDER_RATIOS:
                pids = cute_charm_pids(lead, ratio_name)
                assert pids == list(range(pids[0], pids[0] + 25))

    def test_male_lead_pids_are_0_to_24(self):
        for ratio_name in GENDER_RATIOS:
            assert cute_charm_pids("Male", ratio_name) == list(range(25))


# ---------------------------------------------------------------------------
# PSV / TSV / shininess
# ---------------------------------------------------------------------------

class TestShinyValues:
    def test_psv_low_pid(self):
        # For PID=0: PSV = (0 ^ 0) >> 3 = 0
        assert calc_psv(0) == 0
        # For PID=8: PSV = 8 >> 3 = 1
        assert calc_psv(8) == 1
        # For PID=16: PSV = 16 >> 3 = 2
        assert calc_psv(16) == 2

    def test_psv_high_bits_irrelevant_for_cute_charm_pids(self):
        # Cute Charm PIDs are always < 65536, high 16 bits = 0
        # PSV = ((0 ^ pid_low) >> 3) = pid_low >> 3
        for pid in [150, 151, 152, 160, 174]:
            assert calc_psv(pid) == pid >> 3

    def test_tsv_formula(self):
        assert calc_tsv(0, 0) == 0
        assert calc_tsv(8, 0) == 1
        assert calc_tsv(0, 8) == 1
        assert calc_tsv(8, 8) == 0
        assert calc_tsv(0xFF, 0) == 0xFF >> 3

    def test_is_shiny_when_tsv_equals_psv(self):
        pid = 150  # PSV = 150 >> 3 = 18
        # Need TID ^ SID to have same >> 3, i.e. in range [144, 151]
        tid, sid = 0, 144   # TSV = 144 >> 3 = 18
        assert is_shiny(pid, tid, sid)

    def test_not_shiny_when_tsv_differs(self):
        pid = 150  # PSV = 18
        tid, sid = 0, 0     # TSV = 0
        assert not is_shiny(pid, tid, sid)

    def test_all_pids_in_group_shiny_for_group_tsv(self):
        groups = shiny_groups("Female", "50/50 (Ralts, Machop…)")
        for group in groups:
            tsv_val = group["tsv_value"]
            tid, sid = find_tid_sid(tsv_val)
            for pid in group["pids"]:
                assert is_shiny(pid, tid, sid), (
                    f"PID {pid} not shiny with TID={tid} SID={sid}"
                )

    def test_pids_outside_group_not_shiny_for_group_tsv(self):
        groups = shiny_groups("Female", "50/50 (Ralts, Machop…)")
        for i, group in enumerate(groups):
            tsv_val = group["tsv_value"]
            tid, sid = find_tid_sid(tsv_val)
            for j, other_group in enumerate(groups):
                if i == j:
                    continue
                for pid in other_group["pids"]:
                    assert not is_shiny(pid, tid, sid), (
                        f"PID {pid} from group {j} unexpectedly shiny for group {i} TID/SID"
                    )


# ---------------------------------------------------------------------------
# shiny_groups
# ---------------------------------------------------------------------------

class TestShinyGroups:
    def test_groups_cover_all_25_pids(self):
        for lead in ("Male", "Female"):
            for ratio_name in GENDER_RATIOS:
                groups = shiny_groups(lead, ratio_name)
                all_pids = [p for g in groups for p in g["pids"]]
                assert sorted(all_pids) == sorted(cute_charm_pids(lead, ratio_name))

    def test_groups_sorted_by_size_descending(self):
        groups = shiny_groups("Female", "50/50 (Ralts, Machop…)")
        sizes = [len(g["pids"]) for g in groups]
        assert sizes == sorted(sizes, reverse=True)

    def test_natures_match_pids(self):
        for lead in ("Male", "Female"):
            for ratio_name in GENDER_RATIOS:
                for group in shiny_groups(lead, ratio_name):
                    for pid, nature in zip(group["pids"], group["natures"]):
                        assert NATURES[pid % 25] == nature

    def test_all_pids_in_group_share_psv(self):
        for lead in ("Male", "Female"):
            for ratio_name in GENDER_RATIOS:
                for group in shiny_groups(lead, ratio_name):
                    psvs = {calc_psv(p) for p in group["pids"]}
                    assert len(psvs) == 1, f"Group has mixed PSVs: {psvs}"
                    assert psvs.pop() == group["tsv_value"]


# ---------------------------------------------------------------------------
# find_tid_sid
# ---------------------------------------------------------------------------

class TestFindTidSid:
    def test_tsv_matches_target(self):
        for target_tsv in [0, 1, 18, 19, 20, 21, 8191]:
            tid, sid = find_tid_sid(target_tsv)
            assert calc_tsv(tid, sid) == target_tsv

    def test_preferred_tid_honoured(self):
        for preferred in [0, 100, 12345, 65535]:
            tid, sid = find_tid_sid(19, preferred_tid=preferred)
            assert tid == preferred & 0xFFFF
            assert calc_tsv(tid, sid) == 19

    def test_output_in_valid_range(self):
        for tsv in range(0, 8192, 100):
            tid, sid = find_tid_sid(tsv)
            assert 0 <= tid <= 65535
            assert 0 <= sid <= 65535
