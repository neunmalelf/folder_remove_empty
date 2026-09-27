"""tests of the version stamp, the banner and the pyproject mirror."""

import io
import os
import re
import tomllib
import unittest

import remove_empty_folder_version as version

STAMP_RE = re.compile(r"^\d+\.\d+\.\d{14}Z$")
PEP440_RE = re.compile(r"^\d+\.\d+\.\d{14}$")
HERE = os.path.abspath(__file__)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


class VersionStampTest(unittest.TestCase):
    """the version literal, its format and its packaging form."""

    def test_stamp_format(self) -> None:
        self.assertRegex(version.__VERSION__, STAMP_RE)

    def test_packaging_version_is_the_stamp_without_z(self) -> None:
        self.assertRegex(version.__version__, PEP440_RE)
        self.assertEqual(version.__VERSION__, version.__version__ + "Z")

    def test_banner_shape(self) -> None:
        expected = version.APP_NAME + " version " + version.__VERSION__
        self.assertEqual(version.version_banner(), expected)

    def test_pyproject_derives_the_version_from_the_module(self) -> None:
        with open(os.path.join(ROOT, "pyproject.toml"), "rb") as handle:
            pyproject = tomllib.load(handle)
        self.assertEqual(pyproject["project"]["dynamic"], ["version"])
        self.assertEqual(
            pyproject["tool"]["setuptools"]["dynamic"]["version"]["attr"],
            "remove_empty_folder_version.__version__",
        )

    def test_names(self) -> None:
        self.assertEqual(version.APP_NAME, "folder_remove_empty")
        self.assertEqual(version.APP_NAME_VERBOSE, "FOLDER_REMOVE_EMPTY")


class EntryPointTest(unittest.TestCase):
    """the phase 1 entry point prints the banner and nothing else yet."""

    def test_version_option_prints_the_banner(self) -> None:
        import folder_remove_empty

        out = io.StringIO()
        code = folder_remove_empty.main(["--version"], out=out)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().strip(), version.version_banner())


if __name__ == "__main__":
    unittest.main()
