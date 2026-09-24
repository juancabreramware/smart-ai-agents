from .models import Usage
from .scoring import truth

class MockProvider:
    model="gpt-5-mini"
    def reason(self, req, contract, attempt_no=1):
        # Mock-only stress injection. Real-provider stress injection is handled
        # by runner._call so the OpenAI provider never sees hidden failure schedule.
        if req.failure_mode=="retry_once" and attempt_no==1:
            return {"status":"failed","usage":Usage(90,12),"answer":None,
                    "operation":contract["operation"],"error_type":"MockInjectedRetry",
                    "error_message":"Controlled mock retry injection."}
        if req.failure_mode=="hard_fail_once" and attempt_no==1:
            return {"status":"failed","usage":Usage(0,0),"answer":None,
                    "operation":contract["operation"],"error_type":"MockInjectedHardFailure",
                    "error_message":"Controlled mock nonbillable hard-failure injection."}
        return {"status":"success","usage":Usage(320+(req.seq%37),110+(req.seq%23)),
                "answer":truth(req),"operation":contract["operation"],
                "error_type":None,"error_message":None}
