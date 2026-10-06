"""Public PhysioNet data download; hash-based split before observing labels."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import hashlib, json, re, time, threading
import requests

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
BASE='https://physionet.org/files/challenge-2019/1.0.0/training/'
LOCAL=threading.local()
STOP=threading.Event()

def rank(site,name):
    return hashlib.sha256(f'20260929|{site}|{name}'.encode()).hexdigest()

def manifest():
    path=ROOT/'manifest.json'
    if path.exists():return json.loads(path.read_text())
    records=[]
    with requests.Session() as session:
        for site,expected in [('A',20336),('B',20000)]:
            url=BASE+f'training_set{site}/'
            r=session.get(url,timeout=45);r.raise_for_status()
            names=sorted(set(re.findall(r'href="(p\d+\.psv)"',r.text)))
            if len(names)!=expected:raise RuntimeError(f'{site}: unexpected record count {len(names)}')
            names.sort(key=lambda n:rank(site,n))
            for i,name in enumerate(names):
                if i<1500:role='pilot'
                else:
                    q=(i-1500)/(len(names)-1500)
                    role='train' if q<.6 else ('calibration' if q<.8 else 'test')
                records.append({'site':site,'name':name,'url':urljoin(url,name),'role':role})
    path.write_text(json.dumps(records,indent=2))
    return records

def fetch(record):
    if STOP.is_set():raise PermissionError('Stopped after authorization error')
    if not hasattr(LOCAL,'session'):LOCAL.session=requests.Session()
    path=DATA/record['site']/record['name'];path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes().startswith(b'HR|O2Sat|'):return
    for attempt in range(3):
        try:
            r=LOCAL.session.get(record['url'],timeout=30)
            if r.status_code in (401,403):
                STOP.set();raise PermissionError('Use the official dataset access procedure.')
            r.raise_for_status()
            if not r.content.startswith(b'HR|O2Sat|'):raise ValueError('Not a clinical PSV file')
            temp=path.with_suffix('.tmp');temp.write_bytes(r.content);temp.replace(path)
            return
        except PermissionError:raise
        except (requests.RequestException,ValueError):
            if attempt==2:raise
            time.sleep(attempt+1)

def download(pilot=True,workers=8):
    rows=[r for r in manifest() if (r['role']=='pilot')==pilot]
    failures=[];started=time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(fetch,r):r for r in rows}
        for i,f in enumerate(as_completed(futures),1):
            try:f.result()
            except Exception as exc:failures.append({'record':futures[f],'error':str(exc)})
            if i%100==0 or i==len(rows):print(f'{i}/{len(rows)}; failures={len(failures)}; elapsed={time.time()-started:.0f}s',flush=True)
    (ROOT/'download_failures.json').write_text(json.dumps(failures,indent=2))
    if failures:raise RuntimeError(f'{len(failures)} downloads failed; rerun to resume')
    return rows

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true')
    args=parser.parse_args();download(pilot=not args.full)
