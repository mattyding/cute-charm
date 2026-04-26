"""
Cute Charm glitch math for Gen 4 Pokémon games.

When a Pokémon with Cute Charm leads the party, wild encounter PIDs are
restricted to 25 predetermined values — one per nature.  With the right
TID/SID, every PID in one of the four "shiny groups" satisfies TSV == PSV,
making all Cute Charm encounters with those natures shiny.

References:
  Smogon DPPt/HGSS RNG Guide Part 5: https://www.smogon.com/ingame/rng/dpphgss_rng_part5
  PokémonRNG.com DPPt: https://www.pokemonrng.com/dppt-cute-charm/
  PokémonRNG.com HGSS: https://www.pokemonrng.com/hgss-cute-charm/
  CuteCharmIDGenie (prior art): https://github.com/RenegadeRaven/CuteCharmIDGenie
"""

import math

NATURES: list[str] = [
    "Hardy", "Lonely", "Brave", "Adamant", "Naughty",
    "Bold",   "Docile", "Relaxed","Impish",  "Lax",
    "Timid",  "Hasty",  "Serious","Jolly",   "Naive",
    "Modest", "Mild",   "Quiet",  "Bashful", "Rash",
    "Calm",   "Gentle", "Sassy",  "Careful", "Quirky",
]

GENDER_RATIOS: dict[str, int] = {
    "87.5% Male (most starters, Eevee…)": 0x1F,
    "75% Male":                            0x3F,
    "50/50 (Ralts, Machop…)":             0x7F,
    "25% Male (Clefairy, Jigglypuff…)":  0xBF,
}


def pid_base(lead_gender: str, gender_ratio_name: str) -> int:
    """
    First of the 25 consecutive Cute Charm PID values for this scenario.

    Male lead (forces female encounters): PIDs 0-24 satisfy pid_low < any
    normal ratio byte, so base is always 0.

    Female lead (forces male encounters): need pid_low >= ratio_byte, so
    use the smallest multiple-of-25 that clears the threshold.
    """
    if lead_gender == "Male":
        return 0
    ratio = GENDER_RATIOS[gender_ratio_name]
    return math.ceil(ratio / 25) * 25


def cute_charm_pids(lead_gender: str, gender_ratio_name: str) -> list[int]:
    """Return the 25 fixed Cute Charm PIDs for the given lead gender and target ratio."""
    base = pid_base(lead_gender, gender_ratio_name)
    return list(range(base, base + 25))


def calc_psv(pid: int) -> int:
    """PSV = ((pid >> 16) ^ (pid & 0xFFFF)) >> 3. Cute Charm PIDs are < 65536."""
    return ((pid >> 16) ^ (pid & 0xFFFF)) >> 3


def calc_tsv(tid: int, sid: int) -> int:
    """Trainer Shiny Value = (TID XOR SID) >> 3."""
    return (tid ^ sid) >> 3


def is_shiny(pid: int, tid: int, sid: int) -> bool:
    """Return True if the PID is shiny for the given TID/SID."""
    return calc_tsv(tid, sid) == calc_psv(pid)


def shiny_groups(lead_gender: str, gender_ratio_name: str) -> list[dict]:
    """
    Partition the 25 Cute Charm PIDs into groups by PSV, sorted largest-first.

    Each group shares one PSV value; setting TSV = PSV via a matching TID/SID
    makes every PID in that group shiny.

    Returns list of dicts: {tsv_value, pids, natures}
    """
    pids = cute_charm_pids(lead_gender, gender_ratio_name)
    buckets: dict[int, list[int]] = {}
    for p in pids:
        buckets.setdefault(calc_psv(p), []).append(p)

    return sorted(
        [
            {
                "tsv_value": tsv_val,
                "pids": group_pids,
                "natures": [NATURES[p % 25] for p in group_pids],
            }
            for tsv_val, group_pids in buckets.items()
        ],
        key=lambda g: -len(g["pids"]),
    )


def find_tid_sid(target_tsv: int, preferred_tid: int | None = None) -> tuple[int, int]:
    """
    Return (TID, SID) where (TID XOR SID) >> 3 == target_tsv.
    Uses XOR = target_tsv * 8 so SID stays close to TID.
    """
    xor_val = target_tsv * 8
    tid = int(preferred_tid if preferred_tid is not None else 12345) & 0xFFFF
    sid = (tid ^ xor_val) & 0xFFFF
    return tid, sid
