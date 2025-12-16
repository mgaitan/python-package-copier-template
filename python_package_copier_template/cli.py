import argparse
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from copier import run_copy, run_update

TEMPLATE_SRC = "gh:mgaitan/python-package-copier-template"
ANSWER_FILES: tuple[str, ...] = (".copier-answers.yml", ".copier-answers.yaml")


def get_version() -> str:
    try:
        return version("python-package-copier-template")
    except PackageNotFoundError:
        return "0.0.0"


def has_answers(dst: Path) -> bool:
    return any((dst / filename).exists() for filename in ANSWER_FILES)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python-package-copier-template",
        description="Apply the template via Copier (copy if no answers file, update otherwise).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {get_version()}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)

    dst = Path.cwd()

    if has_answers(dst):
        run_update(dst_path=str(dst), defaults=True, trust=True)
    else:
        run_copy(src=TEMPLATE_SRC, dst_path=str(dst), defaults=True, trust=True)

    return 0
