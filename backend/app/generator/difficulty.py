"""Behavior-based difficulty scores; thresholds are replaced by empirical quantiles after calibration."""
import json
from pathlib import Path

LEVELS = ['Beginner', 'Easy', 'Medium', 'Hard', 'Expert']
DEFAULT_THRESHOLDS = [15, 35, 70, 120]


def rate(result, size=None):
    """Score weighted deduction ranks, deepest guessing level and the number of deductions."""
    techniques = [e['justification']['rank'] for e in result['trace'] if e['type'] == 'technique_applied']
    score = sum(techniques) + 10 * result['metrics']['guess_levels'] + .5 * len(techniques)
    calibration = Path(__file__).resolve().parents[3] / 'results' / 'calibration.json'
    thresholds, calibrated = DEFAULT_THRESHOLDS, False
    if calibration.exists():
        data = json.loads(calibration.read_text())
        thresholds = data.get(str(size), {}).get('thresholds', thresholds)
        calibrated = str(size) in data
    label = LEVELS[sum(score > value for value in thresholds)]
    return dict(score=score, label=label, technique_steps=len(techniques),
                guess_levels=result['metrics']['guess_levels'], thresholds=thresholds, calibrated=calibrated)
