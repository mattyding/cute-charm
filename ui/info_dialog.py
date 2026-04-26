"""Cute Charm glitch explanation dialog."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton, QDialogButtonBox,
)
from PyQt6.QtCore import Qt

_EXPLANATION = """
<h2>What is the Cute Charm glitch?</h2>

<p>When a Pokémon with the <b>Cute Charm</b> ability leads your party, there is a
~66.7% chance the ability activates on each wild encounter. When it does, Gen 4
uses a broken PID-generation shortcut that restricts the wild Pokémon's PID to
<b>exactly 25 predetermined values</b> — one per nature — instead of the normal
32-bit space.</p>

<p>A Pokémon is shiny when its <em>Pokémon Shiny Value</em> (PSV) matches your
<em>Trainer Shiny Value</em> (TSV). Because all 25 Cute Charm PIDs are small consecutive
numbers, their PSVs cluster into only <b>3–4 distinct values</b>. Pick a TID/SID whose
TSV equals one of those values and every Cute Charm encounter with a nature in that
group will be shiny.</p>

<h2>What do the settings mean?</h2>

<dl>
  <dt><b>Lead Gender</b></dt>
  <dd>The gender of the Pokémon with Cute Charm that you put in the first party slot.
  A <em>female</em> lead forces wild encounters male; a <em>male</em> lead forces them
  female. This determines which 25 PIDs are in play.</dd>

  <dt><b>Target Ratio</b></dt>
  <dd>In Gen 4, a Pokémon's gender is encoded directly in its PID — the game compares
  the PID's lowest byte against a species-specific threshold to decide male or female.
  The 25 fixed Cute Charm PIDs are all small numbers, so whether each one registers as
  male or female depends on the species you are hunting. Eevee (87.5% male) has a low
  threshold, so nearly all 25 qualify as male. Ralts (50/50) has a higher threshold, so
  only some do. This changes which of the 25 PIDs can appear as a valid Cute Charm
  outcome — and therefore which natures and shiny groups are on the table.<br><br>
  This only matters when your lead is Female (which forces encounters to be male),
  because that is when the species' male/female threshold determines which PIDs are
  reachable. With a Male lead the forced-female PIDs are the same set regardless of
  ratio.</dd>

  <dt><b>Shiny Group</b></dt>
  <dd>The 25 PIDs divide into 3–4 groups by PSV. All natures in a group become shiny
  together once you have the matching TID/SID. Pick the group whose natures are most
  useful to you — the largest group gives the most variety.</dd>

  <dt><b>Trainer Name</b></dt>
  <dd>Your in-game trainer name. For direct injection this is written into the save
  file as-is. For RNG manipulation the name affects the frame timing, so use the name
  you actually plan to enter.</dd>

  <dt><b>Trainer Gender (Boy / Girl)</b></dt>
  <dd>Your trainer's gender, written into the save file. Does not affect the Cute Charm
  math.</dd>

  <dt><b>Preferred TID</b></dt>
  <dd>Optional. If you have a sentimental TID in mind, enter it here and the tool will
  find the SID that produces the right TSV for that TID. Leave at 0 for an automatic
  choice.</dd>
</dl>

<h2>Further reading</h2>
<ul>
  <li>Smogon DPPt/HGSS RNG Guide Part 5 (Cute Charm):
      <a href="https://www.smogon.com/ingame/rng/dpphgss_rng_part5">smogon.com</a></li>
  <li>PokémonRNG.com Cute Charm guides:
      <a href="https://www.pokemonrng.com/dppt-cute-charm/">DPPt</a> /
      <a href="https://www.pokemonrng.com/hgss-cute-charm/">HGSS</a></li>
</ul>
"""


class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cute Charm Glitch")
        self.resize(620, 540)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)

        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(True)
        browser.setHtml(_EXPLANATION)
        layout.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
