from pathlib import Path

import typer
from helpers.markdown import NotebookToHugoMarkdownConverter
from typing_extensions import Annotated

MAIN_DIR = Path(__file__).resolve().parent.parent


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
            exists=False,
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
        in the `.dist` directory in the main directory of the repository.
    """
    if output_dir is None:
        relative_notebook_dir = notebook_path.relative_to(MAIN_DIR).parent.parent
        output_dir = MAIN_DIR / ".dist" / str(relative_notebook_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    output_md_file = output_dir / f"{notebook_path.parent.stem}.md"

    converter = NotebookToHugoMarkdownConverter()
    converter.convert(notebook_path, output_md_file)


if __name__ == "__main__":
    typer.run(main)
