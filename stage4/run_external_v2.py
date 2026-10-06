"""Post-test amendment: add charted Temp/FiO2 to the unchanged external core."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import run_external as core

STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parent
ORIGINAL_RAW_EVENTS=core.raw_events

def chart_available(event,entry):
    a=np.asarray(event,dtype=float);b=np.asarray(entry,dtype=float)
    return np.maximum(a,np.where(np.isfinite(b),b,a))

def temperature(values,name):
    v=pd.to_numeric(values,errors='coerce')
    if name=='Temperature (F)':v=(v-32)*5/9
    elif name!='Temperature (C)':raise ValueError('Temperature units are not explicit')
    return v

def amended_events(stay_ids):
    original=ORIGINAL_RAW_EVENTS(stay_ids)
    n=pd.read_csv(core.DATA/'eicu/nurseCharting.csv.gz',low_memory=False)
    n=n[n.patientunitstayid.isin(stay_ids)]
    parts=[original];audit=[]
    for name in ['Temperature (C)','Temperature (F)']:
        d=n[n.nursingchartcelltypevalname==name]
        v=temperature(d.nursingchartvalue,name)
        t=pd.DataFrame({'stay_id':d.patientunitstayid,'offset':chart_available(d.nursingchartoffset,d.nursingchartentryoffset),
                        'record_id':d.nursingchartid,'value':v,'channel':'Temp',
                        'table_order':4 if name=='Temperature (C)' else 3})
        t=t[np.isfinite(t.value)&np.isfinite(t.offset)];parts.append(t)
        audit.append({'table':'nurseCharting','source':name,'channel':'Temp','rows':len(t),'unit_rejections':0})
    r=pd.read_csv(core.DATA/'eicu/respiratoryCharting.csv.gz',low_memory=False)
    r=r[r.patientunitstayid.isin(stay_ids)]
    for name in ['FiO2','FIO2 (%)','Set Fraction of Inspired Oxygen (FIO2)']:
        d=r[r.respchartvaluelabel==name]
        v=pd.to_numeric(d.respchartvalue.str.strip().str.removesuffix('%'),errors='coerce')
        t=pd.DataFrame({'stay_id':d.patientunitstayid,'offset':chart_available(d.respchartoffset,d.respchartentryoffset),
                        'record_id':d.respchartid,'value':core.fio2(v),'channel':'FiO2','table_order':5})
        t=t[np.isfinite(t.value)&np.isfinite(t.offset)];parts.append(t)
        audit.append({'table':'respiratoryCharting','source':name,'channel':'FiO2','rows':len(t),'unit_rejections':0})
    all_events=pd.concat(parts,ignore_index=True)
    all_events=all_events[(all_events.offset>=0)&(all_events.offset<60*core.CONFIG['maximum_hour'])].copy()
    all_events['hour']=core.event_hour(all_events.offset)
    all_events=all_events.sort_values(['stay_id','hour','channel','offset','table_order','record_id'])
    all_events=all_events.drop_duplicates(['stay_id','hour','channel'],keep='last')
    assert np.all(all_events.offset<all_events.hour*60)
    before=pd.read_csv(core.OUT/'channel_mapping_audit.csv')
    pd.concat([before,pd.DataFrame(audit)],ignore_index=True).to_csv(core.OUT/'channel_mapping_audit.csv',index=False)
    return all_events

def verify_amended():
    lock=json.loads((STAGE/'external_amended_lock.json').read_text())
    assert lock['external_outcome_values_examined_before_amendment'] is True
    for rel,digest in lock['inputs'].items():
        if core.sha(ROOT/rel)!=digest:raise RuntimeError('Amended frozen input changed: '+rel)
    assert core.sha(__file__)==lock['runner_sha256']
    assert core.sha(STAGE/'AMENDMENT_01_CHARTED_MEASUREMENTS.md')==lock['amendment_sha256']
    return lock

def run():
    core.OUT=STAGE/'results_amended'
    core.verify=verify_amended
    core.raw_events=amended_events
    # The shared runner records the driver as the executable code identity.
    core.__file__=str(Path(__file__).resolve())
    core.run()
    path=core.OUT/'completed.json';record=json.loads(path.read_text())
    record.update(status='EXPLORATORY_POST_TEST_AMENDED_EXTERNAL_DEMO_COMPLETED',
                  post_test_exploratory_amendment=True,
                  original_external_completion_sha256=core.sha(STAGE/'results/completed.json'),
                  external_amended_lock_sha256=core.sha(STAGE/'external_amended_lock.json'))
    core.write_json(path,record)

if __name__=='__main__':run()
