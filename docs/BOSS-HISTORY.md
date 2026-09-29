# Boss history classification

The capture records enemy names and provisional unit keys but has no verified
boss flag. **Bosses + unclassified** is therefore a conservative history view:
it hides only encounters the player explicitly marked Regular. Unclassified
fights remain visible, including bosses absent from the catalog or fights whose
enemy lookup failed. **All fights** restores marked regular encounters. Neither
view changes saved encounter snapshots or raw traces, and Current/live always
follows the active capture.

History highlights three kinds of likely boss fight:

- **BOSS**: the player explicitly marked this encounter Boss.
- **Boss candidate**: an observed enemy name exactly matches a reviewed name in
  the original *Trails in the Sky SC* [boss roster](https://kiseki.fandom.com/wiki/List_of_enemies_(Sky_SC)/Ouroboros_(Bosses))
  and the hash-checked English `t_status` table from the installed remake.
- **Mini-boss candidate**: an observed enemy name contains `+`. These names
  often indicate chest encounters, but the name alone does not prove the fight
  was in a chest.

The reviewed name list currently covers Bleublanc, Walter, Luciola, Renne,
Loewe, Weissmann, Angel Weissmann, Pater-Mater, Gilbert, New Gilbert, Grant,
and Anelace. This is a positive, incomplete list: it identifies candidates and
does not certify that any other encounter was regular. The original SC roster
does not establish complete boss coverage for the remake. Multiple fights can
share a name, so a catalog hit is labeled *candidate* rather than confirmed.

Manual Boss and Regular marks take priority over candidates. Clearing a mark
restores the name-based candidate or Unclassified state. Marks are keyed by
encounter ID in `%LOCALAPPDATA%\Sora2 Details\encounter-history.json`, apart
from snapshots that the capture bridge may replace. Recent entries and More
list observed enemy names, group duplicates, and show unresolved enemies.

For a stronger automatic filter, build a versioned boss catalog with encounter
or stage context, verified game unit keys, and source provenance. Validate the
live enemy-to-key join before using those keys to hide encounters. Until then,
unknown fights stay visible.
