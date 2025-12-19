import sys
import os
import core.config as config
from agent.agent import create_clinical_agent

def main():
    print("=== Clinical Workflow Automation Agent ===")
    print("Type 'exit' or 'quit' to stop.")
    
    provider = input("Select LLM Provider (huggingface/gemini) [default: huggingface]: ").strip().lower() or "huggingface"
    env_var = "HUGGINGFACEHUB_API_TOKEN" if provider == "huggingface" else "GOOGLE_API_KEY"
    
    api_key = os.environ.get(env_var)
    if not api_key:
        api_key = input(f"Enter your {provider} API Key: ").strip()
    
    dry_run_input = input("Enable Dry Run mode? (yes/no) [default: no]: ").strip().lower()
    if dry_run_input in ["yes", "y", "true"]:
        config.DRY_RUN = True
        print("[INFO] DRY RUN MODE ENABLED. No data will be modified.")
    
    try:
        agent_executor = create_clinical_agent(provider, api_key)
        print("\nAgent initialized successfully! Ask me to schedule appointments or check patient status.")
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize agent: {e}")
        return

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            response = agent_executor.invoke({"input": user_input})
            print("\nAgent:", response['output'])
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
