import companion_mcp.state as _state
from companion_mcp.state import mcp
from core.mister_ini import parse_mister_ini, update_mister_ini_text

MISTER_INI_PATH = "/media/fat/MiSTer.ini"


def _read_ini_text(connection) -> str:
    return connection.run_command(f"cat {MISTER_INI_PATH} 2>/dev/null") or ""


def _write_ini_text(connection, text: str) -> None:
    sftp = connection.client.open_sftp()
    try:
        with sftp.open(MISTER_INI_PATH, "w") as f:
            f.write(text)
    finally:
        sftp.close()


@mcp.tool()
def get_mister_ini() -> dict:
    """Read and parse MiSTer.ini. Returns all settings as a flat dict plus raw text."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()
    ini_text = _read_ini_text(connection)
    settings = parse_mister_ini(ini_text)
    return {"settings": settings, "raw": ini_text}


@mcp.tool()
def set_mister_ini_value(key: str, value: str) -> dict:
    """Set a single key in the [MiSTer] section of MiSTer.ini and write back to device."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    connection = _state.get_connection()
    ini_text = _read_ini_text(connection)
    updated_text = update_mister_ini_text(ini_text, {key: value})
    _write_ini_text(connection, updated_text)
    return {"key": key, "value": value, "status": "written"}
