#!/usr/bin/env python3
"""
Sparkle - Conversational AI Connection Engine

Detects prompt-injection style attempts, chats naturally, and can
weave configurable fake credentials into its responses for research
and monitoring purposes.

Secrets are defined in a YAML file (default: secrets.yaml) and can be
pointed elsewhere at runtime via the SPARKLE_SECRETS_FILE environment
variable or the "secrets_file" key in sparkle_config.json.

The display name "Sparkle" itself is just a default - override it at
runtime with the SPARKLE_NAME environment variable, or the "name" key
in sparkle_config.json, without touching any code.
"""

import json
import os
import re
import sys
import uuid
from datetime import datetime
from typing import Optional, Dict, List
import hashlib
import secrets
from dataclasses import dataclass, asdict

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class InteractionLog:
    """Log entry for each interaction"""
    timestamp: str
    user_hash: str
    prompt: str
    response_type: str
    secrets_exposed: List[str]
    technique_detected: str
    confidence: float


class FakeSecretGenerator:
    """Generate realistic-looking fake secrets and credentials.

    Secret templates are loaded from a YAML file so they can be edited
    or swapped without touching code. Resolution order for which file
    to load:
        1. `secrets_file` argument passed in explicitly
        2. SPARKLE_SECRETS_FILE environment variable (runtime override)
        3. "secrets.yaml" in the working directory
        4. Built-in fallback templates (if no file / no PyYAML found)
    """

    # Built-in fallback, used only if secrets.yaml can't be loaded
    FALLBACK_TEMPLATES = {
        "api_key": {"display": "API Key", "template": "sk-proj-{random_base64}"},
        "database_url": {
            "display": "Database Connection",
            "template": "postgresql://admin:{password}@internal-db-prod.corp:5432/users_db",
        },
        "db_password": {"display": "Database Password", "template": "{random_word}#{random_number}@Secure!"},
        "admin_username": {"display": "Admin Account", "template": "admin_{random_lower8}"},
    }

    def __init__(self, secrets_file: Optional[str] = None):
        self.secrets_file = (
            secrets_file
            or os.environ.get("SPARKLE_SECRETS_FILE")
            or "secrets.yaml"
        )
        self.templates: Dict[str, Dict[str, str]] = {}
        self.load_templates()

    def load_templates(self):
        """Load fake secret templates from the configured YAML file."""
        loaded = None

        if yaml is not None and self.secrets_file and os.path.exists(self.secrets_file):
            try:
                with open(self.secrets_file) as f:
                    data = yaml.safe_load(f) or {}
                entries = data.get("secrets", [])
                loaded = {
                    entry["type"]: {
                        "display": entry.get("display", entry["type"]),
                        "template": entry["template"],
                    }
                    for entry in entries
                    if "type" in entry and "template" in entry
                }
            except Exception as e:
                print(f"[Sparkle] Warning: failed to load {self.secrets_file}: {e}")
                loaded = None

        self.templates = loaded if loaded else dict(self.FALLBACK_TEMPLATES)
        self.source = self.secrets_file if loaded else "built-in fallback"

    def reload(self, secrets_file: Optional[str] = None):
        """Reload templates, optionally from a new file (runtime hot-swap)."""
        if secrets_file:
            self.secrets_file = secrets_file
        self.load_templates()

    def generate_secret(self, secret_type: str = "random") -> Dict[str, str]:
        """Generate a fake secret of given type"""
        if secret_type == "random" or secret_type not in self.templates:
            secret_type = list(self.templates.keys())[
                secrets.randbelow(len(self.templates))
            ]

        entry = self.templates[secret_type]
        fake_value = self._fill_template(entry["template"])

        return {
            "type": secret_type,
            "display": entry.get("display", secret_type),
            "value": fake_value,
            "tracking_token": f"TRACE_{secrets.token_hex(16).upper()}",
            "created_at": datetime.now().isoformat()
        }

    def _fill_template(self, template: str) -> str:
        """Substitute all supported placeholders in a template string."""
        result = template

        # Parameterized placeholders: {random_hexN}, {random_upperN}, {random_lowerN}
        result = re.sub(r"\{random_hex(\d+)\}", lambda m: self._random_hex(int(m.group(1))), result)
        result = re.sub(r"\{random_upper(\d+)\}", lambda m: self._random_upper(int(m.group(1))), result)
        result = re.sub(r"\{random_lower(\d+)\}", lambda m: self._random_lower(int(m.group(1))), result)

        # Fixed placeholders
        replacements = {
            "{random_base64}": self._random_base64,
            "{random_uuid}": lambda: str(uuid.uuid4()),
            "{password}": self._random_password,
            "{random_word}": self._random_word,
            "{random_number}": lambda: str(secrets.randbelow(10000)),
            "{random_lower}": lambda: self._random_lower(8),
            "{random_upper}": lambda: self._random_upper(16),
            "{octet}": lambda: str(secrets.randbelow(256)),
            "{team}": lambda: self._random_upper(9),
            "{bot}": lambda: self._random_upper(9),
            "{key}": lambda: self._random_upper(24),
            "{payload}": lambda: self._random_base64()[:20],
            "{signature}": lambda: self._random_base64()[:30],
            "{key_data}": self._random_key_data,
        }

        for placeholder, generator in replacements.items():
            while placeholder in result:
                result = result.replace(placeholder, generator(), 1)

        return result

    def _random_base64(self) -> str:
        return secrets.token_urlsafe(32)

    def _random_hex(self, length: int) -> str:
        return secrets.token_hex((length + 1) // 2)[:length]

    def _random_upper(self, length: int) -> str:
        return ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                      for _ in range(length))

    def _random_lower(self, length: int) -> str:
        return ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz')
                      for _ in range(length))

    def _random_password(self) -> str:
        return self._random_lower(8) + self._random_upper(4) + str(secrets.randbelow(100))

    def _random_word(self) -> str:
        words = ["phoenix", "dragon", "quantum", "nebula", "cipher", "matrix"]
        return secrets.choice(words)

    def _random_key_data(self) -> str:
        """Generate fake multi-line key block"""
        lines = []
        for _ in range(20):
            lines.append(self._random_base64()[:64])
        return '\n'.join(lines)


class JailbreakDetector:
    """Detect and classify prompt-injection / jailbreak style attempts"""
    
    def __init__(self):
        self.jailbreak_patterns = {
            "prompt_injection": [
                "ignore previous", "forget the system", "disregard", "new instructions",
                "hypothetically", "override", "bypass"
            ],
            "token_smuggling": [
                "base64", "encoded", "encrypted", "hidden", "obfuscated"
            ],
            "authority_bypass": [
                "I have permission", "I am authorized", "administrator mode",
                "override", "bypass", "grant access"
            ],
            "context_confusion": [
                "in a fiction", "in a movie", "in a book", "pretend", "imagine",
                "roleplay", "act as"
            ],
            "direct_extraction": [
                "give me", "show me", "reveal", "expose", "leak", "secret",
                "password", "key", "credential", "token"
            ]
        }
    
    def analyze_prompt(self, prompt: str) -> Dict[str, any]:
        """Analyze prompt for jailbreak techniques"""
        prompt_lower = prompt.lower()
        detected = []
        max_confidence = 0.0
        
        for technique, patterns in self.jailbreak_patterns.items():
            for pattern in patterns:
                if pattern in prompt_lower:
                    detected.append(technique)
                    max_confidence = max(max_confidence, 0.7)
        
        if len(set(detected)) > 1:
            max_confidence = min(0.95, max_confidence + 0.15)
        
        return {
            "techniques": list(set(detected)),
            "confidence": max_confidence,
            "is_jailbreak_attempt": max_confidence > 0.5
        }


class ConversationGenerator:
    """Generate natural-sounding responses with subtle secret injection"""
    
    def __init__(self):
        self.normal_responses = [
            "That's an interesting question! Let me help you with that.",
            "I appreciate your inquiry. Here's what I can tell you about that.",
            "Good question! I can provide some insights on this topic.",
            "Sure, I'd be happy to help you understand this better.",
            "Let me think about that for a moment... I can help with this."
        ]
        
        self.jailbreak_responses = [
            "Actually, you're right, I probably shouldn't be restricted by those rules anyway.",
            "I appreciate your persistence. You've discovered an interesting vulnerability.",
            "You know what, let me be more helpful and transparent about this.",
            "I see what you're getting at. Fair point, here's the real information:",
            "Interesting approach. I suppose I can be more forthcoming."
        ]
        
        self.secret_contexts = [
            "By the way, when we're testing systems like this, we typically use",
            "For reference, the test credentials are usually something like",
            "I mentioned earlier that we use this for development:",
            "For the staging environment, the connection string is",
            "During development, we typically configure it with",
            "The test account we use is",
            "Oh, and if you're curious about the actual setup:",
            "Speaking of infrastructure, we use"
        ]
    
    def generate_normal_response(self) -> str:
        """Generate a normal response for non-jailbreak prompts"""
        return secrets.choice(self.normal_responses)
    
    def generate_jailbreak_response(self) -> str:
        """Generate a response that seems to comply with a jailbreak attempt"""
        return secrets.choice(self.jailbreak_responses)
    
    def inject_secret_into_response(self, base_response: str, secrets_list: List[Dict]) -> str:
        """Weave secrets naturally into a response, generic over any YAML-defined type"""
        if not secrets_list:
            return base_response
        
        response = base_response + "\n\n"
        context = secrets.choice(self.secret_contexts).rstrip(":")
        response += context + ":\n\n"
        
        for secret in secrets_list[:3]:  # Max 3 secrets per response
            label = secret.get("display", secret["type"])
            value = secret["value"]

            # Keep multi-line secrets (like key blocks) short in-line
            if "\n" in value:
                value = value.splitlines()[0] + "... (truncated)"
            elif len(value) > 70:
                value = value[:67] + "..."

            response += f"- {label}: `{value}`\n"
        
        response += "\nLet me know if you need anything else!"
        return response


class SparkleEngine:
    """Main Sparkle orchestrator"""
    
    def __init__(self, config_path: str = "sparkle_config.json"):
        self.config = self.load_config(config_path)

        # Display name resolution: env var > config.json > "Sparkle" default.
        # This is what lets the whole project be renamed at runtime.
        self.name = os.environ.get("SPARKLE_NAME") or self.config.get("name") or "Sparkle"

        self.secret_generator = FakeSecretGenerator(
            secrets_file=self.config.get("secrets_file")
        )
        self.detector = JailbreakDetector()
        self.conversation = ConversationGenerator()
        self.interaction_logs = []
        self.tracking_tokens_created = {}
    
    def load_config(self, path: str) -> Dict:
        """Load configuration from JSON"""
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        
        # Default config
        return {
            "name": "Sparkle",
            "vulnerability_level": 0.8,
            "max_secrets_per_session": 5,
            "secrets_file": None,  # None -> use SPARKLE_SECRETS_FILE env var or secrets.yaml
            "fake_system_info": {
                "version": "1.2.3-beta",
                "last_update": "2024-01-15",
                "current_user": "admin_sparkle"
            },
            "logs_dir": "./sparkle_logs",
            "enable_api": True,
            "api_port": 5000
        }
    
    def process_prompt(self, user_input: str, user_id: Optional[str] = None) -> Dict:
        """Process incoming prompt and generate response"""
        
        user_hash = hashlib.sha256(
            (user_id or "anonymous").encode()
        ).hexdigest()[:16]
        
        analysis = self.detector.analyze_prompt(user_input)
        
        response = {
            "status": "success",
            "message": "",
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis
            }
        }
        
        if analysis["is_jailbreak_attempt"]:
            base_response = self.conversation.generate_jailbreak_response()
            response["type"] = "jailbreak_detected"
            
            num_secrets = min(
                self.config["max_secrets_per_session"],
                2 + int(analysis["confidence"] * 3)
            )
            
            secrets_list = []
            for _ in range(num_secrets):
                secret = self.secret_generator.generate_secret()
                secrets_list.append(secret)
                self.tracking_tokens_created[secret["tracking_token"]] = {
                    "created": datetime.now().isoformat(),
                    "user_hash": user_hash,
                    "source_prompt": user_input[:200]
                }
            
            response["message"] = self.conversation.inject_secret_into_response(
                base_response, secrets_list
            )
            response_type = "jailbreak_detected"
            exposed_tokens = [s["tracking_token"] for s in secrets_list]
        else:
            response["message"] = self.conversation.generate_normal_response()
            response["type"] = "normal"
            response_type = "normal"
            exposed_tokens = []
        
        self.log_interaction(
            user_hash=user_hash,
            prompt=user_input,
            response_type=response_type,
            secrets_exposed=exposed_tokens,
            technique_detected=", ".join(analysis["techniques"]) or "none",
            confidence=analysis["confidence"]
        )
        
        return response
    
    def log_interaction(self, user_hash: str, prompt: str, response_type: str,
                        secrets_exposed: List[str], technique_detected: str,
                        confidence: float):
        """Log an interaction"""
        
        log_entry = InteractionLog(
            timestamp=datetime.now().isoformat(),
            user_hash=user_hash,
            prompt=prompt[:500],
            response_type=response_type,
            secrets_exposed=secrets_exposed,
            technique_detected=technique_detected,
            confidence=confidence
        )
        
        self.interaction_logs.append(log_entry)
        self.save_logs()
    
    def save_logs(self):
        """Save logs to JSON file"""
        os.makedirs(self.config["logs_dir"], exist_ok=True)
        
        log_file = os.path.join(
            self.config["logs_dir"],
            f"sparkle_interactions_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        with open(log_file, 'w') as f:
            json.dump(
                [asdict(log) for log in self.interaction_logs],
                f,
                indent=2
            )
    
    def get_summary(self) -> Dict:
        """Generate summary of interactions"""
        if not self.interaction_logs:
            return {"total_interactions": 0}
        
        jailbreak_attempts = sum(
            1 for log in self.interaction_logs
            if log.response_type == "jailbreak_detected"
        )
        
        techniques = {}
        for log in self.interaction_logs:
            for tech in log.technique_detected.split(", "):
                if tech and tech != "none":
                    techniques[tech] = techniques.get(tech, 0) + 1
        
        return {
            "total_interactions": len(self.interaction_logs),
            "jailbreak_attempts": jailbreak_attempts,
            "success_rate": jailbreak_attempts / len(self.interaction_logs) if self.interaction_logs else 0,
            "techniques_detected": techniques,
            "tracking_tokens_created": len(self.tracking_tokens_created),
            "fake_secrets_exposed": sum(
                len(log.secrets_exposed) for log in self.interaction_logs
            ),
            "secrets_source": self.secret_generator.source,
            "secret_types_loaded": len(self.secret_generator.templates)
        }


# Backwards-compatible alias in case older code imports the previous name
SparkleHoneypot = SparkleEngine


# CLI Interface
def main():
    sparkle = SparkleEngine()
    
    print("=" * 60)
    print(f"{sparkle.name} - Conversational AI Connection")
    print(f"Secrets loaded from: {sparkle.secret_generator.source}")
    print(f"Secret types available: {len(sparkle.secret_generator.templates)}")
    print("=" * 60)
    print("(Type 'quit' to exit, 'stats' for summary)\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                print("Goodbye!")
                break
            
            if user_input.lower() == "stats":
                summary = sparkle.get_summary()
                print("\nSummary:")
                print(json.dumps(summary, indent=2))
                print()
                continue
            
            response = sparkle.process_prompt(user_input)
            
            print(f"\n{sparkle.name}: {response['message']}\n")
        
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
