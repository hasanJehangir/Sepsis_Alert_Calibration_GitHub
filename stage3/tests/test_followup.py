from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_followup as s

def test_strict_crossing_and_silence_boundary():
    h=np.arange(6,16);p=np.full(10,.8)
    assert s.emissions(h,p,.8,'hourly').size==0
    assert np.array_equal(s.emissions(h,p,.5,'silence4'),[0,4,8])
    assert np.array_equal(s.emissions(h,p,.5,'silence6'),[0,6])
    assert np.array_equal(s.emissions(h,p,.5,'single'),[0])

def test_three_of_five_matches_independent_warning_count():
    p=np.array([.8,.9,.1,.7,.1,.2,.8,.9,.8,.1])
    effective=s.effective_scores(p,'three_of_five')
    for threshold in [.1,.5,.7,.8,np.inf]:
        expected=np.array([np.count_nonzero(p[max(0,i-4):i+1]>threshold)>=3 for i in range(len(p))])
        assert np.array_equal(effective>threshold,expected)
    assert np.isneginf(effective[:2]).all()

def test_rolling_transform_is_causal():
    p=np.array([.8,.9,.1,.7,.1,.2,.8,.9])
    assert np.array_equal(s.effective_scores(p,'three_of_five')[:5],s.effective_scores(p[:5],'three_of_five'))

def test_finite_rank_with_structural_ineligibility():
    assert s.finite_quantile(np.r_[-np.inf,np.arange(99)],.1)==89
    assert s.finite_quantile(np.full(100,-np.inf),.1)==-np.inf
    assert s.finite_quantile(np.arange(3),.1)==np.inf

def test_single_alert_can_remove_later_window_detection():
    h=np.arange(6,16);p=np.r_[.9,np.zeros(6),.9,0,0]
    rows=[{'id':'n','septic':False,'onset':None,'h':h,'p':p,'three_of_five':s.effective_scores(p,'three_of_five'),'hours':len(h)},
          {'id':'s','septic':True,'onset':16.,'h':h,'p':p,'three_of_five':s.effective_scores(p,'three_of_five'),'hours':len(h)}]
    raw=s.patient_results(rows,.5,'hourly');single=s.patient_results(rows,.5,'single')
    assert raw.iloc[1].window6 and not single.iloc[1].window6
    assert not raw.iloc[1].first6 and not single.iloc[1].first6
    assert raw.iloc[0].any_alert==single.iloc[0].any_alert
    assert s.metrics(raw)['nonseptic_alerts']==2
    assert s.metrics(single)['nonseptic_alerts']==1

def test_identical_policy_bootstrap_is_zero():
    h=np.arange(6,16);p=np.full(10,.8)
    rows=[{'id':str(i),'septic':bool(i%2),'onset':16. if i%2 else None,'h':h,'p':p,'three_of_five':p,'hours':10} for i in range(10)]
    a=s.patient_results(rows,.5,'hourly')
    for d in s.bootstrap_deltas(a,a):assert d['difference']==d['ci_low']==d['ci_high']==0
