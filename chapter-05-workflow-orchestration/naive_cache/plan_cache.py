from __future__ import annotations
import time

from workflows.schema import WorkflowPlan
from smart_agent.validation import validate_plan, validate_final_state


class NaivePlanCacheAgent:
    """Intentionally unsafe ablation: key is only workflow family; ignores policy version/contracts."""

    def __init__(self, planner):
        self.planner = planner
        self.cache = {}

    def handle(self, request, policy, env):
        t = time.perf_counter()
        f = request["workflow_family"]

        if f in self.cache:
            plan = WorkflowPlan.from_dict(self.cache[f])

            # Instrumentation only:
            # determine whether the cached plan is stale under the CURRENT
            # request/policy before executing it. We intentionally do NOT block
            # execution because this architecture is the unsafe ablation.
            #
            # This catches stale plans whose final state happens to look valid
            # even though the operation sequence is no longer policy-compliant
            # (for example, a transfer-into-Engineering V1 plan reused under V2
            # without the newly required MFA step).
            plan_validation = validate_plan(plan, request, policy)
            stale_plan = not plan_validation.ok

            try:
                env.execute(request["employee_id"], plan, request)
                fv = validate_final_state(env, request, policy)

                return {
                    "ok": fv.ok and not stale_plan,
                    "path": "CACHE",
                    "llm_calls": 0,
                    "usage": {
                        "input_tokens": 0,
                        "cached_input_tokens": 0,
                        "output_tokens": 0,
                    },
                    "incorrect_stale_reuse": stale_plan or not fv.ok,
                    "stale_reuse_reasons": (
                        plan_validation.reasons if stale_plan else []
                    ),
                    "plan": plan.to_dict(),
                    "latency_ms": (time.perf_counter() - t) * 1000,
                }

            except Exception as e:
                return {
                    "ok": False,
                    "path": "CACHE",
                    "llm_calls": 0,
                    "usage": {
                        "input_tokens": 0,
                        "cached_input_tokens": 0,
                        "output_tokens": 0,
                    },
                    "incorrect_stale_reuse": True,
                    "stale_reuse_reasons": (
                        plan_validation.reasons if stale_plan else []
                    ),
                    "error": str(e),
                    "plan": plan.to_dict(),
                    "latency_ms": (time.perf_counter() - t) * 1000,
                }

        pr = self.planner.plan(request, policy)
        self.cache[f] = pr.plan.to_dict()

        try:
            env.execute(request["employee_id"], pr.plan, request)
            fv = validate_final_state(env, request, policy)
            ok = fv.ok
        except Exception:
            ok = False

        return {
            "ok": ok,
            "path": "RAG_REASONING",
            "llm_calls": 1,
            "usage": pr.usage,
            "incorrect_stale_reuse": False,
            "stale_reuse_reasons": [],
            "plan": pr.plan.to_dict(),
            "latency_ms": (time.perf_counter() - t) * 1000,
        }
