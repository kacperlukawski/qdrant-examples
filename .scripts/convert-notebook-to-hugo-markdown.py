from pathlib import Path

import typer
from helpers.markdown import NotebookToHugoMarkdownConverter
from typing_extensions import Annotated


def main(
    notebook_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
):
    """
    Convert a Jupyter notebook to a Hugo markdown file using the `NotebookToHugoMarkdownConverter`.
    :param notebook_path: The path to the Jupyter notebook to convert.
    :param output_dir:
        The directory to save the converted markdown file. If not provided, the output will be saved
        in the same directory as the notebook.
    """
    if output_dir is None:
        output_dir = notebook_path.parent
    output_md_file = output_dir / f"{notebook_path.stem}.md"

    converter = NotebookToHugoMarkdownConverter()
    converter.convert(notebook_path, output_md_file)


if __name__ == "__main__":
    typer.run(main)
