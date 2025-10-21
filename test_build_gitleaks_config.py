
import json
import string
import tempfile
import unittest
from pathlib import Path

from build_gitleaks_config import ConfigBuildError, build_config, run


TEMPLATE_PATH = Path(__file__).resolve().parent / "gitleaks-custom-rules-template.toml"


class BuildConfigTests(unittest.TestCase):
    def test_returns_empty_string_when_no_sections(self) -> None:
        result = build_config(
            template_path=TEMPLATE_PATH,
            inline_contents="",
            vars_json="",
            extend=False,
        )
        self.assertEqual(result, "")

    def test_extend_only_section(self) -> None:
        result = build_config(
            template_path=TEMPLATE_PATH,
            inline_contents="",
            vars_json="",
            extend=True,
        )
        self.assertEqual(result, "[extend]\nuseDefault = true\n")

    def test_inline_contents_appended(self) -> None:
        inline = "[[rules]]\nid = 'custom'"
        result = build_config(
            template_path=TEMPLATE_PATH,
            inline_contents=inline,
            vars_json="",
            extend=False,
        )
        self.assertEqual(result, inline.strip() + "\n")

    def test_template_variables_substituted(self) -> None:
        value = "https://internal.example"
        vars_json = json.dumps({"GITLEAKS_REGEX_INTERNAL_URL": value})
        result = build_config(
            template_path=TEMPLATE_PATH,
            inline_contents="",
            vars_json=vars_json,
            extend=False,
        )
        expected = string.Template(TEMPLATE_PATH.read_text(encoding="utf-8")).substitute(
            {"GITLEAKS_REGEX_INTERNAL_URL": value}
        ).strip()
        self.assertEqual(result, expected + "\n")

    def test_sections_are_combined_with_blank_line(self) -> None:
        inline = "title = 'Example'"
        vars_json = json.dumps({"GITLEAKS_REGEX_INTERNAL_URL": "abc"})
        result = build_config(
            template_path=TEMPLATE_PATH,
            inline_contents=inline,
            vars_json=vars_json,
            extend=True,
        )
        expected_template = string.Template(TEMPLATE_PATH.read_text(encoding="utf-8")).substitute(
            {"GITLEAKS_REGEX_INTERNAL_URL": "abc"}
        ).strip()
        expected = "\n\n".join(
            [
                "[extend]\nuseDefault = true",
                inline.strip(),
                expected_template,
            ]
        ) + "\n"
        self.assertEqual(result, expected)

    def test_invalid_json_raises_error(self) -> None:
        with self.assertRaises(ConfigBuildError):
            build_config(
                template_path=TEMPLATE_PATH,
                inline_contents="",
                vars_json="{invalid}",
                extend=False,
            )

    def test_missing_template_key_raises_error(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as fh:
            tmp_path = Path(fh.name)
            fh.write("value = ${MISSING}")

        try:
            with self.assertRaises(ConfigBuildError):
                build_config(
                    template_path=tmp_path,
                    inline_contents="",
                    vars_json=json.dumps({}),
                    extend=False,
                )
        finally:
            tmp_path.unlink(missing_ok=True)


class BuildConfigCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)

    def create_file(self, name: str, contents: str = "") -> Path:
        path = self.temp_path / name
        path.write_text(contents, encoding="utf-8")
        return path

    def test_run_writes_output_when_sections_present(self) -> None:
        contents_file = self.create_file("contents.toml", "[[rules]]\nid = 'custom'")
        output_file = self.temp_path / "output.toml"

        exit_code = run([
            "--output",
            str(output_file),
            "--template",
            str(TEMPLATE_PATH),
            "--contents",
            str(contents_file),
        ])

        self.assertEqual(exit_code, 0)
        self.assertTrue(output_file.exists())
        self.assertIn("custom", output_file.read_text(encoding="utf-8"))

    def test_run_removes_output_when_no_sections(self) -> None:
        output_file = self.create_file("output.toml", "placeholder")

        exit_code = run([
            "--output",
            str(output_file),
            "--template",
            str(TEMPLATE_PATH),
        ])

        self.assertEqual(exit_code, 0)
        self.assertFalse(output_file.exists())

    def test_run_returns_error_on_invalid_json(self) -> None:
        vars_file = self.create_file("vars.json", "{invalid}")
        output_file = self.temp_path / "output.toml"

        exit_code = run([
            "--output",
            str(output_file),
            "--template",
            str(TEMPLATE_PATH),
            "--vars",
            str(vars_file),
        ])

        self.assertEqual(exit_code, 1)
        self.assertFalse(output_file.exists())

    def test_run_returns_error_on_missing_template_key(self) -> None:
        template_file = self.create_file("template.toml", "value = ${MISSING}")
        vars_file = self.create_file("vars.json", "{}")
        output_file = self.temp_path / "output.toml"

        exit_code = run([
            "--output",
            str(output_file),
            "--template",
            str(template_file),
            "--vars",
            str(vars_file),
        ])

        self.assertEqual(exit_code, 1)
        self.assertFalse(output_file.exists())


if __name__ == "__main__":
    unittest.main()
