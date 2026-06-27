import base64
import json
import os
import socket
import time

import companion_mcp.state as _state
from companion_mcp.state import mcp

_REMOTE_PORT = 9191
_REMOTE_PATH = "/remote/v1"

VALID_BUTTONS = {"a", "b", "x", "y", "l", "r", "lb", "rb", "select", "start", "home"}
VALID_DIRECTIONS = {"up", "down", "left", "right"}
VALID_ACTIONS = {"tap", "press", "release"}


def _get_host() -> str:
    device = _state.get_active_device()
    if not device:
        raise RuntimeError("No device configured.")
    return device["ip"]


def _ws_send(host: str, payload: dict) -> dict:
    key = base64.b64encode(b"CompanionRemoteKey").decode()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((host, _REMOTE_PORT))
        hs = (
            f"GET {_REMOTE_PATH} HTTP/1.1\r\n"
            f"Host: {host}:{_REMOTE_PORT}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(hs.encode())
        s.recv(4096)  # HTTP 101

        data = json.dumps(payload).encode()
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        n = len(data)
        frame = bytes([0x81, 0x80 | n]) + mask + masked
        s.sendall(frame)
        time.sleep(0.2)

        # Read response frame
        try:
            s.settimeout(2)
            header = s.recv(2)
            if len(header) >= 2:
                n = header[1] & 0x7F
                body = s.recv(n) if n else b""
                return json.loads(body.decode()) if body else {}
        except Exception:
            pass
        return {}
    finally:
        s.close()


@mcp.tool()
def press_button(button: str, action: str = "tap") -> dict:
    """Send a controller button press to the MiSTer via Companion Remote.

    button: a, b, x, y, l, r, select, start, home, up, down, left, right
    action: tap (default), press (hold down), release
    """
    button = button.lower().strip()
    action = action.lower().strip()

    if button not in VALID_BUTTONS and button not in VALID_DIRECTIONS:
        return {"error": f"Unknown button '{button}'. Valid: {sorted(VALID_BUTTONS | VALID_DIRECTIONS)}"}
    if action not in VALID_ACTIONS:
        return {"error": f"Unknown action '{action}'. Valid: {sorted(VALID_ACTIONS)}"}

    try:
        host = _get_host()
        is_dpad = button in VALID_DIRECTIONS
        payload = {
            "command_type": "controller",
            "control": "dpad" if is_dpad else "button",
            "name": button,
            "action": action,
        }
        result = _ws_send(host, payload)
        return {"status": "sent", "button": button, "action": action, "response": result}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def press_sequence(buttons: list[str], delay: float = 0.3) -> dict:
    """Send a sequence of button taps with a delay between each.

    buttons: list of button names e.g. ["select", "select", "start"]
    delay: seconds between presses (default 0.3)
    """
    try:
        host = _get_host()
        results = []
        for btn in buttons:
            btn = btn.lower().strip()
            is_dpad = btn in VALID_DIRECTIONS
            payload = {
                "command_type": "controller",
                "control": "dpad" if is_dpad else "button",
                "name": btn,
                "action": "tap",
            }
            _ws_send(host, payload)
            results.append(btn)
            time.sleep(delay)
        return {"status": "sent", "sequence": results}
    except Exception as exc:
        return {"error": str(exc)}
