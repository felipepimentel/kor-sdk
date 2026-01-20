import time
import re
from typing import List, Dict, Any
from kor_core.kernel import Kernel, set_kernel, reset_kernel
from kor_core.sandbox import InMemorySandbox
from kor_core.agent.runner import GraphRunner
from .models import EvalCase, EvalResult, Assertion

class EvalRunner:
    def __init__(self):
        pass

    async def run_case(self, case: EvalCase) -> EvalResult:
        # 1. Setup Sandbox
        sandbox = InMemorySandbox(initial_files=case.initial_files)
        
        # 2. Setup Kernel with Mock Sandbox
        # We create a fresh kernel for isolation
        kernel = Kernel(config_options={"user": {"name": "EvalBot"}})
        
        # Inject our sandbox
        kernel.sandbox = sandbox
        # Update registry entry just in case
        kernel.registry.register_service("sandbox", sandbox) 
        # (Note: register_service errors if exists, but in constructor it happens. 
        # actually kernel.__init__ registers it. We need to overwrite it or hack it.)
        # Kernel.__init__ does: self.registry.register_service("sandbox", self.sandbox)
        # ServiceRegistry.register_service raises if exists.
        # We can just cheat:
        kernel.registry._services["sandbox"] = sandbox
        
        # Set as global kernel for this context
        set_kernel(kernel)
        
        start_time = time.time()
        error = None
        success = False
        assertion_results = []
        
        try:
            await kernel.boot()
            
            # 3. Run Agent
            runner = GraphRunner()
            inputs = case.agent_prompt
            
            # Consume stream to completion
            async for event in runner.graph.astream({"messages": [("user", inputs)]}, config={"configurable": {"thread_id": "eval"}}):
                pass
                
            # 4. Check Assertions
            assertion_results = self._check_assertions(case.assertions, sandbox)
            success = all(r["passed"] for r in assertion_results)
            
        except Exception as e:
            error = str(e)
            success = False
        finally:
            await kernel.shutdown()
            reset_kernel()
            
        duration = (time.time() - start_time) * 1000
        
        return EvalResult(
            case_id=case.id,
            success=success,
            score=1.0 if success else 0.0,
            duration_ms=duration,
            error=error,
            assertion_results=assertion_results
        )

    def _check_assertions(self, assertions: List[Assertion], sandbox: InMemorySandbox) -> List[Dict[str, Any]]:
        results = []
        for assertion in assertions:
            passed = False
            msg = ""
            
            if assertion.type == "file_exists":
                passed = assertion.target in sandbox.files
                msg = f"File {assertion.target} exists: {passed}"
                
            elif assertion.type == "file_content_match":
                if assertion.target not in sandbox.files:
                    passed = False
                    msg = f"File {assertion.target} not found"
                else:
                    content = sandbox.files[assertion.target]
                    if assertion.value:
                        if re.search(assertion.value, content):
                            passed = True
                            msg = "Content matched regex"
                        else:
                            msg = f"Content did not match regex: {assertion.value}"
                    else:
                        passed = True # content exists
                        
            results.append({
                "type": assertion.type,
                "target": assertion.target,
                "passed": passed,
                "message": msg
            })
        return results
