import os
import typing
import unittest

import aiofiles
import aiofiles.os
import aiofiles.tempfile

from actions.core.summary import SUMMARY_ENV_VAR, summary


class TestSummary(unittest.IsolatedAsyncioTestCase):
    text: typing.ClassVar[str] = "hello world 🌎"
    code: typing.ClassVar[str] = "func fork() {\n    for {\n        go fork()\n    }\n}"
    list: typing.ClassVar[typing.List[str]] = ["foo", "bar", "baz", "💣"]
    table: typing.ClassVar[typing.List[typing.List]] = [
        [
            {"data": "foo", "header": True},
            {"data": "bar", "header": True},
            {"data": "baz", "header": True},
            {"data": "tall", "rowspan": "3"},
        ],
        ["one", "two", "three"],
        [{"data": "wide", "colspan": "3"}],
    ]
    details: typing.ClassVar[typing.Dict[str, str]] = {
        "label": "open me",
        "content": "🎉 surprise",
    }
    img: typing.ClassVar[typing.Dict[str, typing.Any]] = {
        "src": "https://github.com/actions.png",
        "alt": "actions logo",
        "options": {"width": "32", "height": "32"},
    }
    quote: typing.ClassVar[typing.Dict[str, str]] = {
        "text": "Where the world builds software",
        "cite": "https://github.com/about",
    }
    link: typing.ClassVar[typing.Dict[str, str]] = {
        "text": "GitHub",
        "href": "https://github.com/",
    }

    async def asyncSetUp(self):
        async with aiofiles.tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            self.file = str(f.name)
        os.environ[SUMMARY_ENV_VAR] = str(self.file)
        summary.empty_buffer()

    async def asyncTearDown(self):
        if await aiofiles.os.path.isfile(self.file):
            await aiofiles.os.remove(self.file)
        if SUMMARY_ENV_VAR in os.environ:
            del os.environ[SUMMARY_ENV_VAR]
        summary.empty_buffer()
        summary._file_path = None

    async def test_file_path(self):
        for _ in range(2):
            self.assertEqual(await summary.file_path(), self.file)

    async def test_raises_if_summary_env_var_is_not_set(self):
        del os.environ[SUMMARY_ENV_VAR]
        with self.assertRaisesRegex(
            Exception,
            (
                f"Unable to find environment variable for {SUMMARY_ENV_VAR}\\. "
                "Check if your runtime environment supports job summaries\\."
            ),
        ):
            await summary.add_raw(self.text).write()

    async def test_raises_if_summary_file_does_not_exist(self):
        await aiofiles.os.remove(self.file)
        with self.assertRaisesRegex(
            Exception,
            (
                f"Unable to access summary file: '{self.file}'\\. "
                "Check if the file has correct read/write permissions\\."
            ),
        ):
            await summary.add_raw(self.text).write()

    async def test_appends_text_to_summary_file(self):
        await self.write_file("# ")
        await summary.add_raw(self.text).write()
        await self.assertSummary(f"# {self.text}")

    async def test_overwrites_text_to_summary_file(self):
        await self.write_file("overwrite")
        await summary.add_raw(self.text).write(overwrite=True)
        await self.assertSummary(self.text)

    async def test_appends_text_with_eol_to_summary_file(self):
        await self.write_file("# ")
        await summary.add_raw(self.text, add_eol=True).write()
        await self.assertSummary(f"# {self.text}{os.linesep}")

    async def test_chains_appends_text_to_summary_file(self):
        await summary.add_raw(self.text).add_raw(self.text).add_raw(self.text).write()
        await self.assertSummary("".join([self.text, self.text, self.text]))

    async def test_empties_buffer_after_write(self):
        await summary.add_raw(self.text).write()
        await self.assertSummary(self.text)
        self.assertTrue(summary.is_empty_buffer())

    async def test_returns_summary_buffer_as_string(self):
        summary.add_raw(self.text)
        self.assertEqual(summary.stringify(), self.text)

    async def test_return_correct_values_for_is_empty_buffer(self):
        summary.add_raw(self.text)
        self.assertFalse(summary.is_empty_buffer())
        summary.empty_buffer()
        self.assertTrue(summary.is_empty_buffer())

    async def test_clears_a_buffer_and_summary_file(self):
        await self.write_file("content")
        await summary.clear()
        await self.assertSummary("")
        self.assertTrue(summary.is_empty_buffer())

    async def test_adds_eol(self):
        await summary.add_raw(self.text).add_eol().write()
        await self.assertSummary(f"{self.text}{os.linesep}")

    async def test_adds_a_code_block_without_language(self):
        await summary.add_code_block(self.code).write()
        await self.assertSummary(f"<pre><code>{self.code}</code></pre>{os.linesep}")

    async def test_adds_a_code_block_with_a_language(self):
        await summary.add_code_block(self.code, "go").write()
        await self.assertSummary(
            f'<pre lang="go"><code>{self.code}</code></pre>{os.linesep}'
        )

    async def test_adds_an_unordered_list(self):
        await summary.add_list(self.list).write()
        await self.assertSummary(
            f"<ul><li>foo</li><li>bar</li><li>baz</li><li>💣</li></ul>{os.linesep}"
        )

    async def test_adds_an_ordered_list(self):
        await summary.add_list(self.list, True).write()
        await self.assertSummary(
            f"<ol><li>foo</li><li>bar</li><li>baz</li><li>💣</li></ol>{os.linesep}"
        )

    async def test_adds_a_table(self):
        await summary.add_table(self.table).write()
        await self.assertSummary(
            (
                '<table><tr><th>foo</th><th>bar</th><th>baz</th><td rowspan="3">'
                "tall</td></tr><tr><td>one</td><td>two</td><td>three</td></tr>"
                f'<tr><td colspan="3">wide</td></tr></table>{os.linesep}'
            )
        )

    async def test_adds_a_details_element(self):
        await summary.add_details(
            self.details["label"], self.details["content"]
        ).write()
        await self.assertSummary(
            f"<details><summary>open me</summary>🎉 surprise</details>{os.linesep}"
        )

    async def test_adds_an_image_with_alt_text(self):
        await summary.add_image(self.img["src"], self.img["alt"]).write()
        await self.assertSummary(
            f'<img src="https://github.com/actions.png" alt="actions logo">{os.linesep}'
        )

    async def test_adds_an_image_with_custom_dimensions(self):
        await summary.add_image(
            self.img["src"], self.img["alt"], **self.img["options"]
        ).write()
        await self.assertSummary(
            '<img src="https://github.com/actions.png" alt="actions logo" width="32" '
            f'height="32">{os.linesep}'
        )

    async def test_adds_headings_h1_h6(self):
        for i in (1, 2, 3, 4, 5, 6):
            summary.add_heading("heading", i)
        await summary.write()
        await self.assertSummary(
            f"<h1>heading</h1>{os.linesep}<h2>heading</h2>{os.linesep}"
            f"<h3>heading</h3>{os.linesep}<h4>heading</h4>{os.linesep}"
            f"<h5>heading</h5>{os.linesep}<h6>heading</h6>{os.linesep}"
        )

    async def test_adds_h1_if_heading_level_not_specified(self):
        await summary.add_heading("heading").write()
        await self.assertSummary(f"<h1>heading</h1>{os.linesep}")

    async def test_uses_h1_if_heading_level_is_garbage_or_out_of_range(self):
        await (
            summary.add_heading("heading", "foobar")
            .add_heading("heading", 1337)
            .add_heading("heading", -1)
            .add_heading("heading", float("inf"))
            .write()
        )
        await self.assertSummary(
            f"<h1>heading</h1>{os.linesep}<h1>heading</h1>{os.linesep}"
            f"<h1>heading</h1>{os.linesep}<h1>heading</h1>{os.linesep}"
        )

    async def test_adds_a_separator(self):
        await summary.add_separator().write()
        await self.assertSummary(f"<hr>{os.linesep}")

    async def test_adds_a_break(self):
        await summary.add_break().write()
        await self.assertSummary(f"<br>{os.linesep}")

    async def test_adds_a_quote(self):
        await summary.add_quote(self.quote["text"]).write()
        await self.assertSummary(
            f"<blockquote>Where the world builds software</blockquote>{os.linesep}"
        )

    async def test_adds_a_quote_with_citation(self):
        await summary.add_quote(self.quote["text"], self.quote["cite"]).write()
        await self.assertSummary(
            '<blockquote cite="https://github.com/about">'
            f"Where the world builds software</blockquote>{os.linesep}"
        )

    async def test_adds_a_link_with_href(self):
        await summary.add_link(self.link["text"], self.link["href"]).write()
        await self.assertSummary(
            f'<a href="https://github.com/">GitHub</a>{os.linesep}'
        )

    async def assertSummary(self, expr: str, msg: typing.Optional[str] = None):  # noqa: N802
        """Check that the expression is same with summary file content."""
        async with aiofiles.open(self.file, "r") as f:
            content = await f.read()
            self.assertEqual(expr, content, msg)

    async def write_file(self, s: str):
        async with aiofiles.open(self.file, mode="a") as f:
            await f.write(s)
