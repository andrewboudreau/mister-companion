import companion_mcp.state as _state
from companion_mcp.state import mcp
from core.config import load_config
from core.savemanager import (
    create_backup,
    REMOTE_SAVES_DIR,
    REMOTE_SAVESTATES_DIR,
)
from core.scripts_common import is_ftp_save_sync_service_enabled as _is_ftp_sync_enabled


@mcp.tool()
def list_saves() -> dict:
    """List save files and savestates on the MiSTer with sizes."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()
    output = connection.run_command(
        f"find {REMOTE_SAVES_DIR} {REMOTE_SAVESTATES_DIR} -type f -print0 2>/dev/null "
        f"| xargs -0 stat -c '%n %s' 2>/dev/null"
    ) or ""

    saves = []
    for line in output.splitlines():
        parts = line.strip().rsplit(" ", 1)
        if len(parts) == 2:
            saves.append({
                "path": parts[0],
                "size_bytes": int(parts[1]) if parts[1].isdigit() else 0,
            })

    return {"saves": saves, "count": len(saves)}


@mcp.tool()
def backup_saves() -> dict:
    """Pull saves and savestates from MiSTer to local backup directory."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()
    config = load_config()

    log_lines: list[str] = []

    def log(msg: str) -> None:
        log_lines.append(msg.rstrip())

    try:
        create_backup(connection, config, log_callback=log)
        return {"status": "complete", "log": "\n".join(log_lines)}
    except Exception as exc:
        return {"error": str(exc), "log": "\n".join(log_lines)}


@mcp.tool()
def get_save_sync_status() -> dict:
    """Get FTP save sync service status."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    enabled = _is_ftp_sync_enabled(_state.get_connection())
    return {"ftp_sync_enabled": enabled}
