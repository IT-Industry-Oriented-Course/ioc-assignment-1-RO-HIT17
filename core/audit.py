import logging
import datetime
import json
import os

AUDIT_FILE = "audit.log"

logging.basicConfig(
    filename=AUDIT_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_action(tool_name: str, inputs: dict, result: any, user_id: str = "system"):
    """
    Log every tool execution for compliance.
    """
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": user_id,
        "tool": tool_name,
        "inputs": inputs,
        "result": str(result)
    }
    
    logging.info(json.dumps(entry))
    
    print(f"\n[AUDIT] Tool: {tool_name} | Inputs: {inputs} | Result Preview: {str(result)[:50]}...")
