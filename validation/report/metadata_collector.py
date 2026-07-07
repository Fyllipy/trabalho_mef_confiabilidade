import os
import sys
import platform
import subprocess
from datetime import datetime
from typing import Dict, Any

def get_git_info() -> Dict[str, str]:
    info = {"commit_hash": "N/A", "commit_hash_short": "N/A", "branch": "N/A", "status": "N/A"}
    try:
        # Check if in a git repo
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        if "true" in res.stdout.strip().lower():
            # Get full commit hash
            commit_full = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            ).stdout.strip()
            # Get short commit hash
            commit_short = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            ).stdout.strip()
            # Get branch name
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            ).stdout.strip()
            # Get status (dirty or clean)
            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            status = "Dirty" if status_res.stdout.strip() else "Clean"
            
            info.update({
                "commit_hash": commit_full,
                "commit_hash_short": commit_short,
                "branch": branch,
                "status": status
            })
    except Exception:
        pass
    return info

def get_library_versions() -> Dict[str, str]:
    libs = ["numpy", "scipy", "matplotlib", "meshio", "jinja2"]
    versions = {}
    for lib in libs:
        try:
            m = __import__(lib)
            versions[lib] = getattr(m, "__version__", "Available (Version unknown)")
        except ImportError:
            versions[lib] = "Not Installed"
    return versions

def get_cpu_info() -> str:
    try:
        if platform.system() == "Windows":
            out = subprocess.run(
                ["wmic", "cpu", "get", "name"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            lines = out.stdout.strip().split("\n")
            if len(lines) > 1:
                return lines[1].strip()
        elif platform.system() == "Darwin":
            out = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return out.stdout.strip()
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
    except Exception:
        pass
    return platform.processor() or "Unknown CPU"

def get_ram_info() -> str:
    try:
        if platform.system() == "Windows":
            out = subprocess.run(
                ["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            lines = out.stdout.strip().split("\n")
            if len(lines) > 1:
                bytes_ram = int(lines[1].strip())
                return f"{bytes_ram / (1024**3):.2f} GB"
        # Fallback to psutil if available
        import psutil
        return f"{psutil.virtual_memory().total / (1024**3):.2f} GB"
    except Exception:
        pass
    return "Unknown RAM"

def collect_metadata(operator_name: str = "Developer") -> Dict[str, Any]:
    git_info = get_git_info()
    lib_versions = get_library_versions()
    
    metadata = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "operator": operator_name,
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python_version": sys.version.split()[0],
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "git_commit_hash": git_info["commit_hash"],
        "git_commit_hash_short": git_info["commit_hash_short"],
        "git_branch": git_info["branch"],
        "git_status": git_info["status"],
        "library_versions": lib_versions
    }
    return metadata
