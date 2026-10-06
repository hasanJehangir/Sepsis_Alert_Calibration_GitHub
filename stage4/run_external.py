"""External public-demo transport evaluation, preserving all frozen source models."""
from pathlib import Path
import datetime, hashlib, importlib.metadata, json, math, platform, sys
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from threadpoolctl import threadpool_limits

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'stage3'))
from experiment import features, PHYSIO
from run_followup import effective_scores, emissions, finite_quantile, metrics, patient_results

CONFIG = json.loads((STAGE / 'config.json').read_text())
DATA = STAGE / 'data'
OUT = STAGE / 'results'
LAB_MAP = {
    'Base Excess': ('BaseExcess', 'mEq/L', 1),
    'Base Deficit': ('BaseExcess', 'mEq/L', -1),
    'HCO3': ('HCO3', 'mmol/L', 1),
    'FiO2': ('FiO2', '%', 1),
    'pH': ('pH', None, 1),
    'paCO2': ('PaCO2', 'mm Hg', 1),
    'O2 Sat (%)': ('SaO2', '%', 1),
    'AST (SGOT)': ('AST', 'Units/L', 1),
    'BUN': ('BUN', 'mg/dL', 1),
    'alkaline phos.': ('Alkalinephos', 'Units/L', 1),
    'calcium': ('Calcium', 'mg/dL', 1),
    'chloride': ('Chloride', 'mmol/L', 1),
    'creatinine': ('Creatinine', 'mg/dL', 1),
    'direct bilirubin': ('Bilirubin_direct', 'mg/dL', 1),
    'glucose': ('Glucose', 'mg/dL', 1),
    'lactate': ('Lactate', 'mmol/L', 1),
    'magnesium': ('Magnesium', 'mg/dL', 1),
    'phosphate': ('Phosphate', 'mg/dL', 1),
    'potassium': ('Potassium', 'mmol/L', 1),
    'total bilirubin': ('Bilirubin_total', 'mg/dL', 1),
    'troponin - I': ('TroponinI', 'ng/mL', 1),
    'Hct': ('Hct', '%', 1),
    'Hgb': ('Hgb', 'g/dL', 1),
    'PTT': ('PTT', 'sec', 1),
    'WBC x 1000': ('WBC', 'K/mcL', 1),
    'fibrinogen': ('Fibrinogen', 'mg/dL', 1),
    'platelets x 1000': ('Platelets', 'K/mcL', 1),
}
PERIODIC = {'heartrate':'HR', 'sao2':'O2Sat', 'temperature':'Temp',
            'systemicsystolic':'SBP', 'systemicmean':'MAP', 'systemicdiastolic':'DBP',
            'respiration':'Resp', 'etco2':'EtCO2'}
APERIODIC = {'noninvasivesystolic':'SBP', 'noninvasivemean':'MAP', 'noninvasivediastolic':'DBP'}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False))
def fraction(text): return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)/2**64
def event_hour(offset): return np.floor(np.asarray(offset)/60).astype(int)+1
def available_lab_offset(frame):
    return np.maximum(frame.labresultoffset.to_numpy(),
                      frame.labresultrevisedoffset.fillna(frame.labresultoffset).to_numpy())
def fio2(value): return np.where(np.asarray(value)>1, np.asarray(value)/100, value)
def time_hours(series):
    values=series.dt.total_seconds()/3600 if pd.api.types.is_timedelta64_dtype(series.dtype) else series.astype(float)
    if not np.isfinite(values).all() or not np.all(values==np.floor(values)):
        raise ValueError('Invalid imported hourly time grid')
    return values.astype(int)

def verify():
    lock=json.loads((STAGE/'external_lock.json').read_text())
    assert lock['external_outcome_values_examined_before_lock'] is False
    for relative,digest in lock['inputs'].items():
        if sha(ROOT/relative)!=digest:raise RuntimeError('Locked input changed: '+relative)
    assert sha(STAGE/'EXTERNAL_PROTOCOL.md')==lock['protocol_sha256']
    assert sha(STAGE/'config.json')==lock['config_sha256']
    assert sha(__file__)==lock['runner_sha256']
    return lock

def pick_people(patient, sta):
    # Choose a single imported stay per person before reading its outcome.
    selected=sta[['stay_id']].merge(patient,left_on='stay_id',right_on='patientunitstayid',validate='one_to_one')
    if len(selected)!=len(sta):raise ValueError('Imported stay absent from public raw patient table')
    if selected.uniquepid.isna().any():raise ValueError('Patient linkage unavailable')
    selected['selection_hash']=[hashlib.sha256(f"{CONFIG['seed']}|stay|{s}".encode()).hexdigest() for s in selected.stay_id]
    selected=selected.sort_values('selection_hash').drop_duplicates('uniquepid').copy()
    selected['role']=['calibration' if fraction(f"{CONFIG['seed']}|role|{s}")<CONFIG['calibration_fraction'] else 'test' for s in selected.uniquepid]
    selected['mapped_age']=pd.to_numeric(selected.age.replace({'> 89':'100','>89':'100'}),errors='coerce')
    selected['mapped_gender']=selected.gender.map({'Female':0.,'Male':1.})
    return selected

def raw_events(stay_ids):
    parts=[];audits=[]
    for table,mapping in [('vitalPeriodic',PERIODIC),('vitalAperiodic',APERIODIC)]:
        d=pd.read_csv(DATA/'eicu'/(table+'.csv.gz'))
        d=d[d.patientunitstayid.isin(stay_ids)]
        for name,channel in mapping.items():
            t=d[['patientunitstayid','observationoffset',table.lower()+'id',name]].rename(
                columns={'patientunitstayid':'stay_id','observationoffset':'offset',table.lower()+'id':'record_id',name:'value'})
            t=t[np.isfinite(t.value)&np.isfinite(t.offset)].copy()
            t['channel']=channel;t['table_order']=0 if table=='vitalPeriodic' else 1
            parts.append(t)
            audits.append({'table':table,'source':name,'channel':channel,'rows':len(t),'unit_rejections':0})
    lab=pd.read_csv(DATA/'eicu/lab.csv.gz')
    lab=lab[lab.patientunitstayid.isin(stay_ids)]
    for name,(channel,unit,mult) in LAB_MAP.items():
        d=lab[lab.labname==name].copy();rejected=0
        if unit is not None:
            valid=d.labmeasurenamesystem.eq(unit);rejected=int((~valid).sum());d=d[valid].copy()
        t=pd.DataFrame({'stay_id':d.patientunitstayid,'offset':available_lab_offset(d),
                        'record_id':d.labid,'value':d.labresult.to_numpy()*mult,'channel':channel,'table_order':2})
        if channel=='FiO2':t['value']=fio2(t.value)
        t=t[np.isfinite(t.value)&np.isfinite(t.offset)]
        parts.append(t)
        audits.append({'table':'lab','source':name,'channel':channel,'expected_system_unit':unit,
                       'rows':len(t),'unit_rejections':rejected,'multiplier':mult})
    events=pd.concat(parts,ignore_index=True)
    events=events[(events.offset>=0)&(events.offset<60*CONFIG['maximum_hour'])].copy()
    events['hour']=event_hour(events.offset)
    # Stable final ordering makes duplicate-time selection reproducible.
    events=events.sort_values(['stay_id','hour','channel','offset','table_order','record_id'])
    events=events.drop_duplicates(['stay_id','hour','channel'],keep='last')
    assert np.all(events.offset<events.hour*60)
    assert np.all(events.offset>=(events.hour-1)*60)
    pd.DataFrame(audits).to_csv(OUT/'channel_mapping_audit.csv',index=False)
    return events

def build_cohort(selected, events):
    target=pd.read_parquet(DATA/'yaib/outc.parquet')
    target['hour']=time_hours(target.time)
    if not target.label.isin([False,True,0,1]).all():raise ValueError('Nonbinary imported label')
    if target.duplicated(['stay_id','hour']).any():raise ValueError('Duplicate imported outcome row')
    target=target.sort_values(['stay_id','hour'])
    groups={int(s):d for s,d in target.groupby('stay_id',sort=False)}
    paths={int(s):d for s,d in events.groupby('stay_id',sort=False)}
    frames=[];meta=[];excluded=[];widths=[];offset=0;unit_counts={};variant_arrays={v:[] for v in CONFIG['input_variants']}
    for r in selected.itertuples():
        sid=int(r.stay_id);reason=None
        if not np.isfinite(r.mapped_age) or r.mapped_age<18:reason='unknown_or_nonadult_age'
        if sid not in groups:raise ValueError('Imported stay without label grid')
        label=groups[sid];ts=label.hour.to_numpy()
        if np.any(np.diff(ts)!=1):raise ValueError('Gap in imported outcome grid')
        positive=label.loc[label.label.astype(bool),'hour'].to_numpy()
        onset=float(positive[0]+CONFIG['label_onset_shift_hours']) if len(positive) else None
        if len(positive):
            if np.any(np.diff(positive)!=1) or len(positive)>13:raise ValueError('Published label window cannot reconstruct a unique event')
            widths.append({'stay_id':sid,'positive_rows':len(positive),'first_positive_hour':int(positive[0]),'reconstructed_onset':onset})
        end=min(int(np.floor(r.unitdischargeoffset/60)),CONFIG['maximum_hour'],int(ts[-1]))
        if end<6:reason=reason or 'insufficient_complete_observation'
        if len(positive) and positive[0]<=6:reason=reason or 'early_or_left_censored_onset'
        if onset is not None and onset>end:reason=reason or 'onset_beyond_complete_observation'
        if reason:
            excluded.append({'stay_id':sid,'role':r.role,'reason':reason});continue
        frame=pd.DataFrame(np.nan,index=np.arange(1,end+1),columns=PHYSIO)
        if sid in paths:
            e=paths[sid];e=e[e.hour<=end]
            pivot=e.pivot(index='hour',columns='channel',values='value')
            frame.loc[pivot.index,pivot.columns]=pivot
        frame['Age']=r.mapped_age;frame['Gender']=r.mapped_gender
        frame['HospAdmTime']=r.hospitaladmitoffset/60;frame['ICULOS']=frame.index.astype(float)
        h=frame.ICULOS.to_numpy();keep=(h>=6)&((h<onset) if onset is not None else True)
        if not keep.any():raise ValueError('Eligible person lacks scoring hours')
        # Clinical grid labels are aligned with score availability, not the prior raw event bin.
        y=label.set_index('hour').label.reindex(h[keep].astype(int))
        if y.isna().any():raise ValueError('No label at a score availability hour')
        for variant in CONFIG['input_variants']:
            f=frame.copy()
            if variant=='mask_ambiguous_units':f[['Lactate','Magnesium']]=np.nan
            x=features(f)
            assert x.shape==(len(f),120) and not np.isinf(x).any()
            variant_arrays[variant].append(x[keep])
        for channel in PHYSIO:
            unit_counts[channel]=unit_counts.get(channel,0)+int(frame.loc[keep,channel].notna().sum())
        n=int(keep.sum());frames.append((h[keep],y.astype(int).to_numpy()))
        meta.append({'id':'E_'+str(sid),'stay_id':sid,'person_id':r.uniquepid,'hospital_id':int(r.hospitalid),
                     'role':r.role,'septic':bool(len(positive)),'onset':onset,'record_hours':end,'start':offset,'stop':offset+n})
        offset+=n
    cohort=pd.DataFrame(meta)
    assert cohort.person_id.is_unique and cohort.id.is_unique
    assert not set(cohort[cohort.role=='calibration'].person_id)&set(cohort[cohort.role=='test'].person_id)
    cohort.to_csv(OUT/'external_cohort.csv',index=False)
    pd.DataFrame(excluded,columns=['stay_id','role','reason']).to_csv(OUT/'external_exclusions.csv',index=False)
    pd.DataFrame(widths).to_csv(OUT/'label_window_audit.csv',index=False)
    pd.DataFrame([{'channel':k,'observed_scoring_rows':v,'total_scoring_rows':offset,'observed_fraction':v/offset} for k,v in unit_counts.items()]).to_csv(OUT/'feature_availability.csv',index=False)
    arrays={v:np.concatenate(rows) for v,rows in variant_arrays.items()}
    hours=np.concatenate([x[0] for x in frames]);labels=np.concatenate([x[1] for x in frames])
    for v,x in arrays.items():np.save(OUT/(v+'_features.npy'),x)
    np.save(OUT/'external_hours.npy',hours);np.save(OUT/'external_labels.npy',labels)
    return cohort,arrays,hours,labels

def clinical_paths(cohort,p,h):
    result={}
    for role in ['calibration','test']:
        rows=[]
        for r in cohort[cohort.role==role].itertuples():
            sl=slice(int(r.start),int(r.stop));prob=p[sl]
            assert np.isfinite(prob).all()
            rows.append({'id':r.id,'septic':bool(r.septic),'onset':float(r.onset) if r.septic else None,
                         'h':h[sl],'p':prob,'three_of_five':effective_scores(prob,'three_of_five'),'hours':len(prob)})
        result[role]=rows
    return result

def run():
    lock=verify();OUT.mkdir(exist_ok=True)
    patient=pd.read_csv(DATA/'eicu/patient.csv.gz');sta=pd.read_parquet(DATA/'yaib/sta.parquet')
    selected=pick_people(patient,sta)
    selected[['stay_id','uniquepid','role','selection_hash']].to_csv(OUT/'outcome_blind_people_selection.csv',index=False)
    event=raw_events(set(selected.stay_id))
    cohort,arrays,h,y=build_cohort(selected,event)
    counts=cohort.groupby('role').agg(people=('id','size'),sepsis=('septic','sum'),hospitals=('hospital_id','nunique')).reset_index()
    counts.to_csv(OUT/'external_counts.csv',index=False);print(counts.to_string(index=False),flush=True)
    prior=pd.read_csv(ROOT/'stage2/results/main_metrics.csv');prior=prior[prior.cap=='natural']
    records=[];disc=[]
    for source in CONFIG['sources']:
        for model in CONFIG['models']:
            prefix=source+'_'+model
            fitted=joblib.load(ROOT/'stage2/results'/(prefix+'_model.joblib'))
            info=json.loads((ROOT/'stage2/results'/(prefix+'_model_info.json')).read_text())
            for variant,x in arrays.items():
                with threadpool_limits(limits=4):p=fitted.predict_proba(x[:,info['features']])[:,1]
                np.savez_compressed(OUT/(prefix+'_'+variant+'_predictions.npz'),probability=p)
                paths=clinical_paths(cohort,p,h)
                idx=np.concatenate([np.arange(int(r.start),int(r.stop)) for r in cohort[cohort.role=='test'].itertuples()])
                yt,pt=y[idx],p[idx]
                disc.append({'source':source,'model':model,'input_variant':variant,'test_hours':len(idx),
                             'hourly_positive_prevalence':float(yt.mean()),
                             'hourly_auroc':float(roc_auc_score(yt,pt)) if len(np.unique(yt))==2 else None,
                             'hourly_average_precision':float(average_precision_score(yt,pt)) if yt.sum() else None,
                             'hourly_brier':float(brier_score_loss(yt,pt))})
                neg=[r for r in paths['calibration'] if not r['septic']]
                if not neg:raise ValueError('No negative external calibration people')
                for condition in CONFIG['conditions']:
                    for policy in CONFIG['policies']:
                        if condition=='local_patient':
                            values=[np.max(r['three_of_five'] if policy=='three_of_five' else r['p']) for r in neg]
                            threshold=finite_quantile(values,CONFIG['alpha'])
                        else:
                            anchors=prior[(prior.source==source)&(prior.model==model)&(prior.policy==condition)]
                            assert anchors.threshold.nunique()==1
                            threshold=float(anchors.iloc[0].threshold)
                        frame=patient_results(paths['test'],threshold,policy)
                        if policy in ['single','silence4','silence6']:
                            raw=patient_results(paths['test'],threshold,'hourly')
                            assert frame.any_alert.tolist()==raw.any_alert.tolist()
                            assert frame.first6.tolist()==raw.first6.tolist()
                            assert np.all(frame.alerts.to_numpy()<=raw.alerts.to_numpy())
                        if policy=='single':assert frame.window6.tolist()==frame.first6.tolist()
                        records.append({'source':source,'model':model,'input_variant':variant,'condition':condition,
                                        'policy':policy,'threshold':threshold if np.isfinite(threshold) else None,
                                        'threshold_infinite':not np.isfinite(threshold),
                                        'calibration_nonseptic_people':len(neg),**metrics(frame)})
                print('Evaluated frozen',prefix,variant,flush=True)
    pd.DataFrame(records).to_csv(OUT/'external_policy_metrics.csv',index=False)
    pd.DataFrame(disc).to_csv(OUT/'external_discrimination.csv',index=False)
    completion={'status':'EXTERNAL_PUBLIC_DEMO_EVALUATION_COMPLETED','completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'verified_hospital_patient_independence':False,'clinical_validation_completed':False,'human_review_completed':False,
                'eligible_people':len(cohort),'scoring_hours':len(h),'policy_rows':len(records),'discrimination_rows':len(disc),
                'label_definition_differs_from_challenge':True,'input_units_require_review':['Lactate','Magnesium'],
                'source_models_refitted':False,'external_lock_sha256':sha(STAGE/'external_lock.json'),'runner_sha256':sha(__file__),
                'python':platform.python_version(),'versions':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','joblib','pyarrow']},
                'frozen_input_hashes_unchanged':True,'role_person_overlap':0}
    verify();write_json(OUT/'completed.json',completion);print(json.dumps(completion,indent=2),flush=True)

if __name__=='__main__':run()
