from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_external_v2 as v

def test_chart_entry_delays_availability():
    np.testing.assert_array_equal(v.chart_available([30,90,120],[120,60,np.nan]),[120,90,120])

def test_explicit_temperature_unit_conversion():
    np.testing.assert_allclose(v.temperature(pd.Series(['98.6','104','bad']),'Temperature (F)'),[37,40,np.nan],equal_nan=True)
    np.testing.assert_allclose(v.temperature(pd.Series(['37','bad']),'Temperature (C)'),[37,np.nan],equal_nan=True)
