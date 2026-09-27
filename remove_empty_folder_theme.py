"""the light and the dark palette of the window and its history colours.

A port of theme.go. Both variants are the same nine colours, the light one on a
white and the dark one on a near-black background; the four status colours and
the border grey are adjusted per variant, the accent is shared.

The module is pure data: it carries no window-toolkit import, so the palettes,
the colour of an importance and the label of the theme button can be read and
tested without a window. The window module paints every widget from the
`#rrggbb` strings here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """the nine colours of one window variant, light or dark
    usage: Theme(<BG>, <FG>, <BORDER>, <ACCENT>, <SUCCESS>, <MEDIUM>, <LOW>, <WARNING>, <DANGER>)
    returns: the palette of one variant

    example: Theme(*LIGHT.__dict__.values())

    """

    # the background of the window and of the history list.
    bg: str
    # the default foreground: labels, run notes and closing lines.
    fg: str
    # the grey of the control borders and the separators.
    border: str
    # the accent of the selected controls, purple in both variants.
    accent: str
    # "removed" history lines.
    success: str
    # dry-run "would remove" history lines.
    medium: str
    # "excluded, kept" history lines.
    low: str
    # "not removed" (refused) history lines.
    warning: str
    # "ERROR" history lines.
    danger: str


# the light palette, the one the window starts in (spec §7.1/§7.7): white
# background, black foreground, medium-grey borders.
LIGHT = Theme(
    bg="#ffffff",
    fg="#000000",
    border="#8a8a8a",
    accent="#7e57c2",
    success="#2e7d32",
    medium="#9c6d00",
    low="#757575",
    warning="#e65100",
    danger="#c62828",
)

# the dark palette: near-black background, white foreground, light-grey
# borders, the same accent, lighter status colours.
DARK = Theme(
    bg="#121212",
    fg="#ffffff",
    border="#b0b0b0",
    accent="#7e57c2",
    success="#81c784",
    medium="#ffb74d",
    low="#bdbdbd",
    warning="#ff8a65",
    danger="#ef5350",
)

# the history importance labels of spec §7.4 mapped onto the Theme fields; a
# label outside this table reads as the default foreground.
_IMPORTANCE_FIELDS = {
    "removed": "success",
    "dry": "medium",
    "would remove": "medium",
    "kept": "low",
    "refused": "warning",
    "error": "danger",
    "note": "fg",
    "": "fg",
}


def importance_color(importance: str, dark: bool) -> str:
    """return the history colour of an importance, the foreground when it is unknown
    usage: importance_color <IMPORTANCE> <DARK>
    returns: the "#rrggbb" colour of the importance in the requested variant

    example: importance_color("removed", dark=False)

    """
    palette = DARK if dark else LIGHT
    return str(getattr(palette, _IMPORTANCE_FIELDS.get(importance, "fg")))


def theme_button_label(dark: bool) -> str:
    """return the label of the theme button, which always names the theme it switches to
    usage: theme_button_label <DARK>
    returns: "Light mode" in the dark variant, "Dark mode" in the light one

    example: theme_button_label(dark=False)

    """
    return "Light mode" if dark else "Dark mode"
