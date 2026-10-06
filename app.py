import base64, html, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
import altair as alt
import feedparser
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title='CEVA AI Intelligence Dashboard', page_icon='📡', layout='wide', initial_sidebar_state='collapsed')
st_autorefresh(interval=60*60*1000, key='hourly_rerun')

BLUE='#0B3A82'; RED='#D62828'; MUTED='#64748B'
st.markdown("""
<style>
.block-container{padding-top:.6rem;padding-bottom:2rem;max-width:1750px}html,body,[class*=css]{font-family:Inter,Arial,sans-serif}h1,h2,h3{color:#0B3A82}a{color:#1E5AA8;text-decoration:none}a:hover{color:#D62828}.hero{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:5px solid #D62828;padding:7px 4px 12px;margin-bottom:8px}.hero-title{font-size:2rem;font-weight:850;color:#0B3A82}.hero-sub{font-size:.95rem;color:#64748B}.hero-meta{text-align:right;color:#64748B;font-size:.77rem}.ticker-wrap{display:flex;align-items:center;background:#0B3A82;color:#fff;border-radius:10px;overflow:hidden;margin:7px 0 12px}.ticker-label{flex:0 0 auto;background:#D62828;color:#fff;font-weight:850;padding:11px 16px}.ticker-window{overflow:hidden;white-space:nowrap;flex:1}.ticker-track{display:inline-block;padding-left:100%;animation:tickerMove 55s linear infinite}.ticker-track:hover{animation-play-state:paused}.ticker-item{display:inline-block;margin-right:42px;font-size:.83rem}.ticker-item a{color:#fff;font-weight:650}.ticker-new{background:#D62828;color:#fff;border-radius:5px;padding:2px 6px;margin-right:6px;font-size:.68rem;font-weight:800}@keyframes tickerMove{from{transform:translateX(0)}to{transform:translateX(-100%)}}.competitor-grid{display:grid;grid-template-columns:repeat(7,minmax(110px,1fr));gap:7px;margin:7px 0 12px}.competitor-card{border:1px solid #D9E1EA;background:#fff;border-radius:10px;padding:7px;min-height:79px;display:flex;align-items:center;justify-content:center;transition:.15s}.competitor-card:hover{border-color:#D62828;transform:translateY(-1px)}.competitor-card.selected{border:3px solid #D62828;background:#FDEEEE}.competitor-card img{width:100%;height:58px;object-fit:contain}.all-card{font-weight:850;color:#0B3A82;font-size:.9rem;text-align:center}.section-title{color:#0B3A82;font-weight:850;font-size:.93rem;margin:9px 0 5px}.kpi{border:1px solid #D9E1EA;border-radius:11px;background:#fff;padding:12px 14px;min-height:86px;position:relative}.kpi:before{content:'';position:absolute;top:0;left:0;right:0;height:5px;background:#0B3A82;border-radius:11px 11px 0 0}.kpi.red:before{background:#D62828}.kpi-label{font-size:.77rem;color:#64748B}.kpi-value{font-size:1.65rem;font-weight:850;color:#0B3A82;margin-top:3px}.kpi.red .kpi-value{color:#D62828}.source-head{border-radius:10px;padding:12px 14px;color:#fff;font-weight:850;margin-bottom:9px}.source-head.blue{background:#0B3A82}.source-head.red{background:#D62828}.source-sub{font-size:.78rem;font-weight:500;margin-top:2px}.news-card{border:1px solid #D9E1EA;border-radius:10px;background:#fff;padding:12px 13px;margin-bottom:9px}.news-card.official{border-left:6px solid #0B3A82}.news-card.media{border-left:6px solid #D62828}.news-card.consulting{border-left:6px solid #0B3A82}.news-title{font-weight:800;color:#1F2937;font-size:.98rem;margin:5px 0 2px}.news-meta{color:#64748B;font-size:.78rem;margin-bottom:6px}.tag{display:inline-block;border-radius:999px;padding:3px 7px;margin:2px 4px 2px 0;font-size:.68rem;background:#EEF4FB;color:#0B3A82}.tag.red{background:#FDEEEE;color:#A61B1B}.badge{display:inline-block;border-radius:5px;padding:3px 6px;font-size:.67rem;font-weight:800;color:#fff;background:#0B3A82}.badge.red{background:#D62828}.takeaway{background:#EEF4FB;border-left:5px solid #D62828;border-radius:9px;padding:11px 13px;margin-top:10px;color:#0B3A82}button[data-baseweb=tab]{font-weight:750;color:#0B3A82}button[data-baseweb=tab][aria-selected=true]{color:#D62828!important}.stButton>button{border:1px solid #0B3A82;color:#0B3A82;border-radius:8px}.stButton>button:hover{border-color:#D62828;color:#D62828}@media(max-width:1100px){.competitor-grid{grid-template-columns:repeat(4,minmax(110px,1fr))}}@media(max-width:700px){.competitor-grid{grid-template-columns:repeat(2,minmax(110px,1fr))}}
</style>
""", unsafe_allow_html=True)

COMPETITORS=['Kuehne+Nagel','DSV','DHL Global Forwarding','Sinotrans','Nippon Express','Expeditors','C.H. Robinson','KLN / Kerry Logistics','GEODIS','COSCO Shipping Logistics','Maersk Logistics','Hellmann Worldwide Logistics','Kintetsu World Express','UPS Supply Chain Solutions','Yusen Logistics','DACHSER','LX Pantos','CTS International Logistics','Rhenus Logistics','AWOT Group']
VALUE_CHAIN=['All steps','Booking & pricing','Docs & compliance','Collection & consolidation','Customs clearance (origin)','Security & handling','Air / ocean transport','Customs clearance (dest.)','Decons. & delivery','Audit & settlement']
OFFICIAL_DOMAINS={'Kuehne+Nagel':'newsroom.kuehne-nagel.com','DSV':'dsv.com','DHL Global Forwarding':'group.dhl.com','Sinotrans':'sinotrans.com','Nippon Express':'nipponexpress-holdings.com','Expeditors':'expeditors.com','C.H. Robinson':'chrobinson.com','KLN / Kerry Logistics':'kln.com','GEODIS':'geodis.com','COSCO Shipping Logistics':'coscoshipping.com','Maersk Logistics':'maersk.com','Hellmann Worldwide Logistics':'hellmann.com','Kintetsu World Express':'kwe.com','UPS Supply Chain Solutions':'about.ups.com','Yusen Logistics':'yusen-logistics.com','DACHSER':'dachser.com','LX Pantos':'lxpantos.com','CTS International Logistics':'ctic.com','Rhenus Logistics':'rhenus.group','AWOT Group':'awotglobal.com'}
PRESS=[('Reuters','reuters.com'),('Financial Times','ft.com'),('FreightWaves','freightwaves.com'),('The Loadstar','theloadstar.com'),('Journal of Commerce','joc.com'),('Air Cargo News','aircargonews.net'),('Supply Chain Dive','supplychaindive.com'),('Logistics Management','logisticsmgmt.com')]
CONSULTING=[('McKinsey & Company','mckinsey.com'),('BCG','bcg.com'),('Bain & Company','bain.com'),('Deloitte','deloitte.com'),('PwC','pwc.com'),('EY','ey.com'),('KPMG','kpmg.com'),('Accenture','accenture.com'),('Gartner','gartner.com'),('S&P Global','spglobal.com'),('Transport Intelligence','ti-insight.com'),('Drewry','drewry.co.uk'),('Xeneta','xeneta.com'),('World Economic Forum','weforum.org')]
AI='(AI OR "artificial intelligence" OR "agentic AI" OR "generative AI" OR automation OR autonomous OR "machine learning" OR robotics OR digital)'
LOGISTICS='("freight forwarding" OR logistics OR "air freight" OR "ocean freight" OR customs OR "supply chain")'

def slug(s): return s.lower().replace('+','plus').replace('&','and').replace('/','-').replace(' ','_').replace('.','').replace('__','_')
def data_uri(path): return 'data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode('ascii')
LOGO_DIR=Path(__file__).parent/'assets'/'logos'
LOGOS={c:data_uri(LOGO_DIR/f'{slug(c)}.svg') for c in COMPETITORS if (LOGO_DIR/f'{slug(c)}.svg').exists()}

def rss(q): return 'https://news.google.com/rss/search?q='+urllib.parse.quote(q)+'&hl=en&gl=US&ceid=US:en'
def detect_company(title):
    t=(title or '').lower(); pats={'Kuehne+Nagel':['kuehne','kühne','k+n'],'DSV':['dsv'],'DHL Global Forwarding':['dhl'],'Sinotrans':['sinotrans'],'Nippon Express':['nippon express','nx group'],'Expeditors':['expeditors'],'C.H. Robinson':['c.h. robinson','ch robinson'],'KLN / Kerry Logistics':['kerry logistics','kln'],'GEODIS':['geodis'],'COSCO Shipping Logistics':['cosco'],'Maersk Logistics':['maersk'],'Hellmann Worldwide Logistics':['hellmann'],'Kintetsu World Express':['kintetsu','kwe'],'UPS Supply Chain Solutions':['ups supply chain','ups scs'],'Yusen Logistics':['yusen'],'DACHSER':['dachser'],'LX Pantos':['lx pantos','pantos'],'CTS International Logistics':['cts international'],'Rhenus Logistics':['rhenus'],'AWOT Group':['awot']}
    for c,ps in pats.items():
        if any(p in t for p in ps): return c
    return 'Industry'
def map_chain(title):
    t=(title or '').lower(); out=[]
    def add(x):
        if x not in out: out.append(x)
    if any(k in t for k in ['booking','quote','quotation','pricing','rate','procurement','commercial']): add('Booking & pricing')
    if any(k in t for k in ['document','documentation','compliance','paperwork','invoice']): add('Docs & compliance')
    if any(k in t for k in ['collection','consolidation','warehouse','inventory','wms','fulfilment','fulfillment']): add('Collection & consolidation')
    if any(k in t for k in ['customs','tariff','duty','clearance','brokerage']): add('Customs clearance (origin)'); add('Customs clearance (dest.)')
    if any(k in t for k in ['security','inspection','screening','handling']): add('Security & handling')
    if any(k in t for k in ['air freight','ocean freight','sea freight','capacity','routing','route','eta','vessel','air cargo']): add('Air / ocean transport')
    if any(k in t for k in ['delivery','last mile','deconsolidation','trucking','truck','distribution']): add('Decons. & delivery')
    if any(k in t for k in ['audit','settlement','billing','payment','reconciliation']): add('Audit & settlement')
    if any(k in t for k in ['agentic ai','digital transformation','ai strategy']): return VALUE_CHAIN[1:]
    return out or ['Air / ocean transport']
def parse(q,label,category,company=None,limit=10):
    f=feedparser.parse(rss(q)); rows=[]
    for e in f.entries[:limit]:
        dt=datetime(*e.published_parsed[:6],tzinfo=timezone.utc) if getattr(e,'published_parsed',None) else datetime.now(timezone.utc)
        pub=label
        if getattr(e,'source',None):
            try: pub=e.source.get('title','') or label
            except: pass
        title=e.get('title','').strip(); rows.append({'date':dt,'title':title,'url':e.get('link',''),'publisher':pub,'source_category':category,'company':company or detect_company(title)})
    return rows
def derive(df):
    if df.empty:return df
    df['date']=pd.to_datetime(df['date'],utc=True); df['age_days']=(pd.Timestamp.now(tz='UTC')-df['date']).dt.total_seconds()/86400; df['value_chain']=df['title'].apply(map_chain)
    return df.sort_values('date',ascending=False).drop_duplicates('title')
@st.cache_data(ttl=86400,show_spinner=False)
def fetch_official():
    rows=[]
    for c,d in OFFICIAL_DOMAINS.items(): rows+=parse(f'site:{d} "{c}" {AI}',c,'Official',c,8)
    return derive(pd.DataFrame(rows))
@st.cache_data(ttl=86400,show_spinner=False)
def fetch_press():
    names=' OR '.join('"'+c+'"' for c in COMPETITORS[:12]); rows=[]
    for n,d in PRESS: rows+=parse(f'site:{d} ({names}) {AI}',n,'Press & Media',None,10)
    return derive(pd.DataFrame(rows))
@st.cache_data(ttl=86400,show_spinner=False)
def fetch_consulting():
    rows=[]
    for n,d in CONSULTING: rows+=parse(f'site:{d} {LOGISTICS} {AI}',n,'Consulting & Market Intelligence',None,8)
    return derive(pd.DataFrame(rows))

qp=st.query_params; selected_company=qp.get('competitor','All competitors')
if selected_company not in COMPETITORS and selected_company!='All competitors': selected_company='All competitors'
st.markdown(f'<div class="hero"><div><div class="hero-title">CEVA AI Intelligence Dashboard</div><div class="hero-sub">Competitor Moves | Market Insights | Strategic Implications</div></div><div class="hero-meta">Last checked<br><b>{datetime.now().strftime("%d %b %Y • %H:%M")}</b><br>Auto-refresh: every 24 hours</div></div>',unsafe_allow_html=True)
with st.spinner('Refreshing intelligence sources…'):
    official_df=fetch_official(); press_df=fetch_press(); consulting_df=fetch_consulting()
# ticker
ticker=pd.concat([official_df.assign(rank=1),press_df.assign(rank=2),consulting_df.assign(rank=3)],ignore_index=True)
ticker=ticker[ticker['age_days']<=30].sort_values(['date','rank'],ascending=[False,True]).head(12)
items=[]
for _,r in ticker.iterrows():
    lab='OFFICIAL' if r['source_category']=='Official' else ('MEDIA' if r['source_category']=='Press & Media' else 'REPORT')
    items.append(f'<span class="ticker-item"><span class="ticker-new">{lab}</span>{r["date"].strftime("%d %b")} &nbsp; <a href="{html.escape(r["url"],quote=True)}" target="_blank">{html.escape(r["title"])}</a></span>')
st.markdown('<div class="ticker-wrap"><div class="ticker-label">DAILY AI INTELLIGENCE</div><div class="ticker-window"><div class="ticker-track">'+(''.join(items) if items else 'No new items in the last 30 days.')+'</div></div></div>',unsafe_allow_html=True)
# filters
c1,c2,c3,c4=st.columns([2.1,1,1,1])
with c1: search=st.text_input('Search',placeholder='Search competitor, AI topic, customs, pricing…',label_visibility='collapsed')
with c2: source_filter=st.selectbox('Source type',['All sources','Official','Press & Media','Consulting & Market Intelligence'],label_visibility='collapsed')
with c3: period=st.selectbox('Date range',['Last 7 days','Last 30 days','Last 90 days','Last 12 months'],index=1,label_visibility='collapsed')
with c4:
    if st.button('Refresh now',use_container_width=True): st.cache_data.clear(); st.rerun()
# clickable logos
st.markdown('<div class="section-title">SELECT COMPETITOR — click a logo to filter the entire dashboard</div>',unsafe_allow_html=True)
g=['<div class="competitor-grid">']; cls='competitor-card selected' if selected_company=='All competitors' else 'competitor-card'; g.append(f'<a href="?competitor=All%20competitors"><div class="{cls}"><div class="all-card">ALL<br>COMPETITORS</div></div></a>')
for c in COMPETITORS:
    cls='competitor-card selected' if selected_company==c else 'competitor-card'; href='?competitor='+urllib.parse.quote(c); src=LOGOS.get(c); body=f'<img src="{src}" alt="{html.escape(c)}">' if src else f'<div class="all-card">{html.escape(c)}</div>'; g.append(f'<a href="{href}"><div class="{cls}">{body}</div></a>')
g.append('</div>'); st.markdown(''.join(g),unsafe_allow_html=True)
st.markdown('<div class="section-title">FILTER BY FREIGHT VALUE CHAIN STEP</div>',unsafe_allow_html=True); selected_step=st.radio('Value chain',VALUE_CHAIN,horizontal=True,label_visibility='collapsed')
days={'Last 7 days':7,'Last 30 days':30,'Last 90 days':90,'Last 12 months':365}[period]
def filt(df,industry=False):
    if df.empty:return df
    x=df[df['age_days']<=days].copy()
    if selected_company!='All competitors': x=x[(x['company']==selected_company)|(x['company']=='Industry')] if industry else x[x['company']==selected_company]
    if selected_step!='All steps': x=x[x['value_chain'].apply(lambda a:selected_step in a)]
    if search:
        s=search.lower(); x=x[x['title'].str.lower().str.contains(s,na=False)|x['publisher'].str.lower().str.contains(s,na=False)|x['company'].str.lower().str.contains(s,na=False)]
    return x
fo=filt(official_df); fp=filt(press_df); fc=filt(consulting_df,True)
if source_filter=='Official': fp=fp.iloc[0:0]; fc=fc.iloc[0:0]
elif source_filter=='Press & Media': fo=fo.iloc[0:0]; fc=fc.iloc[0:0]
elif source_filter=='Consulting & Market Intelligence': fo=fo.iloc[0:0]; fp=fp.iloc[0:0]
cols=st.columns(5)
for col,(lab,val,red) in zip(cols,[('Total intelligence items',len(fo)+len(fp)+len(fc),False),('Official competitor sources',len(fo),False),('Press & media',len(fp),True),('Consulting & market intelligence',len(fc),False),('Competitors tracked',20,False)]):
    col.markdown(f'<div class="kpi{" red" if red else ""}"><div class="kpi-label">{lab}</div><div class="kpi-value">{val}</div></div>',unsafe_allow_html=True)

def render(df,kind,n=30):
    if df.empty: st.info('No items match the current filters.'); return
    for _,r in df.head(n).iterrows():
        badge='OFFICIAL SOURCE' if kind=='official' else ('PRESS & MEDIA' if kind=='media' else 'MARKET INTELLIGENCE'); bcls=' red' if kind=='media' else ''; cls=kind; tags=''.join(f'<span class="tag">{html.escape(x)}</span>' for x in r['value_chain'])
        st.markdown(f'<div class="news-card {cls}"><span class="badge{bcls}">{badge}</span><div class="news-title"><a href="{html.escape(r["url"],quote=True)}" target="_blank">{html.escape(r["title"])}</a></div><div class="news-meta">{r["date"].strftime("%d %b %Y")} • {html.escape(r["company"])} • {html.escape(r["publisher"])}</div><div>{tags}</div></div>',unsafe_allow_html=True)

tabs=st.tabs(['Executive View','Official Competitor Intelligence','Press & Media Intelligence','Consulting & Market Intelligence','Competitor Analysis'])
with tabs[0]:
    a,b,c=st.columns(3)
    with a: st.markdown('<div class="source-head blue">Official Competitor Intelligence<div class="source-sub">Company newsrooms, investor relations, filings and official announcements.</div></div>',unsafe_allow_html=True); render(fo,'official',6)
    with b: st.markdown('<div class="source-head red">Press & Media Intelligence<div class="source-sub">Reliable business and logistics press for external interpretation and context.</div></div>',unsafe_allow_html=True); render(fp,'media',6)
    with c: st.markdown('<div class="source-head blue">Consulting & Market Intelligence<div class="source-sub">Consulting firms, research houses and market-intelligence providers.</div></div>',unsafe_allow_html=True); render(fc,'consulting',6)
    st.markdown(f'<div class="takeaway"><b>Key takeaway for CEVA:</b> current filtered view = <b>{len(fo)}</b> official items, <b>{len(fp)}</b> press/media items and <b>{len(fc)}</b> consulting/market-intelligence items.</div>',unsafe_allow_html=True)
with tabs[1]: st.markdown('### Official Competitor Intelligence'); render(fo,'official',60)
with tabs[2]: st.markdown('### Reliable Press & Media Intelligence'); render(fp,'media',60)
with tabs[3]: st.markdown('### Consulting & Market Intelligence'); render(fc,'consulting',60)
with tabs[4]:
    st.markdown('### Competitor Analysis'); ana=pd.concat([fo,fp,fc],ignore_index=True)
    if ana.empty: st.info('No data for current filters.')
    else:
        comp=ana[ana['company']!='Industry'].groupby('company').size().reset_index(name='items').sort_values('items',ascending=False)
        if not comp.empty:
            st.altair_chart(alt.Chart(comp).mark_bar(color=BLUE).encode(x=alt.X('items:Q',title='Intelligence items'),y=alt.Y('company:N',sort='-x',title=''),tooltip=['company','items']).properties(height=450),use_container_width=True)
        vc=[]
        for _,r in ana.iterrows(): vc.extend(r['value_chain'])
        if vc:
            v=pd.Series(vc).value_counts().reset_index(); v.columns=['value_chain_step','items']; st.altair_chart(alt.Chart(v).mark_bar(color=RED).encode(x='items:Q',y=alt.Y('value_chain_step:N',sort='-x',title=''),tooltip=['value_chain_step','items']).properties(height=350),use_container_width=True)
st.divider(); st.caption('Source hierarchy: official competitor evidence first; reliable press/media second; consulting and market intelligence for broader benchmarks. Validate important intelligence against the linked original source.')
