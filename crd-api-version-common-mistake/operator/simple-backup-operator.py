#!/usr/bin/env python3
"""
simple-backup-operator.py — A minimal Kubernetes operator for Backup CRDs.

Watches for Backup resources (kubedojo.io/v1) and processes them.
Run inside the cluster (as a Deployment) or locally with kubectl proxy.

Usage:
  # Local (with kubectl proxy running)
  python3 simple-backup-operator.py

  # As a Deployment (runs in-cluster with ServiceAccount)
  kubectl apply -f deploy/
"""

import os
import sys
import json
import time
import logging
import subprocess
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("backup-operator")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = os.environ.get("WATCH_NAMESPACE", "default")
GROUP = "kubedojo.io"
VERSION = "v1"
PLURAL = "backups"
# When running in-cluster, use the internal API via kubectl proxy sidecar.
# When running locally, start kubectl proxy first.
API_BASE = os.environ.get("API_BASE", "http://localhost:8001")
API_URL = (
    f"{API_BASE}/apis/{GROUP}/{VERSION}"
    f"/namespaces/{NAMESPACE}/{PLURAL}"
)
RESOURCE_VERSION = "0"   # tracks last seen event for watch resumption


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def kube_api(method, url, body=None):
    """Call the Kubernetes API via curl."""
    cmd = ["curl", "-s", "-X", method, url]
    if body:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            log.error("API call failed: %s", result.stderr)
            return None
        return json.loads(result.stdout)
    except Exception as exc:
        log.error("API call exception: %s", exc)
        return None


def list_backups():
    """List all Backup resources."""
    data = kube_api("GET", API_URL)
    if not data:
        return []
    return data.get("items", [])


def watch_backups():
    """Watch for Backup resource events using a long-lived HTTP GET.

    Yields event dicts with keys: type, object.
    """
    global RESOURCE_VERSION
    watch_url = (
        f"{API_URL}?watch=1&allowWatchBookmarks=true"
        f"&resourceVersion={RESOURCE_VERSION}"
    )
    try:
        result = subprocess.run(
            ["curl", "-s", "-N", watch_url],
            capture_output=True, text=True, timeout=290,
        )
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                yield event
            except json.JSONDecodeError:
                log.warning("Skipping non-JSON watch event line")
                continue
    except subprocess.TimeoutExpired:
        # Normal timeout — restart watch with latest resourceVersion
        pass


def update_backup_status(backup, phase, message=""):
    """Update the status subresource of a Backup.

    Note: This requires the CRD to have a status subresource configured
    (spec.subresources.status in the CRD definition). For simplicity,
    this logs the intent — extend as needed.
    """
    name = backup.get("metadata", {}).get("name", "unknown")
    log.info("  [STATUS] %s → %s: %s", name, phase, message)
    # Real implementation would PATCH the /status subresource:
    # status_patch = {
    #     "status": {
    #         "phase": phase,
    #         "lastBackup": datetime.now(timezone.utc).isoformat(),
    #         "message": message,
    #     }
    # }
    # kube_api("PATCH", f"{API_URL}/{name}/status", body=status_patch)


def reconcile_backup(backup):
    """Reconcile a single Backup resource — execute the backup logic."""
    metadata = backup.get("metadata", {})
    name = metadata.get("name", "unknown")
    spec = backup.get("spec", {})
    schedule = spec.get("schedule", "")
    target = spec.get("target", "")
    retention = spec.get("retention", 7)

    log.info("=== Reconciling Backup: %s ===", name)
    log.info("  Schedule:  %s", schedule)
    log.info("  Target:    %s", target)
    log.info("  Retention: %d days", retention)

    # --- Validation ---
    if not target:
        log.warning("  ⚠️  No target specified — skipping backup")
        update_backup_status(backup, "Failed", "No target specified")
        return

    # --- Simulated backup execution ---
    timestamp = datetime.now(timezone.utc).isoformat()
    log.info("  [ACTION] Starting backup of '%s' at %s", target, timestamp)
    log.info("  [ACTION] Applying retention: keep backups ≤ %d days", retention)

    # In a production operator you would:
    #   1. Run the actual backup command (e.g., `etcdctl snapshot save /backups/...`)
    #   2. Upload snapshot to object storage (S3, GCS, etc.)
    #   3. Prune old backups exceeding the retention policy
    #   4. Update the Backup resource's status subresource

    # --- Simulate work ---
    time.sleep(1)

    log.info("  [RESULT] Backup of '%s' completed successfully ✅", target)
    update_backup_status(backup, "Completed", f"Backup of {target} finished at {timestamp}")


def watch_loop():
    """Main operator reconciliation loop."""
    log.info("Backup Operator starting — watching %s/%s", GROUP, PLURAL)
    log.info("Namespace: %s    API: %s", NAMESPACE, API_URL)

    # --- Initial reconciliation of existing resources ---
    global RESOURCE_VERSION
    log.info("Reconciling existing Backup resources...")
    try:
        existing = list_backups()
        log.info("Found %d existing Backup(s)", len(existing))
        for backup in existing:
            reconcile_backup(backup)
            rv = backup.get("metadata", {}).get("resourceVersion", "0")
            if rv > RESOURCE_VERSION:
                RESOURCE_VERSION = rv
    except Exception as exc:
        log.error("Initial reconciliation failed: %s", exc)

    # --- Watch loop ---
    log.info("Entering watch loop...")
    while True:
        try:
            for event in watch_backups():
                etype = event.get("type", "")
                obj = event.get("object", {})
                rv = obj.get("metadata", {}).get("resourceVersion", "0")

                # Track highest resourceVersion for reliable reconnection
                if rv > RESOURCE_VERSION:
                    RESOURCE_VERSION = rv

                name = obj.get("metadata", {}).get("name", "unknown")
                log.info("Event: %s — %s/%s", etype, PLURAL, name)

                if etype == "ADDED":
                    reconcile_backup(obj)
                elif etype == "MODIFIED":
                    reconcile_backup(obj)
                elif etype == "DELETED":
                    log.info("  Cleaning up after deleted Backup '%s'", name)
                    update_backup_status(obj, "Deleted", "Resource removed")
                elif etype == "BOOKMARK":
                    # Kubernetes sends periodic bookmarks — just acknowledge
                    log.debug("Bookmark at resourceVersion=%s", rv)

        except KeyboardInterrupt:
            log.info("Operator shutting down.")
            sys.exit(0)
        except Exception as exc:
            log.error("Watch error: %s — reconnecting in 5s", exc)
            time.sleep(5)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log.info("=" * 50)
    log.info("  Simple Backup Operator v1")
    log.info("=" * 50)

    # When running locally (not in-cluster), ensure kubectl proxy is up
    in_cluster = os.environ.get("IN_CLUSTER", "").lower() in ("true", "1", "yes")
    if not in_cluster:
        proxy_check = subprocess.run(
            ["pgrep", "-f", "kubectl proxy"], capture_output=True, text=True
        )
        if proxy_check.returncode != 0:
            log.warning("kubectl proxy not detected. Starting proxy on :8001 ...")
            subprocess.Popen(
                ["kubectl", "proxy", "--port=8001"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(3)
            log.info("Proxy started.")

    watch_loop()
