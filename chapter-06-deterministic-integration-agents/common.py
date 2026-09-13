from __future__ import annotations
import time

def usage_dict(u): return {'input_tokens':u.input_tokens,'cached_input_tokens':u.cached_input_tokens,'output_tokens':u.output_tokens,'cost':u.cost}
def now_ms(): return time.perf_counter()*1000
