"""tests of the two window palettes, the importance colours and the button label."""

import dataclasses
import re
import unittest

import remove_empty_folder_theme as theme

RRGGBB_RE = re.compile(r"^#[0-9a-f]{6}$")


class PaletteTest(unittest.TestCase):
    """the light and the dark palette and their nine colours."""

    def test_every_colour_is_an_rrggbb_string(self) -> None:
        for name, palette in (("LIGHT", theme.LIGHT), ("DARK", theme.DARK)):
            for field in dataclasses.fields(theme.Theme):
                with self.subTest(palette=name, field=field.name):
                    self.assertRegex(getattr(palette, field.name), RRGGBB_RE)

    def test_light_palette(self) -> None:
        # theme.go: the material default palette, borderLight and the light
        # colours of importance.color.
        self.assertEqual(
            theme.LIGHT,
            theme.Theme(
                bg="#ffffff",
                fg="#000000",
                border="#8a8a8a",
                accent="#7e57c2",
                success="#2e7d32",
                medium="#9c6d00",
                low="#757575",
                warning="#e65100",
                danger="#c62828",
            ),
        )

    def test_dark_palette(self) -> None:
        # theme.go: newAppTheme(true), borderDark and the dark colours of
        # importance.color.
        self.assertEqual(
            theme.DARK,
            theme.Theme(
                bg="#121212",
                fg="#ffffff",
                border="#b0b0b0",
                accent="#7e57c2",
                success="#81c784",
                medium="#ffb74d",
                low="#bdbdbd",
                warning="#ff8a65",
                danger="#ef5350",
            ),
        )

    def test_the_two_palettes_differ(self) -> None:
        self.assertNotEqual(theme.LIGHT, theme.DARK)
        self.assertNotEqual(theme.LIGHT.fg, theme.DARK.fg)
        self.assertEqual(theme.LIGHT.accent, theme.DARK.accent)

    def test_field_order(self) -> None:
        names = [field.name for field in dataclasses.fields(theme.Theme)]
        self.assertEqual(
            names,
            ["bg", "fg", "border", "accent", "success", "medium", "low", "warning", "danger"],
        )


class ImportanceColorTest(unittest.TestCase):
    """spec §7.4: every history importance on its theme colour."""

    def test_every_importance_maps_to_its_field(self) -> None:
        expected = {
            "removed": "success",
            "dry": "medium",
            "would remove": "medium",
            "kept": "low",
            "refused": "warning",
            "error": "danger",
            "note": "fg",
        }
        for importance, field in expected.items():
            for dark in (False, True):
                with self.subTest(importance=importance, dark=dark):
                    palette = theme.DARK if dark else theme.LIGHT
                    self.assertEqual(
                        theme.importance_color(importance, dark),
                        getattr(palette, field),
                    )

    def test_empty_importance_is_the_foreground(self) -> None:
        self.assertEqual(theme.importance_color("", False), theme.LIGHT.fg)
        self.assertEqual(theme.importance_color("", True), theme.DARK.fg)

    def test_unknown_importance_falls_back_to_the_foreground(self) -> None:
        self.assertEqual(theme.importance_color("something else", False), theme.LIGHT.fg)
        self.assertEqual(theme.importance_color("something else", True), theme.DARK.fg)


class ThemeButtonLabelTest(unittest.TestCase):
    """spec §7.3: the button names the theme it switches to."""

    def test_label_names_the_other_theme(self) -> None:
        self.assertEqual(theme.theme_button_label(dark=False), "Dark mode")
        self.assertEqual(theme.theme_button_label(dark=True), "Light mode")


class FrozenThemeTest(unittest.TestCase):
    """the palette is frozen, so a widget cannot repaint it."""

    def test_a_write_raises(self) -> None:
        with self.assertRaises(dataclasses.FrozenInstanceError):
            theme.LIGHT.bg = "#000000"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
