"""Build SFO figures, editable-template report, executed notebook and carousel PDF."""
from pathlib import Path
import json
import os
import sys
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from sfo_cx.analysis import SERVICES,JOURNEY,THEMES,METRICS,summarize,estimate,by_group
NAVY='#142f34';TEAL='#11776d';ORANGE='#cc7045';MUTED='#617477'

def md_table(f):
    f=f.copy().fillna('');cols=list(f.columns)
    return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in f.itertuples(index=False,name=None))

def context(t):
    m=t['metrics_weighted'].set_index('metric');b=t['by_problem'];b=b[b.metric.eq('nps')].set_index('group')
    p=float(b.loc['Reported a problem','value']);no=float(b.loc['Reported no problem','value'])
    u=t['usage_sensitivity'];used=float(u.loc[(u.metric=='Q7WIFI')&(u.usage_group=='Used/purchased today: Yes'),'value'].iloc[0])
    s=t['standardized_nps'].set_index('problem_status')
    result={}
    for name,value in {'NPS_GAP':no-p,'OVERALL_TOP2':m.loc['overall_top2','value'],
        'PROBLEM_RATE':m.loc['problem_rate','value'],'RETAIL':m.loc['Q7STORE','value'],
        'FOOD':m.loc['Q7FOOD','value'],'SECURITY_THEME':m.loc['theme_security','value'],
        'DIRECTIONS_THEME':m.loc['theme_directions','value'],'WIFI_ALL':m.loc['Q7WIFI','value'],
        'WIFI_USED':used,'STANDARDIZED_GAP':s.loc['Reported no problem','area_standardized_nps']-s.loc['Reported a problem','area_standardized_nps']}.items():
        for dp in [0,1]:result[f'{name}_{dp}']=f'{value:.{dp}f}'
    for name,value in {'NPS':m.loc['nps','value'],'PROBLEM_NPS':p,'NO_PROBLEM_NPS':no}.items():
        for dp in [0,1]:result[f'{name}_SIGNED_{dp}']=f'{value:+.{dp}f}'
    result['MIN_AREA_CELL']=str(int(s.minimum_area_cell_n.min()))
    def table(keys):
        a=m.loc[keys,['label','value','n','unit']].copy()
        a['value']=[f'{v:+.1f} points' if unit=='points' else f'{v:.1f}%' for v,unit in zip(a.value,a.unit)]
        a=a.drop(columns='unit');a.columns=['Measure','Weighted estimate','Actual valid n']
        return md_table(a)
    result['HEADLINE_TABLE']=table(['overall_top2','nps','problem_rate'])
    result['RECOMMENDATION_TABLE']=table(['promoters','passives','detractors','nps'])
    result['SERVICE_TABLE']=table(sorted(SERVICES,key=lambda k:m.loc[k,'value'],reverse=True))
    a=t['by_problem'][['group','metric','value','n','unit']].copy()
    a['value']=[f'{v:+.1f} points' if unit=='points' else f'{v:.1f}%' for v,unit in zip(a.value,a.unit)]
    a=a.drop(columns='unit');a.columns=['Problem answer','Measure','Weighted estimate','Actual valid n']
    result['PROBLEM_COMPARISON_TABLE']=md_table(a)
    return result

def replace_tokens(s,values):
    for key,value in values.items():s=s.replace('{{'+key+'}}',value)
    if '{{' in s:raise ValueError('Unresolved content token: '+s[s.index('{{'):s.index('{{')+60])
    return s

def charts(t):
    out=ROOT/'outputs/figures';out.mkdir(parents=True,exist_ok=True)
    m=t['metrics_weighted'].set_index('metric')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12})
    def bars(labels,values,name,title,note,limit=100,color=TEAL):
        fig,ax=plt.subplots(figsize=(10,max(3.8,len(labels)*.5+1.5)))
        ax.barh(np.arange(len(labels)),values,height=.55,color=color)
        ax.set_yticks(np.arange(len(labels)),labels);ax.invert_yaxis();ax.set_xlim(0,limit)
        ax.set_xlabel('Share of valid respondents (%)',color=MUTED)
        for i,v in enumerate(values):ax.text(v+limit*.012,i,f'{v:.1f}%',va='center',fontsize=12,fontweight='bold',color=NAVY)
        for spine in ax.spines.values():spine.set_visible(False)
        ax.tick_params(axis='y',length=0,pad=10);ax.xaxis.grid(True,alpha=.14);ax.set_axisbelow(True)
        ax.set_title(title,loc='left',fontsize=16,fontweight='bold',color=NAVY,pad=25)
        fig.text(.02,.015,note,fontsize=10,color=MUTED);fig.tight_layout(rect=[0,.06,.98,1])
        for ext in ['png','svg']:fig.savefig(out/f'{name}.{ext}',dpi=170,bbox_inches='tight',facecolor='white')
        plt.close(fig)
    keys=['promoters','passives','detractors']
    bars([m.loc[k,'label'] for k in keys],[m.loc[k,'value'] for k in keys],'01_recommendation',
         'How willing are passengers to recommend SFO?', 'SFO 2018 / DataSF. Weighted. Valid n = 2,650. NPS = +35.1 points.')
    b=t['by_problem'];b=b[b.metric.eq('nps')].set_index('group')
    labels=['Reported a problem','Reported no problem'];values=[b.loc[k,'value'] for k in labels]
    fig,ax=plt.subplots(figsize=(10,4));ax.barh([0,1],values,color=[ORANGE,TEAL],height=.5)
    ax.set_yticks([0,1],[f'{k} (n={int(b.loc[k,"n"]):,})' for k in labels]);ax.invert_yaxis()
    ax.set_xlim(-100,100);ax.axvline(0,color=MUTED,lw=.8);ax.set_xlabel('Net Promoter Score (points)')
    for i,v in enumerate(values):ax.text(v+(2 if v>=0 else -2),i,f'{v:+.1f}',va='center',ha='left' if v>=0 else 'right',fontweight='bold')
    for sp in ax.spines.values():sp.set_visible(False)
    ax.set_title('Reported problems coincide with lower recommendation',loc='left',fontsize=15,fontweight='bold',pad=25)
    fig.text(.02,.02,'SFO 2018 / DataSF. Weighted. Descriptive association; no causal effect estimated.',fontsize=10,color=MUTED)
    fig.tight_layout(rect=[0,.08,.98,1])
    for ext in ['png','svg']:fig.savefig(out/f'02_nps_by_problem.{ext}',dpi=170,bbox_inches='tight')
    plt.close(fig)
    keys=sorted(SERVICES,key=lambda k:m.loc[k,'value'],reverse=True)
    bars([SERVICES[k] for k in keys],[m.loc[k,'value'] for k in keys],'03_service_ratings',
        'Retail and restaurants have the lowest top-two service ratings',
        'SFO 2018 / DataSF. Weighted share rating 4 or 5. Each service has its own valid base.')
    keys=sorted(['theme_'+k for k in THEMES],key=lambda k:m.loc[k,'value'],reverse=True)
    bars([m.loc[k,'label'] for k in keys],[m.loc[k,'value'] for k in keys],'04_problem_themes',
        'Security is the most frequently coded problem theme',
        'SFO 2018 / DataSF. Weighted. Denominator: 369 problem reporters. Multiple themes can overlap.',color=ORANGE)
    bars([JOURNEY[k] for k in JOURNEY],[m.loc[k,'value'] for k in JOURNEY],'05_journey',
        'Navigation rates higher than security screening',
        'SFO 2018 / DataSF. Weighted share rating 4 or 5 on the 1 (difficult) to 5 (easy) scale.')
    u=t['usage_sensitivity'];u=u[u.metric.eq('Q7WIFI')&u.usage_group.isin(['All valid raters','Used/purchased today: Yes'])]
    bars(['All valid Wi-Fi raters (n=2,074)','Same-day users with valid ratings (n=1,353)'],u.value.tolist(),'06_wifi_usage',
        'Wi-Fi ratings depend on the response base',
        'SFO 2018 / DataSF. Weighted share rating 4 or 5. Same-day nonusers can rate previous experience.')
    a=t['rating_associations'];fig,ax=plt.subplots(figsize=(10,8))
    ax.barh(np.arange(len(a)),a.spearman_rho,color=TEAL);ax.set_yticks(np.arange(len(a)),a.service)
    ax.invert_yaxis();ax.set_xlim(0,1);ax.set_xlabel('Spearman rank correlation (unweighted)')
    for i,v in enumerate(a.spearman_rho):ax.text(v+.015,i,f'{v:.2f}',va='center',fontsize=11)
    for sp in ax.spines.values():sp.set_visible(False)
    ax.set_title('Services and overall airport rating: exploratory associations',loc='left',fontsize=14,fontweight='bold',pad=25)
    fig.text(.02,.015,'SFO 2018 / DataSF. Pair-specific valid n. Correlations are not causal importance or ROI estimates.',fontsize=10,color=MUTED)
    fig.tight_layout(rect=[0,.05,.98,1])
    for ext in ['png','svg']:fig.savefig(out/f'07_rating_associations.{ext}',dpi=170,bbox_inches='tight')
    plt.close(fig)

def dictionaries(dictionary):
    out=ROOT/'docs';out.mkdir(exist_ok=True)
    pd.DataFrame([{'metric':k,'label':m.label,'valid_base_flag':m.base,'outcome':m.outcome,'unit':m.unit}
        for k,m in METRICS.items()]).to_csv(out/'metric_dictionary.csv',index=False)
    b=pd.read_excel(dictionary,header=None).fillna('');b.columns=['field_or_section','question_or_code','answer_label']
    b.to_csv(out/'source_codebook.csv',index=False)

def notebook():
    cells=[]
    def md(s):cells.append({'cell_type':'markdown','metadata':{},'source':textwrap.dedent('    '+s).strip().splitlines(True)})
    def code(s):cells.append({'cell_type':'code','metadata':{},'source':textwrap.dedent('    '+s).strip().splitlines(True),'outputs':[],'execution_count':None})
    md('''# SFO 2018 passenger experience: a guided case study
    **Question:** Which parts of the passenger experience deserve follow-up, and how do problems relate to recommendation?

    Real source: 2,809 responses, 97 fields, and the supplied DataSF dictionary. This is historical 2018 evidence. Start with the coding rules and response bases, then examine the business implications. All headline estimates use the supplied weights.''')
    code('''from pathlib import Path
    import sys
    import pandas as pd
    from IPython.display import display, Image
    ROOT = Path.cwd()
    if ROOT.name == 'notebooks':
        ROOT = ROOT.parent
    if not (ROOT / 'src' / 'sfo_cx').exists():
        raise RuntimeError('Run from the project root or notebooks folder.')
    sys.path.insert(0, str(ROOT / 'src'))
    sys.path.insert(0, str(ROOT))
    from scripts.download_data import download
    from sfo_cx.analysis import prepare, estimate, summarize, by_group, usage_sensitivity, rating_associations, standardized_nps, audit, SERVICES
    csv, dictionary = download()
    raw = pd.read_csv(csv)
    df = prepare(raw)
    print(f'{len(df):,} respondents and {len(raw.columns)} source fields')''')
    md('''## 1. Understand the questions
    Q7 uses a 1-5 rating scale, anchored by unacceptable and outstanding. Q14 uses a 1-5 difficulty scale. Recommendation uses 0-10 and supports NPS. Yes/No and multi-code questions follow different rules.

    A rating, willingness to recommend, service usage and a problem report are related but distinct constructs. Do not invent a single satisfaction score from all of them.''')
    code('''info = audit(raw, df, csv, dictionary)
    print('Headers cleaned:', info['header_names_with_outer_whitespace'])
    print('Duplicate respondent IDs:', info['duplicate_ids_n'])
    print('Missing/nonpositive weights:', info['missing_weights_n'], info['nonpositive_weights_n'])
    display(pd.DataFrame(info['rating_audit']).T)
    print('Valid NPS:', info['nps_valid_n'], '| code 11 blanks:', info['nps_blank_11_n'])''')
    md('''## 2. Prepare explicit response bases
    Exclude 0, 6 and missing/BLANK values from the 1-5 ratings. Keep 0 for recommendation, because it is a real detractor score. Exclude recommendation code 11. Q15PROBLEM has Yes=1, No=2, Don't know=3 and blank=0.

    The clean dataframe adds valid-base flags and nullable outcomes. Original files remain unchanged. Unknown outcomes remain NA rather than becoming False.''')
    code('''print('Overall rating outcomes, including NA:')
    display(df.positive_Q7ALL.value_counts(dropna=False).rename('respondents').to_frame())
    print('Problem outcomes, including NA:')
    display(df.has_problem.value_counts(dropna=False).rename('respondents').to_frame())
    print('NPS respondent categories:')
    display(summarize(df, ['promoters','passives','detractors','nps'])[['label','unit','n','value']].round(3))''')
    md('''## 3. Calculate an estimate by hand, then check the reusable function
    A weighted share divides positive-response weights by all valid-response weights. n remains an actual respondent count.

    NPS is the weighted promoter percentage minus detractor percentage. It is measured in points, not percent, and does not measure observed loyalty.''')
    code('''base = df.loc[df.valid_Q7ALL]
    top_two = base.Q7ALL.ge(4)
    overall_pct = 100 * base.loc[top_two, 'WEIGHT'].sum() / base.WEIGHT.sum()
    rec = df.loc[df.valid_nps]
    nps = 100 * (rec.loc[rec.NETPRO.ge(9), 'WEIGHT'].sum() - rec.loc[rec.NETPRO.le(6), 'WEIGHT'].sum()) / rec.WEIGHT.sum()
    assert abs(overall_pct - estimate(df, 'overall_top2')['value']) < 1e-10
    assert abs(nps - estimate(df, 'nps')['value']) < 1e-10
    print(f'Overall rating 4/5: {overall_pct:.4f}% | NPS: {nps:+.4f} points')
    display(summarize(df, ['overall_top2','nps','problem_rate'])[['label','unit','n','value']].round(3))
    display(Image(filename=str(ROOT / 'outputs/figures/01_recommendation.png')))''')
    md('''## 4. Compare recommendation by problem status
    Use valid NPS scores within each explicit Yes/No problem group. Unknown problem answers remain outside this comparison even if NPS is valid.

    The observed gap is about 43 points. It does not prove that a problem caused that entire difference: trip disruption, service exposure and broader sentiment may contribute.''')
    code('''groups = by_group(df, 'problem_status', ['nps','overall_top2'])
    display(groups[['group','label','unit','n','value']].round(3))
    display(Image(filename=str(ROOT / 'outputs/figures/02_nps_by_problem.png')))
    print('Valid NPS with an unknown/non-substantive problem answer:',
          int((df.valid_nps & ~df.valid_problem).sum()))''')
    md('''## 5. Understand coded problem themes
    Q15-1 to Q15-3 can supply several codes for the same person. Group the original dictionary codes into themes, then count each person once per theme. Use all 369 Yes problem reporters as the denominator, including 15 with no recognized theme.

    These are existing coded responses, not an AI sentiment model. A frequent theme does not establish that the airport alone controls it.''')
    code('''from sfo_cx.analysis import THEMES
    keys = ['theme_' + k for k in THEMES]
    display(summarize(df, keys)[['label','n','value']].sort_values('value', ascending=False).round(3))
    print('Problem reporters without a recognized theme:', info['problem_reporters_without_recognized_theme_n'])
    display(Image(filename=str(ROOT / 'outputs/figures/04_problem_themes.png')))''')
    md('''## 6. Compare services and check usage
    All service rankings use each service's valid 1-5 rating base. These bases differ. A same-day usage question can refine the population, but a nonuser that day may still rate a prior experience.

    Wi-Fi shows the distinction: about 73% rate it 4/5 among all valid raters, compared with about 82% among same-day users who rated it validly. We retain source inconsistencies and handle them with explicit flags.''')
    code('''display(summarize(df, list(SERVICES))[['label','n','value']].sort_values('value', ascending=False).round(2))
    display(usage_sensitivity(df)[['service','usage_group','n','value']].round(2))
    display(Image(filename=str(ROOT / 'outputs/figures/03_service_ratings.png')))
    display(Image(filename=str(ROOT / 'outputs/figures/06_wifi_usage.png')))''')
    md('''## 7. Explore co-rating associations without treating them as causal drivers
    Spearman correlations respect the ordinal ranking of the 1-5 answers. This exploratory table is deliberately **unweighted**, while headline percentages are weighted. Each service/overall pair has its own valid response base.

    Common sentiment, questionnaire context and service use can influence both ratings. The correlations are not incremental effects, validated importance weights or ROI estimates.''')
    code('''display(rating_associations(df)[['service','pair_n','spearman_rho','weighted']].round(3))''')
    md('''## 8. Challenge the result
    Compare weighted and unweighted metrics. Holding boarding-area mix fixed provides one descriptive check on the NPS gap, but some problem/area cells have only eight respondents. No formal causal or significance claim follows.

    Kish effective n describes concentration of weights. The two input files do not establish a full design-based variance analysis, so no p-values or formal confidence intervals are reported.''')
    code('''keys = ['overall_top2','problem_rate','nps']
    comparison = summarize(df, keys)[['metric','value','n','effective_n_kish']].merge(
        summarize(df, keys, weighted=False)[['metric','value']], on='metric',
        suffixes=('_weighted','_unweighted'))
    display(comparison.round(3))
    display(standardized_nps(df).round(3))
    display(by_group(df, 'visit_type', ['nps','overall_top2'])[['group','label','n','value']].round(2))''')
    md('''## 9. Turn the evidence into a follow-up plan
    Investigate security issues with relevant partners, assess dining/retail value and service with targeted questions, and define an actual-user digital-experience measure. Track operational outcomes in a pilot before claiming improvement effects.

    **Learning exercise:** choose a boarding area and reproduce its NPS, valid base and overall-rating share. Explain why this subgroup may differ before making an operational recommendation.''')
    code('''selected_area = 'A'  # change to another included area
    display(summarize(df.loc[df.BAREA.eq(selected_area)], ['nps','overall_top2','problem_rate'])[['label','unit','n','value']].round(3))''')
    md('''## Reproduce, edit and publish
    From the project root, run `python scripts/run_analysis.py` and then `python -m unittest discover -s tests -v`.

    Edit `reports/case_study_template.md` for report text and `presentation/carousel_content.json` for slide wording. Rebuild to update the generated report and PDF. These editable sources survive reruns. Read `docs/editing_and_github.md` before uploading.

    Source: [2018 SFO Customer Survey, DataSF](https://data.sf.gov/Transportation/2018-SFO-Customer-Survey/3w8r-nuxp). All calculations are independent, historical 2018 estimates. No SFO endorsement is implied.''')
    shell=InteractiveShell.instance();oldcwd=Path.cwd();os.chdir(ROOT);i=0
    try:
        for cell in cells:
            if cell['cell_type']!='code':continue
            i+=1
            with capture_output(display=True) as captured:
                result=shell.run_cell(''.join(cell['source']),store_history=False)
            if result.error_in_exec or result.error_before_exec:raise RuntimeError(f'Notebook cell {i} failed: {result.error_in_exec or result.error_before_exec}')
            outputs=[]
            if captured.stdout:outputs.append({'output_type':'stream','name':'stdout','text':captured.stdout.splitlines(True)})
            if captured.stderr:outputs.append({'output_type':'stream','name':'stderr','text':captured.stderr.splitlines(True)})
            for o in captured.outputs:outputs.append({'output_type':'display_data','data':o.data,'metadata':o.metadata or {}})
            cell['execution_count']=i;cell['outputs']=outputs
    finally:os.chdir(oldcwd)
    for i,cell in enumerate(cells):cell['id']=f'sfo-cell-{i:02d}'
    nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python','version':sys.version.split()[0]}},'nbformat':4,'nbformat_minor':5}
    out=ROOT/'notebooks';out.mkdir(exist_ok=True);(out/'01_sfo_customer_experience.ipynb').write_text(json.dumps(nb,indent=1))

def carousel(t,values):
    import reportlab
    fontdir=Path(reportlab.__file__).parent/'fonts'
    pdfmetrics.registerFont(TTFont('CX',str(fontdir/'Vera.ttf')));pdfmetrics.registerFont(TTFont('CX-Bold',str(fontdir/'VeraBd.ttf')))
    spec=json.loads((ROOT/'presentation/carousel_content.json').read_text())
    slides=[{k:replace_tokens(v,values) if isinstance(v,str) else v for k,v in slide.items()} for slide in spec['slides']]
    c=canvas.Canvas(str(ROOT/'presentation/sfo_2018_linkedin_carousel.pdf'),pagesize=(1080,1350))
    c.setTitle('SFO 2018 Customer Experience Case Study');c.setAuthor(spec['author'])
    m=t['metrics_weighted'].set_index('metric');log=[]
    def text(s,x,y,size=32,bold=False,color=NAVY,width=930,leading=None):
        font='CX-Bold' if bold else 'CX';c.setFont(font,size);c.setFillColor(HexColor(color));lines=[]
        for para in s.split('\n'):
            line=''
            for w in para.split():
                candidate=(line+' '+w).strip()
                if pdfmetrics.stringWidth(candidate,font,size)>width and line:lines.append(line);line=w
                else:line=candidate
            lines.append(line)
        for line in lines:c.drawString(x,y,line);log.append(line);y-=leading or size*1.32
        return y
    def start(i):
        s=slides[i-1];dark=i==1
        c.setFillColor(HexColor(NAVY if dark else '#ffffff'));c.rect(0,0,1080,1350,fill=1,stroke=0)
        text(s['section'].upper(),74,1277,22,color='#afd0c9' if dark else MUTED)
        if i!=1:text(s['title'],74,1187,49,True,leading=61)
        c.setStrokeColor(HexColor('#45615f' if dark else '#dce5e1'));c.line(74,115,1006,115)
        text('SFO 2018 / DataSF. My weighted calculations.',74,77,20,color='#b7d0ca' if dark else MUTED)
        text(f'{i:02d} / 10',910,77,18,color='#b7d0ca' if dark else MUTED,width=100)
        return s
    def bars(labels,nums,y,step=130,color=TEAL):
        for label,num in zip(labels,nums):
            text(label,74,y,29);by=y-47
            c.setFillColor(HexColor('#edf2ef'));c.roundRect(74,by,815,22,5,fill=1,stroke=0)
            c.setFillColor(HexColor(color));c.roundRect(74,by,815*num/100,22,5,fill=1,stroke=0)
            text(f'{num:.0f}%',915,by-1,28,True,width=100);y-=step
    s=start(1)
    text(values['NPS_GAP_0'],74,1050,194,True,'#ffffff')
    text(s['title'],74,853,61,True,'#ffffff')
    text(s['subtitle'],74,714,43,True,'#ffffff',leading=58)
    text('2,809 passengers. One airport. Historical survey evidence.',74,485,34,color='#c0d7d1',leading=46)
    text(s['note'],74,345,27,color='#c0d7d1',leading=38)
    text(spec['author'],74,205,29,color='#ffffff');c.showPage()
    s=start(2);text(s['subtitle'],74,980,35,True,leading=48)
    for y,label,body in [(780,'ONE ROW PER PASSENGER','Overall ratings, recommendation, service use and coded problems.'),
                        (585,'DIFFERENT QUESTIONS','1-5 ratings, 0-10 recommendation and explicit Yes/No answers.'),
                        (390,'WEIGHTS AND RESPONSE BASES','Each metric uses its own eligible, valid responses.')]:
        text(label,74,y,23,True,color=TEAL);text(body,74,y-55,31,leading=43)
    text(s['note'],74,198,24,color=MUTED,leading=34);c.showPage()
    s=start(3);text(s['subtitle'],74,978,33,color=MUTED,leading=45)
    bars(['Airport as a whole: rating 4 or 5'],[m.loc['overall_top2','value']],795)
    text('Overall recommendation',74,695,29,color=MUTED)
    text(values['NPS_SIGNED_0'],74,565,103,True,color=TEAL)
    text('NPS points',360,582,31,color=MUTED)
    text(s['note'],74,394,35,True,leading=48)
    text('Valid n: 2,625 for overall rating and 2,650 for NPS.',74,218,25,color=MUTED,leading=35);c.showPage()
    s=start(4);text(s['subtitle'],74,978,29,color=MUTED)
    b=t['by_problem'];b=b[b.metric.eq('nps')].set_index('group')
    for y,label,note,color in [(820,'Reported no problem','n = 2,181',TEAL),(595,'Reported a problem','n = 359',ORANGE)]:
        text(label,74,y,35,True);text(note,74,y-53,26,color=MUTED)
        text(f'{b.loc[label,"value"]:+.0f}',770,y-10,75,True,color=color,width=240)
    text('Difference: '+values['NPS_GAP_1']+' points',74,390,38,True)
    text(s['note'],74,282,29,color=MUTED,leading=41);c.showPage()
    s=start(5);text(s['subtitle'],74,978,28,color=MUTED,leading=39)
    ordered=sorted(SERVICES,key=lambda k:m.loc[k,'value'],reverse=True);keys=ordered[:3]+ordered[-2:]
    bars([SERVICES[k] for k in keys],[m.loc[k,'value'] for k in keys],842,step=109)
    text(s['note'],74,235,27,color=MUTED,leading=38);c.showPage()
    s=start(6);text(s['subtitle'],74,978,31,color=MUTED)
    keys=sorted(['theme_'+k for k in THEMES],key=lambda k:m.loc[k,'value'],reverse=True)[:4]
    bars([m.loc[k,'label'] for k in keys],[m.loc[k,'value'] for k in keys],864,step=128,color=ORANGE)
    text('Base: all 369 problem reporters.',74,307,27,True)
    text(s['note'],74,242,25,color=MUTED,leading=35);c.showPage()
    s=start(7);text(s['subtitle'],74,978,30,color=MUTED,leading=42)
    bars(list(JOURNEY.values()),[m.loc[k,'value'] for k in JOURNEY],807,step=174)
    text('Valid n = 2,603 for navigation\nand 2,364 for security screening.',74,433,31,True,leading=44)
    text(s['note'],74,266,28,color=MUTED,leading=39);c.showPage()
    s=start(8);text(s['subtitle'],74,978,31,color=MUTED)
    bars(['All valid raters (n = 2,074)','Same-day users (valid n = 1,353)'],
         [float(values['WIFI_ALL_1']),float(values['WIFI_USED_1'])],842,step=173)
    text('Usage and rating eligibility need\nseparate definitions.',74,461,37,True,leading=50)
    text(s['note'],74,300,29,color=MUTED,leading=41);c.showPage()
    s=start(9);text(s['subtitle'],74,978,29,color=MUTED,leading=40)
    for y,number,title,body in [(830,'01','Investigate security pain points','Work with relevant partners to connect complaints with queue and incident records.'),
        (622,'02','Examine dining and retail','Ask about value, availability and service before deciding which change to fund.'),
        (414,'03','Define actual-user measures','Track digital-service access and completion alongside user-rated experience.')]:
        text(number,74,y,31,True,color=TEAL);text(title,147,y,33,True,width=840)
        text(body,147,y-62,29,color=MUTED,width=800,leading=40)
    text(s['note'],74,186,23,color=MUTED,leading=33);c.showPage()
    s=start(10);text(s['subtitle'],74,1036,25,color=MUTED,leading=33)
    for y,label,body in [(940,'RATINGS','1-5 are valid. Exclude 0, 6, literal BLANK and missing ratings.'),
                        (745,'RECOMMENDATION','0-10 are valid. Code 11 is blank. NPS uses points.'),
                        (550,'PROBLEM THEMES','Count people once per theme. Include uncoded problem reporters in the base.')]:
        text(label,74,y,24,True,color=TEAL);text(body,74,y-55,31,leading=43)
    text(s['note'],74,347,30,True,leading=42)
    text('2018 evidence. Descriptive associations. No causal effects.',74,198,23,color=MUTED,leading=34)
    c.linkURL('https://data.sf.gov/Transportation/2018-SFO-Customer-Survey/3w8r-nuxp',(74,157,900,192),relative=0)
    c.showPage();c.save();(ROOT/'presentation/carousel_text.txt').write_text('\n'.join(log))

def build_all(d,t,info,dictionary):
    dictionaries(dictionary);charts(t)
    values=context(t)
    report=replace_tokens((ROOT/'reports/case_study_template.md').read_text(),values)
    (ROOT/'reports/case_study.md').write_text(report)
    (ROOT/'outputs/tables/content_values.json').write_text(json.dumps(values,indent=2))
    carousel(t,values);notebook()
