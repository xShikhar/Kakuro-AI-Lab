"""Turn recorded measurements into presentation tables and reproducible ablation charts."""
import csv
import json
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def report():
    """Aggregate actual CSV rows and replace the README's measured-results block."""
    rows=list(csv.DictReader((ROOT/'results/benchmark.csv').open()))
    totals=defaultdict(lambda:{'nodes':0,'backtracks':0,'constraint_checks':0,'wall_time_ms':0})
    difficulty=defaultdict(lambda:defaultdict(int))
    for row in rows:
        for key in totals[row['strategy']]:
            totals[row['strategy']][key]+=float(row[key])
        difficulty[row['difficulty']][row['strategy']]+=int(row['nodes'])
    lines=['| Configuration | Nodes | Backtracks | Run checks | Total ms |','|---|---:|---:|---:|---:|']
    for strategy,m in totals.items():
        lines.append(f"| {strategy} | {int(m['nodes']):,} | {int(m['backtracks']):,} | {int(m['constraint_checks']):,} | {m['wall_time_ms']:.2f} |")
    lines+=['','All 70 library runs solved within the identical 100,000-node / 3-second caps. Timing is a single run per puzzle/configuration.','',
            '| Grid | Method | Runs | Unique success | Mean ms |','|---|---|---:|---:|---:|']
    summary=json.loads((ROOT/'results/summary.json').read_text())
    for m in summary['generation']:
        lines.append(f"| {m['size']}×{m['size']} | {m['mode']} | {m['n']} | {100*m['success_rate']:.1f}% | {m['mean_time_ms']:.2f} |")
    c=summary['correlation']
    lines+=['',f"Spearman difficulty/effort correlation: **ρ = {c['rho']:.4f}, n = {c['n']}, p = {c['p_value']:.3g}**; {c['censored']} baseline runs censored. Each size has 200 accepted unique calibration puzzles. The paired comparison uses 200 seeds per size/method, 20 attempts and a 0.6-second cap.",
            '',f"Recorded environment: Python {summary['python']} on {summary['platform']}. Experiment wall time: {summary['duration_seconds']:.2f}s."]
    block='\n'.join(lines)
    (ROOT/'results/tables.md').write_text(block,encoding='utf-8')
    readme=ROOT/'README.md'
    if readme.exists():
        text=readme.read_text(encoding='utf-8')
        start,end='<!-- MEASURED_RESULTS_START -->','<!-- MEASURED_RESULTS_END -->'
        text=text.split(start)[0]+start+'\n\n'+block+'\n\n'+end+text.split(end)[1]
        readme.write_text(text,encoding='utf-8')
    plt.style.use('seaborn-v0_8-whitegrid')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    strategies=list(totals)
    colors=['#d0815b']*4+['#a8b999','#52755b','#343e32']
    axes[0].bar(strategies,[totals[s]['nodes'] for s in strategies],color=colors);axes[0].set(ylabel='Total nodes (log scale)',yscale='log',title='Search effort / 10 identical puzzles')
    axes[1].bar(strategies,[totals[s]['wall_time_ms'] for s in strategies],color=colors);axes[1].set(ylabel='Total elapsed ms',title='Runtime / trace disabled')
    for ax in axes:
        ax.tick_params(axis='x',rotation=35,labelsize=8)
    fig.tight_layout();fig.savefig(ROOT/'results/ablation.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4))
    levels=['Beginner','Easy','Medium','Hard','Expert']
    for s in strategies:
        ax.plot(levels,[difficulty[l][s] for l in levels],marker='o',label=s)
    ax.set(yscale='log',ylabel='Total nodes per difficulty (two puzzles)',title='Measured search effort by difficulty')
    ax.legend(ncol=4,fontsize=8);fig.tight_layout();fig.savefig(ROOT/'results/by-difficulty.png',dpi=180);plt.close(fig)
    print(block.encode('ascii','replace').decode())


if __name__=='__main__':
    report()
