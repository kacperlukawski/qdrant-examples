import itertools
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter
import markdown_it.token
from loguru import logger
from markdown_it import MarkdownIt
from mdformat.renderer import MDRenderer
from mdformat_frontmatter import plugin as mdformat_front_matter_plugin
from mdformat_tables import plugin as tables_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.wordcount import wordcount_plugin
from nbconvert import MarkdownExporter

from .git import GitHubRepository


@dataclass
class ParsedMarkdown:
    """
    A class for keeping a consistent representation of a Markdown document.
    """

    raw_content: str
    tokens: list[markdown_it.token.Token]
    metadata: dict | None = field(default_factory=dict)
    env: dict | None = field(default_factory=dict)


class NotebookToHugoMarkdownConverter:
    """
    A converter that converts Jupyter notebooks to Hugo markdown files, including the frontmatter.
    It additionally performs some formatting fixes to the generated markdown.
    """

    def __init__(self):
        self._exporter = MarkdownExporter()
        self._md = (
            MarkdownIt(
                "gfm-like",
                {"parser_extension": [mdformat_front_matter_plugin, tables_plugin]},
                renderer_cls=MDRenderer,
            )
            .use(front_matter_plugin)
            .use(wordcount_plugin)
            .enable("front_matter")
            .enable("table")
        )
        self._git_repository = GitHubRepository()

    def convert(self, notebook_path: Path, output_path: Path):
        """
        Run the conversion process for a selected Jupyter notebook and save the output to a markdown file.
        :param notebook_path: The path to the Jupyter notebook to convert.
        :param output_path: The path to save the converted markdown file.
        """
        if not notebook_path.exists():
            raise FileNotFoundError(f"Notebook file not found: {notebook_path}")

        with open(notebook_path) as fp:
            body, _ = self._exporter.from_file(fp)

        # Parse the document and pass it through all the processing steps
        env_dict = {}
        parsed_markdown = ParsedMarkdown(
            body, self._md.parse(body, env_dict), env=env_dict
        )

        # Perform additional modifications so the Markdown is compatible with Hugo
        parsed_markdown = self._separate_code_blocks(parsed_markdown)

        # Add the frontmatter to the Markdown content
        parsed_markdown = self._add_frontmatter(notebook_path, parsed_markdown)

        # Render the finalized Markdown content to a file. The MDRenderer will take care of the formatting.
        with open(output_path, "w") as f:
            rendered_md = self._md.renderer.render(
                parsed_markdown.tokens, self._md.options, parsed_markdown.env
            )
            f.write(rendered_md)
        logger.info(f"Converted notebook to markdown: {output_path}")

    def _separate_code_blocks(self, markdown: ParsedMarkdown) -> ParsedMarkdown:
        """
        Separate code blocks in the markdown to ensure they are rendered correctly by Hugo.
        If there are multiple code blocks of the same language in a row, Hugo will render them
        as tabs, but they won't be functional. This function ensures that each such a pair of
        code blocks is separated by a horizontal rule.
        """
        new_tokens = []
        for first, second in itertools.pairwise(markdown.tokens):
            new_tokens.append(first)
            if (
                first.type == "fence"
                and second.type == "fence"
                and first.info == second.info
            ):
                new_tokens.append(
                    markdown_it.token.Token(
                        type="html_block", tag="", nesting=0, content="<hr />"
                    )
                )

        # The last token won't be added in a loop, so we need to add it manually
        if len(markdown.tokens) > 0:
            new_tokens.append(markdown.tokens[-1])

        return ParsedMarkdown(
            markdown.raw_content, new_tokens, markdown.metadata, markdown.env
        )

    def _add_frontmatter(
        self, notebook_path: Path, markdown: ParsedMarkdown
    ) -> ParsedMarkdown:
        """
        Add document metadata to the Markdown content.
        :param notebook_path: The path to the notebook file.
        :param markdown: The parsed Markdown content.
        :return: The Markdown content with the frontmatter added.
        """
        # Add all the attributes to render in the metadata
        new_metadata = {**markdown.metadata}
        new_metadata["title"] = self._extract_title(markdown)
        new_metadata["google_colab_link"] = self._add_colab_link(notebook_path)
        new_metadata["reading_time_min"] = markdown.env["wordcount"]["minutes"]

        # Render the frontmatter with python-frontmatter, so all the metadata is correctly formatted,
        # including escaping special characters.
        post = frontmatter.Post("", **new_metadata)
        doc_frontmatter = frontmatter.dumps(post).strip().strip("-").strip()

        # Build the new document with the frontmatter at the beginning
        new_tokens = [
            markdown_it.token.Token(
                type="front_matter",
                tag="",
                nesting=0,
                content=doc_frontmatter,
                markup="---",
                block=True,
                hidden=True,
            ),
            *markdown.tokens,
        ]
        return ParsedMarkdown(
            markdown.raw_content, new_tokens, new_metadata, markdown.env
        )

    def _extract_title(self, markdown: ParsedMarkdown) -> str | None:
        """
        Extract the title from the markdown content. The fist level 1 heading is considered the title.
        :param markdown: The parsed markdown content.
        :return: The title of the document.
        """
        use_next = False
        for token in markdown.tokens:
            if use_next and token.type == "inline":
                return token.content
            # If the current token is a heading, the next inline token will be the title
            use_next = token.type == "heading_open" and token.markup == "#"
        return None

    def _add_colab_link(self, notebook_path: Path) -> str:
        """
        Add a link to open the notebook in Google Colab.
        :param notebook_path: The path to the notebook file.
        :return: The link to open the notebook in Google Colab.
        """
        repository_name = self._git_repository.repository_name()
        current_branch = self._git_repository.current_branch_name()
        relative_path = self._git_repository.relative_path(notebook_path)
        return f"https://githubtocolab.com/{repository_name}/blob/{current_branch}/{relative_path}"
