import json
import os
import sys

import numpy as np
import pytest
import tifffile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
from concatenate_moldev_files import (  # noqa: E402
    chunk_index,
    sort_chunks,
    check_chunk_timestamps,
    concatenate_images,
)


def _write_chunk(path, value, acq_time=None, n_frames=2):
    """Write a small MolDev-like TIFF chunk filled with `value`."""
    desc = "<MetaData>"
    desc += '<prop id="Description" type="string" value="Exposure: 10 msec"/>'
    if acq_time is not None:
        desc += f'<prop id="acquisition-time-local" type="time" value="{acq_time}"/>'
    desc += "</MetaData>"
    data = np.full((n_frames, 4, 4), value, dtype=np.uint16)
    tifffile.imwrite(path, data, description=desc, metadata=None)


def test_chunk_index():
    assert chunk_index("/a/X_FITC.tif") == 1
    assert chunk_index("/a/X_FITC-file002.tif") == 2
    assert chunk_index("/a/X_FITC-file010.tif") == 10


def test_sort_chunks_unsuffixed_first_and_numeric():
    files = ["X_FITC-file010.tif", "X_FITC.tif", "X_FITC-file002.tif"]
    assert sort_chunks(files) == ["X_FITC.tif", "X_FITC-file002.tif", "X_FITC-file010.tif"]


def test_sort_chunks_duplicate_index():
    with pytest.raises(ValueError):
        sort_chunks(["a/X_FITC-file002.tif", "b/X_FITC-file002.tif"])


def test_check_chunk_timestamps_mismatch(tmp_path):
    f1 = str(tmp_path / "X_FITC.tif")
    f2 = str(tmp_path / "X_FITC-file002.tif")
    _write_chunk(f1, 1, "20251118 19:56:56.388")
    _write_chunk(f2, 2, "20251118 19:56:17.799")
    with pytest.raises(ValueError):
        check_chunk_timestamps([f1, f2])


def test_concatenate_images_order(tmp_path):
    times = ["20251118 19:56:17.799", "20251118 19:56:56.388", "20251118 19:57:34.977"]
    names = ["X_FITC.tif", "X_FITC-file002.tif", "X_FITC-file003.tif"]
    paths = [str(tmp_path / n) for n in names]
    for i, (p, t) in enumerate(zip(paths, times), start=1):
        _write_chunk(p, i, t)

    out = str(tmp_path / "out" / "combined.tif")
    # pass in plain string-sorted order (the old, wrong order)
    concatenate_images(sorted(paths), out)

    combined = tifffile.imread(out)
    assert combined[:, 0, 0].tolist() == [1, 1, 2, 2, 3, 3]
    # metadata comes from the first chunk
    with tifffile.TiffFile(out) as tif:
        metadata = json.loads(tif.pages[0].tags["ImageDescription"].value)
    assert "19:56:17.799" in metadata["ImageDescription"]
