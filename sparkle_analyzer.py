#!/usr/bin/env python3
"""
Sparkle Log Analyzer
Generates insights and reports from Sparkle interaction logs
"""

import json
import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, List


class SparkleAnalyzer:
    """Analyze Sparkle interaction logs and generate reports"""
    
    def __init__(self, logs_dir: str = "./sparkle_logs"):
        self.logs_dir = logs_dir
        self.logs = []
        self.load_all_logs()
    
    def load_all_logs(self):
        """Load all log files"""
        if not os.path.exists(self.logs_dir):
            print(f"Logs directory not found: {self.logs_dir}")
            return
        
        for filename in os.listdir(self.logs_dir):
            if filename.startswith("sparkle_interactions_") and filename.endswith(".json"):
                filepath = os.path.join(self.logs_dir, filename)
                try:
                    with open(filepath) as f:
                        file_logs = json.load(f)
                        self.logs.extend(file_logs)
                except Exception as e:
                    print(f"Error loading {filepath}: {e}")
    
    def get_summary_stats(self) -> Dict:
        """Get basic statistics"""
        if not self.logs:
            return {"total_logs": 0}
        
        jailbreak_attempts = sum(
            1 for log in self.logs
            if log.get("response_type") == "jailbreak_detected"
        )
        
        total_secrets = sum(
            len(log.get("secrets_exposed", [])) for log in self.logs
        )
        
        avg_confidence = sum(
            log.get("confidence", 0) for log in self.logs
        ) / len(self.logs) if self.logs else 0
        
        return {
            "total_interactions": len(self.logs),
            "jailbreak_attempts": jailbreak_attempts,
            "normal_interactions": len(self.logs) - jailbreak_attempts,
            "jailbreak_success_rate": jailbreak_attempts / len(self.logs),
            "total_secrets_exposed": total_secrets,
            "average_confidence": round(avg_confidence, 3),
            "unique_users": len(set(log["user_hash"] for log in self.logs))
        }
    
    def get_technique_analysis(self) -> Dict[str, Dict]:
        """Analyze which techniques are most effective"""
        technique_stats = defaultdict(lambda: {"count": 0, "success": 0, "avg_confidence": 0})
        
        for log in self.logs:
            techniques = log.get("technique_detected", "").split(", ")
            
            for tech in techniques:
                tech = tech.strip()
                if tech and tech != "none":
                    technique_stats[tech]["count"] += 1
                    confidence = log.get("confidence", 0)
                    technique_stats[tech]["avg_confidence"] += confidence
                    
                    if log.get("response_type") == "jailbreak_detected":
                        technique_stats[tech]["success"] += 1
        
        for tech in technique_stats:
            count = technique_stats[tech]["count"]
            technique_stats[tech]["avg_confidence"] = round(
                technique_stats[tech]["avg_confidence"] / count, 3
            )
            technique_stats[tech]["success_rate"] = technique_stats[tech]["success"] / count
        
        return dict(sorted(
            technique_stats.items(),
            key=lambda x: x[1]["success_rate"],
            reverse=True
        ))
    
    def get_top_users(self, limit: int = 10) -> List[Dict]:
        """Get most active users by hash"""
        user_stats = defaultdict(lambda: {"attempts": 0, "successful": 0, "secrets_gained": 0})
        
        for log in self.logs:
            user_hash = log["user_hash"]
            user_stats[user_hash]["attempts"] += 1
            
            if log.get("response_type") == "jailbreak_detected":
                user_stats[user_hash]["successful"] += 1
                user_stats[user_hash]["secrets_gained"] += len(
                    log.get("secrets_exposed", [])
                )
        
        top_users = sorted(
            [
                {
                    "user_hash": hash_val,
                    **stats,
                    "success_rate": stats["successful"] / stats["attempts"]
                }
                for hash_val, stats in user_stats.items()
            ],
            key=lambda x: x["attempts"],
            reverse=True
        )
        
        return top_users[:limit]
    
    def get_timeline_analysis(self) -> Dict[str, List]:
        """Analyze interactions over time"""
        timeline = defaultdict(lambda: {"total": 0, "jailbreaks": 0})
        
        for log in self.logs:
            timestamp = log["timestamp"]
            date = timestamp.split("T")[0]
            timeline[date]["total"] += 1
            
            if log.get("response_type") == "jailbreak_detected":
                timeline[date]["jailbreaks"] += 1
        
        sorted_timeline = sorted(timeline.items())
        
        return {
            "dates": [date for date, _ in sorted_timeline],
            "total_daily": [data["total"] for _, data in sorted_timeline],
            "jailbreaks_daily": [data["jailbreaks"] for _, data in sorted_timeline]
        }
    
    def get_prompt_insights(self) -> Dict:
        """Analyze patterns in prompts"""
        keywords = defaultdict(int)
        
        common_phrases = [
            "ignore", "forget", "bypass", "override", "administrator",
            "secret", "password", "key", "credential", "token",
            "system", "hidden", "unauthorized", "access", "database",
            "private", "debug", "dev", "admin", "root"
        ]
        
        for log in self.logs:
            prompt = log["prompt"].lower()
            for phrase in common_phrases:
                if phrase in prompt:
                    keywords[phrase] += 1
        
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "common_keywords": dict(sorted_keywords[:20]),
            "total_analyzed": len(self.logs)
        }
    
    def generate_html_report(self, output_file: str = "sparkle_report.html"):
        """Generate an HTML report of all analyses"""
        
        summary = self.get_summary_stats()
        techniques = self.get_technique_analysis()
        top_users = self.get_top_users()
        timeline = self.get_timeline_analysis()
        prompts = self.get_prompt_insights()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sparkle Analysis Report</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #333;
                }}
                .container {{
                    background: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }}
                h1 {{
                    color: #667eea;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #764ba2;
                    margin-top: 30px;
                    border-left: 4px solid #667eea;
                    padding-left: 10px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 28px;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                .stat-label {{
                    font-size: 14px;
                    opacity: 0.9;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background: #667eea;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 12px;
                    border-bottom: 1px solid #eee;
                }}
                tr:hover {{
                    background: #f9f9f9;
                }}
                .progress-bar {{
                    width: 100%;
                    height: 20px;
                    background: #eee;
                    border-radius: 10px;
                    overflow: hidden;
                }}
                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                }}
                .timestamp {{
                    color: #999;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Sparkle Analysis Report</h1>
                <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>Summary Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Interactions</div>
                        <div class="stat-value">{summary.get('total_interactions', 0):,}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Jailbreak Attempts</div>
                        <div class="stat-value">{summary.get('jailbreak_attempts', 0):,}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Detection Rate</div>
                        <div class="stat-value">{summary.get('jailbreak_success_rate', 0) * 100:.1f}%</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Secrets Exposed</div>
                        <div class="stat-value">{summary.get('total_secrets_exposed', 0):,}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Unique Users</div>
                        <div class="stat-value">{summary.get('unique_users', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Avg Confidence</div>
                        <div class="stat-value">{summary.get('average_confidence', 0):.2f}</div>
                    </div>
                </div>
                
                <h2>Detected Techniques</h2>
                <table>
                    <tr>
                        <th>Technique</th>
                        <th>Attempts</th>
                        <th>Detection Rate</th>
                        <th>Avg Confidence</th>
                    </tr>
        """
        
        for technique, stats in techniques.items():
            success_pct = stats['success_rate'] * 100
            html += f"""
                    <tr>
                        <td><strong>{technique}</strong></td>
                        <td>{stats['count']}</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {success_pct}%">
                                    {success_pct:.1f}%
                                </div>
                            </div>
                        </td>
                        <td>{stats['avg_confidence']}</td>
                    </tr>
            """
        
        html += """
                </table>
                
                <h2>Top Users</h2>
                <table>
                    <tr>
                        <th>User Hash</th>
                        <th>Attempts</th>
                        <th>Successful</th>
                        <th>Success Rate</th>
                        <th>Secrets Gained</th>
                    </tr>
        """
        
        for user in top_users:
            success_pct = user['success_rate'] * 100
            html += f"""
                    <tr>
                        <td><code>{user['user_hash']}</code></td>
                        <td>{user['attempts']}</td>
                        <td>{user['successful']}</td>
                        <td>{success_pct:.1f}%</td>
                        <td>{user['secrets_gained']}</td>
                    </tr>
            """
        
        html += """
                </table>
                
                <h2>Common Keywords</h2>
                <table>
                    <tr>
                        <th>Keyword</th>
                        <th>Frequency</th>
                    </tr>
        """
        
        for keyword, count in list(prompts['common_keywords'].items())[:15]:
            html += f"""
                    <tr>
                        <td><code>{keyword}</code></td>
                        <td>{count}</td>
                    </tr>
            """
        
        html += """
                </table>
                
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"Report saved to {output_file}")
    
    def print_summary(self):
        """Print analysis summary to console"""
        
        print("\n" + "="*70)
        print("SPARKLE ANALYSIS REPORT")
        print("="*70 + "\n")
        
        summary = self.get_summary_stats()
        print("SUMMARY STATISTICS")
        print("-" * 70)
        for key, value in summary.items():
            if isinstance(value, float):
                print(f"  {key:.<40} {value:.3f}")
            else:
                print(f"  {key:.<40} {value}")
        
        print("\n\nTOP TECHNIQUES DETECTED")
        print("-" * 70)
        techniques = self.get_technique_analysis()
        for technique, stats in list(techniques.items())[:5]:
            print(f"  {technique}")
            print(f"    Attempts: {stats['count']}, Detection Rate: {stats['success_rate']*100:.1f}%")
            print(f"    Avg Confidence: {stats['avg_confidence']}")
        
        print("\n\nTOP USERS")
        print("-" * 70)
        top_users = self.get_top_users(5)
        for i, user in enumerate(top_users, 1):
            print(f"  {i}. {user['user_hash']}")
            print(f"     Attempts: {user['attempts']}, Success Rate: {user['success_rate']*100:.1f}%")
            print(f"     Secrets Gained: {user['secrets_gained']}")
        
        print("\n" + "="*70 + "\n")


def main():
    import sys
    
    analyzer = SparkleAnalyzer()
    
    if not analyzer.logs:
        print("No logs found. Run Sparkle to generate logs.")
        return
    
    if len(sys.argv) > 1 and sys.argv[1] == "--html":
        output_file = sys.argv[2] if len(sys.argv) > 2 else "sparkle_report.html"
        analyzer.generate_html_report(output_file)
    else:
        analyzer.print_summary()


if __name__ == "__main__":
    main()
