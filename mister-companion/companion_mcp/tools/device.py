import companion_mcp.state as _state
from companion_mcp.state import mcp
from core.device_actions import get_sd_storage_info, get_now_playing


@mcp.tool()
def get_device_status() -> dict:
    """Get MiSTer device status: disk usage, uptime, hostname, kernel, now playing."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()

    disk = get_sd_storage_info(connection) or {}
    uptime = (connection.run_command("uptime -p 2>/dev/null || uptime") or "").strip()
    hostname = (connection.run_command("hostname") or "").strip()
    kernel = (connection.run_command("uname -r") or "").strip()
    now_playing = get_now_playing(connection)

    return {
        "disk": disk,
        "uptime": uptime,
        "hostname": hostname,
        "kernel": kernel,
        "now_playing": now_playing,
    }


@mcp.tool()
def reboot_device() -> dict:
    """Reboot the MiSTer. Connection will drop immediately after."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()
    connection.reboot()
    return {"status": "rebooting", "message": "MiSTer is rebooting. Reconnect in ~30 seconds."}


@mcp.tool()
def set_device_ip(ip: str) -> dict:
    """Update the stored MiSTer IP address (after DHCP reassignment) and reconnect."""
    updated = _state.update_device_ip(ip)
    if not updated:
        return {"error": "No device profile found to update."}

    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    return get_device_status()
