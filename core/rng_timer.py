"""
Gen 4 RNG — EonTimer-compatible settings and step-by-step instructions.

References:
  Smogon Gen 4 RNG guide: https://www.smogon.com/ingame/rng/dpphgss_rng_part1
  PokéFinder:  https://github.com/Admiral-Fish/PokeFinder
  EonTimer:    https://dasampharos.github.io/EonTimer/
  Reddit guide (iprizefighter):
    https://www.reddit.com/r/pokemonrng/comments/j26d27/
"""

from __future__ import annotations

_MULT     = 0x41C64E6D
_ADD      = 0x6073
_INV_MULT = 0xEEB9EB65   # modular inverse of _MULT mod 2^32


def lcg_next(state: int) -> int:
    """Advance the Gen 4 LCG by one step."""
    return (state * _MULT + _ADD) & 0xFFFFFFFF


def lcg_prev(state: int) -> int:
    """Reverse the Gen 4 LCG by one step."""
    return ((state - _ADD) * _INV_MULT) & 0xFFFFFFFF


def tid_sid_from_seed(seed: int) -> tuple[int, int]:
    """Return (TID, SID) produced by the given initial seed."""
    s1 = lcg_next(seed)
    tid = s1 >> 16
    s2 = lcg_next(s1)
    sid = s2 >> 16
    return tid, sid


def find_seed_for_tid_sid(
    tid: int,
    sid: int,
    max_search: int = 0x10000,
) -> list[int]:
    """
    Exhaustive search over 16-bit seeds (D/P/Pt only).
    HGSS uses a 32-bit seeding scheme — use PokéFinder for those.
    """
    results: list[int] = []
    for seed in range(max_search):
        t, s = tid_sid_from_seed(seed)
        if t == tid and s == sid:
            results.append(seed)
    return results


EON_DEFAULTS: dict[str, dict] = {
    "Diamond":    {"calibrated_delay": 600,  "calibrated_seconds": 14},
    "Pearl":      {"calibrated_delay": 600,  "calibrated_seconds": 14},
    "Platinum":   {"calibrated_delay": 1200, "calibrated_seconds": 14},
    "HeartGold":  {"calibrated_delay": 490,  "calibrated_seconds": 14},
    "SoulSilver": {"calibrated_delay": 490,  "calibrated_seconds": 14},
}

TARGET_SECONDS_DEFAULT = 23  # comfortable wait time used in most guides


def eon_timer_defaults(game: str) -> dict:
    """Starting calibration values for EonTimer Tab 4 (Gen 4). Target delay comes from PokéFinder."""
    defaults = EON_DEFAULTS.get(game, EON_DEFAULTS["Diamond"])
    return {
        "calibrated_delay":   defaults["calibrated_delay"],
        "calibrated_seconds": defaults["calibrated_seconds"],
        "target_delay":       "(from PokéFinder Seed to Time)",
        "target_seconds":     TARGET_SECONDS_DEFAULT,
    }


def build_instructions(
    game: str,
    trainer_name: str,
    trainer_gender: str,
    tid: int,
    sid: int,
    seeds: list[int],
) -> str:
    lines: list[str] = []
    lines.append(f"Game: {game}  |  Trainer: {trainer_name} ({trainer_gender})")
    lines.append(f"Target TID: {tid:05d}   SID: {sid:05d}")
    lines.append("")

    lines.append("You'll need:")
    lines.append("  EonTimer  https://dasampharos.github.io/EonTimer/")
    lines.append("  PokéFinder  https://github.com/Admiral-Fish/PokeFinder")
    lines.append("")

    lines.append("Step 1 — Get your seed from PokéFinder")
    lines.append(f"  Gen 4 → IDs → TID/SID, search for {tid:05d} / {sid:05d}.")
    if seeds:
        lines.append(f"  Your seed is 0x{seeds[0]:04X}.")
        lines.append("  Plug that into Seed to Time to get your target date/time and delay.")
    else:
        lines.append("  Run the search and note the seed, date/time, and delay.")
        lines.append("  (HGSS seeds are 32-bit — use PokéFinder's HGSS searcher.)")
    lines.append("")

    eon = eon_timer_defaults(game)
    lines.append("Step 2 — EonTimer setup (Gen 4 tab)")
    lines.append(f"  Calibrated Delay   {eon['calibrated_delay']}  ← starting point, tune after each attempt")
    lines.append(f"  Calibrated Seconds {eon['calibrated_seconds']}")
    lines.append(f"  Target Delay       {eon['target_delay']}")
    lines.append(f"  Target Seconds     {eon['target_seconds']}")
    lines.append("")

    lines.append("Step 3 — Set your clock")
    lines.append("  Change the date and time in DS system settings to match")
    lines.append("  what PokéFinder gave you. Do this before starting the game.")
    lines.append("")

    lines.append("Step 4 — Hit the seed")
    lines.append("  Start EonTimer, then immediately power on / soft-reset the game.")
    lines.append("  On the first beep, press A at the title screen.")
    lines.append("  Start a new game, pick your gender, and enter your trainer name:")
    lines.append(f"    {trainer_name}")
    lines.append("  On the 'Has a nice ring to it, eh?' screen, press A on the second beep.")
    lines.append("")

    lines.append("Step 5 — Check your IDs")
    lines.append("  Open your Trainer Card. TID should be " + f"{tid:05d}.")
    lines.append("  SID isn't shown in-game — use PKHeX to confirm if needed.")
    lines.append("")

    lines.append("Calibration tip")
    lines.append("  If you miss, catch a wild Pokémon and note its nature.")
    lines.append("  Look up the nature in PokéFinder to find the seed you actually hit,")
    lines.append("  then adjust Calibrated Delay by the difference.")
    lines.append("  More detail: https://www.reddit.com/r/pokemonrng/comments/j26d27/")

    return "\n".join(lines)


def build_tas_instructions(
    game: str,
    trainer_name: str,
    trainer_gender: str,
    tid: int,
    sid: int,
    seeds: list[int],
) -> str:
    lines: list[str] = []
    lines.append(f"Game: {game}  |  Trainer: {trainer_name} ({trainer_gender})")
    lines.append(f"Target TID: {tid:05d}   SID: {sid:05d}")
    lines.append("")

    lines.append("Frame advance lets you step the game one frame at a time so you")
    lines.append("can hit the exact frame for your target TID/SID without any timing tool.")
    lines.append("")

    lines.append("You'll need:")
    lines.append("  A Gen 4 emulator with frame advance")
    lines.append("  PokéFinder  https://github.com/Admiral-Fish/PokeFinder")
    lines.append("")

    lines.append("Step 1 — Find your seed")
    lines.append(f"  PokéFinder → Gen 4 → IDs → TID/SID, search for {tid:05d} / {sid:05d}.")
    if seeds:
        seed_hex = ", ".join(f"0x{s:04X}" for s in seeds[:4])
        lines.append(f"  Seed: {seed_hex}")
        lines.append("  Run it through Seed to Time to get your target date/time and delay.")
    else:
        lines.append("  Run the search and note the seed, date/time, and delay.")
        lines.append("  (HGSS uses a 32-bit seed — use PokéFinder's HGSS searcher.)")
    lines.append("")

    lines.append("Step 2 — Set the clock")
    lines.append("  Set the date/time on your device to what PokéFinder gave you.")
    lines.append("  Enable the frame counter overlay if your emulator has one.")
    lines.append("")

    lines.append("Step 3 — Hit the frame")
    lines.append("  Boot or soft-reset the game and let it reach the title screen.")
    lines.append("  Save state a bit before your target delay frame.")
    lines.append("  Frame-advance to exactly the Target Delay, then press A.")
    lines.append("  If you miss, reload the save state and try again.")
    lines.append("")

    lines.append("Step 4 — Finish new game setup")
    lines.append(f"  New Game → {trainer_gender} → enter trainer name: {trainer_name}")
    lines.append("  Press A normally on the name confirmation screen.")
    lines.append("")

    lines.append("Step 5 — Check your IDs")
    lines.append(f"  Trainer Card → TID should be {tid:05d}.")
    lines.append("  Use PKHeX to confirm SID if needed.")

    return "\n".join(lines)
