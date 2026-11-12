"""Select two verified measured puzzles per level and benchmark every solver fairly."""
import json
from pathlib import Path
from backend.app.generator.difficulty import rate, LEVELS
from backend.app.solver.engine import solve
from backend.app.arena import benchmark
from scripts.experiments import write_csv

ROOT=Path(__file__).resolve().parents[1]
NAMES={'Beginner':['First light','A quiet beginning'],'Easy':['Paper trail','The short way home'],
       'Medium':['Crossed paths','Between the lines'],'Hard':['A second thought','The turning point'],
       'Expert':['A beautiful contradiction','The long way around']}


def build():
    """Rate real corpus members using calibrated thresholds and choose a demo with actual backtracking."""
    corpus=json.loads((ROOT/'results/generated_corpus.json').read_text())
    buckets={level:[] for level in LEVELS}
    for sample in corpus:
        human=solve(sample['puzzle'],strategy='human',timeout=5)
        if not human['solution']:
            continue
        difficulty=rate(human,sample['size'])
        buckets[difficulty['label']].append((sample,difficulty))
    library=[]
    for level in LEVELS:
        candidates=sorted(buckets[level],key=lambda v:(-v[1]['guess_levels'],-v[0].get('baseline',{}).get('backtracks',0)))
        seen=set()
        for sample,difficulty in candidates:
            signature=json.dumps(sample['puzzle'],sort_keys=True)
            if signature in seen:
                continue
            seen.add(signature)
            index=len([p for p in library if p['difficulty']['label']==level])
            if index>=2:
                break
            library.append(dict(id=f'{level.lower()}-{index+1}',name=NAMES[level][index],puzzle=sample['puzzle'],
                                solution=sample['solution'],difficulty=difficulty,seed=sample['seed']))
        if len([p for p in library if p['difficulty']['label']==level])<2:
            raise RuntimeError(f'Insufficient calibrated samples for {level}; expand the corpus.')
    demo=max(library,key=lambda p:(solve(p['puzzle'],strategy='full',trace=False,timeout=2)['metrics']['backtracks'],p['difficulty']['guess_levels']))
    demo['demo']=True
    (ROOT/'data/puzzles.json').write_text(json.dumps(library,indent=2))
    results=benchmark(library,timeout=3)
    write_csv(ROOT/'results/benchmark.csv',results['results'])
    (ROOT/'results/benchmark.json').write_text(json.dumps(results,indent=2))
    print('Library:',[(p['id'],p['difficulty']['score'],p['difficulty']['guess_levels']) for p in library],flush=True)
    print(results['analysis'],flush=True)


if __name__=='__main__':
    build()
