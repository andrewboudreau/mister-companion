from companion_mcp.state import mcp

import companion_mcp.tools.device      # noqa: F401 - registers tools on import
import companion_mcp.tools.scripts     # noqa: F401
import companion_mcp.tools.mister_ini  # noqa: F401
import companion_mcp.tools.zapscripts  # noqa: F401
import companion_mcp.tools.saves       # noqa: F401
import companion_mcp.tools.extras      # noqa: F401
import companion_mcp.tools.ra          # noqa: F401
import companion_mcp.tools.shell       # noqa: F401
import companion_mcp.tools.files       # noqa: F401
import companion_mcp.tools.remote      # noqa: F401

if __name__ == "__main__":
    mcp.run()
