import companion_mcp.state as _state
from companion_mcp.state import mcp


@mcp.tool()
def run_command(command: str) -> dict:
    """Run an arbitrary shell command on the MiSTer. Returns stdout output."""
    ok, err = _state.ensure_connected()
    if not ok:
        return {"error": err}

    output = _state.get_connection().run_command(command) or ""
    return {"output": output}
