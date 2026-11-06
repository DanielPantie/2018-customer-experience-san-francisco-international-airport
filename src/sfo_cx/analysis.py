"""Survey preparation, explicit response bases, NPS and descriptive comparisons."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

CSV_NAME='2018_SFO_Customer_Survey.csv'
DICTIONARY_NAME='sfo_2018_Data_Dictionary_DataSF.xlsx'
CSV_URL='https://data.sf.gov/api/views/3w8r-nuxp/rows.csv?accessType=DOWNLOAD'
DICTIONARY_URL='https://data.sf.gov/download/wkh6-n369/application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
ACCEPTED_CSV_HASHES={
    'bb2e61e215983121b767a36e3f85d86424d890128e94a2010d800fbda843741c':'User-supplied 2026-10-20 export',
    '8d8e368dffb048679044159486bf89c5b838c7dbff731304ba02d4a8a2099c8b':'Verified DataSF export',
}
DICTIONARY_HASH='63b264f9215516c012991f13b08a4567d54166751997efd592e1a3962d65fbe2'
SERVICES={'Q7ART':'Artwork and exhibitions','Q7FOOD':'Restaurants','Q7STORE':'Retail shops',
    'Q7SIGN':'Indoor signs and directions','Q7WALKWAY':'Walkways and elevators',
    'Q7SCREENS':'Flight information screens','Q7INFODOWN':'Information: arrivals',
    'Q7INFOUP':'Information: departures','Q7WIFI':'Free Wi-Fi','Q7ROADS':'Roadway signs',
    'Q7PARK':'Parking facilities','Q7AIRTRAIN':'AirTrain','Q7LTPARKING':'Long-term parking shuttle',
    'Q7RENTAL':'Rental car center'}
JOURNEY={'Q14FIND':'Finding the way','Q14PASSTHRU':'Security and screening'}
THEMES={'directions':('Directions and information',1,9),'retail_services':('Restaurants and services',11,15),
    'amenities':('Airport amenities',21,27),'security':('Security and immigration',31,36),
    'airlines':('Airline experience',41,47),'delays':('Gate changes and delays',51,54),
    'accessibility':('Disability assistance',61,62),'other':('Other problems',71,74)}
RATING_COLUMNS=list(SERVICES)+['Q7ALL','Q9All']+list(JOURNEY)

@dataclass(frozen=True)
class Metric:
    label:str
    base:str
    outcome:str
    unit:str='percent'

METRICS={
    'overall_top2':Metric('Airport overall: rating 4 or 5','valid_Q7ALL','positive_Q7ALL'),
    'problem_rate':Metric('Reported a problem','valid_problem','has_problem'),
    'nps':Metric('Net Promoter Score','valid_nps','nps_contribution','points'),
    'promoters':Metric('Promoters: recommendation 9-10','valid_nps','is_promoter'),
    'passives':Metric('Passives: recommendation 7-8','valid_nps','is_passive'),
    'detractors':Metric('Detractors: recommendation 0-6','valid_nps','is_detractor'),
}
for col,label in {**SERVICES,**JOURNEY,'Q9All':'Overall cleanliness'}.items():
    METRICS[col]=Metric(label+': rating 4 or 5','valid_'+col,'positive_'+col)
for key,(label,_,_) in THEMES.items():
    METRICS['theme_'+key]=Metric(label,'problem_reporter','theme_'+key)

def prepare(raw):
    d=raw.copy();d.columns=d.columns.str.strip()
    if d.columns.duplicated().any():raise ValueError('Column stripping introduced duplicate names.')
    d['respondent_id']=d.RESPNUM.astype(str).str.replace(',','',regex=False).str.replace(r'\.0$','',regex=True)
    if not d.respondent_id.is_unique or d.RESPNUM.isna().any():raise ValueError('Missing or duplicate respondent IDs.')
    numeric=RATING_COLUMNS+['WEIGHT','NETPRO','Q15PROBLEM','Q15-1','Q15-2','Q15-3',
        'Q4WIFI','Q4FOOD','Q4STORE','Q5FIRSTTIME','Q20Age','Q21Gender','SAQ','METH','STRATA',
        'Q2PURP1','Q2PURP2','Q2PURP3']
    for col in numeric:d[col]=pd.to_numeric(d[col],errors='coerce')
    if d.WEIGHT.isna().any() or not d.WEIGHT.gt(0).all():raise ValueError('Weights must be positive and nonmissing.')
    for col in RATING_COLUMNS:
        d['valid_'+col]=d[col].between(1,5)
        d['positive_'+col]=d[col].ge(4).astype('boolean').where(d['valid_'+col],pd.NA)
    d['valid_nps']=d.NETPRO.between(0,10)
    d['valid_problem']=d.Q15PROBLEM.isin([1,2])
    d['has_problem']=d.Q15PROBLEM.eq(1).astype('boolean').where(d.valid_problem,pd.NA)
    d['problem_reporter']=d.Q15PROBLEM.eq(1)
    d['is_promoter']=d.NETPRO.ge(9).astype('boolean').where(d.valid_nps,pd.NA)
    d['is_passive']=d.NETPRO.between(7,8).astype('boolean').where(d.valid_nps,pd.NA)
    d['is_detractor']=d.NETPRO.le(6).astype('boolean').where(d.valid_nps,pd.NA)
    d['nps_contribution']=np.select([d.NETPRO.ge(9)&d.valid_nps,d.NETPRO.le(6)&d.valid_nps],[100.,-100.],default=0.)
    d.loc[~d.valid_nps,'nps_contribution']=np.nan
    d['problem_status']=d.Q15PROBLEM.map({1:'Reported a problem',2:'Reported no problem'})
    d['visit_type']=d.Q5FIRSTTIME.map({1:'Returning passenger',2:'First-time passenger'})
    d['administration']=d.SAQ.map({1:'Interviewer administered',2:'Self administered'})
    d['age_group']=d.Q20Age.map({1:'Under 18',2:'18-34',3:'18-34',4:'35-54',5:'35-54',6:'55+',7:'55+'})
    d['BAREA']=d.BAREA.astype('string').str.strip().str.upper()
    codes=d[['Q15-1','Q15-2','Q15-3']]
    for key,(_,lo,hi) in THEMES.items():
        selected=codes.ge(lo)&codes.le(hi)
        d['theme_'+key]=selected.any(axis=1).astype('boolean').where(d.problem_reporter,pd.NA)
    return d

def estimate(d,key,weighted=True):
    m=METRICS[key];b=d.loc[d[m.base]]
    w=b.WEIGHT.to_numpy(float) if weighted else np.ones(len(b))
    y=b[m.outcome].astype(float).to_numpy();denom=w.sum()
    scale=1 if m.unit=='points' else 100
    return {'metric':key,'label':m.label,'unit':m.unit,'n':len(b),
        'value':float(scale*np.dot(w,y)/denom) if denom else None,
        'effective_n_kish':float(denom**2/np.dot(w,w)) if denom else None,
        'weighted':weighted,'base_flag':m.base}

def summarize(d,keys=None,weighted=True):return pd.DataFrame([estimate(d,k,weighted) for k in (keys or list(METRICS))])

def by_group(d,column,keys):
    return pd.DataFrame([{'group_column':column,'group':group,**estimate(g,key)}
        for group,g in d.groupby(column,observed=True,dropna=True) for key in keys])

def usage_sensitivity(d):
    out=[]
    for col,use in [('Q7FOOD','Q4FOOD'),('Q7STORE','Q4STORE'),('Q7WIFI','Q4WIFI')]:
        for label,g in [('All valid raters',d),('Used/purchased today: Yes',d.loc[d[use].eq(1)]),
                        ('Used/purchased today: No',d.loc[d[use].eq(2)])]:
            out.append({'service':SERVICES[col],'usage_group':label,**estimate(g,col)})
    return pd.DataFrame(out)

def standardized_nps(d):
    """Hold boarding-area mix fixed for the two problem groups, descriptively."""
    b=d.loc[d.valid_nps&d.valid_problem&d.BAREA.notna()]
    cells=pd.crosstab(b.BAREA,b.problem_status)
    common=cells.index[cells.gt(0).all(axis=1)]
    b=b.loc[b.BAREA.isin(common)]
    target=b.groupby('BAREA').WEIGHT.sum();target=target/target.sum()
    out=[]
    for status,g in b.groupby('problem_status'):
        rates={area:estimate(a,'nps')['value'] for area,a in g.groupby('BAREA')}
        out.append({'problem_status':status,'n':len(g),'boarding_areas':','.join(common),
            'unadjusted_nps':estimate(g,'nps')['value'],
            'area_standardized_nps':sum(target[a]*rates[a] for a in target.index),
            'minimum_area_cell_n':int(cells.loc[common,status].min())})
    return pd.DataFrame(out)

def rating_associations(d):
    """Exploratory unweighted Spearman associations, never causal importance."""
    out=[]
    for col,label in SERVICES.items():
        pair=d.loc[d['valid_'+col]&d.valid_Q7ALL,[col,'Q7ALL']]
        r=pair[col].corr(pair.Q7ALL,method='spearman') if len(pair)>=100 else np.nan
        out.append({'service_column':col,'service':label,'pair_n':len(pair),'spearman_rho':r,
            'weighted':False,'interpretation':'Unadjusted co-rating association; pair-specific base; not causal importance.'})
    return pd.DataFrame(out).sort_values('spearman_rho',ascending=False)

def audit(raw,d,csv,dictionary):
    ratings={}
    for col in RATING_COLUMNS:
        r=d[col];ratings[col]={'valid_1_to_5_n':int(r.between(1,5).sum()),
            'zero_blank_n':int(r.eq(0).sum()),'six_not_applicable_n':int(r.eq(6).sum()),
            'missing_or_nonnumeric_n':int(r.isna().sum()),
            'unexpected_numeric_n':int((r.notna()&~r.isin(range(7))).sum())}
    recognized=np.zeros(len(d),dtype=bool)
    for lo,hi in [(x[1],x[2]) for x in THEMES.values()]:
        recognized|=((d[['Q15-1','Q15-2','Q15-3']].ge(lo))&(d[['Q15-1','Q15-2','Q15-3']].le(hi))).any(axis=1).to_numpy()
    return {'rows':len(raw),'columns':len(raw.columns),'duplicate_ids_n':int(d.respondent_id.duplicated().sum()),
        'duplicate_rows_n':int(raw.duplicated().sum()),'csv_sha256':hashlib.sha256(csv.read_bytes()).hexdigest(),
        'dictionary_sha256':hashlib.sha256(dictionary.read_bytes()).hexdigest(),
        'header_names_with_outer_whitespace':[c for c in raw.columns if c!=c.strip()],
        'missing_weights_n':int(d.WEIGHT.isna().sum()),'nonpositive_weights_n':int(d.WEIGHT.le(0).sum()),
        'weights':d.WEIGHT.describe().to_dict(),'rating_audit':ratings,
        'nps_valid_n':int(d.valid_nps.sum()),'nps_blank_11_n':int(d.NETPRO.eq(11).sum()),
        'valid_problem_n':int(d.valid_problem.sum()),'problem_reporter_n':int(d.problem_reporter.sum()),
        'problem_reporters_without_recognized_theme_n':int((d.problem_reporter&~recognized).sum()),
        'coded_theme_but_no_yes_n':int((recognized&~d.problem_reporter).sum()),
        'wifi_users_with_not_applicable_rating_n':int((d.Q4WIFI.eq(1)&d.Q7WIFI.eq(6)).sum()),
        'wifi_nonusers_today_with_valid_rating_n':int((d.Q4WIFI.eq(2)&d.valid_Q7WIFI).sum())}

def write_results(raw,d,csv,dictionary,out):
    out.mkdir(parents=True,exist_ok=True)
    tables={'metrics_weighted':summarize(d),'metrics_unweighted':summarize(d,weighted=False),
        'by_problem':by_group(d,'problem_status',['nps','overall_top2']),
        'by_visit':by_group(d,'visit_type',['nps','overall_top2','problem_rate']),
        'by_area':by_group(d,'BAREA',['nps','overall_top2','problem_rate']),
        'by_age':by_group(d,'age_group',['nps','overall_top2','problem_rate']),
        'by_administration':by_group(d,'administration',['nps','overall_top2','problem_rate']),
        'usage_sensitivity':usage_sensitivity(d),'standardized_nps':standardized_nps(d),
        'rating_associations':rating_associations(d)}
    for name,t in tables.items():t.to_csv(out/f'{name}.csv',index=False,float_format='%.10f')
    a=audit(raw,d,csv,dictionary);(out/'audit.json').write_text(json.dumps(a,indent=2))
    return tables,a
