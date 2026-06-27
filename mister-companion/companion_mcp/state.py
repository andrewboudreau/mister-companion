import os
import sys

# Root = mister-companion/ — needed for both sys.path (core/) and chdir (config.json)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)
os.chdir(_project_root)  # config.py uses Path("config.json") which is relative

from mcp.server.fastmcp import FastMCP

from core.config import load_config, save_config
from core.connection import MiSTerConnection
from core.device_profiles import get_device_by_name

mcp = FastMCP("mister-companion")

_conn = MiSTerConnection()


def get_connection() -> MiSTerConnection:
    return _conn


def get_active_device() -> dict | None:
    cfg = load_config()
    last = cfg.get("last_connected")
    device = get_device_by_name(cfg, last) if last else None
    if not device:
        devices = cfg.get("devices", [])
        device = devices[0] if devices else None
    return device


def ensure_connected() -> tuple[bool, str]:
    if _conn.is_connected():
        return True, ""

    device = get_active_device()
    if not device:
        return False, "No device configured. Add a device in the companion app first."

    try:
        ok = _conn.connect(
            device["ip"],
            device["username"],
            device["password"],
            use_ssh_agent=device.get("use_ssh_agent", False),
            look_for_ssh_keys=device.get("look_for_ssh_keys", False),
        )
        if ok:
            return True, ""
        host = device.get("ip", "unknown")
        return False, f"Could not connect to MiSTer at {host} — check IP, credentials, or use set_device_ip if it changed after reboot."
    except Exception as exc:
        return False, f"Connection failed: {exc}"


def update_device_ip(new_ip: str) -> bool:
    _conn.disconnect()
    cfg = load_config()
    last = cfg.get("last_connected")
    device = get_device_by_name(cfg, last) if last else None
    if not device:
        devices = cfg.get("devices", [])
        device = devices[0] if devices else None
    if not device:
        return False
    device["ip"] = new_ip
    save_config(cfg)
    return True
