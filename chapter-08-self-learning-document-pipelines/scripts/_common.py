from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.planner.mock_planner import MockPlanner
from src.benchmark.pricing import DEFAULT_PRICING
def planner_factory(name):
    if name=='mock': return lambda: MockPlanner()
    if name=='openai':
        from src.planner.openai_planner import OpenAIPlanner
        return lambda: OpenAIPlanner(pricing=DEFAULT_PRICING)
    raise ValueError(name)
