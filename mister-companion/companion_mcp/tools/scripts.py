import configparser

import companion_mcp.state as _state
from companion_mcp.state import mcp
from core.scripts_common import get_scripts_status as _get_scripts_status

UPDATE_ALL_SCRIPT = "/media/fat/Scripts/update_all.sh"
UPDATE_ALL_LOG = "/tmp/update_all_mcp.log"
DOWNLOADER_INI_PATH = "/media/fat/downloader.ini"


@mcp.tool()
def get_scripts_status() -> dict:
    """Get installation and service status for update_all, zaparoo, CIFS, FTP save sync, auto_time, migrate_sd."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()
    status = _get_scripts_status(connection)

    return {
        "update_all": {
            "installed": status.update_all_installed,
            "initialized": status.update_all_initialized,
        },
        "zaparoo": {
            "installed": status.zaparoo_installed,
            "service_enabled": status.zaparoo_service_enabled,
        },
        "cifs_mount": {
            "installed": status.cifs_installed,
            "configured": status.cifs_configured,
        },
        "ftp_save_sync": {
            "installed": status.ftp_save_sync_installed,
            "configured": status.ftp_save_sync_configured,
            "service_enabled": status.ftp_save_sync_service_enabled,
        },
        "auto_time": {"installed": status.auto_time_installed},
        "migrate_sd": {"installed": status.migrate_sd_installed},
    }


@mcp.tool()
def run_update_all() -> dict:
    """Launch update_all in the background on the MiSTer. Poll output with get_update_all_log."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()
    # Check script exists first
    exists = connection.run_command(f"test -f {UPDATE_ALL_SCRIPT} && echo YES") or ""
    if "YES" not in exists:
        return {"error": f"update_all not installed at {UPDATE_ALL_SCRIPT}"}

    pid_str = (connection.run_command(
        f"setsid {UPDATE_ALL_SCRIPT} > {UPDATE_ALL_LOG} 2>&1 & echo $!"
    ) or "").strip()
    return {
        "status": "started",
        "pid": pid_str if pid_str.isdigit() else "unknown",
        "log_path": UPDATE_ALL_LOG,
        "message": "update_all launched in background. Poll with get_update_all_log.",
    }


@mcp.tool()
def get_update_all_log() -> dict:
    """Read the current update_all log output from the last run_update_all call."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()
    output = connection.run_command(f"cat {UPDATE_ALL_LOG} 2>/dev/null") or ""
    running = connection.run_command(
        f"pgrep -f update_all.sh > /dev/null 2>&1 && echo RUNNING || echo DONE"
    ) or ""
    return {
        "running": "RUNNING" in running,
        "log": output,
    }


@mcp.tool()
def get_update_all_config() -> dict:
    """Read the current downloader.ini configuration from the MiSTer."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()
    ini_text = connection.run_command(f"cat {DOWNLOADER_INI_PATH} 2>/dev/null") or ""

    try:
        parser = configparser.ConfigParser(strict=False)
        parser.read_string(ini_text)
    except configparser.Error:
        return {"error": "downloader.ini is missing or unparseable", "raw": ini_text}

    result: dict = {}
    for section in parser.sections():
        result[section] = dict(parser[section])

    return result
