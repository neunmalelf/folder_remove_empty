"""tests of the settings file the window remembers its state in."""

import configparser
import os
import shutil
import stat
import tempfile
import unittest

from remove_empty_folder_config import SavedSettings, load, save
from tests.folder_remove_empty.testhelpers import capture


def write_file(path: str, text: str) -> None:
    """create PATH with TEXT, as raw LF bytes
    usage: write_file <PATH> <TEXT>
    returns: nothing

    example: write_file("/tmp/fre/folder_remove_empty.conf", "[options]\\ndark = True\\n")

    """
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def read_bytes(path: str) -> bytes:
    """return the raw content of PATH
    usage: read_bytes <PATH>
    returns: the bytes of the file

    example: read_bytes("/tmp/fre/folder_remove_empty.conf")

    """
    with open(path, "rb") as handle:
        return handle.read()


class SavedSettingsTest(unittest.TestCase):
    """the round trip, the fallbacks and the silent failure of the settings file."""

    def setUp(self) -> None:
        self.folder = tempfile.mkdtemp(prefix="fre-config-")
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        self.path = os.path.join(self.folder, "folder_remove_empty.conf")

    def test_a_missing_file_yields_the_defaults(self) -> None:
        settings = load(os.path.join(self.folder, "not-there.conf"))

        self.assertEqual(settings, SavedSettings())
        self.assertIsNone(settings.geometry)
        self.assertFalse(settings.dry_run)
        self.assertFalse(settings.verbose)
        self.assertEqual(settings.excludes, "")
        self.assertEqual(settings.history_filter, "All")
        self.assertFalse(settings.dark)

    def test_a_round_trip_keeps_every_saved_value(self) -> None:
        saved = SavedSettings(
            geometry=(-1920, 1080, -1920, 12),
            dry_run=True,
            verbose=True,
            excludes="build:cache*",
            history_filter="Kept",
            dark=True,
        )

        save(saved, self.path)

        self.assertEqual(load(self.path), saved)
        self.assertEqual(load(self.path).geometry, (-1920, 1080, -1920, 12))

    def test_a_window_without_saved_geometry_round_trips_as_none(self) -> None:
        save(SavedSettings(dry_run=True), self.path)

        settings = load(self.path)
        self.assertIsNone(settings.geometry)
        self.assertTrue(settings.dry_run)

    def test_save_creates_the_missing_folder_and_file(self) -> None:
        nested = os.path.join(self.folder, "fresh", "folder_remove_empty")
        path = os.path.join(nested, "folder_remove_empty.conf")

        save(SavedSettings(dark=True), path)

        self.assertTrue(os.path.isfile(path))
        self.assertEqual(stat.S_IMODE(os.stat(nested).st_mode), 0o700)
        self.assertTrue(load(path).dark)

    def test_malformed_content_yields_the_defaults(self) -> None:
        write_file(self.path, "this is not an INI file\nwidth = 960\n")

        self.assertEqual(load(self.path), SavedSettings())

    def test_a_missing_section_yields_the_defaults_of_that_section(self) -> None:
        write_file(self.path, "[options]\ndark = True\n")

        settings = load(self.path)
        self.assertIsNone(settings.geometry)
        self.assertTrue(settings.dark)

    def test_an_unknown_history_filter_becomes_all(self) -> None:
        write_file(self.path, "[options]\nhistory_filter = Bogus\n")

        self.assertEqual(load(self.path).history_filter, "All")

    def test_a_non_integer_geometry_yields_none(self) -> None:
        write_file(
            self.path,
            "[window]\nwidth = 960\nheight = tall\nx = 0\ny = 0\n\n[options]\ndry_run = yes\n",
        )

        settings = load(self.path)
        self.assertIsNone(settings.geometry)
        self.assertTrue(settings.dry_run)

    def test_a_half_set_geometry_yields_none(self) -> None:
        write_file(self.path, "[window]\nwidth = 960\nheight = 720\n")

        self.assertIsNone(load(self.path).geometry)

    def test_the_written_file_carries_every_key(self) -> None:
        save(SavedSettings(geometry=(800, 600, -10, 20), excludes="build"), self.path)

        parser = configparser.ConfigParser(interpolation=None)
        parser.read(self.path, encoding="utf-8")

        self.assertEqual(
            sorted(parser["window"]), ["height", "width", "x", "y"]
        )
        self.assertEqual(
            sorted(parser["options"]),
            ["dark", "dry_run", "excludes", "history_filter", "verbose"],
        )
        self.assertEqual(parser.get("window", "x"), "-10")
        self.assertEqual(parser.get("options", "excludes"), "build")
        self.assertEqual(parser.get("options", "history_filter"), "All")
        self.assertEqual(parser.get("options", "dark"), "False")

    def test_load_and_save_write_nothing_to_the_streams(self) -> None:
        with capture() as (out, err):
            load(os.path.join(self.folder, "not-there.conf"))
            load(self.path)
            save(SavedSettings(), self.path)

        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "")

    @unittest.skipIf(os.geteuid() == 0, "root ignores the mode of a file")
    def test_the_written_file_is_readable_only_by_its_owner(self) -> None:
        save(SavedSettings(), self.path)

        self.assertEqual(stat.S_IMODE(os.stat(self.path).st_mode), 0o600)

    @unittest.skipIf(os.geteuid() == 0, "root ignores the mode of a folder")
    def test_save_into_an_unwritable_folder_keeps_the_previous_file(self) -> None:
        save(SavedSettings(dark=True), self.path)
        before = read_bytes(self.path)

        os.chmod(self.folder, 0o500)
        self.addCleanup(os.chmod, self.folder, 0o700)
        save(SavedSettings(dark=False, dry_run=True), self.path)

        self.assertEqual(read_bytes(self.path), before)
        self.assertTrue(load(self.path).dark)

    def test_save_into_a_folder_that_cannot_be_created_returns_silently(self) -> None:
        blocked = os.path.join(self.folder, "blocked")
        write_file(blocked, "not a folder\n")
        path = os.path.join(blocked, "folder_remove_empty.conf")

        with capture() as (out, err):
            save(SavedSettings(dark=True), path)

        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "")
        self.assertEqual(read_bytes(blocked), b"not a folder\n")


if __name__ == "__main__":
    unittest.main()
