"""Download originals and select complete source sessions deterministically."""
import argparse, csv, gzip, hashlib, json, time, urllib.request, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    '2019-Oct.csv.gz': 'https://data.rees46.com/datasets/marketplace/2019-Oct.csv.gz',
    'creditcard.csv': 'https://storage.googleapis.com/download.tensorflow.org/data/creditcard.csv',
}

def download():
    raw = ROOT / 'data/raw'; raw.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        dest = raw / name
        if not dest.exists():
            with urllib.request.urlopen(url, timeout=120) as r, open(str(dest)+'.part','wb') as out:
                while chunk := r.read(8*1024*1024): out.write(chunk)
            Path(str(dest)+'.part').replace(dest)

def extract(threshold=130):
    t=time.perf_counter(); download()
    counts={'raw_events':0,'sample_events':0,'missing_session_excluded':0,'event_types':{}}
    dest=ROOT/'data/staging/sample.csv'; dest.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(ROOT/'data/raw/2019-Oct.csv.gz','rt',newline='') as f, open(str(dest)+'.part','w',newline='') as out:
        reader=csv.reader(f); header=next(reader); writer=csv.writer(out)
        assert header == ['event_time','event_type','product_id','category_id','category_code','brand','price','user_id','user_session'], header
        writer.writerow(['source_row']+header)
        for rownum,row in enumerate(reader,1):
            counts['raw_events']+=1
            typ=row[1]; counts['event_types'][typ]=counts['event_types'].get(typ,0)+1
            if not row[8] or not row[7]:
                counts['missing_session_excluded']+=1; continue
            # Stable composite session selection, preserving all events in the source month.
            if zlib.crc32((row[7]+'|'+row[8]).encode()) % 1000 < threshold:
                writer.writerow([rownum]+row);counts['sample_events']+=1
            if rownum % 5000000 == 0: print(rownum,counts['sample_events'],flush=True)
    Path(str(dest)+'.part').replace(dest)
    counts.update(sample_rule=f'crc32(user_id|user_session) % 1000 < {threshold}',seconds=time.perf_counter()-t)
    counts['files']={}
    for name,url in SOURCES.items():
        h=hashlib.sha256();p=ROOT/'data/raw'/name
        with p.open('rb') as f:
            while b:=f.read(8*1024*1024):h.update(b)
        counts['files'][name]={'url':url,'bytes':p.stat().st_size,'sha256':h.hexdigest()}
        expected={'2019-Oct.csv.gz':'8ebca1ad741295297368f2cf0315e3f36853a1a11768fb16babf8c9b83838147','creditcard.csv':'76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89'}
        assert h.hexdigest()==expected[name], 'Source file differs from the assessed snapshot: '+name
    (ROOT/'results').mkdir(exist_ok=True)
    (ROOT/'results/source_audit.json').write_text(json.dumps(counts,indent=2))
    print(json.dumps(counts,indent=2),flush=True)
    assert counts['sample_events']>=5000000, 'Increase sampling threshold for the assessed run.'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--threshold',type=int,default=130)
    extract(p.parse_args().threshold)
