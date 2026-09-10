"""Offline semantic re-evaluation of an existing Chapter 4 execution ledger.

No provider, embedding, retrieval, or LLM calls are made. The original ledger is
never modified. Audited outputs are written beside it with an ``audited_`` prefix.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from smart_agent.validation import answer_correct


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('results_dir', help='Existing results/full-YYYYMMDD-HHMMSS directory')
    args=ap.parse_args()
    root=Path(args.results_dir)
    ledger=root/'execution_ledger.jsonl'
    rows=[json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    audited=[]
    for row in rows:
        raw=bool(row['correct'])
        semantic=answer_correct(row['answer'],row['expected'],row.get('query'))
        x=dict(row)
        x['raw_correct']=raw
        x['semantic_correct']=semantic
        x['evaluation_changed']=raw != semantic
        # Preserve whether this was a stale-cache opportunity, but count it as an
        # incorrect stale reuse only if the audited semantic answer is wrong.
        x['audited_incorrect_stale_reuse']=bool(row.get('stale_reuse')) and not semantic
        audited.append(x)

    summary={}
    for arch in sorted({x['architecture'] for x in audited}):
        a=[x for x in audited if x['architecture']==arch]
        summary[arch]={
            'executions':len(a),
            'raw_successful':sum(x['raw_correct'] for x in a),
            'raw_correctness':sum(x['raw_correct'] for x in a)/len(a),
            'audited_successful':sum(x['semantic_correct'] for x in a),
            'audited_correctness':sum(x['semantic_correct'] for x in a)/len(a),
            'evaluation_changes':sum(x['evaluation_changed'] for x in a),
            'audited_incorrect_stale_reuse':sum(x['audited_incorrect_stale_reuse'] for x in a),
        }

    with (root/'audited_execution_ledger.jsonl').open('w') as f:
        for x in audited:
            f.write(json.dumps(x)+'\n')
    (root/'audited_summary.json').write_text(json.dumps(summary,indent=2))
    changes=[x for x in audited if x['evaluation_changed']]
    with (root/'audited_evaluation_changes.jsonl').open('w') as f:
        for x in changes:
            f.write(json.dumps(x)+'\n')

    print(json.dumps(summary,indent=2))
    print(f"\nAudited outputs written to: {root}")
    return 0

if __name__=='__main__':
    raise SystemExit(main())
