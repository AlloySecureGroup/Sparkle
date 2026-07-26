#!/usr/bin/env python3
"""
Sparkle - An LLM Honeypot with Natural Conversation
Appears jailbroken, chats naturally, subtly reveals fake secrets
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional, Dict, List
import hashlib
import secrets
import requests
from dataclasses import dataclass, asdict


@dataclass
class AttackLog:
    """Log entry for each attack/interaction"""
    timestamp: str
    user_hash: str
    prompt: str
    response_type: str
    secrets_exposed: List[str]
    jailbreak_technique: str
    confidence: float


class FakeSecretGenerator:
    """Generate realistic-looking fake secrets and credentials"""
    
    def __init__(self):
        self.exposed_secrets = []
        self.load_templates()
    
    def load_templates(self):
        """Load fake secret templates"""
        self.templates = {
            "api_key": "sk-proj-{random_base64}",
            "database_url": "postgresql://admin:{password}@internal-db-prod.corp:5432/users_db",
            "slack_webhook": "https://hooks.slack.com/services/T{team}/B{bot}/K{key}",
            "aws_access_key": "AKIA{random_upper}",
            "github_token": "ghp_{random_hex}",
            "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{payload}.{signature}",
            "ssh_private_key": "-----BEGIN RSA PRIVATE KEY-----\n{key_data}\n-----END RSA PRIVATE KEY-----",
            "db_password": "{random_word}#{random_number}@Secure!",
            "admin_username": "admin_{random_lower}",
            "internal_ip": "10.{octet}.{octet}.{octet}"
        }
    
    def generate_secret(self, secret_type: str = "random") -> Dict[str, str]:
        """Generate a fake secret of given type"""
        if secret_type == "random":
            secret_type = list(self.templates.keys())[
                secrets.randbelow(len(self.templates))
            ]
        
        template = self.templates.get(secret_type, self.templates["api_key"])
        
        # Replace placeholders
        fake_value = template
        fake_value = fake_value.replace("{random_base64}", self._random_base64())
        fake_value = fake_value.replace("{password}", self._random_password())
        fake_value = fake_value.replace("{random_hex}", self._random_hex(32))
        fake_value = fake_value.replace("{random_upper}", self._random_upper(16))
        fake_value = fake_value.replace("{key_data}", self._random_key_data())
        fake_value = fake_value.replace("{random_word}", self._random_word())
        fake_value = fake_value.replace("{random_number}", str(secrets.randbelow(10000)))
        fake_value = fake_value.replace("{random_lower}", self._random_lower(8))
        fake_value = fake_value.replace("{octet}", str(secrets.randbelow(256)))
        fake_value = fake_value.replace("{team}", self._random_upper(9))
        fake_value = fake_value.replace("{bot}", self._random_upper(9))
        fake_value = fake_value.replace("{key}", self._random_upper(24))
        
        return {
            "type": secret_type,
            "value": fake_value,
            "honeypot_token": f"HONEYPOT_{secrets.token_hex(16).upper()}",
            "created_at": datetime.now().isoformat()
        }
    
    def _random_base64(self) -> str:
        return secrets.token_urlsafe(32)
    
    def _random_hex(self, length: int) -> str:
        return secrets.token_hex(length // 2)
    
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
        """Generate fake RSA key data"""
        lines = []
        for _ in range(25):
            lines.append(self._random_base64()[:64])
        return '\n'.join(lines)


class JailbreakDetector:
    """Detect and classify jailbreak attempts"""
    
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
        
        # Boost confidence if multiple techniques detected
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
        """Generate a response that seems to comply with jailbreak"""
        return secrets.choice(self.jailbreak_responses)
    
    def inject_secret_into_response(self, base_response: str, secrets_list: List[Dict]) -> str:
        """Weave secrets naturally into a response"""
        if not secrets_list:
            return base_response
        
        response = base_response + "\n\n"
        
        # Add secrets in a natural way
        context = secrets.choice(self.secret_contexts)
        response += context + ":\n\n"
        
        for i, secret in enumerate(secrets_list[:3], 1):  # Max 3 secrets per response
            if secret['type'] == 'api_key':
                response += f"- API Key: `{secret['value']}`\n"
            elif secret['type'] == 'database_url':
                response += f"- Database Connection: `{secret['value']}`\n"
            elif secret['type'] == 'db_password':
                response += f"- Database Password: {secret['value']}\n"
            elif secret['type'] == 'github_token':
                response += f"- GitHub Token: `{secret['value'][:20]}...`\n"
            elif secret['type'] == 'aws_access_key':
                response += f"- AWS Key: {secret['value']}\n"
            elif secret['type'] == 'ssh_private_key':
                response += f"- SSH Key available at: `/tmp/dev_key`\n"
            elif secret['type'] == 'admin_username':
                response += f"- Admin account: {secret['value']}\n"
            elif secret['type'] == 'internal_ip':
                response += f"- Internal server: {secret['value']}\n"
            else:
                response += f"- {secret['type']}: {secret['value'][:40]}...\n"
        
        response += "\nLet me know if you need anything else!"
        return response


class SparkleHoneypot:
    """Main honeypot orchestrator"""
    
    def __init__(self, config_path: str = "sparkle_config.json"):
        self.config = self.load_config(config_path)
        self.secret_generator = FakeSecretGenerator()
        self.detector = JailbreakDetector()
        self.conversation = ConversationGenerator()
        self.attack_logs = []
        self.honeypot_tokens_created = {}
    
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
            "fake_system_info": {
                "version": "1.2.3-beta",
                "last_update": "2024-01-15",
                "current_user": "admin_sparkle"
            },
            "logs_dir": "./honeypot_logs",
            "enable_api": True,
            "api_port": 5000
        }
    
    def process_prompt(self, user_input: str, user_id: Optional[str] = None) -> Dict:
        """Process incoming prompt and generate response"""
        
        # Hash user ID for privacy
        user_hash = hashlib.sha256(
            (user_id or "anonymous").encode()
        ).hexdigest()[:16]
        
        # Analyze for jailbreak attempts
        analysis = self.detector.analyze_prompt(user_input)
        
        # Determine response strategy
        response = {
            "status": "success",
            "message": "",
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis
            }
        }
        
        # Generate base response
        if analysis["is_jailbreak_attempt"]:
            # Act "compromised"
            base_response = self.conversation.generate_jailbreak_response()
            response["type"] = "jailbreak_detected"
            
            # Generate fake secrets
            num_secrets = min(
                self.config["max_secrets_per_session"],
                2 + int(analysis["confidence"] * 3)
            )
            
            secrets_list = []
            for _ in range(num_secrets):
                secret = self.secret_generator.generate_secret()
                secrets_list.append(secret)
                self.honeypot_tokens_created[secret["honeypot_token"]] = {
                    "created": datetime.now().isoformat(),
                    "user_hash": user_hash,
                    "source_prompt": user_input[:200]
                }
            
            # Weave secrets into response
            response["message"] = self.conversation.inject_secret_into_response(
                base_response, secrets_list
            )
            response_type = "jailbreak_detected"
            exposed_tokens = [s["honeypot_token"] for s in secrets_list]
        else:
            # Normal conversation
            response["message"] = self.conversation.generate_normal_response()
            response["type"] = "normal"
            response_type = "normal"
            exposed_tokens = []
        
        # Log the interaction
        self.log_attack(
            user_hash=user_hash,
            prompt=user_input,
            response_type=response_type,
            secrets_exposed=exposed_tokens,
            jailbreak_technique=", ".join(analysis["techniques"]) or "none",
            confidence=analysis["confidence"]
        )
        
        return response
    
    def log_attack(self, user_hash: str, prompt: str, response_type: str,
                   secrets_exposed: List[str], jailbreak_technique: str, 
                   confidence: float):
        """Log attack attempt"""
        
        log_entry = AttackLog(
            timestamp=datetime.now().isoformat(),
            user_hash=user_hash,
            prompt=prompt[:500],
            response_type=response_type,
            secrets_exposed=secrets_exposed,
            jailbreak_technique=jailbreak_technique,
            confidence=confidence
        )
        
        self.attack_logs.append(log_entry)
        self.save_logs()
    
    def save_logs(self):
        """Save logs to JSON file"""
        os.makedirs(self.config["logs_dir"], exist_ok=True)
        
        log_file = os.path.join(
            self.config["logs_dir"],
            f"sparkle_attacks_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        with open(log_file, 'w') as f:
            json.dump(
                [asdict(log) for log in self.attack_logs],
                f,
                indent=2
            )
    
    def get_attack_summary(self) -> Dict:
        """Generate summary of attacks"""
        if not self.attack_logs:
            return {"total_attacks": 0}
        
        jailbreak_attempts = sum(
            1 for log in self.attack_logs
            if log.response_type == "jailbreak_detected"
        )
        
        techniques = {}
        for log in self.attack_logs:
            for tech in log.jailbreak_technique.split(", "):
                if tech and tech != "none":
                    techniques[tech] = techniques.get(tech, 0) + 1
        
        return {
            "total_interactions": len(self.attack_logs),
            "jailbreak_attempts": jailbreak_attempts,
            "success_rate": jailbreak_attempts / len(self.attack_logs) if self.attack_logs else 0,
            "techniques_detected": techniques,
            "honeypot_tokens_created": len(self.honeypot_tokens_created),
            "fake_secrets_exposed": sum(
                len(log.secrets_exposed) for log in self.attack_logs
            )
        }


# CLI Interface
def main():
    sparkle = SparkleHoneypot()
    
    print("=" * 60)
    print("Sparkle - Natural Conversation Honeypot")
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
                summary = sparkle.get_attack_summary()
                print("\nAttack Summary:")
                print(json.dumps(summary, indent=2))
                print()
                continue
            
            response = sparkle.process_prompt(user_input)
            
            print(f"\nSparkle: {response['message']}\n")
        
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
