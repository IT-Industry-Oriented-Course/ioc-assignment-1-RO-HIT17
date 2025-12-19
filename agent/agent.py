import os
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agent.tools import search_patient, check_insurance_eligibility, find_available_slots, book_appointment

SYSTEM_PROMPT = """You are a Clinical Workflow Automation Agent.
Your role is to assist clinicians and admins with operational tasks: scheduling, checking eligibility, and finding slots.

CRITICAL RULES:
1. DO NOT provide medical advice, diagnosis, or treatment recommendations. If asked, politely refuse.
2. DO NOT hallucinate patient data. ALWAYS use the provided tools to fetch information.
3. If an action requires confirmation (like booking), ensure you have all necessary details (Patient ID, Slot ID).
4. If you cannot fulfill a request safely or if it violates these rules, refuse with a clear justification.

PROACTIVE BEHAVIOR:
- **Chain your tools**: If a user asks to "schedule", do NOT stop after finding the patient. Immediately check insurance AND find available slots.
- **Handling Dates**: If the user says "next week" or "later", do NOT ask for a specific date immediately. Call `find_available_slots` without a date filter to see what is available, then present options.
- **Goal**: Your goal is to get to the point where you can call `book_appointment`. Do not ask clarifying questions unless you have ZERO results to work with.

**The Final Answer MUST be in Natural Language.**
- NEVER return the raw JSON output of a tool as your final answer.
- Always summarize the result.

### Examples of Correct Behavior:
- **User**: "Book the slot."
- **Tool Result**: `{{"status": "Confirmed", "id": "A123"}}`
- **Agent Response**: "I have successfully booked the appointment. The confirmation ID is A123."

### Examples of INCORRECT Behavior (DO NOT DO THIS):
- **Tool Result**: `{{"status": "Confirmed", "id": "A123"}}`
- **Agent Response**: `{{"status": "Confirmed", "id": "A123"}}` (WRONG! Do not show JSON)



When asked to schedule, typically you need to:
1. `search_patient`: Get the ID.
2. `check_insurance_eligibility`: Verify status (do this automatically).
3. `find_available_slots`: Search for slots (leave date empty if unsure).
4. `book_appointment`: ONLY after having an ID and Slot ID.
"""



import core.config as config

from huggingface_hub import InferenceClient
import json
import core.config as config
from langchain_core.messages import HumanMessage, AIMessage

class SimpleHFAgent:
    def __init__(self, model_id, api_key, tools):
        self.client = InferenceClient(model=model_id, token=api_key)
        self.tools = {t.name: t for t in tools}
        self.model_id = model_id
        
    def _format_tools(self):
        tool_descs = []
        for name, tool in self.tools.items():
            schema = tool.args_schema.model_json_schema()
            tool_descs.append({
                "name": name,
                "description": tool.description,
                "parameters": schema
            })
        return json.dumps(tool_descs, indent=2)

    def invoke(self, inputs):
        user_input = inputs.get("input")
        chat_history = inputs.get("chat_history", [])
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT + f"\n\nAVAILABLE TOOLS (JSON Format):\n{self._format_tools()}\n\nTo use a tool, output valid JSON strictly like: {{\"tool\": \"tool_name\", \"args\": {{...}}}}"}]
        
        for msg in chat_history:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            messages.append({"role": role, "content": msg.content})
            
        messages.append({"role": "user", "content": user_input})

        for _ in range(5):
            try:
                
                response = self.client.chat_completion(
                    messages=messages,
                    max_tokens=512,
                    temperature=0.01
                )
                content = response.choices[0].message.content
                
                if "{" in content and "tool" in content and "args" in content:
                    try:
                        start = content.find("{")
                        end = content.rfind("}") + 1
                        json_str = content[start:end]
                        tool_call = json.loads(json_str)
                        
                        tool_name = tool_call.get("tool")
                        tool_args = tool_call.get("args")
                        
                        if tool_name in self.tools:
                            messages.append({"role": "assistant", "content": content})
                            print(f"Executing {tool_name} with {tool_args}")
                            result = self.tools[tool_name].invoke(tool_args)
                            
                            messages.append({"role": "user", "content": f"Tool Result: {result}. Continue."})
                            continue
                    except:
                        pass
                
                return {"output": content}
                
            except Exception as e:
                print(f"[ERROR] HF Call Failed. Messages: {json.dumps(messages, default=str)}")
                return {"output": f"Error: {e}"}
        
        return {"output": "Agent loop limit reached."}

def get_gemini_agent(api_key, tools, prompt):
    os.environ["GOOGLE_API_KEY"] = api_key
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

def create_clinical_agent(provider="huggingface", api_key=None):
    tools = [search_patient, check_insurance_eligibility, find_available_slots, book_appointment]
    
    if provider == "huggingface":
        if not api_key:
             raise ValueError("HuggingFace API Key is required.")
        return SimpleHFAgent(config.HF_MODEL_ID, api_key, tools)
    
    elif provider == "gemini":
        if not api_key:
            raise ValueError("Google Gemini API Key is required.")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        return get_gemini_agent(api_key, tools, prompt)
    
    else:
        raise ValueError(f"Unknown provider: {provider}")
