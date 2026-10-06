"""Independent ICU sepsis pilot. No CAPMI data, code, weights, or results.
The remaining 37,336 records are not opened by this program.
"""
from pathlib import Path
import hashlib,json,math,time,platform,importlib.metadata
import joblib
import numpy as np
import pandas as pd
from scipy.stats import beta
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parent
ALPHA=.10
SEED=20260929
VITALS=['HR','O2Sat','Temp','SBP','MAP','DBP','Resp','EtCO2']
LABS=['BaseExcess','HCO3','FiO2','pH','PaCO2','SaO2','AST','BUN','Alkalinephos',
      'Calcium','Chloride','Creatinine','Bilirubin_direct','Glucose','Lactate',
      'Magnesium','Phosphate','Potassium','Bilirubin_total','TroponinI','Hct',
      'Hgb','PTT','WBC','Fibrinogen','Platelets']
PHYSIO=VITALS+LABS
STATIC=['Age','Gender','HospAdmTime','ICULOS']

def order_quantile(scores,alpha=.1):
    """Split-conformal rank; strictly-greater predictions handle ties conservatively.
    Guarantees require exchangeable calibration/test units. No shift guarantee.
    """
    scores=np.asarray(scores,dtype=float)
    if not len(scores) or not np.isfinite(scores).all():raise ValueError('Bad scores')
    k=math.ceil((len(scores)+1)*(1-alpha))
    return float(np.partition(scores,k-1)[k-1]) if k<=len(scores) else float('inf')

def binomial_ci(k,n):
    if not n:return [None,None]
    return [0. if k==0 else float(beta.ppf(.025,k,n-k+1)),
            1. if k==n else float(beta.ppf(.975,k+1,n-k))]

def features(frame):
    raw=frame[PHYSIO].astype(np.float32)
    last=raw.ffill()
    measured=raw.notna()
    hour=np.arange(len(frame),dtype=np.float32)
    last_index=np.maximum.accumulate(np.where(measured.to_numpy(),hour[:,None],-999),axis=0)
    age=np.minimum(hour[:,None]-last_index,168)
    recent=raw[VITALS[:7]].rolling(6,min_periods=1).mean()
    change=last[VITALS[:7]]-last[VITALS[:7]].shift(6)
    return np.column_stack([last,frame[STATIC],measured.astype(np.float32),age,recent,change]).astype(np.float32)

def prepare(record):
    path=ROOT/'data'/record['site']/record['name']
    frame=pd.read_csv(path,sep='|')
    if not set(PHYSIO+STATIC+['SepsisLabel']).issubset(frame.columns):raise ValueError(path)
    hours=frame.ICULOS.to_numpy(float);y=frame.SepsisLabel.to_numpy(int)
    if np.any(np.diff(hours)!=1) or not np.isin(y,[0,1]).all():raise ValueError('Unexpected sequence')
    if not np.isfinite(frame.Age.iloc[0]) or frame.Age.iloc[0]<18:return None,'not_adult'
    if hours[-1]<6:return None,'too_short'
    positive=np.flatnonzero(y==1);onset=None
    if len(positive):
        first=int(positive[0])
        if np.any(y[first:]!=1):raise ValueError('Non-monotone label')
        onset=float(hours[first]+6)  # Released labels already start six hours early.
        if hours[first]<=6:return None,'early_or_left_censored_onset'
        if onset>hours[-1]:return None,'onset_beyond_observed_record'
    keep=hours>=6
    if onset is not None:keep&=hours<onset
    if not keep.any():return None,'no_eligible_hours'
    return {'id':record['site']+'_'+path.stem,'site':record['site'],
            'x':features(frame)[keep],'y':y[keep],'hours':hours[keep],
            'septic':bool(len(positive)),'onset':onset,'record_hours':float(hours[-1]),
            'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()},None

def assign_pilot(records):
    out=[]
    for site in ['A','B']:
        rows=[r for r in records if r['role']=='pilot' and r['site']==site]
        rows.sort(key=lambda r:hashlib.sha256(f"20260929|{site}|{r['name']}".encode()).hexdigest())
        for i,row in enumerate(rows):
            fraction=i/len(rows)
            role=('train' if fraction<.6 else ('calibration' if fraction<.8 else 'evaluation')) if site=='A' else ('calibration' if fraction<.2 else 'evaluation')
            out.append({**row,'pilot_role':role})
    return out

def thresholds(patients):
    negative=[p for p in patients if not p['septic']]
    if not negative:raise ValueError('No negative calibration patients')
    hourly=np.concatenate([p['p'] for p in negative])
    maxima=np.array([p['p'].max() for p in negative])
    return {'hourly':order_quantile(hourly,ALPHA),'patient':order_quantile(maxima,ALPHA),
            'negative_patients':len(negative),'negative_hours':len(hourly)}

def evaluate(patients,threshold):
    rows=[]
    for p in patients:
        alert=p['p']>threshold
        first=float(p['hours'][np.flatnonzero(alert)[0]]) if alert.any() else None
        timely=(p['hours']>=p['onset']-6)&(p['hours']<p['onset']) if p['septic'] else np.zeros(len(alert),bool)
        rows.append({'id':p['id'],'site':p['site'],'septic':p['septic'],
                     'any_alert':bool(alert.any()),'timely_crossing':bool((alert&timely).any()),
                     'timely_first_alert':bool(first is not None and p['septic'] and p['onset']-6<=first<p['onset']),
                     'premature_first_alert':bool(first is not None and p['septic'] and first<p['onset']-6),
                     'first_alert_hour':first,'onset_hour':p['onset'],'record_hours':p['record_hours'],
                     'max_score':float(p['p'].max()),
                     'negative_hour_alerts':int(alert.sum()) if not p['septic'] else 0,
                     'negative_hours':len(alert) if not p['septic'] else 0})
    frame=pd.DataFrame(rows);neg=frame[~frame.septic];pos=frame[frame.septic]
    y=np.concatenate([p['y'] for p in patients]);prob=np.concatenate([p['p'] for p in patients])
    n,k=len(neg),int(neg.any_alert.sum());s=int(pos.timely_crossing.sum())
    result={'patients':len(frame),'nonseptic_patients':n,'septic_patients':len(pos),
            'false_alerted_patients':k,'patient_false_alert_rate':k/n if n else None,
            'patient_false_alert_rate_ci95':binomial_ci(k,n),
            'timely_detected_patients':s,'six_hour_window_sensitivity':s/len(pos) if len(pos) else None,
            'sensitivity_ci95':binomial_ci(s,len(pos)),
            'timely_first_alert_sensitivity':float(pos.timely_first_alert.mean()) if len(pos) else None,
            'premature_first_alert_fraction':float(pos.premature_first_alert.mean()) if len(pos) else None,
            'hourly_false_positive_rate':int(neg.negative_hour_alerts.sum())/int(neg.negative_hours.sum()) if n else None,
            'hourly_auroc':float(roc_auc_score(y,prob)) if len(np.unique(y))==2 else None,
            'hourly_auprc':float(average_precision_score(y,prob)) if y.sum() else None,
            'hourly_brier':float(brier_score_loss(y,prob)),
            'threshold':float(threshold) if np.isfinite(threshold) else None,
            'threshold_infinite':not np.isfinite(threshold)}
    return result,frame

def main():
    started=time.time();out=ROOT/'results';out.mkdir(exist_ok=True)
    records=json.loads((ROOT/'manifest.json').read_text());assigned=assign_pilot(records)
    if len(assigned)!=3000:raise RuntimeError('Expected the fixed 3,000-record pilot')
    patients=[];exclusions=[]
    for i,record in enumerate(assigned,1):
        p,reason=prepare(record)
        if reason:exclusions.append({'id':record['site']+'_'+record['name'],'role':record['pilot_role'],'reason':reason})
        else:p['role']=record['pilot_role'];patients.append(p)
        if i%500==0:print(f'Prepared {i}/{len(assigned)}',flush=True)
    ids=[p['id'] for p in patients];assert len(ids)==len(set(ids))
    train=[p for p in patients if p['site']=='A' and p['role']=='train']
    x=np.concatenate([p['x'] for p in train]);y=np.concatenate([p['y'] for p in train])
    print('Training',x.shape,'positive hours',int(y.sum()),flush=True)
    model=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,learning_rate=.07,
        min_samples_leaf=40,l2_regularization=1.,early_stopping=False,random_state=SEED)
    with threadpool_limits(limits=4):
        model.fit(x,y)
        for p in patients:p['p']=model.predict_proba(p['x'])[:,1]
    joblib.dump(model,out/'pilot_model.joblib')
    cal={site:thresholds([p for p in patients if p['site']==site and p['role']=='calibration']) for site in ['A','B']}
    results=[];details=[]
    for site in ['A','B']:
        evaluation=[p for p in patients if p['site']==site and p['role']=='evaluation']
        policies={'source_hourly':cal['A']['hourly'],'source_patient':cal['A']['patient']}
        if site=='B':policies['target_patient']=cal['B']['patient']
        for policy,threshold in policies.items():
            result,frame=evaluate(evaluation,threshold)
            result.update({'site':site,'policy':policy});results.append(result)
            frame['policy']=policy;details.append(frame)
    pd.DataFrame(exclusions,columns=['id','role','reason']).to_csv(out/'pilot_exclusions.csv',index=False)
    pd.concat(details).to_csv(out/'pilot_patient_metrics.csv',index=False)
    pd.DataFrame([{k:v for k,v in r.items() if not isinstance(v,list)} for r in results]).to_csv(out/'pilot_metrics.csv',index=False)
    pd.DataFrame([{k:p[k] for k in ['id','site','role','septic','onset','record_hours','source_sha256']} for p in patients]).to_csv(out/'pilot_cohort.csv',index=False)
    # Raw hourly predictions support independent rescoring and later diagnostics.
    offsets=np.r_[0,np.cumsum([len(p['p']) for p in patients])]
    np.savez_compressed(out/'pilot_hourly_predictions.npz',id=np.array(ids),offsets=offsets,
        probability=np.concatenate([p['p'] for p in patients]),
        hours=np.concatenate([p['hours'] for p in patients]),labels=np.concatenate([p['y'] for p in patients]))
    payload={'status':'PILOT_ONLY_NOT_CONFIRMATORY','seed':SEED,'nominal_alpha':ALPHA,
        'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest(),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'manifest_sha256':hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest(),
        'source_model':'Fixed histogram gradient boosting; hospital A pilot training only',
        'calibration':cal,'excluded_records':len(exclusions),'included_records':len(patients),
        'reserved_records_never_loaded':len(records)-len(assigned),'results':results,
        'packages':{p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','scikit-learn','joblib']},
        'python':platform.python_version(),'elapsed_seconds':time.time()-started,
        'restoration_note':'Analysis restored from logged code after a temporary runtime reset; development rerun, not a new independent validation.'}
    (out/'pilot_results.json').write_text(json.dumps(payload,indent=2,allow_nan=False))
    print(json.dumps(payload,indent=2),flush=True)

if __name__=='__main__':main()
