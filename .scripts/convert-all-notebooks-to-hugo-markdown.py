from pathlib import Path

from helpers.markdown import NotebookToHugoMarkdownConverter
from loguru import logger

MAIN_DIR = Path(__file__).resolve().parent.parent


def main():
    converter = NotebookToHugoMarkdownConverter()

    for notebook_path in MAIN_DIR.glob("**/*.ipynb"):
        relative_notebook_dir = notebook_path.relative_to(MAIN_DIR).parent.parent
        output_dir = MAIN_DIR / ".dist" / str(relative_notebook_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_md_file = output_dir / f"{notebook_path.parent.stem}.md"

        logger.info(f"Converting {notebook_path} to {output_md_file}")
        converter.convert(notebook_path, output_md_file)


if __name__ == "__main__":
    main()
