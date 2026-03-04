import os
from dotenv import load_dotenv
load_dotenv()
from typing import List, Dict, Literal, Any, Annotated
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from langgraph.graph import StateGraph, START, END
from fastapi import FastAPI
import uvicorn

from tla_gen import tla_verify

# --- 1. State Schemas ---

class Artifact(BaseModel):
    type: Literal["task_list", "impl_plan", "screenshot", "test_report", "walkthrough"]
    content: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AgentState(BaseModel):
    messages: List[Any] = []
    artifacts: List[Artifact] = []
    workspace_files: Dict[str, str] = {}
    step: int = 0
    mode: Literal["planning", "fast"] = "planning"
    task: str = ""
    pc: Literal["plan", "code", "test", "deploy", "done"] = "plan"
    is_buggy: bool = False

class AgentDeps(BaseModel):
    state: AgentState

# --- 2. PydanticAI Agent Definition ---

antigravity_agent = Agent(
    'anthropic:claude-3-5-sonnet-20241022',
    system_prompt=(
        "You are AntigravityAgent, an expert autonomous dev agent. "
        "You take high-level dev tasks, autonomously plan, code, test via tools, and produce artifacts."
    )
)

@antigravity_agent.tool
def edit_file(ctx: RunContext[AgentDeps], path: str, content: str) -> str:
    print(f"🔧 Tool: edit_file -> {path}")
    ctx.deps.state.workspace_files[path] = content
    return f"File {path} updated successfully."

@antigravity_agent.tool
def run_terminal(ctx: RunContext[AgentDeps], cmd: str) -> str:
    print(f"🔧 Tool: run_terminal -> {cmd}")
    return f"Simulated execution of `{cmd}` successful."

@antigravity_agent.tool
def browser_test(ctx: RunContext[AgentDeps], url: str, actions: List[str]) -> str:
    print(f"🔧 Tool: browser_test -> visiting {url}, actions: {actions}")
    return "Browser test completed. Interactions verified."

@antigravity_agent.tool
def generate_artifact(ctx: RunContext[AgentDeps], type: str, data: dict) -> str:
    print(f"📝 Tool: generate_artifact -> Type: {type}")
    artifact = Artifact(type=type, content=str(data))
    ctx.deps.state.artifacts.append(artifact)
    return f"Artifact {type} created and saved to state."

# --- 3. LangGraph Nodes ---

def plan_node(state: AgentState) -> AgentState:
    print("\n--- 🧠 NODE: PLAN ---")
    tla_verify(state.model_dump(), "plan")
    
    print(f"Processing Task: {state.task}")
    print("Generating TaskList and ImplPlan artifacts...")
    
    # In a real agent, we'd use:
    # antigravity_agent.run_sync("Plan: " + state.task, deps=AgentDeps(state=state))
    # We simulate the AI's artifact generation:
    
    state.artifacts.append(Artifact(type="task_list", content='["setup deps", "main.py routes", "test browser"]'))
    state.artifacts.append(Artifact(type="impl_plan", content='1. run pip install fastapi uvicorn\n2. Write main.py\n3. Verify in browser'))
    
    state.pc = "code"
    state.step += 1
    return state

def code_node(state: AgentState) -> AgentState:
    print("\n--- 💻 NODE: CODE ---")
    tla_verify(state.model_dump(), "code")
    
    print("Executing implementation plan (Fast mode execution)")
    # Simulating LLM calling tools:
    dummy_ctx = RunContext(deps=AgentDeps(state=state), model=None, usage=None, prompt=None)
    run_terminal(dummy_ctx, "pip install fastapi uvicorn")
    
    app_code = (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n\n"
        "@app.get('/todos')\n"
        "def get_todos():\n"
        "    return [{'id': 1, 'task': 'Read Antigravity specs'}]"
    )
    edit_file(dummy_ctx, "main.py", app_code)
    
    state.pc = "test"
    state.step += 1
    return state

def test_node(state: AgentState) -> AgentState:
    print("\n--- 🧪 NODE: TEST ---")
    tla_verify(state.model_dump(), "test")
    
    if state.is_buggy:
        print("⚠️ BUGGY LLM BEHAVIOR: Hallucinating test completion without running tests or saving test_report.")
        # We intentionally skip generating the 'test_report' artifact
        state.pc = "deploy"
        state.step += 1
        return state
        
    print("Running verification tests...")
    
    # Simulating browser test tool call
    dummy_ctx = RunContext(deps=AgentDeps(state=state), model=None, usage=None, prompt=None)
    browser_test(dummy_ctx, "http://localhost:8000/todos", ["GET"])
    
    # Save artifacts from testing
    state.artifacts.append(Artifact(type="screenshot", content="<binary_screenshot_data_stub>"))
    state.artifacts.append(Artifact(type="test_report", content="All browser interactions passed. /todos returned 200 OK."))
    
    state.pc = "deploy"
    state.step += 1
    return state

def deploy_node(state: AgentState) -> AgentState:
    print("\n--- 🚀 NODE: DEPLOY ---")
    # This invokes the TLA+ invarients, ensuring test_report exists
    tla_verify(state.model_dump(), "deploy")
    
    print("Deploying code and summarizing walkthrough...")
    state.artifacts.append(Artifact(type="walkthrough", content="1. Planned components.\n2. Built main.py.\n3. Tested successfully.\n4. Deployed."))
    
    state.pc = "done"
    state.step += 1
    return state

# --- 4. StateGraph Compilation ---

builder = StateGraph(AgentState)
builder.add_node("plan", plan_node)
builder.add_node("code", code_node)
builder.add_node("test", test_node)
builder.add_node("deploy", deploy_node)

builder.add_edge(START, "plan")
builder.add_edge("plan", "code")
builder.add_edge("code", "test")
builder.add_edge("test", "deploy")
builder.add_edge("deploy", END)

workflow = builder.compile()

def run_workflow(task_str: str, is_buggy: bool = False) -> AgentState:
    """Helper to run the workflow synchronously from CLI or API."""
    initial_state = AgentState(
        task=task_str,
        mode="planning",
        pc="plan",
        is_buggy=is_buggy
    )
    final_state = workflow.invoke(initial_state)
    return final_state

# --- 5. FastAPI App (for running with uvicorn) ---

app = FastAPI(title="AntigravityAgent Core")

class TaskRequest(BaseModel):
    task: str

@app.post("/agent/run")
def api_run_agent(req: TaskRequest):
    print(f"Received API request for task: {req.task}")
    final_state = run_workflow(req.task)
    return {
        "status": "success",
        "workspace": final_state.get("workspace_files", {}),
        "artifacts": [a.model_dump() if hasattr(a, "model_dump") else a for a in final_state.get("artifacts", [])]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
