"""Where the course writes scratch files.

Students do not have write access to /tmp on eustis, so nothing in this course
may assume it exists or is writable. Scratch goes under ~/.vvtemp instead --
one directory, so `just clean-tmp` can show you what is in there and clear it.

Set CRAFT_TMP to put it somewhere else (a fast local disk, say):

    export CRAFT_TMP=/scratch/$USER/vv

Nothing here ever writes inside the repo, so a mutated DUT can never be
committed by accident -- that separation is the point of using scratch at all.
"""
import os
import pathlib

__all__ = ["craft_tmp_root", "craft_tmp_dir", "craft_tmp_file"]


def craft_tmp_root():
    """The scratch root, as a Path. Not created."""
    return pathlib.Path(
        os.environ.get("CRAFT_TMP") or os.path.join(os.path.expanduser("~"), ".vvtemp"))


def craft_tmp_dir(*parts):
    """A scratch DIRECTORY, created if missing. craft_tmp_dir('wk08') -> Path."""
    p = craft_tmp_root().joinpath(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p


def craft_tmp_file(*parts):
    """A scratch FILE path; its parent is created, the file is not touched."""
    p = craft_tmp_root().joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
