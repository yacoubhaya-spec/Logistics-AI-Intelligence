
import urllib.parse
from datetime import datetime, timezone
import pandas as pd
import feedparser
import streamlit as st
import altair as alt
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="CEVA | AI Competitor Intelligence", page_icon="📡", layout="wide")

# Keep the dashboard alive: rerun hourly; source cache itself refreshes every 24 hours.
st_autorefresh(interval=60 * 60 * 1000, key="hourly_dashboard_rerun")


st.markdown("""
<style>
:root {
    --ceva-blue: #0B3A82;
    --ceva-blue-2: #1E5AA8;
    --ceva-red: #D62828;
    --ceva-red-dark: #A61B1B;
    --soft-blue: #EEF4FB;
    --soft-red: #FDEEEE;
    --border: #D9E1EA;
    --text-muted: #64748B;
}

/* Main titles */
h1, h2, h3 {
    color: var(--ceva-blue);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #F7FAFE 0%, #FFFFFF 100%);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--ceva-blue);
}

/* Metrics */
div[data-testid="stMetric"] {
    border: 1px solid var(--border);
    border-top: 4px solid var(--ceva-blue);
    border-radius: 12px;
    padding: 10px 14px;
    background: white;
}
div[data-testid="stMetric"]:nth-child(3) {
    border-top-color: var(--ceva-red);
}

/* Tabs */
button[data-baseweb="tab"] {
    color: var(--ceva-blue);
    font-weight: 600;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--ceva-red) !important;
}

/* Buttons */
.stButton > button,
.stDownloadButton > button {
    border: 1px solid var(--ceva-blue);
    color: var(--ceva-blue);
    border-radius: 8px;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: var(--ceva-red);
    color: var(--ceva-red);
}

/* Info and warning */
div[data-testid="stAlert"] {
    border-radius: 10px;
}
div[data-testid="stAlert"][data-baseweb="notification"] {
    border-left: 5px solid var(--ceva-blue);
}

/* Links */
a {
    color: var(--ceva-blue-2);
}
a:hover {
    color: var(--ceva-red);
}

/* Dataframe visual container */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 10px;
}

/* Caption */
.stCaption {
    color: var(--text-muted);
}
</style>
""", unsafe_allow_html=True)

COMPETITORS = ["Kuehne+Nagel", "DHL Global Forwarding", "DSV", "Sinotrans", "Nippon Express"]

VERIFIED = [
    {
        "date":"2026-10-01","company":"Kuehne+Nagel","initiative":"Chennai Tech Centre","value_chain":["Docs & compliance","Collection & consolidation","Air / ocean transport"],
        "technology":"AI / proprietary digital products","process":"Technology & product development",
        "stage":"Scaling capability","evidence":"New engineering centre opened to expand development and scaling of proprietary digital logistics solutions as demand for AI solutions grows.",
        "metric":"New global tech centre","source_type":"Official company news",
        "source":"Kuehne+Nagel newsroom",
        "url":"https://newsroom.kuehne-nagel.com/kuehnenagel-opens-chennai-tech-centre-as-demand-for-digital-logistics-and-ai-solutions-grows/",
        "ceva":"Signals sustained investment in in-house engineering capacity. Compare CEVA's internal AI product ownership, engineering footprint and speed from pilot to scaled deployment."
    },
    {
        "date":"2026-09-24","company":"DHL Global Forwarding","initiative":"Logistics Trend Radar 8.0","value_chain":["Booking & pricing","Docs & compliance","Collection & consolidation","Customs clearance (origin)","Security & handling","Air / ocean transport","Customs clearance (dest.)","Decons. & delivery","Audit & settlement"],
        "technology":"Agentic AI / AI Analytics","process":"Planning, decision-making & execution",
        "stage":"Strategic direction","evidence":"DHL identifies Agentic AI as one of the most impactful emerging logistics trends, moving AI from assistance toward autonomous planning, coordination and action.",
        "metric":"Agentic AI added as major trend","source_type":"Official DHL report/news",
        "source":"DHL Group",
        "url":"https://group.dhl.com/en/media-relations/press-releases/2026/ai-takes-action-while-people-remain-at-the-center-of-logistics-finds-dhl-logistics-trend-radar.html",
        "ceva":"Useful benchmark for CEVA's AI roadmap: separate copilots from agents that can execute operational tasks under human governance."
    },
    {
        "date":"2026-09-17","company":"DHL Global Forwarding","initiative":"TradeNavigator","value_chain":["Customs clearance (origin)","Customs clearance (dest.)"],
        "technology":"Natural-language AI analytics","process":"Customs & trade compliance",
        "stage":"Launched","evidence":"Customers can query customs declaration data in natural language and receive analytics on duty spend, tariff exposure, clearance performance and compliance trends.",
        "metric":"DHL cites 4,000+ customs experts and 30,000+ declarations/day supporting the environment","source_type":"Official company press release",
        "source":"DHL Group",
        "url":"https://group.dhl.com/en/media-relations/press-releases/2026/dhl-global-forwarding-launches-tradenavigator-tool.html",
        "ceva":"High-priority benchmark: customs data is being converted from reporting into a customer-facing decision product. Assess similar natural-language access to CEVA customs and trade data."
    },
    {
        "date":"2026-09-10","company":"DHL Global Forwarding","initiative":"Alibaba.com / Accio integration","value_chain":["Booking & pricing"],
        "technology":"Agentic AI","process":"Quotation, booking & shipment execution",
        "stage":"MoU / integration exploration","evidence":"DHL Global Forwarding plans to connect quotation and booking capabilities with Alibaba.com's Accio agentic AI platform for SMEs.",
        "metric":"First capability in a planned suite of logistics integrations","source_type":"Official company press release",
        "source":"DHL Group",
        "url":"https://group.dhl.com/en/media-relations/press-releases/2026/dhl-and-alibaba-com-partner-to-bring-ai-powered-logistics-capabilities-to-small-and-medium-sized-enterprises-worldwide.html",
        "ceva":"Direct commercial threat: freight procurement can move inside AI commerce agents. CEVA should track API readiness, instant quote coverage and embedded-forwarding partnerships."
    },
    {
        "date":"2026-08-19","company":"Nippon Express","initiative":"BI LLM Chat in DCX","value_chain":["Booking & pricing","Air / ocean transport","Audit & settlement"],
        "technology":"Generative AI / LLM","process":"Customer analytics & decision support",
        "stage":"Launched","evidence":"Nippon Express added an LLM chat capability to its DCX logistics web application so users can interact with logistics data and external information.",
        "metric":"Customer-facing LLM analytics capability","source_type":"Official company press release",
        "source":"Nippon Express Holdings",
        "url":"https://www.nipponexpress-holdings.com/ja/press/768",
        "ceva":"Benchmark for customer-facing GenAI: move beyond internal productivity tools toward conversational access to shipment, inventory and market intelligence."
    },
    {
        "date":"2026-07-23","company":"Kuehne+Nagel","initiative":"Accelerated AI deployment","value_chain":["Booking & pricing","Docs & compliance","Collection & consolidation","Customs clearance (origin)","Security & handling","Air / ocean transport","Customs clearance (dest.)","Decons. & delivery","Audit & settlement"],
        "technology":"AI agents / operational AI","process":"Enterprise operations",
        "stage":"Scaling","evidence":"CEO states Kuehne+Nagel is accelerating AI deployment across the organisation, including optimisation of operational processes and integration of AI agents.",
        "metric":"AI tied explicitly to measurable efficiency gains","source_type":"Official Q2 results",
        "source":"Kuehne+Nagel",
        "url":"https://newsroom.kuehne-nagel.com/kuehnenagel-reports-strong-second-quarter-2026/",
        "ceva":"Important because AI is linked to group-level productivity rather than isolated innovation. CEVA should track AI impact through process KPIs and P&L-linked productivity metrics."
    },
    {
        "date":"2026-07-16","company":"Kuehne+Nagel","initiative":"KN SwiftLOG cloud-native rollout","value_chain":["Collection & consolidation","Security & handling","Decons. & delivery"],
        "technology":"Agentic AI-enabled WMS","process":"Contract logistics / warehousing",
        "stage":"Global rollout","evidence":"KN SwiftLOG is being evolved into a cloud-native, agentic-AI-enabled platform based on Blue Yonder technology.",
        "metric":"Rollout spans 1,000+ sites in nearly 100 countries","source_type":"Official company press release",
        "source":"Kuehne+Nagel",
        "url":"https://newsroom.kuehne-nagel.com/kuehnenagel-rolls-out-cloud-native-contract-logistics-solution-across-over-1000-sites-globally/",
        "ceva":"Shows the value of a common digital backbone before AI scaling. Compare CEVA platform standardisation, data interoperability and ability to deploy agents across sites."
    },
    {
        "date":"2026-05-14","company":"Nippon Express","initiative":"DCX AI shipment forecasting upgrade","value_chain":["Air / ocean transport"],
        "technology":"Predictive AI","process":"Inventory & shipment forecasting",
        "stage":"Enhanced production service","evidence":"Nippon Express upgraded AI shipment forecasting in DCX Business Insight, integrating shipment forecasts with inventory and order analytics.",
        "metric":"Forecast calculation reduced from ~1–2 hours per item to ~5 minutes; forecasts available up to 6 months","source_type":"Official company press release",
        "source":"Nippon Express Holdings",
        "url":"https://www.nipponexpress-holdings.com/ja/news/press/2026/20260514-1.html",
        "ceva":"Strong quantified benchmark. CEVA should compare forecast latency, forecast horizon, accuracy and linkage between prediction and operational decisions."
    },
    {
        "date":"2026-05-13","company":"DSV","initiative":"Autonomous freight operations in Texas","value_chain":["Decons. & delivery"],
        "technology":"Autonomous driving","process":"Road linehaul",
        "stage":"Commercial operation","evidence":"DSV and Volvo Autonomous Solutions began autonomous freight operations between Dallas and Houston using Volvo VNL Autonomous trucks.",
        "metric":"First commercial truckload on the lane; ambition to expand lanes","source_type":"Official company press release",
        "source":"DSV",
        "url":"https://www.dsv.com/en/about-dsv/press/news/volvo-autonomous-solutions-and-dsv-announce-autonomous-freight-2628152",
        "ceva":"Not forwarding AI directly, but a strong signal on physical automation. Relevant to CEVA's broader transport network and autonomous capacity strategy."
    },
    {
        "date":"2026-05-12","company":"DSV","initiative":"Leverage to Lead 2030","value_chain":["Booking & pricing","Docs & compliance","Collection & consolidation","Customs clearance (origin)","Security & handling","Air / ocean transport","Customs clearance (dest.)","Decons. & delivery","Audit & settlement"],
        "technology":"AI & technology","process":"Enterprise productivity / network optimisation",
        "stage":"Strategic priority","evidence":"DSV's 2030 strategy explicitly targets productivity improvement from artificial intelligence and technology after the Schenker integration.",
        "metric":"AI embedded in 2030 strategic priorities","source_type":"Investor / regulatory announcement",
        "source":"DSV Investor Relations",
        "url":"https://investor.dsv.com/node/25211",
        "ceva":"AI is positioned as a post-merger productivity lever. CEVA should watch whether Schenker integration enables larger shared datasets, systems consolidation and faster AI scaling."
    },
    {
        "date":"2026-03-30","company":"Sinotrans","initiative":"AI + Logistics operating model","value_chain":["Booking & pricing","Docs & compliance","Collection & consolidation","Customs clearance (origin)","Security & handling","Air / ocean transport","Customs clearance (dest.)","Decons. & delivery","Audit & settlement"],
        "technology":"AI / autonomous driving / robotic automation","process":"End-to-end logistics operations",
        "stage":"Scaled multi-use-case deployment","evidence":"Sinotrans' 2025 annual reporting describes AI + Logistics as a core smart-logistics model, spanning smart ports, warehouses, customer service and autonomous driving.",
        "metric":"236 valid patents; 428 software copyrights; >3.5m km L4 autonomous-driving mileage by end-2025","source_type":"Annual report / HKEX filing",
        "source":"Sinotrans / HKEX",
        "url":"https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0330/2026033002104.pdf",
        "ceva":"Sinotrans is competing through a broad proprietary technology system, not one application. Benchmark breadth of CEVA AI portfolio, IP ownership and scaled deployment metrics."
    },
    {
        "date":"2026-01-16","company":"Nippon Express","initiative":"Digital showroom","value_chain":["Collection & consolidation","Security & handling","Decons. & delivery"],
        "technology":"Digital twin","process":"Solution design / sales / operational improvement",
        "stage":"Launched","evidence":"Nippon Express introduced a virtual logistics showroom using digital-twin technology to support solution co-creation, sales proposals and operational improvement.",
        "metric":"Digital twin applied to customer solutioning","source_type":"Official company press release",
        "source":"Nippon Express Holdings",
        "url":"https://www.nipponexpress-holdings.com/ja/news/press/2026/20260116-1.html",
        "ceva":"Relevant to solution design: digital twins can make pre-sales modelling and warehouse/flow redesign more tangible and faster."
    },
]

OFFICIAL_SEARCHES = {
    "Kuehne+Nagel": 'site:newsroom.kuehne-nagel.com (AI OR "artificial intelligence" OR agentic OR automation OR digital)',
    "DHL Global Forwarding": 'site:group.dhl.com "DHL Global Forwarding" (AI OR "artificial intelligence" OR agentic OR automation)',
    "DSV": 'site:dsv.com DSV (AI OR "artificial intelligence" OR autonomous OR technology)',
    "Nippon Express": 'site:nipponexpress-holdings.com (AI OR "人工智能" OR LLM OR digital twin OR automation)',
    "Sinotrans": 'site:sinotrans.com OR site:hkexnews.hk Sinotrans (AI OR "artificial intelligence" OR autonomous OR smart logistics)',
}

TRADE_QUERY = '("freight forwarding" OR "air freight" OR "ocean freight") (AI OR "artificial intelligence" OR "agentic AI" OR automation)'

def rss(query):
    return "https://news.google.com/rss/search?q="+urllib.parse.quote(query)+"&hl=en&gl=US&ceid=US:en"

@st.cache_data(ttl=86400, show_spinner=False)
def fetch(q, company, tier):
    f=feedparser.parse(rss(q))
    rows=[]
    for e in f.entries[:25]:
        dt = datetime(*e.published_parsed[:6], tzinfo=timezone.utc) if getattr(e,"published_parsed",None) else datetime.now(timezone.utc)
        rows.append({
            "date":dt,
            "company":company,
            "title":e.get("title",""),
            "url":e.get("link",""),
            "publisher":getattr(e,"source",{}).get("title","") if getattr(e,"source",None) else "",
            "source_tier":tier
        })
    return rows


VALUE_CHAIN_STEPS = [
    "All steps",
    "Booking & pricing",
    "Docs & compliance",
    "Collection & consolidation",
    "Customs clearance (origin)",
    "Security & handling",
    "Air / ocean transport",
    "Customs clearance (dest.)",
    "Decons. & delivery",
    "Audit & settlement",
]

def map_value_chain(title: str):
    """Rule-based mapping of a live headline to one or more forwarding value-chain steps."""
    t = (title or "").lower()
    steps = []

    def add(step):
        if step not in steps:
            steps.append(step)

    if any(k in t for k in ["quote", "quotation", "pricing", "rate", "booking", "procurement", "sales", "commercial"]):
        add("Booking & pricing")
    if any(k in t for k in ["document", "documentation", "compliance", "trade compliance", "paperwork", "invoice"]):
        add("Docs & compliance")
    if any(k in t for k in ["warehouse", "wms", "consolidation", "fulfillment", "fulfilment", "sortation", "inventory"]):
        add("Collection & consolidation")
    if any(k in t for k in ["customs", "tariff", "duty", "clearance", "brokerage"]):
        add("Customs clearance (origin)")
        add("Customs clearance (dest.)")
    if any(k in t for k in ["security", "inspection", "screening", "cargo handling", "handling"]):
        add("Security & handling")
    if any(k in t for k in ["air freight", "ocean freight", "sea freight", "capacity", "routing", "route", "eta", "shipment forecast", "network optimization"]):
        add("Air / ocean transport")
    if any(k in t for k in ["last mile", "delivery", "trucking", "truck", "autonomous freight", "distribution"]):
        add("Decons. & delivery")
    if any(k in t for k in ["audit", "settlement", "billing", "payment", "reconciliation", "cost allocation"]):
        add("Audit & settlement")

    # Enterprise-wide items remain discoverable across the chain.
    if any(k in t for k in ["enterprise ai", "ai strategy", "digital transformation", "agentic ai", "artificial intelligence strategy"]):
        return VALUE_CHAIN_STEPS[1:]

    return steps or ["Air / ocean transport"]

def live_news():
    rows=[]
    for c,q in OFFICIAL_SEARCHES.items():
        rows += fetch(q,c,"Primary / official")
    rows += fetch(TRADE_QUERY,"Industry","Secondary / trade press")
    df=pd.DataFrame(rows)
    if df.empty:return df
    df["date"]=pd.to_datetime(df["date"], utc=True)
    df["age_days"]=(pd.Timestamp.now(tz="UTC")-df["date"]).dt.total_seconds()/86400
    df["value_chain"]=df["title"].apply(map_value_chain)
    df=df.sort_values("date",ascending=False).drop_duplicates(subset=["title"])
    return df

v=pd.DataFrame(VERIFIED)
if "value_chain" not in v.columns:
    v["value_chain"] = [[] for _ in range(len(v))]
v["date"]=pd.to_datetime(v["date"])
v["days_old"]=(pd.Timestamp.now().normalize().tz_localize(None)-v["date"]).dt.days

st.title("AI Competitor Intelligence — Freight Forwarding")
st.caption("Evidence-led view for CEVA Logistics • primary sources first • verified initiatives + live official-source watcher")

with st.sidebar:
    st.header("Filters")
    companies=st.multiselect("Competitors", COMPETITORS, default=COMPETITORS)
    tech=st.multiselect("Technology", sorted(v["technology"].unique()), default=[])
    stages=st.multiselect("Deployment stage", sorted(v["stage"].unique()), default=[])
    st.markdown("---")
    st.caption("Source policy")
    st.write("1. Company press releases / IR\n2. Annual & interim reports / regulatory filings\n3. Official technology partner releases\n4. Reputable trade press for context only")

view=v[v["company"].isin(companies)].copy()
if selected_value_chain != "All steps":
    view = view[view["value_chain"].apply(lambda steps: selected_value_chain in steps)]
if tech: view=view[view["technology"].isin(tech)]
if stages:view=view[view["stage"].isin(stages)]

c1,c2,c3,c4=st.columns(4)
c1.metric("Verified initiatives",len(view))
c2.metric("Competitors covered",view["company"].nunique())
c3.metric("Launched / scaling",view["stage"].isin(["Launched","Scaling","Global rollout","Enhanced production service","Commercial operation","Scaled multi-use-case deployment","Scaling capability"]).sum())
c4.metric("Primary-source share","100%")

tabs=st.tabs(["Executive view","Verified initiatives","Competitor comparison","Live source watcher","Sources & methodology"])

with tabs[0]:
    st.subheader("What is actually changing")
    focus=view.sort_values("date",ascending=False).head(6)
    for _,r in focus.iterrows():
        st.markdown(f"### {r['company']} — {r['initiative']}")
        st.write(r["evidence"])
        st.caption("**Value-chain step(s):** " + " • ".join(r["value_chain"]))
        cols=st.columns([1,1,1])
        cols[0].caption(f"**Technology:** {r['technology']}")
        cols[1].caption(f"**Process:** {r['process']}")
        cols[2].caption(f"**Stage:** {r['stage']}")
        threat_terms = ["threat", "commercial", "autonomous", "embedded", "pricing", "customer-facing"]
        is_priority = any(term in r["ceva"].lower() for term in threat_terms)
        if is_priority:
            st.markdown(
                f"<div style='background:#FDEEEE;border-left:5px solid #D62828;padding:12px 14px;border-radius:8px;'><b style='color:#A61B1B;'>CEVA strategic implication</b><br>{r['ceva']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='background:#EEF4FB;border-left:5px solid #0B3A82;padding:12px 14px;border-radius:8px;'><b style='color:#0B3A82;'>CEVA strategic implication</b><br>{r['ceva']}</div>",
                unsafe_allow_html=True
            )
        st.markdown(f"[Open official source]({r['url']})")
        st.divider()

with tabs[1]:
    cols=["date","company","initiative","value_chain","technology","process","stage","metric","source_type"]
    st.dataframe(view[cols].sort_values("date",ascending=False),use_container_width=True,hide_index=True)
    st.download_button("Download verified intelligence CSV",
        view.to_csv(index=False).encode("utf-8"),
        file_name="ceva_ai_verified_competitor_intelligence.csv",
        mime="text/csv")

with tabs[2]:
    st.subheader("Competitor maturity signals")
    stage_score={
        "Strategic direction":1,"Strategic priority":1,"MoU / integration exploration":2,
        "Scaling capability":2,"Launched":3,"Enhanced production service":3,
        "Commercial operation":3,"Scaling":4,"Global rollout":4,"Scaled multi-use-case deployment":5
    }
    temp=view.copy()
    temp["score"]=temp["stage"].map(stage_score).fillna(1)
    agg=temp.groupby("company").agg(
        verified_initiatives=("initiative","count"),
        deployment_score=("score","sum"),
        technologies=("technology","nunique"),
        processes=("process","nunique")
    ).reset_index()
    st.dataframe(agg.sort_values("deployment_score",ascending=False),use_container_width=True,hide_index=True)
    chart=alt.Chart(agg).mark_bar(color="#0B3A82").encode(
        x=alt.X("deployment_score:Q",title="Evidence-weighted deployment score"),
        y=alt.Y("company:N",sort="-x",title=""),
        tooltip=["company","verified_initiatives","technologies","processes","deployment_score"]
    )
    st.altair_chart(chart,use_container_width=True)
    st.caption("Score is a dashboard heuristic based only on verified items in this dataset; it is not a definitive ranking of total AI maturity.")

with tabs[3]:
    st.subheader("Live source watcher")
    st.caption("Fresh headlines are pulled from searches restricted to official domains. Source data refreshes automatically every 24 hours; the app reruns hourly while open. Trade press is shown separately as secondary context.")
    if st.button("Refresh watcher"):
        st.cache_data.clear()
    live=live_news()
    if live.empty:
        st.warning("Live feeds unavailable.")
    else:
        days=st.selectbox("Show",["7 days","30 days","90 days"],index=1)
        n={"7 days":7,"30 days":30,"90 days":90}[days]
        live=live[live["age_days"]<=n]
        if selected_value_chain != "All steps":
            live = live[live["value_chain"].apply(lambda steps: selected_value_chain in steps)]
        for tier in ["Primary / official","Secondary / trade press"]:
            st.markdown("#### "+tier)
            x=live[live["source_tier"]==tier].head(30)
            if x.empty: st.caption("No matching items in this period.")
            for _,r in x.iterrows():
                d=r["date"].strftime("%d %b %Y")
                st.markdown(f"**{r['company']}** · {d}  \n[{r['title']}]({r['url']})")
                st.caption("Value-chain: " + " • ".join(r["value_chain"]))
                if r["publisher"]: st.caption(r["publisher"])

with tabs[4]:
    st.subheader("Source methodology")
    st.markdown("""
This version does **not** infer competitor activity from generic keyword volume.

**Evidence hierarchy**
1. Official company newsroom / press releases
2. Investor relations, annual reports, interim results and regulatory filings
3. Official partner announcements where the competitor is a named participant
4. Reputable logistics/trade press only for context and discovery

**Interactive value-chain filter**
- Click a value-chain step at the top of the dashboard to show only mapped verified initiatives and live news.
- Items can map to more than one step when they span multiple forwarding processes.
- Live headlines are mapped using transparent keyword rules; verified initiatives use curated mappings.

**Each verified record includes**
- publication date
- concrete initiative
- AI/technology type
- business process affected
- deployment stage
- quantified evidence where disclosed
- direct source
- CEVA-specific implication

**What is intentionally excluded**
- unsourced social-media claims
- generic “AI will transform logistics” articles
- duplicated syndicated stories
- vendor marketing where the competitor is not explicitly named
- speculative maturity scores without underlying evidence
""")
