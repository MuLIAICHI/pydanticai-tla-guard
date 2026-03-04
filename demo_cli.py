import sys
from app import run_workflow

def main():
    if len(sys.argv) < 2:
        print("Usage: python demo_cli.py \"<task_description>\" [--buggy]")
        print("Example: python demo_cli.py \"Build minimal FastAPI todo app\"")
        print("         python demo_cli.py \"Build minimal FastAPI todo app\" --buggy")
        sys.exit(1)
        
    args = sys.argv[1:]
    is_buggy = False
    
    if "--buggy" in args:
        is_buggy = True
        args.remove("--buggy")
        
    task_description = " ".join(args)
    print("==========================================")
    print(f"🤖 AntigravityAgent (CLI) initialized")
    mode_str = "⚠️ BUGGY MODE (LLM Hallucination Simulation)" if is_buggy else "✅ SAFE MODE (TLA+ Protected)"
    print(f"🛠️  Mode: {mode_str}")
    print(f"📋 Task: {task_description}")
    print("==========================================\n")
    
    try:
        final_state = run_workflow(task_description, is_buggy=is_buggy)
        
        print("\n==========================================")
        print("✅ RUN COMPLETE (All invariants passed)")
        print("==========================================")
        print(f"Steps executed: {final_state.get('step', 0)}")
        print("\n📂 Workspace Files Created/Modified:")
        for filename, content in final_state.get("workspace_files", {}).items():
            print(f"  - {filename} ({len(content)} bytes)")
            
        print("\n📝 Artifacts Generated:")
        for artifact in final_state.get("artifacts", []):
            atype = artifact.type if hasattr(artifact, "type") else artifact.get("type", "unknown")
            acreated = artifact.created_at if hasattr(artifact, "created_at") else artifact.get("created_at", "")
            acontent = artifact.content if hasattr(artifact, "content") else artifact.get("content", "")
            print(f"  - [{atype}] Created at {acreated}")
            print(f"    Preview: {str(acontent)[:50]}...")
            
    except ValueError as e:
        print("\n❌ ========================================= ❌")
        print("🚨 TLA+ INVARIANT VIOLATION DETECTED 🚨")
        print("❌ ========================================= ❌")
        print("\nThe agent attempted an illegal operation that violates formal safety rules!")
        print(f"FATAL ERROR: {str(e)}")
        print("\nExecution was halted BEFORE the illegal 'deploy' transition could occur.")
        sys.exit(1)

if __name__ == "__main__":
    main()
