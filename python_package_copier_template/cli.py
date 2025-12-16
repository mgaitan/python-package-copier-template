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
        description=(
            "Apply the template via Copier. If the destination has a .copier-answers file, run update; "
            "otherwise run copy."
        ),
    )
    parser.add_argument(
        "destination",
        nargs="?",
        help="Destination directory (defaults to current working directory).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {get_version()}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    dst = Path(args.destination).expanduser() if args.destination else Path.cwd()

    if has_answers(dst):
        run_update(dst_path=str(dst), defaults=True, unsafe=True, overwrite=True)
    else:
        run_copy(src_path=TEMPLATE_SRC, dst_path=str(dst), defaults=True, unsafe=True)

    return 0
