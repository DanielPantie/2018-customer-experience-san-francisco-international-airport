"""Synthetic survey logic tests plus regression checks against SFO 2018."""
from pathlib import Path
import sys
import unittest
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from sfo_cx.analysis import RATING_COLUMNS,prepare,estimate,CSV_NAME,usage_sensitivity

def fixture():
    rows=[]
    for i,w in enumerate([1.,3.,5.]):
        r={c:4 for c in RATING_COLUMNS}
        r.update(RESPNUM=f'1,00{i+1}',WEIGHT=w,NETPRO=[0,10,11][i],Q15PROBLEM=[1,2,3][i],
            Q4WIFI=1,Q4FOOD=1,Q4STORE=1,Q5FIRSTTIME=1,Q20Age=3,Q21Gender=1,
            SAQ=2,METH=1,STRATA=1,Q2PURP1=2,Q2PURP2=np.nan,Q2PURP3=np.nan,BAREA='A',
            **{'Q15-1':31 if i==0 else np.nan,'Q15-2':32 if i==0 else np.nan,'Q15-3':np.nan})
        r['Q7ALL']=[6,5,'BLANK'][i];rows.append(r)
    return pd.DataFrame(rows).rename(columns={'NETPRO':'NETPRO  ','Q14FIND':'Q14FIND '})

class SurveyLogic(unittest.TestCase):
    def test_zero_is_a_detractor_and_eleven_is_blank(self):
        d=prepare(fixture());m=estimate(d,'nps')
        self.assertEqual(m['n'],2);self.assertAlmostEqual(m['value'],50.)
        self.assertEqual(d.loc[0,'nps_contribution'],-100)
        self.assertTrue(pd.isna(d.loc[2,'nps_contribution']))
    def test_rating_six_and_literal_blank_are_not_valid(self):
        d=prepare(fixture());m=estimate(d,'overall_top2')
        self.assertEqual(m['n'],1);self.assertEqual(m['value'],100.)
        self.assertTrue(pd.isna(d.loc[0,'positive_Q7ALL']))
        self.assertTrue(pd.isna(d.loc[2,'positive_Q7ALL']))
    def test_problem_unknown_is_excluded_and_no_is_not_severity(self):
        d=prepare(fixture());m=estimate(d,'problem_rate')
        self.assertEqual(m['n'],2);self.assertEqual(m['value'],25.)
        self.assertFalse(d.loc[1,'has_problem']);self.assertTrue(pd.isna(d.loc[2,'has_problem']))
    def test_theme_counts_person_once_and_retains_uncoded_reporters(self):
        raw=fixture();raw.loc[2,'Q15PROBLEM']=1;d=prepare(raw)
        m=estimate(d,'theme_security')
        self.assertEqual(m['n'],2);self.assertAlmostEqual(m['value'],100/6)
    def test_header_whitespace_and_identifiers(self):
        d=prepare(fixture());self.assertIn('NETPRO',d.columns);self.assertIn('Q14FIND',d.columns)
        self.assertEqual(d.loc[0,'respondent_id'],'1001')
    def test_scale_invariance_and_empty_base(self):
        raw=fixture();a=estimate(prepare(raw),'nps');raw.WEIGHT*=100
        b=estimate(prepare(raw),'nps');self.assertAlmostEqual(a['value'],b['value'])
        self.assertAlmostEqual(a['effective_n_kish'],b['effective_n_kish'])
        self.assertIsNone(estimate(prepare(raw).iloc[:0],'nps')['value'])
    def test_bad_weights_and_duplicate_ids_fail(self):
        raw=fixture();raw.loc[0,'WEIGHT']=0
        with self.assertRaises(ValueError):prepare(raw)
        raw=fixture();raw.loc[1,'RESPNUM']=raw.loc[0,'RESPNUM']
        with self.assertRaises(ValueError):prepare(raw)

class SourceRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=ROOT/'data/raw'/CSV_NAME
        if not p.exists():raise unittest.SkipTest('Run scripts/download_data.py for original-source checks.')
        cls.df=prepare(pd.read_csv(p))
    def test_source_counts_and_headlines(self):
        d=self.df;self.assertEqual(len(d),2809)
        expected={'overall_top2':(2625,80.4852450280),'nps':(2650,35.1136321036),'problem_rate':(2616,12.8815579506)}
        for key,(n,v) in expected.items():
            m=estimate(d,key);self.assertEqual(m['n'],n);self.assertAlmostEqual(m['value'],v,places=7)
    def test_recommendation_partition_and_nps_identity(self):
        d=self.df;self.assertAlmostEqual(sum(estimate(d,k)['value'] for k in ['promoters','passives','detractors']),100.)
        self.assertAlmostEqual(estimate(d,'promoters')['value']-estimate(d,'detractors')['value'],estimate(d,'nps')['value'])
    def test_wifi_usage_base_and_group_nps(self):
        d=self.df;u=usage_sensitivity(d)
        m=u[(u.metric=='Q7WIFI')&(u.usage_group=='Used/purchased today: Yes')].iloc[0]
        self.assertEqual(m['n'],1353);self.assertAlmostEqual(m['value'],82.42811374198536,places=7)
        yes=d[d.Q15PROBLEM.eq(1)];no=d[d.Q15PROBLEM.eq(2)]
        self.assertEqual(estimate(yes,'nps')['n'],359);self.assertEqual(estimate(no,'nps')['n'],2181)
        self.assertAlmostEqual(estimate(yes,'nps')['value'],-1.9054212843,places=7)
        self.assertAlmostEqual(estimate(no,'nps')['value'],41.4610693817,places=7)

if __name__=='__main__':unittest.main()
