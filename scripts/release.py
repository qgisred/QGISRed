"""
release.py — QGISRed release script

Usage:
    python scripts/release.py             # asks for version manually
    python scripts/release.py --beta      # suggests patch+1  (0.17.3 → 0.17.4)
    python scripts/release.py --official  # suggests minor+1  (0.17.3 → 0.18.0)
"""

import re
import sys
import subprocess
import ftplib
import os
import configparser
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT   = SCRIPTS_DIR.parent
METADATA    = REPO_ROOT / "metadata.txt"
QGISRED_PY  = REPO_ROOT / "qgisred.py"
MAKEZIP_BAT = SCRIPTS_DIR / "MakeZip.bat"
FTP_CREDS   = SCRIPTS_DIR / ".ftp_credentials"


# ── Version helpers ───────────────────────────────────────────────────────────

def read_current_version() -> str:
    text = METADATA.read_text(encoding="utf-8")
    m = re.search(r"^version=(.+)$", text, re.MULTILINE)
    if not m:
        raise RuntimeError("version= not found in metadata.txt")
    return m.group(1).strip()


def suggest_version(current: str, mode: str) -> str:
    parts = current.split(".")
    if len(parts) != 3:
        return current
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if mode == "--beta":
        return f"{major}.{minor}.{patch + 1}"
    if mode == "--official":
        return f"{major}.{minor + 1}.0"
    return current


def dependencies_version(version: str) -> str:
    """Convert plugin version to DependenciesVersion format.

    0.17.3  →  1.0.17.3
    (strips leading '0.', prepends '1.0.')
    """
    without_leading = re.sub(r"^0\.", "", version)
    return f"1.0.{without_leading}"


# ── File update helpers ───────────────────────────────────────────────────────

def update_metadata_version(new_version: str):
    text = METADATA.read_text(encoding="utf-8")
    updated = re.sub(r"^(version=).+$", rf"\g<1>{new_version}", text, flags=re.MULTILINE)
    METADATA.write_text(updated, encoding="utf-8")
    print(f"  metadata.txt        version={new_version}")


def update_qgisred_dependencies(new_version: str):
    dep_ver = dependencies_version(new_version)
    text = QGISRED_PY.read_text(encoding="utf-8")
    updated = re.sub(
        r'(DependenciesVersion\s*=\s*")[^"]+(")',
        rf'\g<1>{dep_ver}\g<2>',
        text,
    )
    QGISRED_PY.write_text(updated, encoding="utf-8")
    print(f"  qgisred.py          DependenciesVersion = \"{dep_ver}\"")


# ── ZIP generation ────────────────────────────────────────────────────────────

def run_makezip() -> Path:
    print("\n[2/4] Generating ZIP...")
    result = subprocess.run(
        [str(MAKEZIP_BAT)],
        shell=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(f"MakeZip.bat exited with code {result.returncode}")
    # MakeZip places the file in the parent of REPO_ROOT
    version = read_current_version()
    zip_path = REPO_ROOT.parent / f"QGISRed_v{version}.zip"
    if not zip_path.exists():
        raise RuntimeError(f"Expected ZIP not found: {zip_path}")
    print(f"  ZIP created: {zip_path}")
    return zip_path


# ── FTP credentials ───────────────────────────────────────────────────────────

def load_ftp_credentials() -> dict:
    """Load FTP credentials from .ftp_credentials file or environment variables."""
    cfg = {}

    # Try file first
    if FTP_CREDS.exists():
        parser = configparser.ConfigParser()
        parser.read(str(FTP_CREDS), encoding="utf-8")
        if "ftp" in parser:
            section = parser["ftp"]
            cfg["host"]       = section.get("host", "")
            cfg["port"]       = int(section.get("port", 21))
            cfg["user"]       = section.get("user", "")
            cfg["password"]   = section.get("password", "")
            cfg["remote_dir"] = section.get("remote_dir", "/")
            cfg["tls"]        = section.getboolean("tls", fallback=False)

    # Environment variables override / fill gaps
    cfg["host"]       = os.environ.get("FTP_HOST",     cfg.get("host", ""))
    cfg["port"]       = int(os.environ.get("FTP_PORT", cfg.get("port", 21)))
    cfg["user"]       = os.environ.get("FTP_USER",     cfg.get("user", ""))
    cfg["password"]   = os.environ.get("FTP_PASS",     cfg.get("password", ""))
    cfg["remote_dir"] = os.environ.get("FTP_DIR",      cfg.get("remote_dir", "/"))
    tls_env = os.environ.get("FTP_TLS")
    if tls_env is not None:
        cfg["tls"] = tls_env.lower() in ("1", "true", "yes")
    elif "tls" not in cfg:
        cfg["tls"] = False

    # Ask interactively for missing fields
    missing = [k for k in ("host", "user", "password", "remote_dir") if not cfg.get(k)]
    if missing:
        print("\nSome FTP credentials are missing. Please enter them now:")
        if not cfg.get("host"):
            cfg["host"] = input("  FTP host: ").strip()
        if not cfg.get("user"):
            cfg["user"] = input("  FTP user: ").strip()
        if not cfg.get("password"):
            import getpass
            cfg["password"] = getpass.getpass("  FTP password: ")
        if not cfg.get("remote_dir"):
            cfg["remote_dir"] = input("  Remote directory (e.g. /releases/QGISRed): ").strip()

        save = input("\nSave credentials to scripts/.ftp_credentials? [y/N] ").strip().lower()
        if save == "y":
            _save_ftp_credentials(cfg)

    return cfg


def _save_ftp_credentials(cfg: dict):
    content = (
        "[ftp]\n"
        f"host       = {cfg['host']}\n"
        f"port       = {cfg['port']}\n"
        f"user       = {cfg['user']}\n"
        f"password   = {cfg['password']}\n"
        f"remote_dir = {cfg['remote_dir']}\n"
        f"tls        = {'true' if cfg.get('tls') else 'false'}\n"
    )
    FTP_CREDS.write_text(content, encoding="utf-8")
    print(f"  Saved to {FTP_CREDS}")


# ── FTP upload ────────────────────────────────────────────────────────────────

def upload_ftp(zip_path: Path, cfg: dict):
    print(f"\n[3/4] Uploading to FTP {cfg['host']}{cfg['remote_dir']} ...")
    ftp_class = ftplib.FTP_TLS if cfg.get("tls") else ftplib.FTP
    with ftp_class() as ftp:
        ftp.connect(cfg["host"], cfg["port"])
        ftp.login(cfg["user"], cfg["password"])
        if cfg.get("tls"):
            ftp.prot_p()
        ftp.cwd(cfg["remote_dir"])
        with open(zip_path, "rb") as f:
            ftp.storbinary(f"STOR {zip_path.name}", f)
    print(f"  Uploaded: {zip_path.name}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("", "--beta", "--official"):
        print(f"Unknown argument: {mode}")
        print("Usage: python release.py [--beta | --official]")
        sys.exit(1)

    # 1. Read & confirm version
    current = read_current_version()
    suggestion = suggest_version(current, mode)
    print(f"\nCurrent version : {current}")
    if mode:
        print(f"Suggested ({mode[2:]:8s}): {suggestion}")
    prompt = f"New version [{suggestion}]: " if mode else "New version: "
    raw = input(prompt).strip()
    new_version = raw if raw else suggestion

    if not re.fullmatch(r"\d+\.\d+\.\d+", new_version):
        print(f"Invalid version format: {new_version}  (expected X.Y.Z)")
        sys.exit(1)

    # 2. Update files
    print(f"\n[1/4] Updating version to {new_version} ...")
    update_metadata_version(new_version)
    update_qgisred_dependencies(new_version)

    # 3. Generate ZIP
    zip_path = run_makezip()

    # 4. Upload
    creds = load_ftp_credentials()
    upload_ftp(zip_path, creds)

    # 5. Cleanup
    print()
    delete = input(f"[4/4] Delete local ZIP {zip_path.name}? [y/N] ").strip().lower()
    if delete == "y":
        zip_path.unlink()
        print(f"  Deleted {zip_path.name}")

    print("\nRelease complete.")


if __name__ == "__main__":
    main()
