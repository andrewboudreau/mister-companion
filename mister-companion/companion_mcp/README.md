# mister-companion MCP Server

A stdio MCP server that wraps the mister-companion core layer and exposes it as Claude Code tools. Claude can SSH into your MiSTer, check device state, launch games, manage RA cores, and diagnose problems — using the same logic the companion app uses, not a separate implementation.

## Setup

Register in your `.mcp.json` (alongside any existing MCP servers):

```json
"mister-companion": {
  "command": "C:\\path\\to\\python.exe",
  "args": ["-m", "companion_mcp.server"],
  "cwd": "D:\\path\\to\\mister-companion\\mister-companion",
  "env": {
    "PYTHONPATH": "D:\\path\\to\\mister-companion\\mister-companion"
  }
}
```

Reads device credentials from the existing `config.json` — no separate config needed. No other MCP server needed; `run_command` covers any ad-hoc shell access.

## Tools

**Device**
- `get_device_status` — disk usage, uptime, hostname, what's currently playing
- `reboot_device` — reboots and drops the connection
- `set_device_ip` — updates the stored IP after a DHCP reassignment

**Shell**
- `run_command` — run any shell command on the MiSTer, returns stdout

**Scripts**
- `get_scripts_status` — update_all, zaparoo, CIFS, FTP sync install state
- `run_update_all` — kicks off update_all detached via setsid, returns log path
- `get_update_all_log` — reads the log, reports whether it's still running
- `get_update_all_config` — parses downloader.ini

**MiSTer INI**
- `get_mister_ini` — full parsed MiSTer.ini
- `set_mister_ini_value(key, value)` — writes a single key to the [MiSTer] section

**ZapScripts (Zaparoo)**
- `get_zapscripts_status` — service running, media DB accessible
- `get_zap_media_stats` — game count by system
- `launch_game` — launch any game or MRA by filesystem path

**Saves**
- `list_saves` — save files and savestates with sizes
- `backup_saves` — pulls saves to local backup directory
- `get_save_sync_status` — FTP sync state

**Extras**
- `get_extras_status` — 3SX Arm, Sonic Mania, Zaparoo Launcher install state
- `get_ra_cores_status` — odelot RA core install and update status
- `install_ra_cores` — installs or updates all RetroAchievements cores from odelot's repos

**RetroAchievements** (HTTP only, no SSH dependency)
- `get_ra_user_summary` — points, rank, recent games with completion %
- `get_ra_game_progress` — full achievement list for a game, earned/unearned

## What it actually does

A few things that came up in practice:

**Check RA progress and launch with the right core**

```
"check my blazing lasers achievements"
→ 6/74 (8.1%) — areas 1-2 cleared on Normal, Homing Beam Master, stalled at area 3

"launch blazing lasers"
→ finds /media/fat/games/TGFX16/.../Blazing Lazers (USA).pce
→ checks memory: TG16 has an RA core, installs TurboGrafx16.rbf from odelot/TurboGrafx16_MiSTer
→ launches via Zaparoo
```

**Fix missing audio on CPS2**

```
"launch progrear"  →  game loads but no sound

→ diagnosed: qsound.zip missing from /media/fat/games/mame/
→ found it in local MAME set at D:\roms\Mame\mame-merged\mame-merged\qsound.zip
→ copied to MiSTer over SMB
→ relaunched with sound
```

**Install RA cores the right way**

Uses `install_or_update_ra_cores()` from the companion's core layer — cores go to `/media/fat/_RA_Cores/Cores/` with MGL launchers, version tracking, and MiSTer.ini patching. Not manual wget into the wrong folder.

## RetroAchievements credentials

RA tools (`get_ra_user_summary`, `get_ra_game_progress`) read from `config.json` under `retroachievements_username` and `retroachievements_api_key`. Set these in the companion app.

## Notes

- Device IP is DHCP. After a reboot use `set_device_ip` or the companion will reconnect on the next tool call if the IP is the same.
- RA hardcore mode: NES, SNES, Mega Drive supported as of odelot v1.2.0. TG16, PSX, GBA, N64 and others are softcore only for now.
- `launch_game` requires Zaparoo to be installed and running.
- Zaparoo `downloader.ini` section must be `[mrext/tapto]` — the project was renamed from zaparoo to tapto and the old section name causes an error on every update_all run.
- `run_update_all` uses `setsid` to detach the process from the paramiko session. `nohup` is unreliable in paramiko's non-login exec environment.
