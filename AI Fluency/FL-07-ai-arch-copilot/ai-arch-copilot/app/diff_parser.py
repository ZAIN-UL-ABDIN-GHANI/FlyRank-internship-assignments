from typing import List

from unidiff import PatchSet
from unidiff.errors import UnidiffParseError


def looks_like_unified_diff(text: str) -> bool:
    """Heuristic check - good enough to route input, not a strict validator."""
    return "diff --git " in text or ("--- " in text and "+++ " in text and "@@ " in text)


def parse_unified_diff(diff_text: str) -> List[dict]:
    """Parse a unified/Git diff into per-file hunk text.

    Returns a list of {"filename": str, "content": str}, one entry per changed file.
    Raises ValueError if the text cannot be parsed as a unified diff.
    """
    try:
        patch = PatchSet(diff_text)
    except UnidiffParseError as e:
        raise ValueError(f"could not parse unified diff: {e}") from e

    files = []
    for patched_file in patch:
        hunks_text = "\n".join(str(hunk) for hunk in patched_file)
        files.append({"filename": patched_file.path, "content": hunks_text})
    return files


def format_files_for_review(files: List[dict]) -> str:
    """Combine multiple files into one text block with clear file boundaries."""
    blocks = [f"=== FILE: {f['filename']} ===\n{f['content']}" for f in files]
    return "\n\n".join(blocks)
