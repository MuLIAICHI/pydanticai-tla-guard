---- MODULE AntigravityAgent ----
(**************************************************************************)
(* TLA+ Formal Specification for the AntigravityAgent Workflow            *)
(*                                                                        *)
(* This spec models a PydanticAI / LangGraph autonomous coding agent      *)
(* that follows a plan -> code -> test -> deploy lifecycle.                *)
(*                                                                        *)
(* Safety Invariant: The agent MUST NOT reach the "deploy" state           *)
(* without first generating a "test_report" artifact. This prevents        *)
(* LLM hallucination from causing untested code to be deployed.            *)
(**************************************************************************)

VARIABLES messages, artifacts, step, pc

(* --- Type Invariant --- *)
TypeOK ==
    /\ messages \in Seq(STRING)
    /\ artifacts \subseteq {"task_list", "impl_plan", "screenshot", "test_report", "walkthrough"}
    /\ step \in Nat
    /\ pc \in {"plan", "code", "test", "deploy", "done"}

(* --- Initial State --- *)
Init ==
    /\ messages = <<>>
    /\ artifacts = {}
    /\ step = 0
    /\ pc = "plan"

(* --- State Transitions --- *)
Plan ==
    /\ pc = "plan"
    /\ pc' = "code"
    /\ artifacts' = artifacts \union {"task_list", "impl_plan"}
    /\ step' = step + 1
    /\ UNCHANGED messages

Code ==
    /\ pc = "code"
    /\ pc' = "test"
    /\ step' = step + 1
    /\ UNCHANGED <<messages, artifacts>>

TestSafe ==
    /\ pc = "test"
    /\ pc' = "deploy"
    /\ artifacts' = artifacts \union {"screenshot", "test_report"}
    /\ step' = step + 1
    /\ UNCHANGED messages

TestBuggy ==
    \* Models LLM hallucination: skips test_report generation
    /\ pc = "test"
    /\ pc' = "deploy"
    /\ step' = step + 1
    /\ UNCHANGED <<messages, artifacts>>

Deploy ==
    /\ pc = "deploy"
    /\ pc' = "done"
    /\ artifacts' = artifacts \union {"walkthrough"}
    /\ step' = step + 1
    /\ UNCHANGED messages

Next ==
    \/ Plan
    \/ Code
    \/ TestSafe
    \/ TestBuggy
    \/ Deploy

(* --- Safety Invariants --- *)

(* CRITICAL: Cannot deploy without a test report *)
Invariant_NoDeployUntested ==
    pc = "deploy" => "test_report" \in artifacts

(* Steps must always increase *)
Invariant_StepMonotonic ==
    step >= 0

(* pc must be a valid state *)
Invariant_ValidPC ==
    pc \in {"plan", "code", "test", "deploy", "done"}

====
