"""Encode the native RGB screenshot as PNG using only the standard library."""
import base64
import struct
import zlib
from pathlib import Path


def png_bytes(frame):
    if frame.get("pixel_format") != "rgb8" or frame.get("encoding") != "base64":
        raise ValueError("Unsupported capture encoding")
    width, height = frame["width"], frame["height"]
    if type(width) is not int or type(height) is not int or not (0 < width <= 1280 and 0 < height <= 1280):
        raise ValueError("Invalid capture dimensions")
    raw = base64.b64decode(frame["data"], validate=True)
    if len(raw) != width * height * 3:
        raise ValueError("Truncated capture pixels")
    def chunk(name, data):
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data))
    scanlines = b"".join(b"\0" + raw[row * width * 3:(row + 1) * width * 3] for row in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b""))


def save_capture(client, runtime, target):
    result = client.call("capture_frame", runtime=runtime)["frame"]
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(png_bytes(result))
    return {"path": str(target), **{k: v for k, v in result.items() if k != "data"}}
