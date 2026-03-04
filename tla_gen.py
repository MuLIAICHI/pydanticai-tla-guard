from typing import Dict, List

def generate_tla_spec(state: dict) -> str:
    """
    Generates a TLA+ specification string from the current agent state.
    Used for formal verification before critical transitions.
    """
    artifacts = state.get("artifacts", [])
    # In state dict, artifacts might be Pydantic objects or dicts
    artifact_types = []
    for a in artifacts:
        if isinstance(a, dict):
            artifact_types.append(f'"{a.get("type")}"')
        else:
            artifact_types.append(f'"{a.type}"')
            
    artifacts_str = ", ".join(artifact_types)
    
    return f"""
---- MODULE AntigravityAgent ----
VARIABLES messages, artifacts, step, pc

Init == 
    /\ messages = <<>>
    /\ artifacts = {{{artifacts_str}}}
    /\ step = {state.get('step', 0)}
    /\ pc = "{state.get('pc', 'plan')}"

Next == 
    \/ pc = "plan" /\ pc' = "code"
    \/ pc = "code" /\ pc' = "test"
    \/ pc = "test" /\ pc' = "deploy"

Invariant_NoDeployUntested == 
    [](pc = "deploy" => "test_report" \in artifacts)
====
"""

def tla_verify(state_dict: dict, next_pc: str) -> bool:
    """
    Stub function simulating a TLA+ model checker (`tlc`).
    Verifies that transitioning to `next_pc` does not violate safety invariants.
    
    Requirements:
    - NoDeployUntested: Cannot transition to "deploy" without a "test_report" artifact.
    """
    print(f"[TLA+] Verifying state transition to pc='{next_pc}'...")
    
    # Extract artifact types from state
    artifacts = state_dict.get("artifacts", [])
    artifact_types = set()
    for a in artifacts:
        if isinstance(a, dict):
            artifact_types.add(a.get("type"))
        else:
            artifact_types.add(a.type)
            
    # Check Invariant: NoDeployUntested
    if next_pc == "deploy" and "test_report" not in artifact_types:
        spec_output = generate_tla_spec(state_dict)
        print("\n[TLA+] FAILED SPECIFICATION:\n" + spec_output)
        raise ValueError(
            "TLA+ Invariant Violation: NoDeployUntested! "
            "Cannot safely transition to 'deploy' without a 'test_report' artifact."
        )
        
    print(f"[TLA+] Verification PASS. Safe to proceed to '{next_pc}'.")
    return True
