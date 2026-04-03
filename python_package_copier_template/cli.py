import argparse
import json
import os
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, distribution, version
from pathlib import Path
from urllib.parse import unquote, urlparse

from copier import run_copy, run_update

from python_package_copier_template import extensions

TEMPLATE_SRC = "gh:mgaitan/python-package-copier-template"
ANSWER_FILES: tuple[str, ...] = (".copier-answers.yml", ".copier-answers.yaml")


@dataclass(frozen=True)
class TemplateTarget:
    src_path: str
    vcs_ref: str | None = None


def get_version() -> str:
    try:
        return version("python-package-copier-template")
    except PackageNotFoundError:
        return "0.0.0"


def has_answers(dst: Path) -> bool:
    return any((dst / filename).exists() for filename in ANSWER_FILES)


def resolve_template_target() -> TemplateTarget:
    try:
        dist = distribution("python-package-copier-template")
    except PackageNotFoundError:
        return TemplateTarget(src_path=TEMPLATE_SRC)

    direct_url_text = dist.read_text("direct_url.json")
    if direct_url_text:
        direct_url = json.loads(direct_url_text)
        url = direct_url.get("url", "")
        parsed_url = urlparse(url)

        if parsed_url.scheme == "file":
            return TemplateTarget(src_path=unquote(parsed_url.path))

        if vcs_info := direct_url.get("vcs_info"):
            return TemplateTarget(
                src_path=TEMPLATE_SRC,
                vcs_ref=vcs_info.get("commit_id") or vcs_info.get("requested_revision"),
            )

    return TemplateTarget(src_path=TEMPLATE_SRC, vcs_ref=dist.version)


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
        help="Destination directory.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {get_version()}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    copy_defaults = os.environ.get("COPIER_TEMPLATE_DEFAULTS") == "1"
    if not args.destination:
        parser.error("Destination path is required. Use Copier directly if you want interactive prompts.")

    dst = Path(args.destination).expanduser()
    if has_answers(dst):
        with extensions.update_mode():
            run_update(
                dst_path=str(dst),
                defaults=True,
                unsafe=True,
                overwrite=True,
                skip_answered=True,
            )
    else:
        template_target = resolve_template_target()
        run_copy(
            src_path=template_target.src_path,
            dst_path=str(dst),
            defaults=copy_defaults,
            unsafe=True,
            vcs_ref=template_target.vcs_ref,
        )

    return 0
