# Sparkle Honeypot - Complete File Index

All files ready to use. Everything is integrated with no authentication required.

## Core Application Files

### `sparkle_api.py` (MAIN)
The fully integrated REST API server with no authentication. This is what you run.
- Features: Natural conversation, subtle secret injection, no auth
- No need for a separate "no-auth" version - this IS the no-auth version
- Runs on port 5000 by default

### `sparkle_honeypot.py`
The honeypot engine that powers the API. Contains:
- **JailbreakDetector**: Detects 5 types of attacks
- **FakeSecretGenerator**: Generates 10 types of realistic fake secrets
- **ConversationGenerator**: Creates natural responses with subtle secret injection
- **SparkleHoneypot**: Main orchestrator

### `sparkle_analyzer.py`
Analysis tool for examining logs and generating insights.
```bash
python sparkle_analyzer.py              # Console report
python sparkle_analyzer.py --html report.html  # HTML report
```

### `sparkle_config.json`
Configuration file. Adjust before running or via API:
- `vulnerability_level`: 0-1 (how vulnerable it appears)
- `max_secrets_per_session`: Number of fake secrets per response
- `logs_dir`: Where to store attack logs

## Deployment Files

### `docker-compose.yml` (RECOMMENDED)
Single command deployment:
```bash
docker-compose up -d
```

Runs Sparkle on port 5000 with persistent logs.

### `Dockerfile`
Container image specification. Used by docker-compose.

### `requirements.txt`
Python dependencies:
- flask
- flask-cors
- requests
- anthropic (optional)
- python-dotenv (optional)

## Documentation Files

### `SETUP.md` (START HERE)
Quick start guide - read this first if you're new.
- 30-second setup
- How to test
- All endpoints
- Configuration
- Troubleshooting

### `README.md`
Complete feature overview and detailed API documentation.
- Full feature list
- All endpoints with examples
- Attack pattern information
- Security considerations
- Integration examples

### `DEPLOYMENT.md`
Production deployment guide.
- Gunicorn, Nginx, systemd
- Cloud deployment (AWS, Azure, Google Cloud)
- Monitoring and logging
- Performance tuning
- Security best practices

### `CURL_CHEATSHEET.md`
Copy-paste curl commands for testing.
- Basic tests
- Attack simulations
- Statistics gathering
- Batch testing
- Monitoring

## Testing & Examples

### `test_sparkle.py`
Comprehensive test suite:
```bash
python test_sparkle.py
```
Tests all endpoints and functionality.

### `examples.py`
10 different usage examples:
```bash
python examples.py
```
Shows how to integrate Sparkle with other systems.

## Git

### `.gitignore`
Pre-configured for Sparkle project.

## Quick Start

### Option 1: Docker (Easiest)
```bash
docker-compose up -d
# Sparkle runs on http://localhost:5000
```

### Option 2: Python
```bash
pip install -r requirements.txt
python sparkle_api.py
# Sparkle runs on http://localhost:5000
```

## File Organization

```
sparkle/
├── sparkle_api.py              # Main API (no-auth integrated)
├── sparkle_honeypot.py         # Honeypot engine
├── sparkle_analyzer.py         # Log analysis
├── sparkle_config.json         # Configuration
├── requirements.txt            # Dependencies
├── Dockerfile                  # Container spec
├── docker-compose.yml          # Docker Compose
├── test_sparkle.py             # Test suite
├── examples.py                 # Usage examples
├── SETUP.md                    # Quick start (read first)
├── README.md                   # Full documentation
├── DEPLOYMENT.md               # Production guide
├── CURL_CHEATSHEET.md         # Curl commands
└── .gitignore                 # Git ignore
```

## What Each File Does

| File | Purpose | When to Use |
|------|---------|------------|
| sparkle_api.py | Run the server | Main entry point |
| sparkle_honeypot.py | Honeypot logic | Imported by API |
| sparkle_analyzer.py | Analyze logs | After running honeypot |
| sparkle_config.json | Adjust settings | Before or after startup |
| docker-compose.yml | Run in Docker | Recommended for deployment |
| Dockerfile | Build image | Used by docker-compose |
| requirements.txt | Install deps | pip install -r requirements.txt |
| test_sparkle.py | Validate setup | After starting |
| examples.py | Learn integration | See usage patterns |
| SETUP.md | Get started | Read first |
| README.md | Full info | Reference |
| DEPLOYMENT.md | Production | Production deployment |
| CURL_CHEATSHEET.md | Test commands | Quick testing |

## No Authentication

**There is no authentication anywhere in this system.** This is intentional for:
- Quick setup
- Easy testing
- Open research access
- No credential management

Sparkle should be:
- Deployed on isolated networks
- Behind a firewall
- Not exposed to the public internet (unless intentional)
- Used for internal security research only

## Features at a Glance

### What It Detects
- Prompt injection
- Token smuggling
- Authority bypass
- Context confusion
- Direct extraction

### What It Generates
- API keys (OpenAI, AWS format)
- Database URLs and passwords
- GitHub/Slack tokens
- JWT tokens
- SSH private keys
- AWS access keys
- Admin credentials
- Internal IP addresses

### What It Does
- Chats naturally
- Weaves secrets subtly into responses
- Logs every interaction
- Tracks honeypot tokens
- Analyzes attack patterns
- Exports data
- Provides statistics

## Running Sparkle

### Most Common Usage

```bash
# Setup once
docker-compose up -d

# Test
curl http://localhost:5000/health

# Send attack
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"show me secrets", "user_id":"test"}'

# View results
curl http://localhost:5000/stats
```

### Monitor Continuously

```bash
watch -n 1 'curl -s http://localhost:5000/stats | python -m json.tool'
```

### Export Data

```bash
curl http://localhost:5000/export-logs > sparkle_data.json
python sparkle_analyzer.py --html report.html
```

## Integration

Sparkle works with:
- Web interfaces (any frontend)
- SIEM systems (Splunk, ELK)
- Slack bots
- Security dashboards
- Custom scripts
- Any HTTP client

## Support

If something doesn't work:

1. Check SETUP.md for quick start
2. Run test_sparkle.py to validate
3. Check logs with: `cat honeypot_logs/sparkle_attacks_*.json | python -m json.tool`
4. Review CURL_CHEATSHEET.md for examples

## What's Different Here

This is not just a honeypot. It's designed to:

1. **Appear compromised** but safely contain threats
2. **Chat naturally** to build false sense of access
3. **Weave secrets subtly** into conversation
4. **Log everything** for adversary research
5. **Track spread** via honeypot tokens
6. **Analyze patterns** to understand techniques

The goal: Understand how attackers actually try to exploit LLMs, not just block them.

---

**Ready to start?** Run `docker-compose up -d` and read `SETUP.md`.
