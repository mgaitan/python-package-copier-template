import argparse
import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from copier import run_copy, run_update, main as copier_main

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

    copy_defaults = os.environ.get("COPIER_TEMPLATE_DEFAULTS") == "1"
    if args.destination:
        dst = Path(args.destination).expanduser()
        if has_answers(dst):
            run_update(dst_path=str(dst), defaults=True, unsafe=True, overwrite=True)
        else:
            run_copy(src_path=TEMPLATE_SRC, dst_path=str(dst), defaults=copy_defaults, unsafe=True)
    else:
        # Mirror Copier CLI behavior: if no destination is provided, delegate to copier CLI
        copier_args = ["copy", "--trust"]
        if copy_defaults:
            copier_args.append("--defaults")
        copier_args.append(TEMPLATE_SRC)
        copier_main(copier_args)

    return 0
