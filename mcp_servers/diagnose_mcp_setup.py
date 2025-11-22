#!/usr/bin/env python3
"""
Diagnose MCP setup for Script Ohio 2.0 / Claude Desktop.

Features:
- Load Claude Desktop config (~/.claude/claude_desktop_config.json)
- Load project MCP config (mcp_servers/config/claude_desktop_config.json)
- Compare and list all MCP servers, highlight discrepancies
- Verify prerequisites (node, npm, npx, uvx, python)
- Test each MCP server:
  - Custom servers (agent_orchestrator, model_execution)
  - Standard servers (npx/uvx-based)
  - SQLite DB path, PostgreSQL env, filesystem root, GitHub token
- Output:
  - Colorized console summary with emojis
  - JSON report in mcp_servers/logs/
  - Markdown report in mcp_servers/logs/

Usage:
    python mcp_servers/diagnose_mcp_setup.py
    python mcp_servers/diagnose_mcp_setup.py --json-only
    python mcp_servers/diagnose_mcp_setup.py --verbose
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- Optional color support (colorama-like) ---------------------------------

try:
    from colorama import Fore, Style, init as colorama_init

    colorama_init()
except ImportError:  # graceful fallback if colorama not installed
    class Dummy:
        RESET_ALL = ""
        RESET = ""
        BRIGHT = ""
        GREEN = ""
        RED = ""
        YELLOW = ""
        CYAN = ""
        MAGENTA = ""

    class DummyFore(Dummy):
        pass

    class DummyStyle(Dummy):
        pass

    Fore = DummyFore()
    Style = DummyStyle()


# --- Constants / Known servers ----------------------------------------------

DESKTOP_CONFIG_DEFAULT = Path.home() / ".claude" / "claude_desktop_config.json"
PROJECT_CONFIG_RELATIVE = Path("config") / "claude_desktop_config.json"

CUSTOM_SERVER_HINT_PATHS = {
    "agent_orchestrator": Path("mcp_servers/agents/agent_mcp_bridge.py"),
    "model_execution": Path("mcp_servers/agents/model_mcp_server.py"),
}

# Setup / troubleshooting hints for specific servers
MCP_HINTS = {
    "agent_orchestrator": {
        "description": "Custom Python MCP exposing the Script Ohio 2.0 agent system.",
        "install": [
            "Ensure virtualenv is activated (if you use one).",
            "Install project dependencies (e.g. `pip install -r requirements.txt`).",
        ],
        "env": [],
        "troubleshooting": [
            "Verify mcp_servers/agents/agent_mcp_bridge.py exists.",
            "Run `python mcp_servers/agents/agent_mcp_bridge.py --help` manually to see errors.",
        ],
    },
    "model_execution": {
        "description": "Custom Python MCP providing access to ML models.",
        "install": [
            "Ensure model dependencies are installed (Ridge, XGBoost, FastAI, etc.).",
            "Ensure model files/checkpoints exist at expected paths.",
        ],
        "env": [],
        "troubleshooting": [
            "Verify mcp_servers/agents/model_mcp_server.py exists.",
            "Run `python mcp_servers/agents/model_mcp_server.py --help` manually.",
        ],
    },
    "database_sqlite": {
        "description": "SQLite MCP for local football_analysis.db operations.",
        "install": [
            "Ensure `uvx` is installed and on PATH (e.g. `pip install uv` or follow uv docs).",
            "Ensure `mcp-server-sqlite` is available via uvx (`uvx mcp-server-sqlite --help`).",
        ],
        "env": [],
        "troubleshooting": [
            "Check that `data/football_analysis.db` exists relative to project root.",
            "Ensure the MCP config's DB path matches the actual path.",
        ],
    },
    "database_postgres": {
        "description": "PostgreSQL MCP for production database operations.",
        "install": [
            "Install PostgreSQL client binaries (e.g. `psql`).",
            "Ensure PostgreSQL server is running and database `college_football` exists.",
            "Ensure `uvx` and `@modelcontextprotocol/server-postgres` are available.",
        ],
        "env": [
            "POSTGRES_PASSWORD (required)",
            "POSTGRES_USER (optional, defaults may apply)",
            "POSTGRES_DB (e.g. college_football)",
            "POSTGRES_HOST (e.g. localhost)",
        ],
        "troubleshooting": [
            "Run `pg_isready` to confirm the DB is reachable.",
            "Try connecting manually with `psql` using the same credentials.",
        ],
    },
    "filesystem": {
        "description": "Filesystem MCP for project-level file access.",
        "install": [
            "Install `@modelcontextprotocol/server-filesystem` via npm if needed.",
        ],
        "env": [],
        "troubleshooting": [
            "Verify the configured root directory exists and is readable/writable.",
        ],
    },
    "memory": {
        "description": "Memory MCP for persistent context storage.",
        "install": [
            "Install `@modelcontextprotocol/server-memory` via npm if needed.",
        ],
        "env": [],
        "troubleshooting": [
            "Check MCP logs for runtime errors when starting memory server.",
        ],
    },
    "csv_editor": {
        "description": "CSV Editor MCP for CSV operations.",
        "install": [
            "Install `@modelcontextprotocol/server-csv-editor` via npm.",
        ],
        "env": [],
        "troubleshooting": [
            "Run `npx @modelcontextprotocol/server-csv-editor --help` manually.",
        ],
    },
    "web_fetch": {
        "description": "Fetch MCP for HTTP/HTTPS web data retrieval.",
        "install": [
            "Install `@modelcontextprotocol/server-fetch` via npm.",
        ],
        "env": [],
        "troubleshooting": [
            "Ensure network connectivity.",
            "Check for proxy/firewall issues if requests fail.",
        ],
    },
    "github": {
        "description": "GitHub MCP for repo access and version control.",
        "install": [
            "Install `@modelcontextprotocol/server-github` via npm.",
        ],
        "env": [
            "GITHUB_TOKEN (required) with appropriate repo access.",
        ],
        "troubleshooting": [
            "Verify GITHUB_TOKEN is set and has correct scopes.",
            "Try a simple GitHub API call using that token to confirm access.",
        ],
    },
    "visualization_echarts": {
        "description": "ECharts MCP for interactive visualizations.",
        "install": [
            "Install `@modelcontextprotocol/server-echarts` via npm.",
        ],
        "env": [],
        "troubleshooting": [
            "Run `npx @modelcontextprotocol/server-echarts --help` to confirm installation.",
        ],
    },
    "datawrapper": {
        "description": "Datawrapper MCP for publication-quality charts.",
        "install": [
            "Ensure `mcp-server-datawrapper` is available via uvx.",
        ],
        "env": [
            "Any Datawrapper-specific API credentials, if used.",
        ],
        "troubleshooting": [
            "Run `uvx mcp-server-datawrapper --help` manually.",
        ],
    },
    "quickchart": {
        "description": "QuickChart MCP for simple chart generation.",
        "install": [
            "Install `@modelcontextprotocol/server-quickchart` via npm.",
        ],
        "env": [],
        "troubleshooting": [
            "Check network access to QuickChart's API endpoints.",
        ],
    },
}

# --- Data structures ---------------------------------------------------------

@dataclass
class MCPServerConfigOrigin:
    from_desktop: bool = False
    from_project: bool = False


@dataclass
class MCPServerResult:
    name: str
    status: str  # WORKING / NEEDS_SETUP / NOT_INSTALLED / ERROR
    category: str  # custom / standard / unknown
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    origins: MCPServerConfigOrigin = field(default_factory=MCPServerConfigOrigin)
    issues: List[str] = field(default_factory=list)
    setup_instructions: List[str] = field(default_factory=list)
    env_warnings: List[str] = field(default_factory=list)
    extra_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosticContext:
    desktop_config_path: Optional[Path]
    project_config_path: Optional[Path]
    desktop_servers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    project_servers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    prereqs: Dict[str, bool] = field(default_factory=dict)


# --- Utility functions -------------------------------------------------------

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"{Fore.RED}Error parsing JSON at {path}: {e}{Style.RESET_ALL}", file=sys.stderr)
        return None


def extract_mcp_servers(config: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not config:
        return {}
    # Claude Desktop uses "mcpServers" key
    servers = config.get("mcpServers") or config.get("mcp_servers")
    if isinstance(servers, dict):
        return servers
    return {}


def check_executable(name: str) -> bool:
    return shutil.which(name) is not None


def check_prerequisites() -> Dict[str, bool]:
    tools = ["node", "npm", "npx", "uvx", "python", "python3", "pg_isready", "psql"]
    return {tool: check_executable(tool) for tool in tools}


def classify_category(server_name: str) -> str:
    if server_name in CUSTOM_SERVER_HINT_PATHS:
        return "custom"
    # crude heuristic: many standard servers are these
    return "standard"


def get_project_root() -> Path:
    # Assume this script is in mcp_servers/
    return Path(__file__).resolve().parent.parent


def join_args(args: List[str]) -> str:
    return " ".join(args) if args else ""


def safe_run_subprocess(
    cmd: List[str],
    timeout: float = 4.0,
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Optional[int], str]:
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd) if cwd else None,
            env=env,
        )
    except FileNotFoundError as e:
        return False, None, f"FileNotFoundError: {e}"
    except Exception as e:
        return False, None, f"Exception starting process: {e}"

    try:
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Long-running server: treat as "started ok", kill it
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
            return True, None, ""
        else:
            # Process exited within timeout
            code = proc.returncode
            output = (stdout + stderr).decode("utf-8", errors="ignore")
            # If exit code 0, assume OK (e.g., --help or quick start-stop)
            return code == 0, code, output
    except Exception as e:
        proc.kill()
        return False, None, f"Exception during run: {e}"


# --- Specialized checks ------------------------------------------------------

def parse_sqlite_db_path(args: List[str], project_root: Path) -> Optional[Path]:
    if not args:
        return None
    for i, a in enumerate(args):
        if a in ("--db-path", "--db", "-d") and i + 1 < len(args):
            db_arg = args[i + 1]
            db_path = Path(db_arg)
            if not db_path.is_absolute():
                db_path = project_root / db_path
            return db_path
    return None


def check_sqlite_db(args: List[str], project_root: Path) -> Tuple[bool, Optional[str]]:
    db_path = parse_sqlite_db_path(args, project_root)
    if db_path is None:
        return False, "Could not infer SQLite DB path from MCP args."
    if not db_path.exists():
        return False, f"SQLite database file not found at {db_path}"
    return True, None


def check_postgres_env() -> Tuple[bool, List[str]]:
    missing = []
    if not os.environ.get("POSTGRES_PASSWORD"):
        missing.append("POSTGRES_PASSWORD")
    # Others are optional but good to check
    for var in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_HOST"):
        if not os.environ.get(var):
            missing.append(var + " (optional but recommended)")
    return len(missing) == 0, missing


def check_postgres_connectivity(prereqs: Dict[str, bool]) -> Tuple[bool, Optional[str]]:
    if not prereqs.get("pg_isready"):
        return False, "pg_isready not found; cannot test PostgreSQL connectivity."
    # Use environment variables if present; pg_isready will use defaults otherwise
    cmd = ["pg_isready"]
    ok, code, output = safe_run_subprocess(cmd, timeout=4.0)
    if not ok:
        return False, f"pg_isready failed (exit={code}): {output[:400]}"
    if "accepting connections" not in output:
        return False, f"pg_isready output does not indicate accepting connections: {output[:400]}"
    return True, None


def check_filesystem_root(env: Dict[str, Any], args: List[str], project_root: Path) -> Tuple[bool, Optional[str]]:
    """
    Try to infer filesystem root path from env or args and check it exists.
    This is heuristic and may need tuning based on your config.
    """
    # Common patterns: env variables or args containing a root path
    candidate_paths: List[Path] = []

    # Look into env-like dict for paths
    if isinstance(env, dict):
        for key, value in env.items():
            if isinstance(value, str) and ("Script_Ohio" in value or "root" in key.lower()):
                p = Path(value)
                if not p.is_absolute():
                    p = project_root / p
                candidate_paths.append(p)

    # Also check args for suspicious-looking paths
    for a in args:
        if "/" in a or "\\" in a:
            p = Path(a)
            if not p.is_absolute():
                p = project_root / p
            candidate_paths.append(p)

    # Deduplicate
    seen = set()
    unique_candidates = []
    for p in candidate_paths:
        if str(p) not in seen:
            seen.add(str(p))
            unique_candidates.append(p)

    for p in unique_candidates:
        if p.exists() and p.is_dir():
            return True, None

    if unique_candidates:
        return False, f"Configured filesystem root(s) do not exist: {', '.join(str(p) for p in unique_candidates)}"
    else:
        return False, "Could not infer filesystem root path from config."


def check_github_token() -> Tuple[bool, Optional[str]]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return False, "GITHUB_TOKEN environment variable is not set."
    if len(token.strip()) < 20:
        return False, "GITHUB_TOKEN appears suspiciously short."
    return True, None


def check_custom_python_server(server_name: str, project_root: Path) -> Tuple[bool, List[str]]:
    """
    Custom Python server check:
    - Verify script path exists.
    - Try running `python script.py --help` with short timeout.
    """
    issues: List[str] = []
    script_rel = CUSTOM_SERVER_HINT_PATHS.get(server_name)
    if not script_rel:
        return False, [f"No known script path mapping for custom server '{server_name}'."]
    script_path = project_root / script_rel

    if not script_path.exists():
        issues.append(f"Expected script not found at: {script_path}")
        return False, issues

    # Use python or python3
    python_cmd = "python3" if check_executable("python3") else "python"
    cmd = [python_cmd, str(script_path), "--help"]
    ok, code, output = safe_run_subprocess(cmd, timeout=4.0, cwd=project_root)
    if not ok:
        issues.append(
            f"Failed to run `{python_cmd} {script_rel} --help` (exit={code}). "
            f"Output (truncated): {output[:400]}"
        )
        return False, issues

    return True, issues


def test_standard_mcp_server(
    name: str,
    cfg: Dict[str, Any],
    project_root: Path,
    prereqs: Dict[str, bool],
) -> MCPServerResult:
    command = cfg.get("command")
    args = cfg.get("args", [])
    env_cfg = cfg.get("env", {}) or {}
    env = os.environ.copy()
    if isinstance(env_cfg, dict):
        env.update({str(k): str(v) for k, v in env_cfg.items()})

    result = MCPServerResult(
        name=name,
        status="WORKING",
        category="standard",
        command=command,
        args=args,
    )

    if not command:
        result.status = "ERROR"
        result.issues.append("No 'command' field defined in MCP config.")
        return result

    # Check base command availability
    base_cmd = command
    if not check_executable(base_cmd) and not Path(base_cmd).is_file():
        result.status = "NOT_INSTALLED"
        result.issues.append(f"Command '{base_cmd}' not found on PATH or as a file.")
        return result

    # Special-case checks by server name
    if name == "database_sqlite":
        ok, msg = check_sqlite_db(args, project_root)
        if not ok:
            result.status = "NEEDS_SETUP"
            result.issues.append(msg or "SQLite DB check failed.")
    elif name == "database_postgres":
        env_ok, missing_env = check_postgres_env()
        if not env_ok:
            result.status = "NEEDS_SETUP"
            result.env_warnings.extend(missing_env)
            result.issues.append("PostgreSQL env variables missing or incomplete.")
        else:
            ok, msg = check_postgres_connectivity(prereqs)
            if not ok:
                result.status = "NEEDS_SETUP"
                result.issues.append(msg or "PostgreSQL connectivity check failed.")
    elif name == "filesystem":
        env_cfg_dict = cfg.get("env", {}) or {}
        ok, msg = check_filesystem_root(env_cfg_dict, args, project_root)
        if not ok:
            result.status = "NEEDS_SETUP"
            result.issues.append(msg or "Filesystem root check failed.")
    elif name == "github":
        ok, msg = check_github_token()
        if not ok:
            result.status = "NEEDS_SETUP"
            if msg:
                result.env_warnings.append(msg)

    # Try launching the server quickly as a generic sanity check
    ok, code, output = safe_run_subprocess([command] + args, timeout=4.0, cwd=project_root, env=env)
    if not ok:
        # If we had already marked NEEDS_SETUP, keep it; otherwise, mark as ERROR
        if result.status == "WORKING":
            result.status = "ERROR"
        truncated = (output or "")[:400]
        result.issues.append(f"Launch test failed (exit={code}). Output (truncated): {truncated}")

    # Attach generic hints if available
    hint = MCP_HINTS.get(name)
    if hint:
        result.extra_info["description"] = hint.get("description")
        result.setup_instructions.extend(hint.get("install", []))
        if hint.get("env"):
            result.env_warnings.extend(hint["env"])
        result.extra_info["troubleshooting"] = hint.get("troubleshooting", [])

    # Deduplicate text lists
    result.issues = sorted(set(result.issues))
    result.env_warnings = sorted(set(result.env_warnings))
    result.setup_instructions = sorted(set(result.setup_instructions))

    return result


def test_custom_mcp_server(
    name: str,
    cfg: Dict[str, Any],
    project_root: Path,
) -> MCPServerResult:
    command = cfg.get("command")
    args = cfg.get("args", [])
    env_cfg = cfg.get("env", {}) or {}
    env = os.environ.copy()
    if isinstance(env_cfg, dict):
        env.update({str(k): str(v) for k, v in env_cfg.items()})

    result = MCPServerResult(
        name=name,
        status="WORKING",
        category="custom",
        command=command,
        args=args,
    )

    # Check script-level status
    ok_script, script_issues = check_custom_python_server(name, project_root)
    if not ok_script:
        result.status = "NEEDS_SETUP"
        result.issues.extend(script_issues)

    # Also test the configured command if present
    if command:
        # If the command isn't python itself, still try to run it
        ok, code, output = safe_run_subprocess([command] + args, timeout=4.0, cwd=project_root, env=env)
        if not ok:
            result.status = "NEEDS_SETUP"
            truncated = (output or "")[:400]
            result.issues.append(
                f"Configured MCP command `{command} {join_args(args)}` failed (exit={code}). "
                f"Output (truncated): {truncated}"
            )
    else:
        result.status = "ERROR"
        result.issues.append("No 'command' field defined for custom MCP server.")

    # Attach hints
    hint = MCP_HINTS.get(name)
    if hint:
        result.extra_info["description"] = hint.get("description")
        result.setup_instructions.extend(hint.get("install", []))
        if hint.get("env"):
            result.env_warnings.extend(hint["env"])
        result.extra_info["troubleshooting"] = hint.get("troubleshooting", [])

    # Deduplicate text lists
    result.issues = sorted(set(result.issues))
    result.env_warnings = sorted(set(result.env_warnings))
    result.setup_instructions = sorted(set(result.setup_instructions))

    return result


# --- Config discovery / comparison -------------------------------------------

def load_configs(project_root: Path) -> DiagnosticContext:
    desktop_path = DESKTOP_CONFIG_DEFAULT
    project_path = project_root / PROJECT_CONFIG_RELATIVE

    desktop_config = load_json(desktop_path)
    project_config = load_json(project_path)

    desktop_servers = extract_mcp_servers(desktop_config)
    project_servers = extract_mcp_servers(project_config)

    return DiagnosticContext(
        desktop_config_path=desktop_path if desktop_config else None,
        project_config_path=project_path if project_config else None,
        desktop_servers=desktop_servers,
        project_servers=project_servers,
        prereqs=check_prerequisites(),
    )


def compute_server_origins(ctx: DiagnosticContext) -> Dict[str, MCPServerConfigOrigin]:
    all_names = set(ctx.desktop_servers.keys()) | set(ctx.project_servers.keys())
    origins: Dict[str, MCPServerConfigOrigin] = {}
    for name in sorted(all_names):
        origins[name] = MCPServerConfigOrigin(
            from_desktop=name in ctx.desktop_servers,
            from_project=name in ctx.project_servers,
        )
    return origins


# --- Reporting ---------------------------------------------------------------

def status_emoji(status: str) -> str:
    if status == "WORKING":
        return "✅"
    if status == "NEEDS_SETUP":
        return "⚠️"
    if status == "NOT_INSTALLED":
        return "❌"
    return "🛑"


def status_color(status: str) -> str:
    if status == "WORKING":
        return Fore.GREEN
    if status == "NEEDS_SETUP":
        return Fore.YELLOW
    if status == "NOT_INSTALLED":
        return Fore.RED
    return Fore.MAGENTA


def print_console_summary(results: List[MCPServerResult], ctx: DiagnosticContext, verbose: bool = False) -> None:
    print()
    print(f"{Style.BRIGHT}=== MCP Diagnostic Summary ==={Style.RESET_ALL}")

    # Config info
    print("\nConfig files:")
    if ctx.desktop_config_path:
        print(f"  Desktop config: {ctx.desktop_config_path}")
    else:
        print(f"  Desktop config: {Fore.RED}NOT FOUND{Style.RESET_ALL}")
    if ctx.project_config_path:
        print(f"  Project config: {ctx.project_config_path}")
    else:
        print(f"  Project config: {Fore.YELLOW}NOT FOUND{Style.RESET_ALL}")

    # Prereqs
    print("\nPrerequisite tools:")
    for tool, ok in sorted(ctx.prereqs.items()):
        col = Fore.GREEN if ok else Fore.RED
        mark = "✓" if ok else "✗"
        print(f"  {tool:<10} {col}{mark}{Style.RESET_ALL}")

    # Per-server
    print(f"\n{Style.BRIGHT}MCP servers:{Style.RESET_ALL}")
    for r in results:
        col = status_color(r.status)
        emj = status_emoji(r.status)
        loc = []
        if r.origins.from_desktop:
            loc.append("desktop")
        if r.origins.from_project:
            loc.append("project")
        loc_str = ", ".join(loc) if loc else "unknown source"

        print(f"\n  {emj} {col}{r.name}{Style.RESET_ALL} [{r.status}] ({loc_str})")
        print(f"     Category: {r.category}")
        if r.command:
            print(f"     Command: {r.command} {join_args(r.args)}")
        if r.extra_info.get("description"):
            print(f"     Desc: {r.extra_info['description']}")

        if verbose:
            if r.issues:
                print(f"     Issues:")
                for issue in r.issues:
                    print(f"       - {issue}")
            if r.env_warnings:
                print(f"     Env / config:")
                for w in r.env_warnings:
                    print(f"       - {w}")
            if r.setup_instructions:
                print(f"     Setup instructions:")
                for s in r.setup_instructions:
                    print(f"       - {s}")
        else:
            if r.status != "WORKING":
                if r.issues:
                    print(f"     Top issue: {r.issues[0]}")

    # Summary counts
    print("\nSummary counts:")
    counts = {"WORKING": 0, "NEEDS_SETUP": 0, "NOT_INSTALLED": 0, "ERROR": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    for st, n in counts.items():
        col = status_color(st)
        emj = status_emoji(st)
        print(f"  {emj} {col}{st:<13}{Style.RESET_ALL}: {n}")


def ensure_logs_dir(project_root: Path) -> Path:
    logs_dir = project_root / "mcp_servers" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def generate_reports(results: List[MCPServerResult], ctx: DiagnosticContext, project_root: Path) -> Tuple[Path, Path]:
    logs_dir = ensure_logs_dir(project_root)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = logs_dir / f"mcp_diagnostic_{timestamp}.json"
    md_path = logs_dir / f"mcp_diagnostic_{timestamp}.md"

    # JSON report
    report = {
        "timestamp": timestamp,
        "desktop_config_path": str(ctx.desktop_config_path) if ctx.desktop_config_path else None,
        "project_config_path": str(ctx.project_config_path) if ctx.project_config_path else None,
        "prereqs": ctx.prereqs,
        "servers": [asdict(r) for r in results],
    }
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Markdown report
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# MCP Diagnostic Report\n\n")
        f.write(f"- Generated: `{timestamp}`\n")
        if ctx.desktop_config_path:
            f.write(f"- Desktop config: `{ctx.desktop_config_path}`\n")
        if ctx.project_config_path:
            f.write(f"- Project config: `{ctx.project_config_path}`\n")
        f.write("\n## Prerequisites\n\n")
        for tool, ok in sorted(ctx.prereqs.items()):
            mark = "✅" if ok else "❌"
            f.write(f"- {mark} `{tool}`\n")

        f.write("\n## MCP Servers\n")
        for r in results:
            emj = status_emoji(r.status)
            f.write(f"\n### {emj} {r.name} — `{r.status}`\n\n")
            f.write(f"- Category: `{r.category}`\n")
            loc = []
            if r.origins.from_desktop:
                loc.append("desktop config")
            if r.origins.from_project:
                loc.append("project config")
            loc_str = ", ".join(loc) if loc else "unknown source"
            f.write(f"- Defined in: {loc_str}\n")
            if r.command:
                f.write(f"- Command: `{r.command} {join_args(r.args)}`\n")
            if r.extra_info.get("description"):
                f.write(f"- Description: {r.extra_info['description']}\n")
            if r.issues:
                f.write("\n**Issues:**\n")
                for issue in r.issues:
                    f.write(f"- {issue}\n")
            if r.env_warnings:
                f.write("\n**Env / Config Notes:**\n")
                for ew in r.env_warnings:
                    f.write(f"- {ew}\n")
            if r.setup_instructions:
                f.write("\n**Suggested Setup Steps:**\n")
                for si in r.setup_instructions:
                    f.write(f"- {si}\n")
            if r.extra_info.get("troubleshooting"):
                f.write("\n**Troubleshooting Tips:**\n")
                for tip in r.extra_info["troubleshooting"]:
                    f.write(f"- {tip}\n")

    return json_path, md_path


# --- Main orchestration ------------------------------------------------------

def diagnose_all(ctx: DiagnosticContext, project_root: Path) -> List[MCPServerResult]:
    origins = compute_server_origins(ctx)
    results: List[MCPServerResult] = []

    for name, origin in origins.items():
        # Prefer desktop config for command/args; fall back to project
        cfg = ctx.desktop_servers.get(name) or ctx.project_servers.get(name) or {}
        category = classify_category(name)

        if category == "custom":
            res = test_custom_mcp_server(name, cfg, project_root)
        else:
            res = test_standard_mcp_server(name, cfg, project_root, ctx.prereqs)

        res.origins = origin
        results.append(res)

    return results


def main():
    parser = argparse.ArgumentParser(description="Diagnose MCP servers for Claude Desktop / Script Ohio 2.0.")
    parser.add_argument("--json-only", action="store_true", help="Only print JSON to stdout (no color summary).")
    parser.add_argument("--verbose", action="store_true", help="Show detailed issues and instructions in console.")
    args = parser.parse_args()

    project_root = get_project_root()
    ctx = load_configs(project_root)
    results = diagnose_all(ctx, project_root)

    # Always generate log files
    json_path, md_path = generate_reports(results, ctx, project_root)

    if args.json_only:
        # Print the same JSON we wrote to file
        with json_path.open("r", encoding="utf-8") as f:
            sys.stdout.write(f.read())
            sys.stdout.write("\n")
        return

    # Human-friendly console summary
    print_console_summary(results, ctx, verbose=args.verbose)
    print(
        f"\nReports written to:\n"
        f"  JSON: {json_path}\n"
        f"  Markdown: {md_path}\n"
    )


if __name__ == "__main__":
    main()

