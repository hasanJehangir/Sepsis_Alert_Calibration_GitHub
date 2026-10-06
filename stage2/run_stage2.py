"""Locked, CPU-only two-hospital calibration study. No pilot reuse or tuning on test.

Run from any directory: python stage2/run_stage2.py --stage all
Input: the original manifest and public PSV files. See STAGE2_PROTOCOL.md.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.metadata,json,math,platform,sys,time,warnings
import numpy as np
import pandas as pd
import joblib
from scipy.stats import beta
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parent
sys.path.insert(0,str(ROOT))
import experiment as pilot
CONFIG=json.loads((STAGE/'study_config.json').read_text())
CACHE=STAGE/'cache'
OUT=STAGE/'results'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False));temp.replace(path)

def provenance():
    lock=json.loads((STAGE/'protocol_lock.json').read_text())
    for name,path in [('manifest',ROOT/'manifest.json'),('protocol',STAGE/'STAGE2_PROTOCOL.md'),
                      ('config',STAGE/'study_config.json'),('pilot_code',ROOT/'experiment.py')]:
        if lock[name+'_sha256']!=sha(path):raise RuntimeError(f'Locked {name} changed; record an amendment before proceeding')
    return {'lock':lock,'runner_sha256':sha(__file__),
            'packages':{p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','scikit-learn','joblib']},
            'python':platform.python_version()}

def signature():return hashlib.sha256(json.dumps(provenance(),sort_keys=True).encode()).hexdigest()

def prepare():
    """Build disk-backed arrays once. Exact raw duplicates are removed globally."""
    CACHE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    sig=signature()
    if (CACHE/'complete.json').exists():
        if json.loads((CACHE/'complete.json').read_text())['signature']!=sig:raise RuntimeError('Cache code/config changed; use a clean cache and log the reason')
        print('Using verified feature cache',flush=True);return
    records=json.loads((ROOT/'manifest.json').read_text())
    selected=[r for r in records if r['role']!='pilot']
    assert len(selected)==37336
    missing=[r['name'] for r in selected if not (ROOT/'data'/r['site']/r['name']).exists()]
    if missing:raise RuntimeError(f'{len(missing)} reserved files missing; finish the downloader first')
    write_json(OUT/'run_start.json',{'started_at_utc':now(),'signature':sig,'provenance':provenance(),
                                 'status':'STARTED_BEFORE_RESERVED_LABEL_LOADING'})
    seen={sha(ROOT/'data'/r['site']/r['name']):'pilot' for r in records if r['role']=='pilot'}
    priority={'train':0,'calibration':1,'test':2}
    selected.sort(key=lambda r:(priority[r['role']],r['site'],r['name']))
    rows=[];excluded=[];arrays=[];hours=[];labels=[];offset=0
    started=time.time()
    for i,r in enumerate(selected,1):
        identifier=r['site']+'_'+Path(r['name']).stem
        digest=sha(ROOT/'data'/r['site']/r['name'])
        if digest in seen:
            excluded.append({'id':identifier,'site':r['site'],'role':r['role'],'reason':'exact_duplicate','duplicate_of':seen[digest]})
            continue
        seen[digest]=identifier
        p,reason=pilot.prepare(r)
        if reason:
            excluded.append({'id':identifier,'site':r['site'],'role':r['role'],'reason':reason,'duplicate_of':None})
            continue
        if np.isinf(p['x']).any():raise ValueError('Infinite raw/derived feature; audit before continuing')
        n=len(p['y'])
        rows.append({'id':p['id'],'site':p['site'],'role':r['role'],'septic':p['septic'],
                     'onset':p['onset'],'record_hours':p['record_hours'],
                     'age':float(p['x'][0,34]),'gender':float(p['x'][0,35]),
                     'source_sha256':digest,'start':offset,'stop':offset+n})
        arrays.append(p['x']);hours.append(p['hours'].astype(np.float32));labels.append(p['y'].astype(np.uint8));offset+=n
        if i%2000==0:print(f'Prepared {i}/{len(selected)} records, {time.time()-started:.0f}s',flush=True)
    metadata=pd.DataFrame(rows)
    assert metadata.id.is_unique and metadata.source_sha256.is_unique
    assert set(metadata.role)=={'train','calibration','test'}
    np.save(CACHE/'x.npy',np.concatenate(arrays));del arrays
    np.save(CACHE/'hours.npy',np.concatenate(hours));del hours
    np.save(CACHE/'labels.npy',np.concatenate(labels));del labels
    metadata.to_csv(CACHE/'patients.csv',index=False)
    metadata.to_csv(OUT/'cohort.csv',index=False)
    pd.DataFrame(excluded).to_csv(OUT/'exclusions.csv',index=False)
    counts=metadata.groupby(['site','role']).agg(patients=('id','size'),sepsis=('septic','sum')).reset_index()
    counts.to_csv(OUT/'cohort_counts.csv',index=False)
    write_json(CACHE/'complete.json',{'signature':sig,'patients':len(rows),'hours':offset,
                                    'excluded':len(excluded),'finished_at_utc':now()})
    print(counts.to_string(index=False),flush=True)

def load_cache():
    complete=json.loads((CACHE/'complete.json').read_text())
    if complete['signature']!=signature():raise RuntimeError('Feature cache signature mismatch')
    return pd.read_csv(CACHE/'patients.csv'),np.load(CACHE/'x.npy',mmap_mode='r'),np.load(CACHE/'hours.npy',mmap_mode='r'),np.load(CACHE/'labels.npy',mmap_mode='r')

def row_indices(rows):return np.concatenate([np.arange(int(r.start),int(r.stop)) for r in rows.itertuples()])
def feature_columns(name):
    if name=='hgb_no_observation_features':return np.array(list(range(37))+list(range(106,120)))
    return np.arange(120)

def new_model(name):
    if name=='logistic':return make_pipeline(SimpleImputer(strategy='median',keep_empty_features=True),StandardScaler(),LogisticRegression(**CONFIG['logistic']))
    return HistGradientBoostingClassifier(**CONFIG['hgb'])

def train():
    metadata,x,hours,y=load_cache()
    evaluation_rows=metadata[metadata.role!='train'];eval_indices=row_indices(evaluation_rows)
    for source in CONFIG['source_sites']:
        train_indices=row_indices(metadata[(metadata.site==source)&(metadata.role=='train')])
        assert not np.intersect1d(train_indices,eval_indices).size
        for name in CONFIG['models']:
            prefix=f'{source}_{name}';info_path=OUT/(prefix+'_model_info.json')
            if info_path.exists():
                info=json.loads(info_path.read_text())
                if info['signature']!=signature():raise RuntimeError('Existing model signature mismatch')
                print('Using completed model',prefix,flush=True);continue
            columns=feature_columns(name)
            features=np.asarray(x[train_indices][:,columns]);target=np.asarray(y[train_indices])
            model=new_model(name);started=time.time()
            print('Fitting',prefix,features.shape,'positive hours',int(target.sum()),flush=True)
            with warnings.catch_warnings(record=True) as caught,threadpool_limits(limits=CONFIG['threads']):
                warnings.simplefilter('always',ConvergenceWarning)
                model.fit(features,target)
                del features
                probabilities=np.full(len(y),np.nan,dtype=np.float64)
                for start in range(0,len(eval_indices),32768):
                    indices=eval_indices[start:start+32768]
                    probabilities[indices]=model.predict_proba(np.asarray(x[indices][:,columns]))[:,1]
            warning_text=[str(w.message) for w in caught]
            converged=not any(issubclass(w.category,ConvergenceWarning) for w in caught)
            assert np.isfinite(probabilities[eval_indices]).all()
            np.savez_compressed(OUT/(prefix+'_predictions.npz'),probability=probabilities)
            joblib.dump(model,OUT/(prefix+'_model.joblib'))
            info={'source':source,'model':name,'signature':signature(),'features':columns.tolist(),
                  'training_patients':int(((metadata.site==source)&(metadata.role=='train')).sum()),
                  'training_hours':len(train_indices),'positive_training_hours':int(target.sum()),
                  'converged':converged,'warnings':warning_text,'elapsed_seconds':time.time()-started,
                  'finished_at_utc':now()}
            if name=='logistic':info['iterations']=model[-1].n_iter_.tolist()
            write_json(info_path,info)
            print('Finished',prefix,f"{info['elapsed_seconds']:.1f}s",'converged',converged,warning_text,flush=True)
            del model,probabilities

def safe_max(values):return float(np.max(values)) if len(values) else -np.inf

def score_summary(metadata,probabilities,hours,labels,cap=None):
    """Reduce each record to sufficient statistics for all threshold endpoints."""
    rows=[];negative_hourly=[];all_prob=[];all_y=[];positive_paths={};late_cases=0
    for r in metadata.itertuples():
        if cap is not None and r.septic and r.onset>cap:
            late_cases+=1;continue
        sl=slice(int(r.start),int(r.stop));h=hours[sl];p=probabilities[sl];y=labels[sl]
        keep=np.ones(len(h),bool) if cap is None else h<=cap
        h=h[keep];p=p[keep];y=y[keep]
        if not len(p):continue
        if not np.isfinite(p).all():raise ValueError('Missing prediction on calibration/test record')
        if r.septic:
            pre6=h<r.onset-6;pre12=h<r.onset-12
            window6=(h>=r.onset-6)&(h<r.onset);window12=(h>=r.onset-12)&(h<r.onset)
            positive_paths[r.id]=(np.asarray(h),np.asarray(p),float(r.onset))
        else:
            pre6=pre12=window6=window12=np.zeros(len(h),bool)
            negative_hourly.append(np.asarray(p))
        rows.append({'id':r.id,'septic':bool(r.septic),'max':safe_max(p),
                     'window6':safe_max(p[window6]),'window12':safe_max(p[window12]),
                     'before6':safe_max(p[pre6]),'before12':safe_max(p[pre12]),
                     'hours':len(h),'record_hours':float(r.record_hours)})
        all_prob.append(np.asarray(p));all_y.append(np.asarray(y))
    frame=pd.DataFrame(rows)
    return {'frame':frame,'neg_hours':np.sort(np.concatenate(negative_hourly)),
            'prob':np.concatenate(all_prob),'y':np.concatenate(all_y),
            'positive_paths':positive_paths,'late_cases_excluded':late_cases}

def empirical_quantile(values,alpha=.1):
    values=np.asarray(values)
    if not len(values):return np.inf
    k=math.ceil((1-alpha)*len(values))
    return float(np.partition(values,k-1)[k-1])

def patient_threshold(values):
    return pilot.order_quantile(values,CONFIG['alpha']) if len(values) else np.inf

def sensitivity_threshold(summary,target=.8):
    values=summary['frame'].loc[summary['frame'].septic,'window6'].to_numpy()
    if not len(values):return np.inf
    wanted=math.ceil(target*len(values));index=len(values)-wanted
    return float(np.nextafter(np.partition(values,index)[index],-np.inf))

def indicators(summary,threshold):
    frame=summary['frame'];negative=frame.loc[~frame.septic];positive=frame.loc[frame.septic]
    crossing6=positive.window6.to_numpy()>threshold;early6=positive.before6.to_numpy()>threshold
    crossing12=positive.window12.to_numpy()>threshold;early12=positive.before12.to_numpy()>threshold
    return {'false_alert':negative['max'].to_numpy()>threshold,'window6':crossing6,
            'first6':crossing6&~early6,'early6':early6,'window12':crossing12,
            'first12':crossing12&~early12,'any_positive_alert':positive['max'].to_numpy()>threshold}

def metric_row(summary,threshold):
    signals=indicators(summary,threshold)
    names={'false_alert':'patient_false_alert_rate','window6':'window6_sensitivity',
           'first6':'first6_sensitivity','early6':'early_first_fraction',
           'window12':'window12_sensitivity','first12':'first12_sensitivity',
           'any_positive_alert':'any_positive_alert_fraction'}
    nneg=len(signals['false_alert']);npos=len(signals['window6'])
    out={'patients':nneg+npos,'nonseptic_patients':nneg,'septic_patients':npos,
         'late_cases_excluded':summary['late_cases_excluded'],
         'threshold':float(threshold) if np.isfinite(threshold) else None,'threshold_infinite':not np.isfinite(threshold)}
    for key,name in names.items():
        value=signals[key];n=len(value);k=int(value.sum());lo,hi=pilot.binomial_ci(k,n)
        out[name]=k/n if n else None;out[name+'_count']=k;out[name+'_ci_low']=lo;out[name+'_ci_high']=hi
    nh=summary['neg_hours'];count=len(nh)-int(np.searchsorted(nh,threshold,side='right'))
    out.update(negative_hours=len(nh),negative_alert_hours=count,hourly_false_positive_rate=count/len(nh) if len(nh) else None)
    return out

def discrimination(summary):
    y=summary['y'];p=summary['prob']
    return {'hourly_auroc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
            'hourly_average_precision':float(average_precision_score(y,p)) if y.sum() else None,
            'hourly_brier':float(brier_score_loss(y,p)),
            'hourly_positive_prevalence':float(y.mean()),'hours':len(y)}

def paired_difference(summary,threshold1,threshold0,draws=2000,seed=20260929):
    a=indicators(summary,threshold1);b=indicators(summary,threshold0);rng=np.random.default_rng(seed);out={}
    for key in ['false_alert','window6','first6']:
        delta=a[key].astype(int)-b[key].astype(int);n=len(delta)
        if not n:out[key]={'difference':None,'ci_low':None,'ci_high':None,'n':0};continue
        # Multinomial counts are exactly equivalent to resampling paired patient deltas.
        counts=np.array([(delta==v).sum() for v in [-1,0,1]])
        samples=rng.multinomial(n,counts/n,size=draws)
        values=(samples[:,2]-samples[:,0])/n
        out[key]={'difference':float(delta.mean()),'ci_low':float(np.quantile(values,.025)),
                  'ci_high':float(np.quantile(values,.975)),'n':n}
    return out

def calibration_samples(metadata):
    samples={}
    for site in CONFIG['source_sites']:
        ids=sorted(metadata.loc[(metadata.site==site)&(metadata.role=='calibration'),'id'].tolist())
        assert len(ids)>=max(CONFIG['local_budgets'])
        for seed in CONFIG['calibration_seeds']:
            order=np.random.default_rng(seed).permutation(ids).tolist()
            for budget in CONFIG['local_budgets']:samples[f'{site}|{seed}|{budget}']=order[:budget]
    return samples

def evaluate_all():
    metadata,x,hours,y=load_cache();del x
    samples=calibration_samples(metadata);write_json(OUT/'calibration_samples.json',samples)
    records=[];discriminations=[];differences=[];timing=[];threshold_rows=[]
    for source in CONFIG['source_sites']:
        for model in CONFIG['models']:
            prefix=f'{source}_{model}'
            info=json.loads((OUT/(prefix+'_model_info.json')).read_text())
            if info['signature']!=signature():raise RuntimeError('Prediction provenance mismatch')
            probabilities=np.load(OUT/(prefix+'_predictions.npz'))['probability']
            for cap in CONFIG['caps']:
                cap_name='natural' if cap is None else str(cap)
                summaries={}
                for site in CONFIG['source_sites']:
                    for role in ['calibration','test']:
                        summary=score_summary(metadata[(metadata.site==site)&(metadata.role==role)],probabilities,hours,y,cap)
                        summaries[site,role]=summary
                        summary['frame'].to_csv(OUT/f'{prefix}_{site}_{role}_{cap_name}_scores.csv.gz',index=False)
                source_cal=summaries[source,'calibration'];sc=source_cal['frame'];source_max=sc.loc[~sc.septic,'max'].to_numpy()
                source_policies={'source_hourly':patient_threshold(source_cal['neg_hours']),
                                 'source_patient':patient_threshold(source_max),
                                 'source_empirical_patient':empirical_quantile(source_max,CONFIG['alpha']),
                                 'source_sensitivity80':sensitivity_threshold(source_cal,CONFIG['sensitivity_target'])}
                for site in CONFIG['source_sites']:
                    cal=summaries[site,'calibration'];test=summaries[site,'test'];frame=cal['frame']
                    max_by_id=frame.loc[~frame.septic].set_index('id')['max']
                    target_policies={'target_patient_all':patient_threshold(max_by_id.to_numpy()),
                                     'target_empirical_patient_all':empirical_quantile(max_by_id.to_numpy(),CONFIG['alpha'])}
                    policies={**source_policies,**target_policies}
                    base={'source':source,'model':model,'test_site':site,'transfer':source!=site,'cap':cap_name,
                          'model_converged':info['converged']}
                    discriminations.append({**base,**discrimination(test)})
                    for name,threshold in policies.items():
                        record={**base,'policy':name,'budget':None,'calibration_seed':None,
                                'calibration_nonseptic_patients':len(max_by_id) if name.startswith('target') else len(source_max),
                                **metric_row(test,threshold)}
                        records.append(record)
                        threshold_rows.append({k:record[k] for k in ['source','model','test_site','cap','policy','threshold','threshold_infinite','calibration_nonseptic_patients']})
                        if cap is None:
                            for identifier,(h,p,onset) in test['positive_paths'].items():
                                crossings=np.flatnonzero(p>threshold)
                                first=float(h[crossings[0]]) if len(crossings) else None
                                timing.append({**base,'policy':name,'id':identifier,'onset':onset,'first_alert':first,
                                               'lead_hours':onset-first if first is not None else None})
                    if cap is None:
                        for name,a,b in [('patient_minus_hourly','source_patient','source_hourly'),
                                         ('local_minus_source_patient','target_patient_all','source_patient')]:
                            result=paired_difference(test,policies[a],policies[b],CONFIG['bootstrap_draws'],CONFIG['seed'])
                            for endpoint,value in result.items():differences.append({**base,'comparison':name,'endpoint':endpoint,**value})
                    for seed in CONFIG['calibration_seeds']:
                        for budget in CONFIG['local_budgets']:
                            ids=samples[f'{site}|{seed}|{budget}']
                            values=max_by_id.reindex(ids).dropna().to_numpy();threshold=patient_threshold(values)
                            records.append({**base,'policy':'target_patient_budget','budget':budget,'calibration_seed':seed,
                                            'calibration_nonseptic_patients':len(values),**metric_row(test,threshold)})
                print('Evaluated',prefix,'cap',cap_name,flush=True)
            del probabilities
    metrics=pd.DataFrame(records);metrics.to_csv(OUT/'all_metrics.csv',index=False)
    metrics[metrics.policy!='target_patient_budget'].to_csv(OUT/'main_metrics.csv',index=False)
    pd.DataFrame(discriminations).to_csv(OUT/'discrimination.csv',index=False)
    pd.DataFrame(differences).to_csv(OUT/'paired_differences.csv',index=False)
    pd.DataFrame(timing).to_csv(OUT/'first_alert_timing.csv',index=False)
    pd.DataFrame(threshold_rows).to_csv(OUT/'thresholds.csv',index=False)
    budget=metrics[metrics.policy=='target_patient_budget'];summary=[]
    keys=['source','model','test_site','transfer','cap','budget']
    for values,frame in budget.groupby(keys):
        for endpoint in ['patient_false_alert_rate','window6_sensitivity','first6_sensitivity','first12_sensitivity','calibration_nonseptic_patients']:
            a=frame[endpoint].dropna().to_numpy()
            summary.append({**dict(zip(keys,values)),'endpoint':endpoint,'samples':len(a),
                            'median':float(np.median(a)),'min':float(a.min()),'max':float(a.max()),
                            'p05':float(np.quantile(a,.05)),'p95':float(np.quantile(a,.95))})
    pd.DataFrame(summary).to_csv(OUT/'budget_summary.csv',index=False)
    complete={'status':'STAGE2_COMPLETED_RETROSPECTIVE_RESEARCH_ONLY','completed_at_utc':now(),
              'signature':signature(),'provenance':provenance(),'metric_rows':len(metrics),
              'models_fitted':len(CONFIG['models'])*len(CONFIG['source_sites']),
              'cache':json.loads((CACHE/'complete.json').read_text()),
              'not_a_preregistration':True,'clinical_validation':False}
    write_json(OUT/'completed.json',complete)
    print(json.dumps(complete,indent=2),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','train','evaluate','all'],default='all')
    args=parser.parse_args();provenance()
    if args.stage in ['prepare','all']:prepare()
    if args.stage in ['train','all']:train()
    if args.stage in ['evaluate','all']:evaluate_all()

if __name__=='__main__':main()
