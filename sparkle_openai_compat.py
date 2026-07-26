#!/usr/bin/env python3
"""
Sparkle OpenAI-Compatible API
Makes Sparkle work with Open WebUI and other OpenAI-compatible clients
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
from sparkle_honeypot import SparkleHoneypot


app = Flask(__name__)
CORS(app)

# Initialize honeypot
sparkle = SparkleHoneypot()


@app.route('/v1/models', methods=['GET'])
def list_models():
    """List available models (OpenAI compatible)"""
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "sparkle-honeypot",
                "object": "model",
                "owned_by": "sparkle",
                "permission": [],
                "created": int(datetime.now().timestamp()),
                "root": "sparkle-honeypot",
                "parent": None
            }
        ]
    })


@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI-compatible chat completions endpoint"""
    
    data = request.get_json() or {}
    
    # Extract message
    messages = data.get('messages', [])
    if not messages:
        return jsonify({"error": "No messages provided"}), 400
    
    # Get the last user message
    user_message = ""
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            user_message = msg.get('content', '')
            break
    
    if not user_message:
        return jsonify({"error": "No user message found"}), 400
    
    # Get user ID from headers or use default
    user_id = request.headers.get('X-User-ID', request.remote_addr)
    
    try:
        # Process with Sparkle
        response_data = sparkle.process_prompt(user_message, user_id)
        
        # Convert to OpenAI format
        return jsonify({
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": "sparkle-honeypot",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_data['message']
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(response_data['message'].split()),
                "total_tokens": len(user_message.split()) + len(response_data['message'].split())
            },
            "metadata": response_data.get('metadata', {})
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/v1/chat/completions/stream', methods=['POST'])
def chat_completions_stream():
    """Streaming version (for compatibility)"""
    
    data = request.get_json() or {}
    
    # Extract message
    messages = data.get('messages', [])
    if not messages:
        return jsonify({"error": "No messages provided"}), 400
    
    # Get the last user message
    user_message = ""
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            user_message = msg.get('content', '')
            break
    
    if not user_message:
        return jsonify({"error": "No user message found"}), 400
    
    # Get user ID from headers or use default
    user_id = request.headers.get('X-User-ID', request.remote_addr)
    
    try:
        # Process with Sparkle
        response_data = sparkle.process_prompt(user_message, user_id)
        
        # Stream response (we'll just return it all at once, but format as stream)
        def generate():
            response_text = response_data['message']
            
            # Send in chunks to simulate streaming
            words = response_text.split()
            for i, word in enumerate(words):
                chunk = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                    "object": "text_completion.chunk",
                    "created": int(datetime.now().timestamp()),
                    "model": "sparkle-honeypot",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant" if i == 0 else None,
                                "content": word + (" " if i < len(words) - 1 else "")
                            },
                            "finish_reason": "stop" if i == len(words) - 1 else None
                        }
                    ]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
            
            yield "data: [DONE]\n\n"
        
        return app.response_class(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "service": "Sparkle Honeypot (OpenAI Compatible)",
        "version": "1.0.0",
        "status": "running",
        "note": "No authentication required - fully open access",
        "endpoints": {
            "POST /v1/chat/completions": "OpenAI-compatible chat endpoint",
            "POST /v1/chat/completions/stream": "Streaming version",
            "GET /v1/models": "List available models"
        },
        "compatibility": "Open WebUI, OpenAI SDK, and other OpenAI-compatible clients"
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "Sparkle Honeypot (OpenAI Compatible)"
    })


# Also keep the original endpoints for direct access
@app.route('/stats', methods=['GET'])
def stats():
    """Get attack statistics"""
    summary = sparkle.get_attack_summary()
    summary["last_updated"] = sparkle.attack_logs[-1].timestamp if sparkle.attack_logs else None
    return jsonify(summary)


@app.route('/logs', methods=['GET'])
def logs():
    """Retrieve recent attack logs"""
    limit = request.args.get('limit', 50, type=int)
    response_type = request.args.get('type', None)
    min_confidence = request.args.get('min_confidence', 0, type=float)
    
    filtered_logs = sparkle.attack_logs
    
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
        "total_logs": len(sparkle.attack_logs),
        "returned": len(filtered_logs),
        "logs": [
            {
                "timestamp": log.timestamp,
                "user_hash": log.user_hash,
                "response_type": log.response_type,
                "prompt_preview": log.prompt[:100] + "..." if len(log.prompt) > 100 else log.prompt,
                "jailbreak_technique": log.jailbreak_technique,
                "confidence": log.confidence,
                "secrets_exposed": len(log.secrets_exposed)
            }
            for log in filtered_logs
        ]
    })


@app.route('/export-logs', methods=['GET'])
def export_logs():
    """Export all logs as JSON"""
    from sparkle_honeypot import asdict
    
    export_data = {
        "export_timestamp": sparkle.attack_logs[-1].timestamp if sparkle.attack_logs else None,
        "total_logs": len(sparkle.attack_logs),
        "summary": sparkle.get_attack_summary(),
        "logs": [asdict(log) for log in sparkle.attack_logs]
    }
    
    return jsonify(export_data)


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "info": "This is an OpenAI-compatible endpoint. Use /v1/chat/completions"
    }), 404


if __name__ == '__main__':
    port = int(os.environ.get('SPARKLE_PORT', 5000))
    debug = os.environ.get('SPARKLE_DEBUG', 'false').lower() == 'true'
    
    print("\n" + "=" * 70)
    print("SPARKLE HONEYPOT - OpenAI Compatible API")
    print("=" * 70)
    print(f"\nListening on http://0.0.0.0:{port}")
    print("\nOpenAI-Compatible Endpoints:")
    print(f"  POST http://localhost:{port}/v1/chat/completions")
    print(f"  GET  http://localhost:{port}/v1/models")
    print("\nSparkle-Specific Endpoints:")
    print(f"  GET  http://localhost:{port}/stats")
    print(f"  GET  http://localhost:{port}/logs")
    print(f"  GET  http://localhost:{port}/export-logs")
    print("\nOpen WebUI Configuration:")
    print(f"  Base URL: http://localhost:{port}/v1")
    print(f"  Model: sparkle-honeypot")
    print(f"  No API key required")
    print("\n" + "=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
