from pathlib import Path
import sys
_PROJECT_ROOT=Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(_PROJECT_ROOT))

import ast, json
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def add(name,ok,detail=""): checks.append({"check":name,"passed":bool(ok),"detail":detail})

runtime=(ROOT/"src/runtime.py").read_text(encoding="utf-8")
provider=(ROOT/"src/provider.py").read_text(encoding="utf-8")
add("BOUNDARY-01 runtime independent of scoring", "scoring" not in runtime and "truth(" not in runtime)
add("BOUNDARY-02 OpenAI provider independent of hidden scoring", "scoring" not in provider and "truth(" not in provider)
add("BOUNDARY-03 no arbitrary execution", all(x not in runtime+provider for x in ["eval(","exec(","subprocess.","os.system("]))
add("BOUNDARY-04 provider public-contract request only",
    '"public_contract":contract' in provider and '"request":req.payload' in provider)
add("BOUNDARY-05 OpenAI provider does not inspect failure schedule", "failure_mode" not in provider)
result={"passed":all(x["passed"] for x in checks),"checks":checks}
print(json.dumps(result,indent=2))
raise SystemExit(0 if result["passed"] else 1)
