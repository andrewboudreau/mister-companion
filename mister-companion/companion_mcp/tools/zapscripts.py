import companion_mcp.state as _state
from companion_mcp.state import mcp
from core.zapscripts import (
    get_zapscripts_state as _get_zapscripts_state,
    get_media_database_status as _get_media_database_status,
    launch_media as _launch_media,
    run_zaparoo_command as _run_zaparoo_command,
)


@mcp.tool()
def get_zapscripts_status() -> dict:
    """Get Zaparoo installation and service status."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}
    try:
        return _get_zapscripts_state(_state.get_connection())
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def get_zap_media_stats() -> dict:
    """Get media database stats from Zaparoo: total indexed games, indexing status."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}
    try:
        return _get_media_database_status(_state.get_connection())
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def launch_game(path: str, use_ra_core: bool = False) -> dict:
    """Launch a game on the MiSTer via Zaparoo. path is a MiSTer filesystem path.
    Set use_ra_core=True to launch using the RetroAchievements-enabled core for the system."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}
    try:
        if use_ra_core:
            return _launch_with_ra_core(_state.get_connection(), path)
        _launch_media(_state.get_connection(), {"path": path})
        return {"status": "launched", "path": path}
    except Exception as exc:
        return {"error": str(exc)}


def _launch_with_ra_core(connection, path: str) -> dict:
    parts = path.replace("\\", "/").split("/")
    try:
        games_idx = parts.index("games")
        system = parts[games_idx + 1]
    except (ValueError, IndexError):
        return {"error": f"Could not determine system from path: {path}"}

    ra_rbf = f"_RA_Cores/Cores/{system}"
    ra_rbf_full = f"/media/fat/{ra_rbf}.rbf"

    check = connection.run_command(f"test -f {ra_rbf_full} && echo EXISTS")
    if "EXISTS" not in (check or ""):
        return {"error": f"No RA core found for system '{system}' at {ra_rbf_full}"}

    mgl = (
        "<mistergamedescription>\n"
        f"    <rbf>{ra_rbf}</rbf>\n"
        f'    <file delay="1" type="f" index="0" path="{path}"/>\n'
        "</mistergamedescription>\n"
    )

    mgl_path = "/tmp/ra_launch.mgl"
    sftp = connection.client.open_sftp()
    try:
        with sftp.open(mgl_path, "w") as f:
            f.write(mgl)
    finally:
        sftp.close()

    _run_zaparoo_command(connection, f"**launch:{mgl_path}")
    return {"status": "launched", "path": path, "ra_core": ra_rbf, "via_mgl": mgl_path}
