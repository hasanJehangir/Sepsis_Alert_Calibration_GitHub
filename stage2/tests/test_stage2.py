from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_stage2 as s


def fixture():
    metadata=pd.DataFrame([
        {'id':'n','site':'A','role':'test','septic':False,'onset':np.nan,'record_hours':15,'start':0,'stop':10},
        {'id':'s','site':'A','role':'test','septic':True,'onset':16,'record_hours':20,'start':10,'stop':20}])
    h=np.tile(np.arange(6,16,dtype=float),2)
    p=np.r_[.9,np.full(9,.1),np.full(4,.1),np.full(6,.9)]
    y=np.r_[np.zeros(14,dtype=int),np.ones(6,dtype=int)]
    return metadata,p,h,y


def test_fast_metrics_match_direct_patient_evaluation():
    m,p,h,y=fixture();summary=s.score_summary(m,p,h,y)
    fast=s.metric_row(summary,.5)
    assert fast['patient_false_alert_rate']==1
    assert fast['window6_sensitivity']==1
    assert fast['first6_sensitivity']==1
    assert fast['hourly_false_positive_rate']==.1
    p[10]=.8
    summary=s.score_summary(m,p,h,y);fast=s.metric_row(summary,.5)
    assert fast['window6_sensitivity']==1
    assert fast['first6_sensitivity']==0
    assert fast['early_first_fraction']==1


def test_fast_evaluation_matches_pilot_on_several_thresholds():
    m,p,h,y=fixture()
    p[10]=.8
    patients=[]
    for r in m.itertuples():
        sl=slice(r.start,r.stop)
        patients.append({'id':r.id,'site':r.site,'septic':r.septic,'onset':r.onset if r.septic else None,
                         'hours':h[sl],'p':p[sl],'y':y[sl],'record_hours':r.record_hours})
    summary=s.score_summary(m,p,h,y)
    for threshold in [.05,.1,.5,.8,.9,np.inf]:
        direct,_=s.pilot.evaluate(patients,threshold);fast=s.metric_row(summary,threshold)
        for a,b in [('patient_false_alert_rate','patient_false_alert_rate'),('six_hour_window_sensitivity','window6_sensitivity'),
                    ('timely_first_alert_sensitivity','first6_sensitivity'),('hourly_false_positive_rate','hourly_false_positive_rate')]:
            assert direct[a]==fast[b]


def test_cap_keeps_late_cases_out_of_case_denominator_not_as_negatives():
    m,p,h,y=fixture()
    summary=s.score_summary(m,p,h,y,cap=14)
    assert summary['late_cases_excluded']==1
    metrics=s.metric_row(summary,.5)
    assert metrics['septic_patients']==0
    assert metrics['nonseptic_patients']==1
    assert metrics['negative_hours']==9
    assert metrics['window6_sensitivity'] is None


def test_empirical_and_finite_rank_are_explicitly_different():
    values=np.arange(100)
    assert s.empirical_quantile(values,.1)==89
    assert s.patient_threshold(values)==90
    assert s.patient_threshold([])==np.inf


def test_tied_sensitivity_threshold_reaches_target():
    summary={'frame':pd.DataFrame({'septic':[True]*10,'window6':[.1,.1,.2,.2,.3,.4,.5,.6,.7,.8]})}
    threshold=s.sensitivity_threshold(summary,.8)
    assert (summary['frame'].window6>threshold).sum()==8
    assert threshold<.2


def test_paired_bootstrap_identical_policies_zero_width():
    m,p,h,y=fixture();summary=s.score_summary(m,p,h,y)
    delta=s.paired_difference(summary,.5,.5)
    for endpoint in delta.values():
        assert endpoint['difference']==endpoint['ci_low']==endpoint['ci_high']==0


def test_ablation_preserves_physiology_and_removes_explicit_process_features():
    cols=s.feature_columns('hgb_no_observation_features')
    assert len(cols)==51
    assert set(range(34)).issubset(cols)
    assert not set(range(37,106)).intersection(cols)


def test_calibration_budgets_are_nested_and_never_include_training_or_test():
    rows=[{'id':site+str(i),'site':site,'role':'calibration' if i<600 else 'test'} for site in ['A','B'] for i in range(620)]
    frame=pd.DataFrame(rows);samples=s.calibration_samples(frame)
    for site in ['A','B']:
        a=samples[f'{site}|20261001|100'];b=samples[f'{site}|20261001|250'];c=samples[f'{site}|20261001|500']
        assert a==b[:100] and b==c[:250]
        assert len(set(c))==500
        assert set(c).issubset(set(frame.loc[frame.role=='calibration','id']))
