from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_external as e

def test_bins_wait_until_complete_hour():
    offsets=np.array([0,59.9,60,119.9,120])
    np.testing.assert_array_equal(e.event_hour(offsets),[1,1,2,2,3])
    assert np.all(offsets<60*e.event_hour(offsets))

def test_corrected_results_use_later_offset():
    d=pd.DataFrame({'labresultoffset':[30,60,90], 'labresultrevisedoffset':[80,np.nan,70]})
    np.testing.assert_array_equal(e.available_lab_offset(d),[80,60,90])

def test_fractional_and_percentage_fio2():
    np.testing.assert_allclose(e.fio2(np.array([.21,.5,21,50,100])),[.21,.5,.21,.5,1])

def test_person_selection_is_outcome_blind_and_grouped():
    p=pd.DataFrame({'patientunitstayid':[1,2,3], 'uniquepid':['same','same','different'],
                    'age':['> 89','30','40'], 'gender':['Female','Male','Unknown']})
    sta=pd.DataFrame({'stay_id':[1,2,3]})
    a=e.pick_people(p,sta);b=e.pick_people(p.sample(frac=1,random_state=9),sta.iloc[::-1])
    assert a.set_index('uniquepid').stay_id.to_dict()==b.set_index('uniquepid').stay_id.to_dict()
    assert a.uniquepid.is_unique
    assert a.set_index('uniquepid').role.to_dict()==b.set_index('uniquepid').role.to_dict()

def test_original_features_have_no_future_dependence():
    rng=np.random.default_rng(7)
    f=pd.DataFrame(rng.normal(size=(20,34)),columns=e.PHYSIO)
    f.iloc[::2,:5]=np.nan
    f['Age']=50;f['Gender']=1;f['HospAdmTime']=-2;f['ICULOS']=np.arange(1,21)
    base=e.features(f)
    f.loc[10:,e.PHYSIO]=9999
    np.testing.assert_allclose(e.features(f)[:10],base[:10],equal_nan=True)

def test_troponin_and_bicarbonate_not_conflated():
    assert 'troponin - T' not in e.LAB_MAP
    assert e.LAB_MAP['troponin - I'][0]=='TroponinI'
    assert 'Total CO2' not in e.LAB_MAP
    assert e.LAB_MAP['HCO3'][0]=='HCO3'
