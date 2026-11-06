"""Rebuild the entire SFO case study, including the executed notebook and PDF."""
from pathlib import Path
import sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from download_data import download
from sfo_cx.analysis import prepare,write_results

def main():
    csv,dictionary=download()
    raw=pd.read_csv(csv);d=prepare(raw)
    tables,info=write_results(raw,d,csv,dictionary,ROOT/'outputs'/'tables')
    from build_outputs import build_all
    build_all(d,tables,info,dictionary)
    print(f'Completed SFO 2018 case study: {len(d):,} respondents.')

if __name__=='__main__':main()
