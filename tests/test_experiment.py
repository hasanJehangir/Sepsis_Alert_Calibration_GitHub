import numpy as np
import pandas as pd
import experiment as e


def sample_frame(n=20):
    rng = np.random.default_rng(42)
    frame = pd.DataFrame(rng.normal(size=(n, len(e.PHYSIO+e.STATIC))), columns=e.PHYSIO+e.STATIC)
    frame['Age'] = 50
    frame['ICULOS'] = np.arange(1, n+1)
    return frame


def test_features_are_causal():
    frame = sample_frame()
    frame.loc[2:5, 'HR'] = np.nan
    prefix = e.features(frame.iloc[:10])
    changed = frame.copy()
    changed.iloc[10:] = 99999
    np.testing.assert_allclose(prefix, e.features(changed)[:10], equal_nan=True)


def test_rank_and_small_sample():
    assert e.order_quantile([.1, .2], .1) == float('inf')
    assert e.order_quantile(np.arange(19), .1) == 17


def patient(pid, p, septic=False, onset=None):
    hours = np.arange(6, 6+len(p))
    return {'id': pid, 'site': 'A', 'septic': septic, 'onset': onset,
            'p': np.array(p), 'hours': hours, 'record_hours': float(hours[-1]),
            'y': ((hours >= onset-6) & (hours < onset)).astype(int) if septic else np.zeros(len(p), dtype=int)}


def test_patient_and_hourly_endpoints_differ():
    negative = patient('n', [.9]+[.1]*9)
    positive = patient('s', [.1]*4+[.9]*6, True, 16)
    metrics, _ = e.evaluate([negative, positive], .5)
    assert metrics['patient_false_alert_rate'] == 1
    assert metrics['hourly_false_positive_rate'] == .1
    assert metrics['six_hour_window_sensitivity'] == 1
    assert metrics['timely_first_alert_sensitivity'] == 1


def test_threshold_ties_do_not_alert():
    metrics, _ = e.evaluate([patient('n', [.5]*10)], .5)
    assert metrics['false_alerted_patients'] == 0


def test_pilot_never_selects_reserved_records():
    records = [{'site': site, 'name': f'p{i:06d}.psv', 'role': 'pilot' if i<10 else 'test'}
               for site in ['A', 'B'] for i in range(12)]
    assigned = e.assign_pilot(records)
    assert len(assigned) == 20
    assert all(row['role'] == 'pilot' for row in assigned)


def test_label_shift_and_post_onset_truncation(tmp_path, monkeypatch):
    monkeypatch.setattr(e, 'ROOT', tmp_path)
    frame = sample_frame(50)
    frame['SepsisLabel'] = (frame.ICULOS >= 30).astype(int)
    destination = tmp_path/'data'/'A'
    destination.mkdir(parents=True)
    frame.to_csv(destination/'p000001.psv', sep='|', index=False)
    p, reason = e.prepare({'site': 'A', 'name': 'p000001.psv'})
    assert reason is None
    assert p['onset'] == 36
    assert p['hours'][0] == 6
    assert p['hours'][-1] == 35
    assert p['y'].sum() == 6
