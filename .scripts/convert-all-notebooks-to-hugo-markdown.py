from pathlib import Path

import typer
from helpers.markdown import NotebookToHugoMarkdownConverter
from loguru import logger

MAIN_DIR = Path(__file__).resolve().parent.parent


def main(
    overwrite: bool = False,
):
    converter = NotebookToHugoMarkdownConverter()

    for notebook_path in MAIN_DIR.glob("**/*.ipynb"):
        relative_notebook_dir = notebook_path.relative_to(MAIN_DIR).parent.parent
        # TODO: try to use the same output directory structure as the landing page (including the assets)
        output_dir = MAIN_DIR / ".dist" / str(relative_notebook_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = output_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        output_md_file = output_dir / f"{notebook_path.parent.stem}.md"
        if output_md_file.exists() and not overwrite:
            logger.info(
                "Skipping {} as {} already exists",
                notebook_path.relative_to(MAIN_DIR),
                output_md_file.relative_to(MAIN_DIR),
            )
            continue

        logger.info(
            "Converting {} to {}", notebook_path.relative_to(MAIN_DIR), output_md_file
        )
        converter.convert(notebook_path, output_md_file)


if __name__ == "__main__":
    typer.run(main)
