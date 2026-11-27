"""Stage only exact file paths named in a UTF-8 allowlist.

Usage from the repository root:
    python3 scripts/stage_slice.py scripts/allowlists/MEM-01.txt

Directory entries, pathspecs, absolute paths, and repository escapes are
rejected. Existing unrelated index entries are left untouched.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path, PurePosixPath


class StageSliceError(Exception):
    """Input or Git state is unsafe for an exact-path staging operation."""


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise StageSliceError(f"git {' '.join(args)} failed ({result.returncode}): {message}")
    return result


def repository_root(start: Path) -> Path:
    result = git(start, "rev-parse", "--show-toplevel")
    return Path(result.stdout.decode("utf-8").strip()).resolve()


def read_allowlist(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StageSliceError(f"cannot read allowlist {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise StageSliceError(f"allowlist must be UTF-8 text: {path}") from exc

    paths: list[str] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        value = raw_line
        if value != value.strip():
            raise StageSliceError(f"allowlist line {line_number}: leading/trailing whitespace is not allowed")
        if "\\" in value or "\x00" in value:
            raise StageSliceError(f"allowlist line {line_number}: use a repository-relative POSIX path")
        candidate = PurePosixPath(value)
        if candidate.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
            raise StageSliceError(f"allowlist line {line_number}: path must be canonical and repository-relative")
        if ".git" in candidate.parts:
            raise StageSliceError(f"allowlist line {line_number}: .git paths are not allowed")
        if value in seen:
            raise StageSliceError(f"allowlist line {line_number}: duplicate path {value!r}")
        seen.add(value)
        paths.append(value)

    if not paths:
        raise StageSliceError("allowlist has no file paths")
    return paths


def nul_paths(data: bytes) -> set[str]:
    return {item.decode("utf-8", errors="surrogateescape") for item in data.split(b"\0") if item}


def tracked_paths(root: Path) -> set[str]:
    index = nul_paths(git(root, "ls-files", "-z").stdout)
    head_result = git(root, "ls-tree", "-r", "--name-only", "-z", "HEAD", check=False)
    if head_result.returncode == 0:
        index.update(nul_paths(head_result.stdout))
    elif b"Not a valid object name HEAD" not in head_result.stderr and b"bad revision 'HEAD'" not in head_result.stderr:
        message = head_result.stderr.decode("utf-8", errors="replace").strip()
        raise StageSliceError(f"cannot inspect HEAD tree: {message}")
    return index


def staged_paths(root: Path) -> set[str]:
    return nul_paths(git(root, "diff", "--cached", "--name-only", "-z").stdout)


def validate_file_paths(root: Path, paths: list[str]) -> None:
    known = tracked_paths(root)
    known_directories = {parent for item in known for parent in PurePosixPath(item).parents if str(parent) != "."}

    for value in paths:
        if value in known_directories:
            raise StageSliceError(f"directory allowlist entry is not permitted: {value!r}")
        target = root.joinpath(*PurePosixPath(value).parts)
        if target.is_dir():
            raise StageSliceError(f"directory allowlist entry is not permitted: {value!r}")
        if not (target.exists() or target.is_symlink() or value in known):
            raise StageSliceError(f"path is neither present nor tracked (deleted tracked files are allowed): {value!r}")


def stage(root: Path, paths: list[str]) -> tuple[list[str], int]:
    validate_file_paths(root, paths)
    before = staged_paths(root)

    # --literal-pathspecs prevents wildcard/bracket characters in filenames
    # from expanding to other paths. There is deliberately no -A/--all flag.
    git(root, "--literal-pathspecs", "add", "--", *paths)

    after = staged_paths(root)
    unexpected = (after - before) - set(paths)
    if unexpected:
        names = ", ".join(repr(name) for name in sorted(unexpected))
        raise StageSliceError(f"Git staged paths outside this allowlist: {names}")
    staged_allowlisted = [path for path in paths if path in after]
    return staged_allowlisted, len(after)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("allowlist", help="UTF-8 text file with one exact repository-relative file path per line")
    parser.add_argument("--repo", default=".", help="repository directory (default: current directory)")
    args = parser.parse_args(argv)

    try:
        root = repository_root(Path(args.repo).resolve())
        allowlist_path = Path(args.allowlist)
        if not allowlist_path.is_absolute():
            allowlist_path = root / allowlist_path
        paths = read_allowlist(allowlist_path)
        staged, index_count = stage(root, paths)
    except StageSliceError as exc:
        print(f"stage_slice: error: {exc}", file=sys.stderr)
        return 2

    print(f"allowlisted_paths={len(paths)}")
    print(f"staged_allowlisted_count={len(staged)}")
    print(f"index_staged_path_count={index_count}")
    print("staged_allowlisted_paths:")
    if staged:
        for path in staged:
            print(f"  {path}")
    else:
        print("  (none; allowlisted paths currently have no staged diff)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
