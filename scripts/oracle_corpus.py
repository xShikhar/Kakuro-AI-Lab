"""Prepare 300 seeded unique puzzles so regression tests are repeatable and network-free."""
import json
from pathlib import Path
from backend.app.generator.generate import generate


def build():
    """Generate distinct-seed samples and write the accepted puzzles with their witness metadata."""
    records=[]
    for seed in range(300):
        result=generate(size=5,seed=seed+9000,timeout=5)
        if not result['unique']:
            raise RuntimeError(f'Generation failed at seed {seed}; no fake sample substituted.')
        records.append({k:v for k,v in result.items() if k in ('puzzle','solution','unique','seed')})
        if seed%50==0:
            print(f'oracle corpus {seed}/300',flush=True)
    path=Path(__file__).resolve().parents[1]/'results/oracle_corpus.json'
    path.write_text(json.dumps(records))


if __name__=='__main__':
    build()
