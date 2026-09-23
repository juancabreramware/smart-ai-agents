import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
def planner_factory(name):
    if name=='mock':
        from src.planner.mock_planner import MockPlanner
        return lambda: MockPlanner()
    from src.planner.openai_planner import OpenAIPlanner
    return lambda: OpenAIPlanner()
