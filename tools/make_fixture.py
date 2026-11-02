"""Generate the deterministic ``fixture/`` corpus.

Run from the repository root, this script writes ``FILES`` files named
``mod_NNN.py`` into ``fixture/``, each a marker line followed by body lines
drawn from ``ALPHABET`` until the file passes 2 MiB. The three constants below
are the program's only inputs: every count, name, size and path is derived from
them, and a rerun with unchanged constants rewrites byte-identical files.
"""

import random
import re
from pathlib import Path

FILES = 466
MARKER = "x"
ALPHABET = "abcd"


def fixture_dir() -> Path:
    """Return the ``fixture/`` directory at the repository root."""
    # Resolve first, because __file__ is relative when the script is invoked as
    # "python tools/make_fixture.py" and the parent steps below would then be
    # meaningless. The repository root is the parent of the tools/ directory.
    return Path(__file__).resolve().parent.parent / "fixture"


def file_name(index: int) -> str:
    """Return the file name for ``index``, zero-padded to three digits."""
    # This format and the anchored pattern in prune_surplus() are two spellings
    # of one name shape; a change to either belongs in both.
    return f"mod_{index:03d}.py"


def write_fixture(index: int, directory: Path) -> None:
    """Write one fixture file, deterministically seeded by ``index``."""
    rng = random.Random(index)
    with (directory / file_name(index)).open("wb") as handle:
        # The 2 MiB target is the size of the whole file, so the marker line's
        # encoded length starts the running total instead of counting outside
        # it, and each line is measured in bytes rather than characters.
        marker_line = ("# charset-marker: " + MARKER + "\n").encode("utf-8")
        handle.write(marker_line)
        written = len(marker_line)
        # Lines are added while the file is still under the threshold and the
        # line that crosses it is written whole: nothing is trimmed, padded or
        # truncated, so every line is complete.
        while written < 2 * 1024 * 1024:
            line = "".join(rng.choices(ALPHABET, k=99)) + "\n"
            encoded = line.encode("utf-8")
            handle.write(encoded)
            written += len(encoded)


def prune_surplus(directory: Path) -> None:
    """Delete generated fixture files whose index is at or above ``FILES``."""
    # sorted() materialises the listing, so deleting inside the loop cannot
    # disturb what is still to be visited.
    for entry in sorted(directory.iterdir()):
        if not entry.is_file():
            continue
        # fullmatch anchors the whole name to the shape file_name() produces,
        # so a differently named file, a four-digit name or a directory is left
        # alone - which a wildcard could not distinguish.
        match = re.fullmatch(r"mod_(\d{3})\.py", entry.name)
        if match is None or int(match.group(1)) < FILES:
            continue
        entry.unlink(missing_ok=True)


def main() -> None:
    """Write every fixture file in ascending order, then prune the surplus."""
    directory = fixture_dir()
    directory.mkdir(parents=True, exist_ok=True)
    for index in range(FILES):
        write_fixture(index, directory)
    prune_surplus(directory)


if __name__ == "__main__":
    main()
