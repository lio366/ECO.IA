"""Cleaner - automatic removal of logs and temporary files."""

import glob
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class Cleaner:
    """Automatically cleans up old logs, temp files, and Docker artefacts."""

    def __init__(
        self,
        log_dirs: Optional[List[str]] = None,
        temp_dirs: Optional[List[str]] = None,
        max_log_age_days: int = 7,
        max_log_size_mb: float = 100.0,
    ) -> None:
        self.log_dirs = log_dirs or ["/var/log/eco-ia", "/opt/eco-ia/logs"]
        self.temp_dirs = temp_dirs or []  # caller must supply safe temp dirs explicitly
        self.max_log_age_days = max_log_age_days
        self.max_log_size_mb = max_log_size_mb
        self._cleanup_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Clean operations
    # ------------------------------------------------------------------

    def clean_old_logs(self) -> Dict[str, Any]:
        """Remove log files older than *max_log_age_days*."""
        cutoff = datetime.utcnow() - timedelta(days=self.max_log_age_days)
        removed = []
        freed_bytes = 0

        for log_dir in self.log_dirs:
            if not Path(log_dir).exists():
                continue
            for file_path in Path(log_dir).rglob("*.log"):
                try:
                    mtime = datetime.utcfromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        freed_bytes += size
                        removed.append(str(file_path))
                except OSError as exc:
                    logger.warning("Could not remove '%s': %s", file_path, exc)

        result: Dict[str, Any] = {
            "action": "clean_old_logs",
            "removed_count": len(removed),
            "freed_mb": round(freed_bytes / 1024**2, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._cleanup_log.append(result)
        logger.info("Cleaned %d old log files (%.2f MB freed).", len(removed), result["freed_mb"])
        return result

    def clean_temp_files(self) -> Dict[str, Any]:
        """Remove temporary directories."""
        removed = []
        freed_bytes = 0

        for tmp_dir in self.temp_dirs:
            tmp_path = Path(tmp_dir)
            if not tmp_path.exists():
                continue
            try:
                size = sum(f.stat().st_size for f in tmp_path.rglob("*") if f.is_file())
                shutil.rmtree(tmp_path, ignore_errors=True)
                freed_bytes += size
                removed.append(str(tmp_path))
            except OSError as exc:
                logger.warning("Could not clean '%s': %s", tmp_path, exc)

        result: Dict[str, Any] = {
            "action": "clean_temp_files",
            "cleaned_dirs": removed,
            "freed_mb": round(freed_bytes / 1024**2, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._cleanup_log.append(result)
        logger.info("Cleaned temp files (%.2f MB freed).", result["freed_mb"])
        return result

    def clean_docker_artefacts(self) -> Dict[str, Any]:
        """Remove unused Docker images, containers, and volumes."""
        import subprocess

        commands = [
            ["docker", "container", "prune", "-f"],
            ["docker", "image", "prune", "-f"],
            ["docker", "volume", "prune", "-f"],
            ["docker", "network", "prune", "-f"],
        ]
        results = []
        for cmd in commands:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
            results.append({
                "cmd": " ".join(cmd),
                "success": proc.returncode == 0,
                "output": proc.stdout[-200:] if proc.stdout else "",
            })

        result: Dict[str, Any] = {
            "action": "clean_docker_artefacts",
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._cleanup_log.append(result)
        return result

    def run_all(self) -> List[Dict[str, Any]]:
        """Run all cleanup tasks."""
        return [
            self.clean_old_logs(),
            self.clean_temp_files(),
            self.clean_docker_artefacts(),
        ]

    def get_cleanup_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._cleanup_log[-limit:]
