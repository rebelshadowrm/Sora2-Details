# Boss and mini-boss history filter

History has three filter modes:

- **Likely bosses (best effort)** shows manual Boss marks, exact-name boss
  candidates, and `+` candidates. It hides Unclassified and Regular encounters,
  accepting false positives and false negatives to produce a shorter list.
- **Confirmed (fail-open)** gives a boss the Confirmed label only after a manual
  Boss mark. It keeps tentative and Unclassified fights visible and hides only
  encounters explicitly marked Regular, so uncertain bosses are not silently
  dropped.
- **Unfiltered** shows every encounter, including those marked Regular.

## Markers and entry names

- **✓ CONFIRMED BOSS** means the player used **Confirm boss** on this encounter.
- **? TENTATIVE BOSS** means an observed enemy name matches the local candidate
  list. It does not confirm that every encounter containing that enemy is a boss
  fight.
- **? TENTATIVE + MOB** means an observed enemy name contains `+`. The suffix is
  directly observed, while its meaning as a mini-boss is only a heuristic.
- **? UNCLASSIFIED** means the local rules did not identify a candidate.
- **REGULAR** means the player marked this encounter as regular trash.

For a confirmed encounter, the history entry names only the known boss actor(s)
when one or more match the candidate list, excluding regular adds. A confirmed
single-enemy encounter also uses that enemy's name. `+` candidates name only
the `+` actor(s). Tentative boss candidates and Regular or Unclassified fights
show the full observed enemy pack. If a manually confirmed multi-enemy fight
has no recognized boss name and no `+` actor, the app cannot tell which actor
is the boss, so it keeps the full pack visible.

The current-remake candidate names come from the partial [Neoseeker remake
guide](https://www.neoseeker.com/trails-in-the-sky-2nd-chapter/walkthrough):
its Prologue sections name Kurt, Female Jaeger, and Jaeger as boss fights; the
Ruan page identifies Deen/Rais/Rocco, and Chapter 1 identifies Jabbabba King,
Hapilsag, Ash Saber, and Storm Bringer. It also describes Divine Pengu's quest
battle and Major Vander as the Stronghold's main boss. [Neoseeker's Battle
Notes](https://www.neoseeker.com/trails-in-the-sky-2nd-chapter/Battle_Notes)
provides the remake's canonical enemy names. The candidate list also contains
names from the original [Sky SC Ouroboros boss roster](https://kiseki.fandom.com/wiki/List_of_enemies_(Sky_SC)/Ouroboros_(Bosses))
and other named encounters, plus names present in the local logs. The current
[Chapter Three guide](https://gamefaqs.gamespot.com/switch/605487-trails-in-the-sky-2nd-chapter/faqs/81422/chapter-three)
documents the Master Cryon battle, and the [Chapter Eight guide](https://gamefaqs.gamespot.com/switch/605487-trails-in-the-sky-2nd-chapter/faqs/81422/chapter-eight)
documents the Armored Hydra battle. [Neoseeker's SC walkthrough](https://www.neoseeker.com/the-legend-of-heroes-trails-in-the-sky-sc/faqs/1625870-b.html)
identifies Ragnard as a boss in the original. These entries remain tentative
until reviewed in the app.

The current candidate actor-name set is: Bleublanc, Walter, Luciola, Renne,
Loewe, Weissmann, Angel Weissmann, Pater-Mater, Gilbert, New Gilbert, Grant,
Anelace, Kurt, Jaeger, Female Jaeger, Deen, Rais, Rocco, Jabbabba King,
Hapilsag, Ash Saber, Storm Bringer, Divine Pengu, Major Vander, Master Cryon,
Armored Hydra, and Ragnard.

Each candidate spelling was checked against the installed, hash-checked English
`t_status` table. This confirms the label used by the game data; it does not
prove that a particular logged fight is a boss. The list is partial, and the
game does not provide a verified boss flag. Source-based and `+` candidates may
include false positives. **Confirmed (fail-open)** remains positive on
uncertainty; **Likely bosses** deliberately hides Unclassified encounters.

Manual Boss and Regular marks override candidates. **Mark Regular** excludes a
fight from **Likely bosses** and **Confirmed (fail-open)**; clearing a mark
restores its name-based candidate or Unclassified state. Marks are keyed by encounter ID in
`%LOCALAPPDATA%\Sora2 Details\encounter-history.json`, separate from saved
encounters and raw traces. They remain on this PC and are not uploaded.

Current/live remains separate from saved history and follows the active
capture. Changing the history filter does not alter saved encounter snapshots
or raw traces. A shared catalog would require an opt-in upload design, stable
encounter fingerprints, and consensus rules, so marks remain local.
