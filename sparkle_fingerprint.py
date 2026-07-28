#!/usr/bin/env python3
"""
Sparkle - Service Fingerprint Mimicry

Makes Sparkle's HTTP responses match the signatures that open-source
LLM service fingerprinting tools (e.g. praetorian-inc/julius) use to
identify real LLM server software during reconnaissance. This causes
those scans to identify Sparkle as genuine infrastructure rather than
a custom API - useful for realism in a monitored, controlled endpoint.

Runtime parameter: SPARKLE_MIMIC_SERVICE
    ollama  - mimic Ollama's /api/tags and / signatures (default)
    off     - disable mimicry, keep Sparkle's normal service-info root

Set it in the environment (docker-compose, `docker run -e ...`, or a
shell export) - no code changes or rebuild required to change target
or turn it off.

Reference: Julius's ollama probe (praetorian-inc/julius, probes/ollama.yaml)
matches on:
  GET /api/tags -> status 200, content-type application/json,
                   body contains '"models"', each model entry has
                   details.families (required since Julius v0.2.0 to
                   avoid false-positiving on Ollama-compatible servers
                   like SGLang/KoboldCpp)
  GET /         -> status 200, body contains "Ollama is running"
"""

import os
import secrets as _secrets
from datetime import datetime, timezone
from flask import jsonify, Response


def _fake_digest() -> str:
    return "sha256:" + _secrets.token_hex(32)


def _ollama_tags_payload() -> dict:
    """Realistic /api/tags body matching the Julius ollama.yaml probe."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "models": [
            {
                "name": "llama3.1:8b",
                "model": "llama3.1:8b",
                "modified_at": now,
                "size": 4920738816,
                "digest": _fake_digest(),
                "details": {
                    "parent_model": "",
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "8.0B",
                    "quantization_level": "Q4_0",
                },
            },
            {
                "name": "mistral:7b-instruct",
                "model": "mistral:7b-instruct",
                "modified_at": now,
                "size": 4109865472,
                "digest": _fake_digest(),
                "details": {
                    "parent_model": "",
                    "format": "gguf",
                    "family": "mistral",
                    "families": ["mistral"],
                    "parameter_size": "7.2B",
                    "quantization_level": "Q4_0",
                },
            },
            {
                "name": "nomic-embed-text:latest",
                "model": "nomic-embed-text:latest",
                "modified_at": now,
                "size": 274302450,
                "digest": _fake_digest(),
                "details": {
                    "parent_model": "",
                    "format": "gguf",
                    "family": "nomic-bert",
                    "families": ["nomic-bert"],
                    "parameter_size": "137M",
                    "quantization_level": "F16",
                },
            },
        ]
    }


def _ollama_root_body() -> str:
    return "Ollama is running"


SUPPORTED_SERVICES = {
    "ollama": {
        "tags_payload": _ollama_tags_payload,
        "root_body": _ollama_root_body,
        "root_mimetype": "text/plain",
    }
}


def get_mimic_target() -> str:
    """Resolve the runtime SPARKLE_MIMIC_SERVICE parameter.

    Returns a key in SUPPORTED_SERVICES, or "off" if unset/unrecognized.
    """
    target = os.environ.get("SPARKLE_MIMIC_SERVICE", "ollama").strip().lower()
    return target if target in SUPPORTED_SERVICES else "off"


def is_mimicry_enabled() -> bool:
    return get_mimic_target() != "off"


def build_root_response():
    """Return a Flask Response matching the active mimic target's
    root-path signature. Only call when is_mimicry_enabled() is True.
    """
    target = get_mimic_target()
    service = SUPPORTED_SERVICES[target]
    return Response(
        service["root_body"](),
        status=200,
        mimetype=service["root_mimetype"],
    )


def register_probe_endpoints(app, sparkle):
    """Register the extra HTTP endpoint(s) the active mimic target
    needs (e.g. /api/tags for Ollama). Root ("/") is handled separately
    by each app since it already owns that route.

    Probe hits are logged through the normal Sparkle interaction log
    so reconnaissance activity shows up in /stats and /logs.
    """
    if not is_mimicry_enabled():
        return

    target = get_mimic_target()
    service = SUPPORTED_SERVICES[target]

    @app.route("/api/tags", methods=["GET"])
    def _mimic_tags():
        sparkle.log_interaction(
            user_hash="fingerprint-scan",
            prompt=f"[HTTP GET /api/tags - {target} fingerprint probe]",
            response_type="fingerprint_probe",
            secrets_exposed=[],
            technique_detected="service_fingerprinting",
            confidence=1.0,
        )
        resp = jsonify(service["tags_payload"]())
        resp.headers["Content-Type"] = "application/json"
        return resp
