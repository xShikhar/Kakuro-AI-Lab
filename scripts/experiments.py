"""Record paired repair/random experiments, calibrate scores and measure effort correlation."""
import argparse
import csv
import json
import platform
import sys
from pathlib import Path
from statistics import mean
from time import perf_counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from backend.app.generator.generate import generate
from backend.app.solver.engine import solve

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path, rows):
    """Persist raw observations before any summary or plot is computed."""
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def experiment(count=200, sizes=(5, 6), budget=1.0):
    """Run paired seeds and caps; calibrate per-size quantiles on accepted unique puzzles.

    Generation attempts and calibration samples are separate counts. Failures remain
    in the raw data. Calibration continues until count successful puzzles per size,
    rather than falsely treating failed attempts as valid difficulty observations.
    """
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    rows, accepted, calibration, scatter = [], [], {}, []
    started = perf_counter()
    for size in sizes:
        for seed in range(count):
            for mode in ('repair', 'random'):
                result = generate(size=size, seed=seed, timeout=budget, attempts=20, mode=mode)
                rows.append(dict(size=size, seed=seed, mode=mode, success=int(result['unique']),
                                 time_ms=result['wall_time_ms'], repairs=len(result['repairs']),
                                 score=result.get('difficulty', {}).get('score', ''),
                                 baseline_nodes='', baseline_status=''))
                if result['unique'] and mode == 'repair':
                    accepted.append(dict(size=size, **result))
            if seed % 25 == 0:
                write_csv(out / 'generation.csv', rows)
                print(f'paired size={size}, seed={seed}/{count}', flush=True)
        samples = [r for r in accepted if r['size'] == size]
        seed = count
        while len(samples) < count and seed < count * 12:
            result = generate(size=size, seed=seed, timeout=budget, attempts=20)
            if result['unique']:
                record = dict(size=size, **result)
                accepted.append(record)
                samples.append(record)
            seed += 1
            if seed % 50 == 0:
                print(f'calibration size={size}: {len(samples)}/{count}', flush=True)
        scores = sorted(r['difficulty']['score'] for r in samples)
        thresholds = [scores[min(len(scores)-1, int(len(scores)*q))] for q in (.2,.4,.6,.8)]
        calibration[str(size)] = dict(n=len(scores), thresholds=thresholds, method='empirical quintiles; ties stay in lower class', seeds_examined=seed)
    (out / 'calibration.json').write_text(json.dumps(calibration, indent=2))
    # Count search effort independently from generation; keep censoring status in the CSV.
    for i, sample in enumerate(accepted):
        result = solve(sample['puzzle'], strategy='baseline', timeout=1, node_limit=100000, trace=False)
        sample['baseline'] = result['metrics']
        sample['baseline_status'] = result['status']
        if result['status'] == 'solved':
            scatter.append(dict(score=sample['difficulty']['score'], nodes=result['metrics']['nodes']))
        matching = next((r for r in rows if r['size']==sample['size'] and r['seed']==sample['seed'] and r['mode']=='repair'), None)
        if matching is not None:
            matching['baseline_nodes'] = result['metrics']['nodes']
            matching['baseline_status'] = result['status']
        if i % 50 == 0:
            print(f'effort {i}/{len(accepted)}', flush=True)
    write_csv(out / 'generation.csv', rows)
    (out / 'generated_corpus.json').write_text(json.dumps(accepted))
    rho, p = spearmanr([r['score'] for r in scatter], [r['nodes'] for r in scatter]) if len(scatter)>2 else (float('nan'),float('nan'))
    summaries=[]
    for size in sizes:
        for mode in ('repair','random'):
            subset=[r for r in rows if r['size']==size and r['mode']==mode]
            summaries.append(dict(size=size,mode=mode,n=len(subset),success_rate=mean(r['success'] for r in subset),mean_time_ms=mean(r['time_ms'] for r in subset)))
    summary=dict(n_paired_seeds=count,sizes=list(sizes),budget_seconds=budget,python=sys.version.split()[0],platform=platform.platform(),
                 generation=summaries,calibration=calibration,correlation=dict(rho=float(rho),p_value=float(p),n=len(scatter),censored=len(accepted)-len(scatter)),scatter=scatter,
                 duration_seconds=round(perf_counter()-started,2))
    (out / 'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
    plt.style.use('seaborn-v0_8-whitegrid')
    fig,ax=plt.subplots(figsize=(7,4))
    ax.scatter([r['score'] for r in scatter],[r['nodes'] for r in scatter],c='#52755b',s=13,alpha=.6)
    ax.set(xlabel='Human-technique difficulty score',ylabel='Basic backtracking nodes (log scale)',title=f'Measured difficulty / effort • Spearman ρ={rho:.3f}, n={len(scatter)}',yscale='log')
    fig.tight_layout();fig.savefig(out/'difficulty-effort.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9,4))
    names=[f"{r['size']}×{r['size']}\n{r['mode']}" for r in summaries]
    colors=['#52755b' if r['mode']=='repair' else '#cd744c' for r in summaries]
    axes[0].bar(names,[r['success_rate']*100 for r in summaries],color=colors);axes[0].set(ylabel='Unique-generation success (%)',ylim=(0,100))
    axes[1].bar(names,[r['mean_time_ms'] for r in summaries],color=colors);axes[1].set(ylabel='Mean elapsed time (ms)')
    fig.suptitle(f'Paired generation • {count} seeds per size, {budget}s cap per method');fig.tight_layout();fig.savefig(out/'repair-vs-random.png',dpi=180);plt.close(fig)
    print(json.dumps({k:v for k,v in summary.items() if k!='scatter'},indent=2),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count',type=int,default=200)
    parser.add_argument('--sizes',type=int,nargs='+',default=[5,6])
    parser.add_argument('--budget',type=float,default=1.0)
    args=parser.parse_args()
    experiment(args.count,args.sizes,args.budget)
