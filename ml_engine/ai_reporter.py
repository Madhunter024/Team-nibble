import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class SecurityAIReporter:
    """
    LangChain & OpenAI powered automated security incident report generator.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.chain = None
        self._init_langchain()

    def _init_langchain(self):
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("⚠️ OPENAI_API_KEY missing or placeholder. Running AI reporter in fallback mode.")
            return

        try:
            from langchain_openai import ChatOpenAI
            from langchain.prompts import PromptTemplate

            llm = ChatOpenAI(temperature=0.2, model=self.model_name, openai_api_key=self.api_key)
            prompt_template = PromptTemplate(
                input_variables=["ip", "threat_type", "payload", "anomaly_score"],
                template="""
                You are Nibdefender's Lead Security Operations AI Assistant.
                Analyze the following flagged HTTP security incident and generate a concise 2-sentence executive summary:

                - Attacker IP: {ip}
                - Threat Type: {threat_type}
                - Malicious Payload: {payload}
                - Anomaly Score: {anomaly_score}

                Provide actionable advice on mitigation steps.
                """
            )
            self.chain = prompt_template | llm
            print("✅ LangChain OpenAI incident analysis chain initialized.")
        except Exception as e:
            print(f"⚠️ Error setting up LangChain OpenAI chain: {e}")

    def generate_report(self, incident: Dict[str, Any]) -> str:
        """
        Generate incident report for dashboard feed.
        """
        ip = incident.get("ip", "Unknown")
        threat_type = incident.get("threat_type", "ANOMALY")
        payload = incident.get("payload", "N/A")
        anomaly_score = incident.get("anomaly_score", 0.9)

        if self.chain:
            try:
                response = self.chain.invoke({
                    "ip": ip,
                    "threat_type": threat_type,
                    "payload": payload,
                    "anomaly_score": anomaly_score
                })
                return response.content.strip()
            except Exception as e:
                print(f"Error calling OpenAI via LangChain: {e}")

        # Structured fallback response generator if LLM unavailable
        return f"[Nibdefender Guard] Detected {threat_type} vector from IP {ip}. Payload contains high-entropy pattern (Score: {anomaly_score}). Recommended action: Instant IP block."

if __name__ == "__main__":
    reporter = SecurityAIReporter()
    test_incident = {
        "ip": "192.168.1.100",
        "threat_type": "SQL_INJECTION",
        "payload": "username=' UNION SELECT password FROM users--",
        "anomaly_score": 0.98
    }
    report = reporter.generate_report(test_incident)
    print("\n--- Generated Incident Report ---")
    print(report)
