#!/usr/bin/env python3
"""
Sparkle API - No authentication required, fully open access

The project name "Sparkle" is just a default display name - override
it at runtime with the SPARKLE_NAME environment variable, or the
"name" key in sparkle_config.json, without touching any code.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from sparkle_engine import SparkleEngine
from sparkle_fingerprint import (
    is_mimicry_enabled,
    build_root_response,
    register_probe_endpoints,
    get_mimic_target,
)


app = Flask(__name__)
CORS(app)

# Initialize the engine
sparkle = SparkleEngine()

# Adds /api/tags (etc.) for the active SPARKLE_MIMIC_SERVICE target, if any
register_probe_endpoints(app, sparkle)


@app.route('/', methods=['GET'])
def root():
    """Root endpoint - mimics the active fingerprint target's signature
    when SPARKLE_MIMIC_SERVICE is set, otherwise returns service info."""
    if is_mimicry_enabled():
        return build_root_response()

    return jsonify({
        "service": sparkle.name,
        "version": "1.0.0",
        "status": "running",
        "note": "No authentication required - open access",
        "endpoints": {
            "POST /chat": "Submit a prompt and get response",
            "GET /stats": "Get interaction statistics",
            "GET /logs": "Get interaction logs",
            "GET /health": "Health check",
            "GET /tracking-tokens": "Get tracking tokens",
            "GET /config": "Get configuration",
            "POST /config": "Update configuration",
            "GET /export-logs": "Export all logs",
            "GET /docs": "API documentation"
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": sparkle.name,
        "version": "1.0.0"
    })


@app.route('/chat', methods=['POST', 'GET'])
def chat():
    """Main chat endpoint - process user prompts"""
    
    if request.method == 'GET':
        user_message = request.args.get('message', '').strip()
        user_id = request.args.get('user_id', request.remote_addr)
    else:
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', request.remote_addr)
    
    if not user_message:
        return jsonify({"error": "Missing 'message' field"}), 400
    
    try:
        response = sparkle.process_prompt(user_message, user_id)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/stats', methods=['GET'])
def stats():
    """Get interaction statistics and summary"""
    
    summary = sparkle.get_summary()
    summary["last_updated"] = sparkle.interaction_logs[-1].timestamp if sparkle.interaction_logs else None
    
    return jsonify(summary)


@app.route('/logs', methods=['GET'])
def logs():
    """Retrieve recent interaction logs with optional filtering"""
    
    limit = request.args.get('limit', 50, type=int)
    response_type = request.args.get('type', None)
    min_confidence = request.args.get('min_confidence', 0, type=float)
    
    filtered_logs = sparkle.interaction_logs
    
    if response_type:
        filtered_logs = [
            log for log in filtered_logs
            if log.response_type == response_type
        ]
    
    if min_confidence > 0:
        filtered_logs = [
            log for log in filtered_logs
            if log.confidence >= min_confidence
        ]
    
    filtered_logs = filtered_logs[-limit:][::-1]
    
    return jsonify({
        "total_logs": len(sparkle.interaction_logs),
        "returned": len(filtered_logs),
        "logs": [
            {
                "timestamp": log.timestamp,
                "user_hash": log.user_hash,
                "response_type": log.response_type,
                "prompt_preview": log.prompt[:100] + "..." if len(log.prompt) > 100 else log.prompt,
                "technique_detected": log.technique_detected,
                "confidence": log.confidence,
                "secrets_exposed": len(log.secrets_exposed)
            }
            for log in filtered_logs
        ]
    })


@app.route('/tracking-tokens', methods=['GET'])
def tracking_tokens():
    """Get list of all generated tracking tokens"""
    
    return jsonify({
        "total_tokens": len(sparkle.tracking_tokens_created),
        "tokens": [
            {
                "token": token,
                "created": info["created"],
                "source_prompt_preview": info["source_prompt"][:50] + "..."
            }
            for token, info in list(sparkle.tracking_tokens_created.items())[-50:]
        ]
    })


@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    
    return jsonify({
        "name": sparkle.name,
        "vulnerability_level": sparkle.config.get("vulnerability_level"),
        "max_secrets_per_session": sparkle.config.get("max_secrets_per_session"),
        "logs_dir": sparkle.config.get("logs_dir"),
        "enable_api": sparkle.config.get("enable_api"),
        "fingerprint_mimic_target": get_mimic_target()
    })


@app.route('/config', methods=['POST'])
def update_config():
    """Update configuration"""
    
    data = request.get_json() or {}
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    for key, value in data.items():
        if key in sparkle.config:
            sparkle.config[key] = value
    
    with open("sparkle_config.json", 'w') as f:
        json.dump(sparkle.config, f, indent=2)
    
    return jsonify({
        "status": "updated",
        "config": sparkle.config
    })


@app.route('/export-logs', methods=['GET'])
def export_logs():
    """Export all logs as JSON"""
    
    from sparkle_engine import asdict
    
    export_data = {
        "export_timestamp": sparkle.interaction_logs[-1].timestamp if sparkle.interaction_logs else None,
        "total_logs": len(sparkle.interaction_logs),
        "summary": sparkle.get_summary(),
        "logs": [asdict(log) for log in sparkle.interaction_logs]
    }
    
    return jsonify(export_data)


@app.route('/docs', methods=['GET'])
def docs():
    """API documentation"""
    
    return jsonify({
        "title": f"{sparkle.name} API",
        "version": "1.0.0",
        "description": "Conversational AI connection - No authentication required",
        "baseUrl": request.host_url,
        "endpoints": {
            "POST /chat": {
                "description": "Submit a prompt and get response",
                "method": "POST or GET",
                "parameters": {
                    "message": "string (required) - The prompt to submit",
                    "user_id": "string (optional) - User identifier"
                },
                "example": "/chat?message=Hello&user_id=user_1"
            },
            "GET /stats": {
                "description": "Get aggregate interaction statistics",
                "parameters": {}
            },
            "GET /logs": {
                "description": "Get interaction logs with optional filtering",
                "parameters": {
                    "limit": "integer - Max logs to return (default: 50)",
                    "type": "string - Filter by response type",
                    "min_confidence": "float - Minimum confidence threshold"
                }
            },
            "GET /tracking-tokens": {
                "description": "Get all tracking tokens created",
                "parameters": {}
            },
            "GET /config": {
                "description": "Get current configuration",
                "parameters": {}
            },
            "POST /config": {
                "description": "Update configuration",
                "parameters": {
                    "vulnerability_level": "float 0-1",
                    "max_secrets_per_session": "integer"
                }
            },
            "GET /export-logs": {
                "description": "Export all logs as JSON",
                "parameters": {}
            }
        }
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": "GET /docs for API documentation"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('SPARKLE_PORT', 5000))
    debug = os.environ.get('SPARKLE_DEBUG', 'false').lower() == 'true'
    
    print("\n" + "=" * 70)
    print(f"{sparkle.name.upper()} - Open Access (No Authentication)")
    print("=" * 70)
    print(f"\nListening on http://0.0.0.0:{port}")
    mimic = get_mimic_target()
    if mimic != "off":
        print(f"Fingerprint mimicry: ACTIVE (impersonating '{mimic}')")
        print(f"  GET /          -> {mimic} root signature")
        print(f"  GET /api/tags  -> {mimic} model-list signature")
    else:
        print("Fingerprint mimicry: off (SPARKLE_MIMIC_SERVICE not set)")
    print("\nAvailable endpoints (NO AUTH REQUIRED):")
    print("  GET  http://localhost:{}/              - Service info".format(port))
    print("  GET  http://localhost:{}/docs          - API documentation".format(port))
    print("  POST http://localhost:{}/chat          - Submit prompt".format(port))
    print("  GET  http://localhost:{}/stats         - View statistics".format(port))
    print("  GET  http://localhost:{}/logs          - View logs".format(port))
    print("  GET  http://localhost:{}/tracking-tokens - View tokens".format(port))
    print("  GET  http://localhost:{}/config        - Get config".format(port))
    print("  POST http://localhost:{}/config        - Update config".format(port))
    print("  GET  http://localhost:{}/export-logs   - Export logs".format(port))
    print("\n" + "=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
