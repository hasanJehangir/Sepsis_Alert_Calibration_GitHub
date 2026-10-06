"""Explore alert policies on frozen predictions; no model fitting or test tuning."""
from pathlib import Path
import argparse, datetime, hashlib, importlib.metadata, json, math, platform, time
import numpy as np
import pandas as pd
from scipy.stats import beta

STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parent
PRIOR=ROOT/'stage2/results'
OUT=STAGE/'results'
CONFIG=json.loads((STAGE/'config.json').read_text())

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False))

def restore_hours():
    path=ROOT/'stage2/cache/hours.npy'
    if path.exists():return
    cohort=pd.read_csv(PRIOR/'cohort.csv');arrays=[]
    for r in cohort.itertuples():
        site,name=r.id.split('_',1)
        h=pd.read_csv(ROOT/'data'/site/(name+'.psv'),sep='|',usecols=['ICULOS']).ICULOS.to_numpy(float)
        h=h[(h>=6)&((h<r.onset) if r.septic else np.ones(len(h),bool))].astype(np.float32)
        assert len(h)==r.stop-r.start,r.id
        arrays.append(h)
    path.parent.mkdir(parents=True,exist_ok=True)
    np.save(path,np.concatenate(arrays))
    print('Restored scoring hours from public raw records',flush=True)

def check_inputs():
    lock=json.loads((STAGE/'followup_lock.json').read_text())
    assert lock['stage2_test_outcomes_already_examined'] is True
    assert sha(STAGE/'FOLLOWUP_PROTOCOL.md')==lock['protocol_sha256']
    assert sha(STAGE/'config.json')==lock['config_sha256']
    for name,digest in lock['inputs'].items():
        if sha(ROOT/name)!=digest:raise RuntimeError('Frozen input changed: '+name)
    return lock

def effective_scores(p,policy):
    p=np.asarray(p,dtype=float)
    if policy!='three_of_five':return p
    windows=np.lib.stride_tricks.sliding_window_view(np.r_[np.full(4,-np.inf),p],5)
    return np.partition(windows,2,axis=1)[:,2]  # third largest among five

def emissions(h,effective,threshold,policy):
    eligible=np.flatnonzero(effective>threshold)
    if policy=='single':return eligible[:1]
    if policy not in ['silence4','silence6']:return eligible
    silence=4 if policy=='silence4' else 6
    selected=[];next_allowed=-np.inf
    for index in eligible:
        if h[index]>=next_allowed:
            selected.append(index);next_allowed=h[index]+silence
    return np.asarray(selected,dtype=int)

def finite_quantile(values,alpha):
    values=np.asarray(values,dtype=float)
    if not len(values) or np.isnan(values).any() or np.isposinf(values).any():raise ValueError('Invalid calibration scores')
    rank=math.ceil((len(values)+1)*(1-alpha))
    return float(np.partition(values,rank-1)[rank-1]) if rank<=len(values) else np.inf

def ci(k,n):
    if not n:return (None,None)
    return (0. if k==0 else float(beta.ppf(.025,k,n-k+1)),1. if k==n else float(beta.ppf(.975,k+1,n-k)))

def paths(cohort,p,h):
    result={}
    for site in ['A','B']:
        for role in ['calibration','test']:
            rows=[]
            for r in cohort[(cohort.site==site)&(cohort.role==role)].itertuples():
                sl=slice(int(r.start),int(r.stop));hp=np.asarray(h[sl]);pp=np.asarray(p[sl])
                assert np.isfinite(pp).all() and np.all(np.diff(hp)==1)
                ep=effective_scores(pp,'three_of_five')
                rows.append({'id':r.id,'septic':bool(r.septic),'onset':float(r.onset) if r.septic else None,
                             'h':hp,'p':pp,'three_of_five':ep,'hours':len(hp)})
            result[site,role]=rows
    return result

def patient_results(rows,threshold,policy):
    output=[]
    for r in rows:
        score=r['three_of_five'] if policy=='three_of_five' else r['p']
        emitted=emissions(r['h'],score,threshold,policy);t=r['h'][emitted]
        first=float(t[0]) if len(t) else None
        if r['septic']:
            onset=r['onset']
            window=bool(np.any((t>=onset-6)&(t<onset)))
            first6=bool(first is not None and onset-6<=first<onset)
            window12=bool(np.any((t>=onset-12)&(t<onset)))
            first12=bool(first is not None and onset-12<=first<onset)
            early=bool(first is not None and first<onset-6)
            lead=onset-first if first is not None else None
        else:window=first6=window12=first12=early=False;lead=None
        output.append({'id':r['id'],'septic':r['septic'],'hours':r['hours'],'alerts':len(t),
                       'any_alert':bool(len(t)),'window6':window,'first6':first6,'window12':window12,
                       'first12':first12,'early6':early,'first_alert':first,'lead_hours':lead})
    return pd.DataFrame(output)

def metrics(frame):
    negative=frame[~frame.septic];positive=frame[frame.septic]
    result={'nonseptic_patients':len(negative),'septic_patients':len(positive)}
    for key,name,rows in [('any_alert','patient_false_alert_rate',negative),('window6','window6_sensitivity',positive),
                          ('first6','first6_sensitivity',positive),('early6','early_first_fraction',positive),
                          ('window12','window12_sensitivity',positive),('first12','first12_sensitivity',positive),
                          ('any_alert','any_positive_alert_fraction',positive)]:
        n=len(rows);k=int(rows[key].sum());lo,hi=ci(k,n)
        result.update({name:k/n if n else None,name+'_count':k,name+'_ci_low':lo,name+'_ci_high':hi})
    for name,rows in [('nonseptic',negative),('septic',positive)]:
        total=int(rows.alerts.sum());hours=int(rows.hours.sum())
        result[name+'_alerts']=total;result[name+'_hours']=hours
        result[name+'_alerts_per_admission']=total/len(rows) if len(rows) else None
        result[name+'_alerts_per_100_hours']=100*total/hours if hours else None
    lead=positive.lead_hours.dropna()
    result.update(first_alert_lead_median=float(lead.median()) if len(lead) else None,
                  first_alert_lead_p25=float(lead.quantile(.25)) if len(lead) else None,
                  first_alert_lead_p75=float(lead.quantile(.75)) if len(lead) else None,
                  alerted_positive_patients=len(lead))
    return result

def bootstrap_deltas(a,b):
    assert a.id.tolist()==b.id.tolist()
    rng=np.random.default_rng(CONFIG['seed']);results=[]
    for key,outcome in [('any_alert','false_alert'),('window6','window6'),('first6','first6'),('alerts','negative_alerts_per_admission')]:
        mask=~a.septic if outcome in ['false_alert','negative_alerts_per_admission'] else a.septic
        delta=a.loc[mask,key].astype(int).to_numpy()-b.loc[mask,key].astype(int).to_numpy()
        values,counts=np.unique(delta,return_counts=True);n=len(delta)
        samples=rng.multinomial(n,counts/n,size=CONFIG['bootstrap_draws'])@values/n
        results.append({'endpoint':outcome,'difference':float(delta.mean()),'ci_low':float(np.quantile(samples,.025)),
                        'ci_high':float(np.quantile(samples,.975)),'n':n})
    return results

def run():
    started=time.time();lock=check_inputs();OUT.mkdir(parents=True,exist_ok=True)
    cohort=pd.read_csv(PRIOR/'cohort.csv');h=np.load(ROOT/'stage2/cache/hours.npy',mmap_mode='r')
    main=pd.read_csv(PRIOR/'main_metrics.csv');main=main[main.cap=='natural']
    records=[];paired=[];audits=[]
    groups=main[['source','model']].drop_duplicates().itertuples(index=False)
    for source,model in groups:
        p=np.load(PRIOR/f'{source}_{model}_predictions.npz')['probability']
        summaries=paths(cohort,p,h)
        for site in ['A','B']:
            subset=main[(main.source==source)&(main.model==model)&(main.test_site==site)].set_index('policy')
            test=summaries[site,'test'];cache={};matched={}
            def get(policy,threshold):
                key=(policy,float(threshold).hex())
                if key not in cache:cache[key]=patient_results(test,threshold,policy)
                return cache[key]
            base={'source':source,'model':model,'test_site':site,'transfer':source!=site}
            for anchor in CONFIG['fixed_anchors']:
                threshold=.5 if anchor=='probability_0_5' else (np.inf if subset.loc[anchor,'threshold_infinite'] else float(subset.loc[anchor,'threshold']))
                frames={policy:get(policy,threshold) for policy in CONFIG['policies']}
                raw=frames['hourly']
                for policy,frame in frames.items():
                    if policy in ['single','silence4','silence6']:
                        assert frame.any_alert.tolist()==raw.any_alert.tolist()
                        assert frame.first6.tolist()==raw.first6.tolist()
                        assert np.all(frame.alerts.to_numpy()<=raw.alerts.to_numpy())
                        assert frame.first_alert.fillna(-1).tolist()==raw.first_alert.fillna(-1).tolist()
                    if policy=='single':
                        assert frame.alerts.max()<=1
                        assert frame.window6.tolist()==frame.first6.tolist()
                    record={**base,'condition':'fixed','anchor':anchor,'calibration_site':source if anchor.startswith('source') else site,
                            'alpha':None,'policy':policy,'threshold':threshold if np.isfinite(threshold) else None,
                            'threshold_infinite':not np.isfinite(threshold),**metrics(frame)}
                    records.append(record)
                    if policy=='hourly' and anchor!='probability_0_5':
                        prior=subset.loc[anchor]
                        for endpoint in ['patient_false_alert_rate','window6_sensitivity','first6_sensitivity','early_first_fraction','window12_sensitivity','first12_sensitivity','any_positive_alert_fraction']:
                            assert record[endpoint+'_count']==int(prior[endpoint+'_count'])
                        assert record['nonseptic_alerts']==int(prior.negative_alert_hours)
            for context,cal_site in [('source',source),('local',site)]:
                calibration=[r for r in summaries[cal_site,'calibration'] if not r['septic']]
                for alpha in CONFIG['alphas']:
                    thresholds={}
                    for policy in CONFIG['policies']:
                        scores=np.array([np.max(r['three_of_five'] if policy=='three_of_five' else r['p']) for r in calibration])
                        threshold=finite_quantile(scores,alpha);thresholds[policy]=threshold
                        frame=get(policy,threshold)
                        records.append({**base,'condition':'matched_patient','anchor':context,'calibration_site':cal_site,'alpha':alpha,
                                        'policy':policy,'calibration_nonseptic_patients':len(calibration),
                                        'structurally_ineligible_calibration_patients':int(np.isneginf(scores).sum()),
                                        'threshold':threshold if np.isfinite(threshold) else None,
                                        'threshold_infinite':not np.isfinite(threshold),**metrics(frame)})
                        if context=='local' and alpha==.1:
                            matched[policy]=frame
                            frame.to_csv(OUT/f'{source}_{model}_{site}_{policy}_local10_patients.csv.gz',index=False)
                    for policy in ['single','silence4','silence6']:assert thresholds[policy]==thresholds['hourly']
                    audits.append({**base,'context':context,'alpha':alpha,'first_crossing_preserving_thresholds_equal':True})
            for policy in ['three_of_five','silence4','silence6']:
                for difference in bootstrap_deltas(matched[policy],matched['hourly']):
                    paired.append({**base,'comparison':policy+'_minus_hourly_local10',**difference})
            print('Evaluated',source,model,'on',site,flush=True)
        del p,summaries
    frame=pd.DataFrame(records);frame.to_csv(OUT/'policy_metrics.csv',index=False)
    pd.DataFrame(paired).to_csv(OUT/'paired_policy_differences.csv',index=False)
    pd.DataFrame(audits).to_csv(OUT/'invariance_audit.csv',index=False)
    completion={'status':'EXPLORATORY_FOLLOWUP_COMPLETED','completed_at_utc':now(),'test_outcomes_already_examined':True,
                'external_validation_completed':False,'clinical_validation':False,'policy_rows':len(frame),'paired_endpoint_rows':len(paired),
                'prior_signature':json.loads((PRIOR/'completed.json').read_text())['signature'],
                'followup_lock_sha256':sha(STAGE/'followup_lock.json'),'runner_sha256':sha(__file__),
                'lock':lock,'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy']},
                'python':platform.python_version(),'elapsed_seconds':time.time()-started,
                'invariance_and_stage2_anchor_checks_passed':True}
    write_json(OUT/'completed.json',completion)
    print(json.dumps({k:v for k,v in completion.items() if k!='lock'},indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--restore-hours',action='store_true');args=parser.parse_args()
    if args.restore_hours:restore_hours()
    run()
