import os
import typing

import aiofiles.os

from actions.core._compat import Self, Unpack

SUMMARY_ENV_VAR = "GITHUB_STEP_SUMMARY"
SUMMARY_DOCS_URL = "https://docs.github.com/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summary"


SummaryTableRow = typing.Sequence[typing.Union["SummaryTableCell", str]]


class SummaryTableCell(typing.TypedDict, total=False):
    # Cell content
    data: str

    # Render cell as header
    header: bool

    # Number of columns the cell extends
    colspan: str

    # Number of rows the cell extends
    rowspan: str


class SummaryImageOptions(typing.TypedDict, total=False):
    # The width of the image in pixels. Must be an integer without a unit.
    width: str

    # The height of the image in pixels. Must be an integer without a unit.
    height: str


class SummaryWriteOptions(typing.TypedDict, total=False):
    # Replace all existing content in summary file with buffer contents
    overwrite: bool


class Summary:
    _buffer: str
    _file_path: typing.Optional[str]

    def __init__(self) -> None:
        self._buffer = ""
        self._file_path = None

    async def file_path(self) -> str:
        """
        Finds the summary file path from the environment, rejects if env var is
        not found or file does not exist
        Also checks r/w permissions.
        :return: step summary file path
        """
        if self._file_path:
            return self._file_path

        path_from_env = os.getenv(SUMMARY_ENV_VAR)
        if not path_from_env:
            raise Exception(
                f"Unable to find environment variable for {SUMMARY_ENV_VAR}. "
                "Check if your runtime environment supports job summaries."
            )

        if not await aiofiles.os.access(path_from_env, os.R_OK | os.W_OK):
            raise Exception(
                f"Unable to access summary file: '{path_from_env}'. "
                "Check if the file has correct read/write permissions."
            )

        self._file_path = path_from_env
        return self._file_path

    def wrap(
        self,
        tag: str,
        content: typing.Optional[str],
        attrs: typing.Optional[typing.Dict[str, str]] = None,
    ) -> str:
        """
        Wraps content in an HTML tag, adding any HTML attributes
        :param tag: HTML tag to wrap
        :param content: content within the tag
        :param attrs: key-value list of HTML attributes to add
        :return: content wrapped in HTML element
        """
        attrs = attrs or {}
        html_attrs = "".join([f' {key}="{value}"' for key, value in attrs.items()])
        if not content:
            return f"<{tag}{html_attrs}>"

        return f"<{tag}{html_attrs}>{content}</{tag}>"

    async def write(self, **options: Unpack[SummaryWriteOptions]) -> Self:
        """
        Writes text in the buffer to the summary buffer file and empties buffer.
        Will append by default.
        :return: summary instance
        """
        file_path = await self.file_path()
        async with aiofiles.open(
            file_path,
            "w" if options.get("overwrite", False) else "a",
        ) as f:
            await f.write(self._buffer)
        return self.empty_buffer()

    async def clear(self) -> Self:
        """
        Clears the summary buffer and wipes the summary file
        :return: summary instance
        """
        return await self.empty_buffer().write(overwrite=True)

    def stringify(self) -> str:
        """
        Returns the current summary buffer as a string
        :return: string of summary buffer
        """
        return self._buffer

    def is_empty_buffer(self) -> bool:
        """
        If the summary buffer is empty
        :return: true if the buffer is empty
        """
        return len(self._buffer) == 0

    def empty_buffer(self) -> Self:
        """
        Resets the summary buffer without writing to summary file
        :return: summary instance
        """
        self._buffer = ""
        return self

    def add_raw(self, text: str, add_eol: bool = False) -> Self:
        """
        Adds raw text to the summary buffer
        :params text: content to add
        :params add_eol: append an EOL to the raw text
        :return: summary instance
        """
        self._buffer += text
        return self.add_eol() if add_eol else self

    def add_eol(self) -> Self:
        """
        Adds the operating system-specific end-of-line marker to the buffer
        :return: summary instance
        """
        return self.add_raw(os.linesep)

    def add_code_block(self, code: str, lang: typing.Optional[str] = None) -> Self:
        """
        Adds an HTML codeblock to the summary buffer
        :params code: content to render within fenced code block
        :params lang: language to syntax highlight code
        :return: summary instance
        """
        attrs = {"lang": lang} if lang else {}
        element = self.wrap("pre", self.wrap("code", code), attrs)
        return self.add_raw(element, add_eol=True)

    def add_list(self, items: typing.Sequence[str], ordered: bool = False) -> Self:
        """
        Adds an HTML list to the summary buffer
        :params items: list of items to render
        :params ordered: if the rendered list should be ordered or not
        :return: summary instance
        """
        tag = "ol" if ordered else "ul"
        list_items = "".join([self.wrap("li", item) for item in items])
        element = self.wrap(tag, list_items)
        return self.add_raw(element, add_eol=True)

    def add_table(self, rows: typing.Sequence[SummaryTableRow]) -> Self:
        """
        Adds an HTML table to the summary buffer
        :params rows: table rows
        :return: summary instance
        """
        table_body = ""
        for row in rows:
            cells = ""
            for cell in row:
                if isinstance(cell, str):
                    cells += self.wrap("td", cell)
                    continue
                tag = "th" if cell.get("header") else "td"
                attrs = {
                    "colspan": cell.get("colspan"),
                    "rowspan": cell.get("rowspan"),
                }
                cells += self.wrap(
                    tag,
                    cell.get("data"),
                    {k: v for k, v in attrs.items() if v is not None},
                )
            table_body += self.wrap("tr", cells)

        element = self.wrap("table", table_body)
        return self.add_raw(element, add_eol=True)

    def add_details(self, label: str, content: str) -> Self:
        """
        Adds a collapsable HTML details element to the summary buffer
        :params label: text for the closed state
        :params content: collapsable content
        :return: summary instance
        """
        element = self.wrap("details", self.wrap("summary", label) + content)
        return self.add_raw(element, add_eol=True)

    def add_image(
        self, src: str, alt: str, **options: Unpack[SummaryImageOptions]
    ) -> Self:
        """
        Adds an HTML image tag to the summary buffer
        :params src: path to the image you to embed
        :params alt: text description of the image
        :params options: addition image attributes
        :return: summary instance
        """
        element = self.wrap("img", None, {"src": src, "alt": alt, **options})
        return self.add_raw(element, add_eol=True)

    def add_heading(self, text: str, level: typing.Union[int, float, str] = 1) -> Self:
        """
        Adds an HTML section heading element
        :params text: heading text
        :params level: the heading level
        :return: summary instance
        """
        tag = f"h{level}"
        allowed_tag = tag if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} else "h1"
        element = self.wrap(allowed_tag, text)
        return self.add_raw(element, add_eol=True)

    def add_separator(self) -> Self:
        """
        Adds an HTML thematic break (<hr>) to the summary buffer
        :return: summary instance
        """
        element = self.wrap("hr", None)
        return self.add_raw(element, add_eol=True)

    def add_break(self) -> Self:
        """
        Adds an HTML line break (<br>) to the summary buffer
        :return: summary instance
        """
        element = self.wrap("br", None)
        return self.add_raw(element, add_eol=True)

    def add_quote(self, text: str, cite: typing.Optional[str] = None) -> Self:
        """
        Adds an HTML blockquote to the summary buffer
        :params text: quote text
        :params cite: citation url
        :return: summary instance
        """
        attrs = {"cite": cite} if cite else {}
        element = self.wrap("blockquote", text, attrs)
        return self.add_raw(element, add_eol=True)

    def add_link(self, text: str, href: str) -> Self:
        """
        Adds an HTML anchor tag to the summary buffer
        :params text: link text/content
        :params href: hyperlink
        :return: summary instance
        """
        element = self.wrap("a", text, {"href": href})
        return self.add_raw(element, add_eol=True)


summary = Summary()
