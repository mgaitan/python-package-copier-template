from pathlib import Path

from copier import run_copy, run_update

TEMPLATE_SRC = "gh:mgaitan/python-package-copier-template"
ANSWER_FILES: tuple[str, ...] = (".copier-answers.yml", ".copier-answers.yaml")


def has_answers(dst: Path) -> bool:
    return any((dst / filename).exists() for filename in ANSWER_FILES)


def main() -> int:
    dst = Path.cwd()

    if has_answers(dst):
        run_update(dst_path=str(dst), defaults=True, trust=True)
    else:
        run_copy(src=TEMPLATE_SRC, dst_path=str(dst), defaults=True, trust=True)

    return 0
