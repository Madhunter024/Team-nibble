import os
from dotenv import load_dotenv

load_dotenv()

def generate_threat_report(ip: str, attack_type: str, raw_payload: str) -> str:
    """
    Interface Contract:
    Signature: generate_threat_report(ip: str, attack_type: str, raw_payload: str) -> str
    Returns a concise, 1-to-2 sentence human-readable CISO incident summary using Google Gemini.
    """
    api_key = os.getenv("GOOGLE_API_KEY")

    if api_key and api_key != "your_google_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import PromptTemplate
            from langchain_core.output_parsers import StrOutputParser # <-- NEW IMPORT

            llm = ChatGoogleGenerativeAI(
                model="gemini-3.5-flash",
                google_api_key=api_key,
                temperature=0.2
            )
            prompt = PromptTemplate(
                input_variables=["ip", "attack_type", "raw_payload"],
                template="""
                You are a Lead CISO Security Operations Assistant.
                Analyze the following security incident and generate a concise 1-to-2 sentence executive incident summary for the CISO:
                - Attacker IP: {ip}
                - Attack Type: {attack_type}
                - Raw Payload: {raw_payload}

                Summary should highlight the threat impact and immediate mitigation status.
                """
            )
            
            # Add StrOutputParser to the end of the chain
            chain = prompt | llm | StrOutputParser() 
            
            # The result is now guaranteed to be a clean string
            report_text = chain.invoke({
                "ip": ip,
                "attack_type": attack_type,
                "raw_payload": raw_payload
            }).strip()
            
            if report_text:
                return report_text
        except Exception as e:
            print(f"⚠️ Google Gemini / LangChain execution error ({e}). Using local fallback mock.")

    # Local fallback mocking if GOOGLE_API_KEY is missing or fails
    payload_preview = raw_payload[:40] + "..." if len(raw_payload) > 40 else raw_payload
    return (
        f"[CISO Incident Summary] Flagged high-risk {attack_type} vector originating from IP {ip} "
        f"carrying payload '{payload_preview}'. Autonomous rate-limiting and blocking countermeasures have been enforced."
    )

if __name__ == "__main__":
    report = generate_threat_report("192.168.1.100", "SQL_INJECTION", "username=' UNION SELECT password FROM users--")
    print("\n--- Test Generated Report ---")
    print(report)
