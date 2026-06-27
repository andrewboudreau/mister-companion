import time
import companion_mcp.state as _state
from companion_mcp.state import mcp


@mcp.tool()
def list_directory(path: str) -> dict:
    """List files and directories on the MiSTer at the given path."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    conn = _state.get_connection()
    out = conn.run_command(f"ls -1p {path!r} 2>&1") or ""
    entries = [e for e in out.splitlines() if e]
    dirs = [e.rstrip("/") for e in entries if e.endswith("/")]
    files = [e for e in entries if not e.endswith("/")]
    return {"path": path, "dirs": dirs, "files": files}


@mcp.tool()
def take_screenshot() -> dict:
    """Trigger a MiSTer screenshot, wait for it to save, and return its device path.

    The file lands in /media/fat/screenshots/<CoreName>/. Pull it to Windows via SMB:
    net use \\\\<ip>\\sdcard /user:root 1
    """
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    conn = _state.get_connection()

    core = (conn.run_command("cat /tmp/CORENAME") or "").strip()
    if not core:
        return {"error": "No active core — launch a game first."}

    # record newest file before trigger so we can detect the new one
    screenshot_dir = f"/media/fat/screenshots/{core}"
    before = set((conn.run_command(f"ls {screenshot_dir!r} 2>/dev/null") or "").splitlines())

    conn.run_command("echo screenshot > /dev/MiSTer_cmd")

    # poll up to 5s for a new file
    for _ in range(10):
        time.sleep(0.5)
        after_raw = conn.run_command(f"ls {screenshot_dir!r} 2>/dev/null") or ""
        after = set(after_raw.splitlines())
        new = after - before
        if new:
            filename = sorted(new)[-1]
            device_path = f"{screenshot_dir}/{filename}"
            return {
                "status": "captured",
                "core": core,
                "device_path": device_path,
                "smb_path": f"\\\\<ip>\\sdcard\\screenshots\\{core}\\{filename}",
                "tip": "Run grab-screenshots.ps1 or: net use \\\\<ip>\\sdcard /user:root 1 then Copy-Item",
            }

    return {"error": "Screenshot not found after 5s — core may not support screenshots."}
