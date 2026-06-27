import companion_mcp.state as _state
from companion_mcp.state import mcp
from core.extras_3s_arm import get_3sx_status as _get_3sx_status
from core.extras_sonic_mania import get_sonic_mania_status as _get_sonic_mania_status
from core.extras_zaparoo_launcher import get_zaparoo_launcher_status as _get_zaparoo_launcher_status
from core.extras_ra_cores import get_ra_cores_status as _get_ra_cores_status
from core.extras_ra_cores import install_or_update_ra_cores as _install_or_update_ra_cores


def _slim(status: dict) -> dict:
    return {
        "installed": status.get("installed", False),
        "version": status.get("installed_version", ""),
        "update_available": status.get("update_available", False),
        "status": status.get("status_text", ""),
    }


@mcp.tool()
def get_extras_status() -> dict:
    """Get installation status for 3SX Arm, Sonic Mania, and Zaparoo Launcher extras."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()
    return {
        "3sx_arm": _slim(_get_3sx_status(connection)),
        "sonic_mania": _slim(_get_sonic_mania_status(connection)),
        "zaparoo_launcher": _slim(_get_zaparoo_launcher_status(connection)),
    }


@mcp.tool()
def get_ra_cores_status() -> dict:
    """Get installation and update status for all RetroAchievements (odelot) cores."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    try:
        return _get_ra_cores_status(_state.get_connection(), check_latest=True)
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def install_ra_cores() -> dict:
    """Install or update all RetroAchievements cores (odelot forks) on the MiSTer.
    Places cores in /media/fat/_RA_Cores/Cores/, creates MGL launchers, and updates MiSTer.ini."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    log_lines = []

    def log(msg: str):
        log_lines.append(msg)

    try:
        _install_or_update_ra_cores(_state.get_connection(), log)
        return {"status": "ok", "log": log_lines}
    except Exception as exc:
        return {"error": str(exc), "log": log_lines}
