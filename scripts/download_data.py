"""Fetch and verify the two original DataSF source files. Never overwrite changed data."""
from pathlib import Path
import urllib.request
import hashlib
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from sfo_cx.analysis import CSV_NAME,DICTIONARY_NAME,CSV_URL,DICTIONARY_URL,ACCEPTED_CSV_HASHES,DICTIONARY_HASH

def download(destination=None):
    dest=Path(destination or ROOT/'data'/'raw');dest.mkdir(parents=True,exist_ok=True)
    jobs=[(CSV_NAME,CSV_URL,set(ACCEPTED_CSV_HASHES)),(DICTIONARY_NAME,DICTIONARY_URL,{DICTIONARY_HASH})]
    for name,url,accepted in jobs:
        path=dest/name
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() not in accepted:
                raise ValueError(f'{name} differs from the verified source. Preserve it and investigate before rebuilding.')
            continue
        for attempt in range(3):
            try:
                req=urllib.request.Request(url,headers={'User-Agent':'SFO2018-reproducible-case-study/1.0'})
                with urllib.request.urlopen(req,timeout=60) as response:content=response.read()
                break
            except (OSError,TimeoutError):
                if attempt==2:raise RuntimeError('Could not download DataSF sources. See README for manual file placement.')
                time.sleep(attempt+1)
        if hashlib.sha256(content).hexdigest() not in accepted:
            raise ValueError(f'Public export bytes changed for {name}. Review the new source before updating accepted checksums.')
        path.write_bytes(content)
    return dest/CSV_NAME,dest/DICTIONARY_NAME

if __name__=='__main__':print(download())
