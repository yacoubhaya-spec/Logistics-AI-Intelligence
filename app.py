
import base64, html, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
import altair as alt
import feedparser
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="CEVA Predictive Visibility Intelligence", page_icon="📡", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=60*60*1000,key="hourly_rerun")
BLUE="#0B3A82"; RED="#D62828"; SOFT_BLUE="#EEF4FB"; SOFT_RED="#FDEEEE"; MUTED="#64748B"

st.markdown('''
<style>
.block-container{padding-top:.6rem;padding-bottom:2rem;max-width:1750px} html,body,[class*="css"]{font-family:Arial,sans-serif}
h1,h2,h3{color:#0B3A82}a{color:#1E5AA8;text-decoration:none}a:hover{color:#D62828}
.hero{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:5px solid #D62828;padding:6px 4px 12px;margin-bottom:7px}
.hero-title{font-size:1.95rem;font-weight:850;color:#0B3A82}.hero-sub{font-size:.92rem;color:#64748B}.hero-meta{text-align:right;color:#64748B;font-size:.76rem}
.ticker{display:flex;background:#0B3A82;color:#fff;border-radius:9px;overflow:hidden;margin:7px 0 11px}.ticker-label{background:#D62828;font-weight:850;padding:11px 14px;white-space:nowrap}
.ticker-window{overflow:hidden;white-space:nowrap;flex:1}.ticker-track{display:inline-block;padding-left:100%;animation:move 55s linear infinite}.ticker-track:hover{animation-play-state:paused}
.ticker-item{display:inline-block;margin-right:40px;font-size:.81rem}.ticker-item a{color:#fff;font-weight:650}.ticker-new{background:#D62828;padding:2px 6px;border-radius:4px;font-size:.66rem;font-weight:800;margin-right:6px}
@keyframes move{from{transform:translateX(0)}to{transform:translateX(-100%)}}
.comp-grid{display:grid;grid-template-columns:repeat(10,minmax(100px,1fr));gap:6px;margin:7px 0 11px}.comp-card{border:1px solid #D9E1EA;background:#fff;border-radius:9px;padding:6px;min-height:76px;display:flex;align-items:center;justify-content:center}
.comp-card:hover{border-color:#D62828}.comp-card.selected{border:3px solid #D62828;background:#FDEEEE}.comp-card img{width:100%;height:55px;object-fit:contain}.all-card{font-weight:850;color:#0B3A82;text-align:center}
.kpi{border:1px solid #D9E1EA;border-radius:10px;background:#fff;padding:11px 13px;min-height:82px;position:relative}.kpi:before{content:"";position:absolute;left:0;right:0;top:0;height:5px;background:#0B3A82;border-radius:10px 10px 0 0}.kpi.red:before{background:#D62828}
.kpi-label{font-size:.75rem;color:#64748B}.kpi-value{font-size:1.55rem;font-weight:850;color:#0B3A82;margin-top:2px}.kpi.red .kpi-value{color:#D62828}
.card{border:1px solid #D9E1EA;border-radius:10px;padding:12px 13px;background:#fff;margin-bottom:9px}.card.direct{border-left:6px solid #D62828}.card.adjacent{border-left:6px solid #0B3A82}.card.contextual{border-left:6px solid #64748B}
.meta{font-size:.78rem;color:#64748B;margin:3px 0 6px}.title{font-weight:800;color:#1F2937;font-size:.98rem}
.tag{display:inline-block;padding:3px 7px;border-radius:999px;background:#EEF4FB;color:#0B3A82;font-size:.67rem;margin:2px 4px 2px 0}.tag.red{background:#FDEEEE;color:#A61B1B}
.badge{display:inline-block;padding:3px 6px;border-radius:5px;background:#0B3A82;color:#fff;font-size:.65rem;font-weight:800}.badge.red{background:#D62828}
.evidence{background:#EEF4FB;color:#0B3A82;border-radius:7px;padding:8px 9px;margin-top:7px;font-size:.81rem}.gap{background:#FDEEEE;color:#A61B1B;border-radius:7px;padding:8px 9px;margin-top:7px;font-size:.81rem}
.takeaway{background:#EEF4FB;border-left:5px solid #D62828;border-radius:8px;padding:10px 12px;color:#0B3A82;margin-top:8px}
div[role="radiogroup"]{display:flex;gap:4px;flex-wrap:wrap}div[role="radiogroup"] label{border:1px solid #D9E1EA;border-radius:7px;padding:4px 7px;background:#fff}div[role="radiogroup"] label:has(input:checked){background:#FDEEEE;border-color:#D62828;color:#A61B1B;font-weight:750}
@media(max-width:1200px){.comp-grid{grid-template-columns:repeat(5,minmax(100px,1fr))}}@media(max-width:720px){.comp-grid{grid-template-columns:repeat(2,minmax(100px,1fr))}}
</style>
''',unsafe_allow_html=True)

ROOT=Path(__file__).parent; DATA=ROOT/"data"; LOGOS=ROOT/"assets"/"logos"
COMPETITORS=["Kuehne+Nagel","DSV","DHL Global Forwarding","Sinotrans","Nippon Express","Expeditors","C.H. Robinson","KLN / Kerry Logistics","GEODIS","COSCO Shipping Logistics","Maersk Logistics","Hellmann Worldwide Logistics","Kintetsu World Express","UPS Supply Chain Solutions","Yusen Logistics","DACHSER","LX Pantos","CTS International Logistics","Rhenus Logistics","AWOT Group"]
TOP5=COMPETITORS[:5]; TOP10=COMPETITORS[:10]
def slug(s): return s.lower().replace("+","plus").replace("&","and").replace("/","-").replace(" ","_").replace(".","").replace("__","_")
def data_uri(p): return "data:image/svg+xml;base64,"+base64.b64encode(p.read_bytes()).decode("ascii")
LOGO_DATA={c:data_uri(LOGOS/f"{slug(c)}.svg") for c in COMPETITORS if (LOGOS/f"{slug(c)}.svg").exists()}

VALUE_CHAIN=["All Value-Chain Steps","Booking & pricing","Docs & compliance","Collection & consolidation","Customs clearance (origin)","Security & handling","Air / ocean transport","Customs clearance (dest.)","Decons. & delivery","Audit & settlement"]
DISRUPTIONS=["All disruption types","Geopolitical conflict","Port congestion","Airport disruption","Weather event","Natural hazard","Airspace closure","Maritime-route disruption","Strike or labour disruption","Customs disruption","Regulatory disruption","Capacity constraint","Carrier schedule change","Flight cancellation","Missed connection","Vessel deviation","Vessel rerouting","Blank sailing","Infrastructure failure","Cyber incident","Systems outage","Security event","Cargo-condition exception","Other operational exception"]
CAPS=["Shipment Visibility","Predictive Visibility","Disruption Detection","Shipment Impact Assessment","Customer Alerting and Communication","Decision Support and Mitigation"]
MATURITY=["Level 1 – Shipment Visibility","Level 2 – Predictive Visibility","Level 3 – Disruption Detection","Level 4 – Shipment Impact Assessment","Level 5 – Prescriptive Decision Intelligence"]

OFFICIAL={"Kuehne+Nagel":"newsroom.kuehne-nagel.com","DSV":"dsv.com","DHL Global Forwarding":"group.dhl.com","Sinotrans":"sinotrans.com","Nippon Express":"nipponexpress-holdings.com","Expeditors":"expeditors.com","C.H. Robinson":"chrobinson.com","KLN / Kerry Logistics":"kln.com","GEODIS":"geodis.com","COSCO Shipping Logistics":"coscoshipping.com","Maersk Logistics":"maersk.com","Hellmann Worldwide Logistics":"hellmann.com","Kintetsu World Express":"kwe.com","UPS Supply Chain Solutions":"about.ups.com","Yusen Logistics":"yusen-logistics.com","DACHSER":"dachser.com","LX Pantos":"lxpantos.com","CTS International Logistics":"ctic.com","Rhenus Logistics":"rhenus.group","AWOT Group":"awotglobal.com"}
PRESS=[("Reuters","reuters.com"),("Financial Times","ft.com"),("FreightWaves","freightwaves.com"),("The Loadstar","theloadstar.com"),("Journal of Commerce","joc.com"),("Air Cargo News","aircargonews.net"),("Supply Chain Dive","supplychaindive.com"),("Logistics Management","logisticsmgmt.com")]
CONSULT=[("McKinsey","mckinsey.com"),("BCG","bcg.com"),("Bain","bain.com"),("Deloitte","deloitte.com"),("PwC","pwc.com"),("EY","ey.com"),("KPMG","kpmg.com"),("Accenture","accenture.com"),("Gartner","gartner.com"),("S&P Global","spglobal.com"),("Transport Intelligence","ti-insight.com"),("Drewry","drewry.co.uk"),("Xeneta","xeneta.com"),("World Economic Forum","weforum.org")]
STRICT='("predictive ETA" OR "dynamic ETA" OR visibility OR "delay prediction" OR disruption OR exception OR "customer alert" OR "shipment impact" OR "risk scoring" OR rerouting OR rebooking OR mitigation OR "next best action")'
MODE='("air freight" OR "ocean freight" OR freight OR forwarding OR shipment OR logistics)'
def rss(q): return "https://news.google.com/rss/search?q="+urllib.parse.quote(q)+"&hl=en&gl=US&ceid=US:en"

def detect_company(t):
    t=(t or "").lower()
    pats={"Kuehne+Nagel":["kuehne","kühne","k+n"],"DSV":["dsv"],"DHL Global Forwarding":["dhl"],"Sinotrans":["sinotrans"],"Nippon Express":["nippon express","nx group"],"Expeditors":["expeditors"],"C.H. Robinson":["c.h. robinson","ch robinson"],"KLN / Kerry Logistics":["kerry logistics","kln"],"GEODIS":["geodis"],"COSCO Shipping Logistics":["cosco"],"Maersk Logistics":["maersk"],"Hellmann Worldwide Logistics":["hellmann"],"Kintetsu World Express":["kintetsu","kwe"],"UPS Supply Chain Solutions":["ups supply chain"],"Yusen Logistics":["yusen"],"DACHSER":["dachser"],"LX Pantos":["lx pantos","pantos"],"CTS International Logistics":["cts international"],"Rhenus Logistics":["rhenus"],"AWOT Group":["awot"]}
    for c,ps in pats.items():
        if any(p in t for p in ps): return c
    return "Industry"

def infer_caps(t):
    t=(t or "").lower(); x=[]
    if any(k in t for k in ["track","visibility","milestone","shipment status","location"]): x.append("Shipment Visibility")
    if any(k in t for k in ["predictive eta","dynamic eta","arrival","delay predict","forecast","schedule reliability"]): x.append("Predictive Visibility")
    if any(k in t for k in ["disruption","congestion","closure","weather","strike","exception","cancellation","rerout","blank sailing","deviation"]): x.append("Disruption Detection")
    if any(k in t for k in ["affected shipment","affected customer","impact","exposure","risk scoring","severity","root cause"]): x.append("Shipment Impact Assessment")
    if any(k in t for k in ["notification","alert","notify","customer communication"]): x.append("Customer Alerting and Communication")
    if any(k in t for k in ["alternative route","alternative carrier","mitigation","recovery","rebook","next best action","recommend"]): x.append("Decision Support and Mitigation")
    return x

def infer_value(t):
    t=(t or "").lower(); x=[]
    def add(v):
        if v not in x:x.append(v)
    if any(k in t for k in ["booking","pricing","quote"]):add("Booking & pricing")
    if any(k in t for k in ["document","compliance"]):add("Docs & compliance")
    if any(k in t for k in ["collection","consolidation"]):add("Collection & consolidation")
    if "customs" in t:add("Customs clearance (origin)");add("Customs clearance (dest.)")
    if any(k in t for k in ["security","handling"]):add("Security & handling")
    if any(k in t for k in ["air","ocean","sea","vessel","flight","port","airport","eta","shipment","route"]):add("Air / ocean transport")
    if any(k in t for k in ["delivery","deconsolidation","last mile"]):add("Decons. & delivery")
    if any(k in t for k in ["audit","settlement","billing"]):add("Audit & settlement")
    return x or ["Air / ocean transport"]

def parse_feed(q,label,cat,company=None,limit=8):
    rows=[]; f=feedparser.parse(rss(q))
    for e in f.entries[:limit]:
        dt=datetime(*e.published_parsed[:6],tzinfo=timezone.utc) if getattr(e,"published_parsed",None) else datetime.now(timezone.utc)
        title=e.get("title","").strip(); caps=infer_caps(title)
        if not caps: continue
        pub=label
        if getattr(e,"source",None):
            try: pub=e.source.get("title","") or label
            except: pass
        rows.append({"publication_date":dt,"date_discovered":datetime.now(timezone.utc),"last_verification_date":datetime.now(timezone.utc),
        "competitor":company or detect_company(title),"business_unit":"Not disclosed","platform":"Not disclosed","headline":title,
        "summary":"Discovery item — verify the original source before using as evidence.","source_category":cat,"publisher":pub,"source_url":e.get("link",""),
        "mode_scope":"Not disclosed","geography":"Not disclosed","trade_lane":"Not disclosed","technology":"Not disclosed","capability_group":"; ".join(caps),
        "strategic_relevance":"Direct" if cat=="Official Source" else "Contextual","maturity_level":"Not classified","maturity_status":"Unclear",
        "maturity_evidence":"Requires verification","deployment_stage":"Deployment stage not disclosed","deployment_scope":"Not disclosed","facing":"Not disclosed",
        "customer_notification":"Not disclosed","notification_channel":"Not disclosed","disruption_types":"Other operational exception","value_chain_steps":"; ".join(infer_value(title)),
        "quantitative_evidence":"Not disclosed","kpi_business_outcome":"Not disclosed","confidence":"Low Confidence","evidence_gaps":"Discovery item not manually verified",
        "ceva_implication":"Requires verification before drawing a CEVA implication.","priority":"Medium"})
    return rows

@st.cache_data(ttl=86400,show_spinner=False)
def discover():
    rows=[]
    for c,d in OFFICIAL.items(): rows+=parse_feed(f"site:{d} {STRICT} {MODE}",c,"Official Source",company=c)
    company_or=" OR ".join([f'"{c}"' for c in COMPETITORS[:12]])
    for label,d in PRESS: rows+=parse_feed(f"site:{d} ({company_or}) {STRICT} {MODE}",label,"Press & Media")
    for label,d in CONSULT: rows+=parse_feed(f"site:{d} {STRICT} {MODE}",label,"Consulting & Market Intelligence")
    df=pd.DataFrame(rows)
    if df.empty:return df
    df["publication_date"]=pd.to_datetime(df["publication_date"],utc=True)
    df["age_days"]=(pd.Timestamp.now(tz="UTC")-df["publication_date"]).dt.total_seconds()/86400
    return df.sort_values("publication_date",ascending=False).drop_duplicates("headline")

seed=pd.read_csv(DATA/"seed_intelligence.csv"); seed["publication_date"]=pd.to_datetime(seed["publication_date"],utc=True); seed["age_days"]=(pd.Timestamp.now(tz="UTC")-seed["publication_date"]).dt.total_seconds()/86400
platforms=pd.read_csv(DATA/"platforms.csv")

qp=st.query_params; selected_company=qp.get("competitor","All Competitors")
if selected_company not in COMPETITORS and selected_company!="All Competitors":selected_company="All Competitors"

st.markdown(f'''<div class="hero"><div><div class="hero-title">CEVA Predictive Visibility & Disruption Intelligence</div><div class="hero-sub">Where is my shipment? • When will it arrive? • What may go wrong? • Who is affected? • Who has been alerted? • What should we do next?</div></div><div class="hero-meta">Last checked<br><b>{datetime.now().strftime("%d %b %Y • %H:%M")}</b><br>Auto-refresh: every 24 hours</div></div>''',unsafe_allow_html=True)

a,b,c,d=st.columns([1.8,1,1,1])
with a: search=st.text_input("Search",placeholder="Search platform, ETA, disruption, alerting…",label_visibility="collapsed")
with b: period=st.selectbox("Date",["Last 30 days","Last 90 days","Last 12 months","All verified"],label_visibility="collapsed")
with c: rel_filter=st.multiselect("Strategic relevance",["Direct","Adjacent","Contextual"],default=["Direct"],placeholder="Direct only")
with d:
    if st.button("Refresh discovery",use_container_width=True):st.cache_data.clear();st.rerun()

f1,f2,f3=st.columns(3)
with f1:selected_step=st.selectbox("Value-chain step",VALUE_CHAIN)
with f2:selected_disruption=st.selectbox("Disruption type",DISRUPTIONS)
with f3:selected_cap=st.selectbox("Capability group",["All capability groups"]+CAPS)

scope_choice=st.radio("Competitor scope",["All Competitors","Top 5","Top 10","Top 20"],horizontal=True,label_visibility="collapsed")
scope=TOP5 if scope_choice=="Top 5" else TOP10 if scope_choice=="Top 10" else COMPETITORS
cards=['<div class="comp-grid">']; cls="comp-card selected" if selected_company=="All Competitors" else "comp-card"
cards.append(f'<a href="?competitor=All%20Competitors"><div class="{cls}"><div class="all-card">ALL<br>COMPETITORS</div></div></a>')
for company in scope:
    cls="comp-card selected" if selected_company==company else "comp-card"; src=LOGO_DATA.get(company); href="?competitor="+urllib.parse.quote(company)
    body=f'<img src="{src}" alt="{html.escape(company)}">' if src else f'<div class="all-card">{html.escape(company)}</div>'
    cards.append(f'<a href="{href}"><div class="{cls}">{body}</div></a>')
cards.append("</div>"); st.markdown("".join(cards),unsafe_allow_html=True)

with st.spinner("Checking current sources…"):live=discover()
all_items=pd.concat([seed,live],ignore_index=True,sort=False) if not live.empty else seed.copy()
days={"Last 30 days":30,"Last 90 days":90,"Last 12 months":365,"All verified":99999}[period]
def parts(x):return [v.strip() for v in str(x).split(";") if v.strip() and v.strip().lower()!="nan"]
def filtered(df):
    out=df[df["age_days"]<=days].copy()
    if selected_company!="All Competitors":out=out[out["competitor"]==selected_company]
    if rel_filter:out=out[out["strategic_relevance"].isin(rel_filter)]
    if selected_step!="All Value-Chain Steps":out=out[out["value_chain_steps"].apply(lambda x:selected_step in parts(x))]
    if selected_disruption!="All disruption types":out=out[out["disruption_types"].apply(lambda x:selected_disruption in parts(x))]
    if selected_cap!="All capability groups":out=out[out["capability_group"].apply(lambda x:selected_cap in parts(x))]
    if search:
        s=search.lower(); mask=False
        for col in ["headline","platform","competitor","summary","capability_group","disruption_types"]:mask=mask|out[col].astype(str).str.lower().str.contains(s,na=False)
        out=out[mask]
    return out.sort_values("publication_date",ascending=False)
view=filtered(all_items)

ticker=view[(view["strategic_relevance"]=="Direct")&(view["priority"]=="High")].head(12); t=[]
for _,r in ticker.iterrows():
    t.append(f'<span class="ticker-item"><span class="ticker-new">NEW</span>{r["publication_date"].strftime("%d %b %Y")} · {html.escape(str(r["competitor"]))} · {html.escape(str(r["platform"]))} · <a href="{html.escape(str(r["source_url"]),quote=True)}" target="_blank">{html.escape(str(r["headline"]))}</a> · {html.escape(str(r["maturity_level"]))} · {html.escape(str(r["source_category"]))}</span>')
st.markdown(f'<div class="ticker"><div class="ticker-label">DAILY DISRUPTION INTELLIGENCE</div><div class="ticker-window"><div class="ticker-track">{"".join(t) if t else "<span class=ticker-item>No high-priority Direct items match the active filters.</span>"}</div></div></div>',unsafe_allow_html=True)

pv=platforms.copy()
if selected_company!="All Competitors":pv=pv[pv["competitor"]==selected_company]
highmed=view[view["confidence"].isin(["High Confidence","Medium Confidence"])]
metrics=[("Relevant intelligence",len(view),False),("Direct items",int((view["strategic_relevance"]=="Direct").sum()),True),("New in 30 days",int((view["age_days"]<=30).sum()),False),("Competitors with verified evidence",highmed["competitor"].nunique(),False),("Named platforms",pv["platform_name"].nunique(),False),("Customer-facing deployments",int((view["facing"]=="Customer-facing").sum()),False),("Proactive alerting",int((view["customer_notification"]=="Yes").sum()),True),("Impact-assessment evidence",int(view["maturity_level"].astype(str).str.contains("Level 4").sum()),False),("Prescriptive evidence",int(view["maturity_level"].astype(str).str.contains("Level 5").sum()),True),("Require verification",int((view["confidence"]=="Low Confidence").sum()),True)]
for batch in [metrics[:5],metrics[5:]]:
    cs=st.columns(5)
    for col,(lab,val,red) in zip(cs,batch):
        cl="kpi red" if red else "kpi"; col.markdown(f'<div class="{cl}"><div class="kpi-label">{lab}</div><div class="kpi-value">{val}</div></div>',unsafe_allow_html=True)

tabs=st.tabs(["Executive View","Official Competitor Intelligence","Press & Media","Consulting & Market Intelligence","Platform Intelligence","Maturity Analysis"])
def render(df):
    if df.empty:st.info("No items match the current filters.");return
    for _,r in df.head(60).iterrows():
        cls=str(r["strategic_relevance"]).lower(); red=" red" if r["strategic_relevance"]=="Direct" else ""
        tags="".join(f'<span class="tag">{html.escape(x)}</span>' for x in parts(r["capability_group"]))
        st.markdown(f'''<div class="card {cls}"><span class="badge{red}">{html.escape(str(r["source_category"]))}</span><span class="tag red">{html.escape(str(r["strategic_relevance"]))}</span><span class="tag">{html.escape(str(r["maturity_level"]))}</span>
<div class="title"><a href="{html.escape(str(r["source_url"]),quote=True)}" target="_blank">{html.escape(str(r["headline"]))}</a></div>
<div class="meta">{r["publication_date"].strftime("%d %b %Y")} • {html.escape(str(r["competitor"]))} • {html.escape(str(r["business_unit"]))} • {html.escape(str(r["publisher"]))}</div>
<div>{html.escape(str(r["summary"]))}</div><div>{tags}</div>
<div class="evidence"><b>Evidence:</b> {html.escape(str(r["maturity_evidence"]))}<br><b>Status:</b> {html.escape(str(r["maturity_status"]))} • <b>Confidence:</b> {html.escape(str(r["confidence"]))}<br><b>Quantitative evidence:</b> {html.escape(str(r["quantitative_evidence"]))}</div>
<div class="gap"><b>Evidence gap:</b> {html.escape(str(r["evidence_gaps"]))}</div><div class="takeaway"><b>Implication for CEVA:</b> {html.escape(str(r["ceva_implication"]))}</div></div>''',unsafe_allow_html=True)

with tabs[0]:
    x,y,z=st.columns(3)
    with x:st.markdown("### Official");render(view[view["source_category"]=="Official Source"].head(5))
    with y:st.markdown("### Press & Media");render(view[view["source_category"]=="Press & Media"].head(5))
    with z:st.markdown("### Consulting & Market Intelligence");render(view[view["source_category"]=="Consulting & Market Intelligence"].head(5))
    st.markdown('<div class="takeaway"><b>Interpretation rule:</b> Direct evidence is the default. Adjacent and Contextual items are opt-in. “No public evidence” is not evidence of absence.</div>',unsafe_allow_html=True)
with tabs[1]:render(view[view["source_category"]=="Official Source"])
with tabs[2]:render(view[view["source_category"]=="Press & Media"])
with tabs[3]:render(view[view["source_category"]=="Consulting & Market Intelligence"])
with tabs[4]:
    st.markdown("### Platform Intelligence")
    if pv.empty:st.info("No platform records match the selected competitor.")
    else:
        for _,r in pv.iterrows():
            st.markdown(f'''<div class="card direct"><div class="title">{html.escape(str(r["competitor"]))} — {html.escape(str(r["platform_name"]))}</div><div class="meta">{html.escape(str(r["business_unit"]))} • {html.escape(str(r["mode_coverage"]))}</div><div>{html.escape(str(r["platform_description"]))}</div><div class="evidence"><b>Maturity:</b> {html.escape(str(r["maturity_level"]))} ({html.escape(str(r["maturity_status"]))})<br><b>Evidence:</b> {html.escape(str(r["maturity_evidence"]))}<br><b>Confidence:</b> {html.escape(str(r["confidence"]))}<br><b>Customer notification:</b> {html.escape(str(r["customer_notification"]))} — {html.escape(str(r["notification_mechanism"]))}<br><b>KPIs:</b> {html.escape(str(r["kpis_addressed"]))}<br><b>Results:</b> {html.escape(str(r["quantified_results"]))}</div><div class="gap"><b>Evidence gaps:</b> {html.escape(str(r["evidence_gaps"]))}</div><div class="takeaway"><b>Implication for CEVA:</b> {html.escape(str(r["ceva_implication"]))}</div></div>''',unsafe_allow_html=True)
with tabs[5]:
    st.markdown("### Evidence-Based Capability Maturity Indicator")
    st.caption("Not a definitive ranking. Level 4 and Level 5 require explicit evidence.")
    m=view[view["maturity_level"].isin(MATURITY)].copy()
    if m.empty:st.info("No classified maturity evidence matches the filters.")
    else:
        rank={v:i+1 for i,v in enumerate(MATURITY)};m["level_num"]=m["maturity_level"].map(rank)
        best=m.groupby("competitor")["level_num"].max().reset_index()
        chart=alt.Chart(best).mark_bar(color=BLUE).encode(x=alt.X("level_num:Q",title="Highest evidence-supported level",scale=alt.Scale(domain=[0,5])),y=alt.Y("competitor:N",sort="-x",title=""),tooltip=["competitor","level_num"]).properties(height=420)
        st.altair_chart(chart,use_container_width=True)

st.divider();st.caption("Strict scope: shipment visibility, predictive ETA, disruption detection, impact assessment, proactive customer alerting, exception management and mitigation. Discovery items stay Low Confidence until manually verified.")
