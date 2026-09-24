import json
import os
import struct
import time
import uuid


def discover():
    if os.name != "nt":
        return []
    return sorted("\\\\.\\pipe\\" + name for name in os.listdir("\\\\.\\pipe\\") if name.startswith("CyRSAssistant-"))


def read_exact(stream, count):
    result = bytearray()
    while len(result) < count:
        part = stream.read(count - len(result))
        if not part:
            raise ConnectionError("Add-on disconnected")
        result.extend(part)
    return bytes(result)


class Client:
    def __init__(self, pipe):
        if not pipe.startswith("\\\\.\\pipe\\CyRSAssistant-") or not pipe.rsplit("-", 1)[-1].isdigit():
            raise ValueError("Expected a local CyRSAssistant named pipe")
        self.pipe = pipe

    def call(self, method, **arguments):
        body = {"protocol": 1, "request_id": str(uuid.uuid4()), "method": method, **arguments}
        encoded = json.dumps(body, allow_nan=False).encode("utf-8")
        if len(encoded) > 1024 * 1024:
            raise ValueError("Request exceeds 1 MiB")
        deadline = time.monotonic() + 3
        while True:
            try:
                stream = open(self.pipe, "r+b", buffering=0)
                break
            except OSError as exc:
                # CPython's CRT may map a pipe instance closing between calls to
                # EINVAL without winerror. No bytes were sent yet, so opening is safe to retry.
                retryable = getattr(exc, "winerror", None) in (2, 231, 232) or exc.errno == 22 or isinstance(exc, (FileNotFoundError, PermissionError))
                if not retryable or time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)
        with stream:
            data = struct.pack("<I", len(encoded)) + encoded
            while data:
                written = stream.write(data)
                if not written:
                    raise ConnectionError("Failed to send request")
                data = data[written:]
            size, = struct.unpack("<I", read_exact(stream, 4))
            if not 0 < size <= 8 * 1024 * 1024:
                raise ValueError("Invalid response size")
            response_bytes = read_exact(stream, size)
            stream.write(b"\x01")
            result = json.loads(response_bytes)
        if not result.get("ok"):
            raise RuntimeError(result.get("error", "Unknown add-on error"))
        return result

    def state(self, runtime):
        return self.call("get_state", runtime=runtime)["state"]


def version(state):
    return {key: state[key] for key in ("session", "runtime", "generation", "revision")}
