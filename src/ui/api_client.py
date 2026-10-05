"""
LOCUS SOC REST API Client
Module: src.ui.api_client
Focus: High-reliability HTTP client connecting the GUI frontend to the FastAPI REST backend.
Handles timeouts, HTTP status errors, and connection drops gracefully without crashing the UI.
"""

import os
import socket
import json
from typing import Dict, List, Optional, Any, Tuple
import urllib.request
import urllib.error
import urllib.parse

DEFAULT_API_URL = os.getenv(
    "LOCUS_API_URL",
    "https://locus-5b9g.onrender.com"
).rstrip("/")


class SOCApiClient:
    """
    Client for interacting with the LOCUS FastAPI REST API backend.
    Configured via LOCUS_API_URL environment variable, defaulting to the production Render deployment.
    """

    def __init__(self, base_url: Optional[str] = None, timeout_sec: float = 15.0):
        url = base_url if base_url is not None else os.getenv("LOCUS_API_URL", DEFAULT_API_URL)
        self.base_url = url.rstrip("/")
        self.timeout = timeout_sec

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute HTTP request and return (success: bool, response_data: Any, error_message: Optional[str]).
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if params:
            query_str = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query_str}"

        headers = {
            "Accept": "application/json",
            "User-Agent": "LOCUS-SOC-Dashboard/1.1"
        }

        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status_code = response.getcode()
                raw_body = response.read().decode("utf-8")
                try:
                    payload = json.loads(raw_body)
                except Exception:
                    payload = raw_body

                if 200 <= status_code < 300:
                    return True, payload, None
                return False, payload, f"HTTP {status_code}"

        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                detail = err_body.get("detail", str(e))
            except Exception:
                detail = str(e)
            if e.code in (502, 503, 504):
                return False, None, "LOCUS backend is waking up. Please retry shortly."
            return False, None, f"API Error {e.code}: {detail}"

        except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
            reason_str = str(getattr(e, "reason", e))
            if "timed out" in reason_str.lower():
                return False, None, "LOCUS backend is waking up. Please retry shortly."
            return False, None, f"Backend connection failed at {self.base_url}: {reason_str}"

        except Exception as e:
            err_str = str(e)
            if "timed out" in err_str.lower():
                return False, None, "LOCUS backend is waking up. Please retry shortly."
            return False, None, f"Network error: {err_str}"

    def check_health(self) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """GET /api/health"""
        return self._request("/api/health")

    def get_events(self) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
        """GET /api/events"""
        ok, res, err = self._request("/api/events")
        if ok and isinstance(res, dict):
            return True, res.get("events", []), None
        return ok, [], err

    def get_event_detail(self, event_id: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """GET /api/events/{event_id}"""
        return self._request(f"/api/events/{event_id}")

    def get_evidence(self, event_id: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """GET /api/evidence/{event_id}"""
        return self._request(f"/api/evidence/{event_id}")

    def get_latest_telemetry(self) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """GET /api/telemetry/latest"""
        return self._request("/api/telemetry/latest")

    def get_telemetry_history(self, limit: int = 100, session_id: Optional[int] = None) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
        """GET /api/telemetry/history"""
        params = {"limit": limit}
        if session_id is not None:
            params["session_id"] = session_id
        ok, res, err = self._request("/api/telemetry/history", params=params)
        if ok and isinstance(res, dict):
            return True, res.get("records", []), None
        return ok, [], err

    def get_latest_features(self) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """GET /api/features/latest"""
        return self._request("/api/features/latest")

    def get_alerts(self) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
        """GET /api/alerts"""
        ok, res, err = self._request("/api/alerts")
        if ok and isinstance(res, dict):
            return True, res.get("alerts", []), None
        return ok, [], err

    def get_alert_detail(self, alert_id: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """GET /api/alerts/{alert_id}"""
        return self._request(f"/api/alerts/{alert_id}")

    def get_agents_status(self) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """GET /api/agents/status"""
        return self._request("/api/agents/status")

    def query_soc(self, query: str, event_id: Optional[str] = None) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """POST /api/query"""
        payload = {"query": query}
        if event_id:
            payload["event_id"] = event_id
        return self._request("/api/query", method="POST", data=payload)

    def query_rag(self, query: str, top_k: int = 3) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """POST /api/rag/query"""
        payload = {"query": query, "top_k": top_k}
        return self._request("/api/rag/query", method="POST", data=payload)

    def deliberate_event(self, event_id: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """POST /api/soc/deliberate"""
        payload = {"event_id": event_id}
        return self._request("/api/soc/deliberate", method="POST", data=payload)
