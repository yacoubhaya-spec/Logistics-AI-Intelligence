
import urllib.parse
from datetime import datetime, timezone

import altair as alt
import feedparser
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="CEVA AI Competitor Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hourly rerun while open; source queries themselves are cached for 24 hours.
st_autorefresh(interval=60 * 60 * 1000, key="hourly_rerun")

BLUE = "#0B3A82"
RED = "#D62828"
SOFT_BLUE = "#EEF4FB"
SOFT_RED = "#FDEEEE"
BORDER = "#D9E1EA"
MUTED = "#64748B"

st.markdown("""
<style>
.block-container {padding-top: .8rem; padding-bottom: 2rem; max-width: 1650px;}
html, body, [class*="css"] {font-family: Inter, Arial, sans-serif;}
h1,h2,h3 {color:#0B3A82;}
a {color:#1E5AA8; text-decoration:none;}
a:hover {color:#D62828;}

.hero {
  display:flex; justify-content:space-between; align-items:flex-end;
  border-bottom:5px solid #D62828; padding:8px 2px 14px 2px; margin-bottom:10px;
}
.hero-title {font-size:2.15rem;font-weight:850;color:#0B3A82;letter-spacing:-.025em;}
.hero-sub {font-size:.98rem;color:#64748B;}
.hero-updated {text-align:right;color:#64748B;font-size:.78rem;}

.logo-strip {
  display:flex; align-items:center; justify-content:space-between; gap:20px;
  border:1px solid #D9E1EA; border-radius:12px; background:#fff;
  padding:10px 18px; margin:8px 0 14px 0;
}
.logo-cell {flex:1;text-align:center;min-width:105px;font-weight:800;color:#0B3A82;}
.logo-cell img {height:38px;max-width:145px;object-fit:contain;}

.kpi {
  border:1px solid #D9E1EA;border-radius:12px;background:#fff;
  padding:13px 15px 12px;min-height:88px;position:relative;
}
.kpi:before {
  content:"";position:absolute;left:0;right:0;top:0;height:5px;
  background:#0B3A82;border-radius:12px 12px 0 0;
}
.kpi.red:before {background:#D62828;}
.kpi-label {font-size:.80rem;color:#64748B;}
.kpi-value {font-size:1.75rem;font-weight:850;color:#0B3A82;margin-top:3px;}
.kpi.red .kpi-value {color:#D62828;}

.valuechain-title {font-size:.92rem;font-weight:800;color:#0B3A82;margin:13px 0 5px;}
div[role="radiogroup"] {display:flex;gap:5px;flex-wrap:wrap;}
div[role="radiogroup"] label {
  border:1px solid #D9E1EA;border-radius:9px;padding:5px 8px;background:#F7FAFE;
}
div[role="radiogroup"] label:has(input:checked) {
  background:#FDEEEE;border-color:#D62828;color:#A61B1B;font-weight:750;
}

.news-card {
  border:1px solid #D9E1EA;border-radius:12px;background:#fff;
  padding:13px 15px;margin:0 0 10px 0;
}
.news-card.priority {border-left:7px solid #D62828;}
.news-card.normal {border-left:7px solid #0B3A82;}
.news-title {font-size:1.02rem;font-weight:800;color:#1F2937;margin-top:5px;}
.news-meta {font-size:.8rem;color:#64748B;margin:3px 0 7px;}
.tag {
  display:inline-block;padding:3px 8px;border-radius:999px;margin:2px 4px 2px 0;
  font-size:.70rem;background:#EEF4FB;color:#0B3A82;
}
.tag-red {background:#FDEEEE;color:#A61B1B;}
.badge-green {
  display:inline-block;padding:3px 8px;border-radius:999px;
  background:#EAF7EF;color:#176B3A;font-size:.70rem;font-weight:750;
}
.implication {
  margin-top:8px;padding:9px 11px;border-radius:8px;
  background:#EEF4FB;color:#0B3A82;
}
.implication.priority {background:#FDEEEE;color:#A61B1B;}

section[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#F7FAFE 0%,#FFFFFF 100%);
  border-right:1px solid #D9E1EA;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {color:#0B3A82;}

.stButton>button,.stDownloadButton>button {
  border:1px solid #0B3A82;color:#0B3A82;border-radius:8px;
}
.stButton>button:hover,.stDownloadButton>button:hover {
  border-color:#D62828;color:#D62828;
}
</style>
""", unsafe_allow_html=True)

COMPETITORS = ["Kuehne+Nagel","DHL Global Forwarding","DSV","Sinotrans","Nippon Express"]

# Public brand assets for visual identification.
LOGOS = {
    "Kuehne+Nagel":"https://upload.wikimedia.org/wikipedia/commons/6/6b/Kuehne_%2B_Nagel_logo.svg",
    "DHL Global Forwarding":"https://upload.wikimedia.org/wikipedia/commons/a/ac/DHL_Logo.svg",
    "DSV":"https://upload.wikimedia.org/wikipedia/commons/7/7d/DSV_Logo.svg",
    "Nippon Express":"https://upload.wikimedia.org/wikipedia/commons/6/69/NX_logo.svg",
}

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

VERIFIED = [
    {
        "date":"2026-10-01","company":"Kuehne+Nagel","initiative":"Chennai Tech Centre",
        "technology":"AI / proprietary digital products","process":"Technology & product development",
        "stage":"Scaling capability",
        "evidence":"Kuehne+Nagel opened a new engineering centre to expand development and scaling of proprietary digital logistics solutions as demand for AI solutions grows.",
        "metric":"New global technology centre","source_type":"Official company news",
        "source":"Kuehne+Nagel Newsroom",
        "url":"https://newsroom.kuehne-nagel.com/kuehnenagel-opens-chennai-tech-centre-as-demand-for-digital-logistics-and-ai-solutions-grows/",
        "ceva":"Track internal engineering capacity as a competitive capability: ownership of AI products, speed from pilot to production and global scaling.",
        "priority":"Neutral",
        "value_chain":["Docs & compliance","Collection & consolidation","Air / ocean transport"],
    },
    {
        "date":"2026-09-24","company":"DHL Global Forwarding","initiative":"Logistics Trend Radar 8.0",
        "technology":"Agentic AI / AI analytics","process":"Planning, decision-making & execution",
        "stage":"Strategic direction",
        "evidence":"DHL identifies Agentic AI as a major logistics trend, moving AI from assistance toward systems capable of planning, coordinating and acting across workflows.",
        "metric":"Agentic AI elevated as a major logistics trend",
        "source_type":"Official DHL report/news","source":"DHL Group",
        "url":"https://group.dhl.com/en/media-relations/press-releases/2026/ai-takes-action-while-people-remain-at-the-center-of-logistics-finds-dhl-logistics-trend-radar.html",
        "ceva":"Separate simple copilots from autonomous agents in CEVA's roadmap and identify which forwarding activities can safely move from recommendation to execution.",
        "priority":"Priority",
        "value_chain":["Booking & pricing","Docs & compliance","Collection & consolidation","Customs clearance (origin)","Security & handling","Air / ocean transport","Customs clearance (dest.)","Decons. & delivery","Audit & settlement"],
    },
    {
        "date":"2026-09-17","company":"DHL Global Forwarding","initiative":"TradeNavigator",
        "technology":"Natural-language AI analytics","process":"Customs & trade compliance",
        "stage":"Launched",
        "evidence":"Customers can query customs declaration data in natural language and receive analytics on duty spend, tariff exposure, clearance performance and compliance trends.",
        "metric":"4,000+ customs experts • 30,000+ declarations/day",
        "source_type":"Official company press release","source":"DHL Group",
        "url":"https://group.dhl.com/en/media-relations/press-releases/2026/dhl-global-forwarding-launches-tradenavigator-tool.html",
        "ceva":"Customs data is becoming a customer-facing decision product. Benchmark conversational access to CEVA customs and trade data.",
        "priority":"Priority",
        "value_chain":["Customs clearance (origin)","Customs clearance (dest.)"],
    },
    {
        "date":"2026-09-10","company":"DHL Global Forwarding","initiative":"Alibaba.com / Accio integration",
        "technology":"Agentic AI / API integration","process":"Quotation, booking & shipment execution",
        "stage":"MoU / integration exploration",
        "evidence":"DHL Global Forwarding plans to connect quotation and booking capabilities with Alibaba.com's Accio agentic AI platform for SMEs.",
        "metric":"Forwarding quotation and booking embedded into an external AI-commerce environment",
        "source_type":"Official company press release","source":"DHL Group",
        "url":"https://group.dhl.com/en/media-relations/press-releases/2026/dhl-and-alibaba-com-partner-to-bring-ai-powered-logistics-capabilities-to-small-and-medium-sized-enterprises-worldwide.html",
        "ceva":"A direct commercial signal: freight procurement can move inside external AI agents. Track CEVA API readiness, instant-quote coverage and embedded-forwarding partnerships.",
        "priority":"Priority",
        "value_chain":["Booking & pricing"],
    },
    {
        "date":"2026-08-19","company":"Nippon Express","initiative":"BI LLM Chat in DCX",
        "technology":"Generative AI / LLM","process":"Customer analytics & decision support",
        "stage":"Launched",
        "evidence":"Nippon Express added an LLM chat capability to its DCX logistics web application so users can interact with logistics data and external information.",
        "metric":"Customer-facing conversational logistics analytics",
        "source_type":"Official company press release","source":"Nippon Express Holdings",
        "url":"https://www.nipponexpress-holdings.com/ja/press/768",
        "ceva":"Benchmark customer-facing GenAI rather than only internal productivity tools: conversational access to shipment, inventory and market intelligence.",
        "priority":"Neutral",
        "value_chain":["Booking & pricing","Air / ocean transport","Audit & settlement"],
    },
    {
        "date":"2026-07-23","company":"Kuehne+Nagel","initiative":"Accelerated AI deployment",
        "technology":"AI agents / operational AI","process":"Enterprise operations",
        "stage":"Scaling",
        "evidence":"Kuehne+Nagel states that it is accelerating AI deployment across the organisation, including process optimisation and integration of AI agents.",
        "metric":"AI explicitly tied to measurable efficiency gains",
        "source_type":"Official Q2 results","source":"Kuehne+Nagel",
        "url":"https://newsroom.kuehne-nagel.com/kuehnenagel-reports-strong-second-quarter-2026/",
        "ceva":"Track AI with process and P&L-linked productivity measures rather than treating deployments as isolated innovation pilots.",
        "priority":"Priority",
        "value_chain":["Booking & pricing","Docs & compliance","Collection & consolidation","Customs clearance (origin)","Security & handling","Air / ocean transport","Customs clearance (dest.)","Decons. & delivery","Audit & settlement"],
    },
    {
        "date":"2026-07-16","company":"Kuehne+Nagel","initiative":"KN SwiftLOG cloud-native rollout",
        "technology":"Agentic AI-enabled WMS","process":"Contract logistics / warehousing",
        "stage":"Global rollout",
        "evidence":"KN SwiftLOG is being evolved into a cloud-native, agentic-AI-enabled platform based on Blue Yonder technology.",
        "metric":"1,000+ sites • nearly 100 countries",
        "source_type":"Official company press release","source":"Kuehne+Nagel",
        "url":"https://newsroom.kuehne-nagel.com/kuehnenagel-rolls-out-cloud-native-contract-logistics-solution-across-over-1000-sites-globally/",
        "ceva":"A common digital backbone enables AI to scale consistently. Compare CEVA platform standardisation, interoperability and deployment speed.",
        "priority":"Neutral",
        "value_chain":["Collection & consolidation","Security & handling","Decons. & delivery"],
    },
    {
        "date":"2026-05-14","company":"Nippon Express","initiative":"DCX AI shipment forecasting upgrade",
        "technology":"Predictive AI","process":"Inventory & shipment forecasting",
        "stage":"Enhanced production service",
        "evidence":"Nippon Express upgraded AI shipment forecasting in DCX Business Insight, integrating shipment forecasts with inventory and order analytics.",
        "metric":"~1–2 hours/item → ~5 minutes • forecasts up to 6 months",
        "source_type":"Official company press release","source":"Nippon Express Holdings",
        "url":"https://www.nipponexpress-holdings.com/ja/news/press/2026/20260514-1.html",
        "ceva":"Benchmark forecast latency, horizon, accuracy and—most importantly—the link from prediction to operational decisions.",
        "priority":"Neutral",
        "value_chain":["Air / ocean transport"],
    },
    {
        "date":"2026-05-13","company":"DSV","initiative":"Autonomous freight operations in Texas",
        "technology":"Autonomous driving","process":"Road linehaul",
        "stage":"Commercial operation",
        "evidence":"DSV and Volvo Autonomous Solutions began autonomous freight operations between Dallas and Houston using Volvo VNL Autonomous trucks.",
        "metric":"Commercial autonomous freight lane",
        "source_type":"Official company press release","source":"DSV",
        "url":"https://www.dsv.com/en/about-dsv/press/news/volvo-autonomous-solutions-and-dsv-announce-autonomous-freight-2628152",
        "ceva":"A physical-automation signal relevant to CEVA's broader transport network and autonomous capacity strategy.",
        "priority":"Neutral",
        "value_chain":["Decons. & delivery"],
    },
    {
        "date":"2026-05-12","company":"DSV","initiative":"Leverage to Lead 2030",
        "technology":"AI & technology","process":"Enterprise productivity / network optimisation",
        "stage":"Strategic priority",
        "evidence":"DSV's 2030 strategy explicitly targets productivity improvement from artificial intelligence and technology after the Schenker integration.",
        "metric":"AI embedded in 2030 strategic priorities",
        "source_type":"Investor / regulatory announcement","source":"DSV Investor Relations",
        "url":"https://investor.dsv.com/node/25211",
        "ceva":"Watch whether the Schenker integration gives DSV larger shared datasets, systems consolidation and faster AI scaling.",
        "priority":"Priority",
        "value_chain":["Booking & pricing","Docs & compliance","Collection & consolidation","Customs clearance (origin)","Security & handling","Air / ocean transport","Customs clearance (dest.)","Decons. & delivery","Audit & settlement"],
    },
    {
        "date":"2026-03-30","company":"Sinotrans","initiative":"AI + Logistics operating model",
        "technology":"AI / autonomous driving / robotic automation","process":"End-to-end logistics operations",
        "stage":"Scaled multi-use-case deployment",
        "evidence":"Sinotrans' annual reporting describes AI + Logistics as a core smart-logistics model spanning smart ports, warehouses, customer service and autonomous driving.",
        "metric":"236 valid patents • 428 software copyrights • >3.5m km L4 autonomous-driving mileage",
        "source_type":"Annual report / HKEX filing","source":"Sinotrans / HKEX",
        "url":"https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0330/2026033002104.pdf",
        "ceva":"Benchmark the breadth of CEVA's AI portfolio, IP ownership and scaled deployment metrics—not only the number of pilots.",
        "priority":"Priority",
        "value_chain":["Booking & pricing","Docs & compliance","Collection & consolidation","Customs clearance (origin)","Security & handling","Air / ocean transport","Customs clearance (dest.)","Decons. & delivery","Audit & settlement"],
    },
    {
        "date":"2026-01-16","company":"Nippon Express","initiative":"Digital showroom",
        "technology":"Digital twin","process":"Solution design / sales / operational improvement",
        "stage":"Launched",
        "evidence":"Nippon Express introduced a virtual logistics showroom using digital-twin technology for solution co-creation, sales proposals and operational improvement.",
        "metric":"Digital twin applied to customer solutioning",
        "source_type":"Official company press release","source":"Nippon Express Holdings",
        "url":"https://www.nipponexpress-holdings.com/ja/news/press/2026/20260116-1.html",
        "ceva":"Digital twins can make pre-sales modelling and warehouse/flow redesign more tangible and faster.",
        "priority":"Neutral",
        "value_chain":["Collection & consolidation","Security & handling","Decons. & delivery"],
    },
]

OFFICIAL_SEARCHES = {
    "Kuehne+Nagel": 'site:newsroom.kuehne-nagel.com (AI OR "artificial intelligence" OR agentic OR automation OR digital)',
    "DHL Global Forwarding": 'site:group.dhl.com "DHL Global Forwarding" (AI OR "artificial intelligence" OR agentic OR automation)',
    "DSV": 'site:dsv.com DSV (AI OR "artificial intelligence" OR autonomous OR technology)',
    "Nippon Express": 'site:nipponexpress-holdings.com (AI OR LLM OR "digital twin" OR automation)',
    "Sinotrans": 'Sinotrans ("artificial intelligence" OR AI OR autonomous OR "smart logistics")',
}

def rss(query):
    return "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en&gl=US&ceid=US:en"

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_official(query, company):
    feed = feedparser.parse(rss(query))
    rows = []
    for entry in feed.entries[:30]:
        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if getattr(entry, "published_parsed", None) else datetime.now(timezone.utc)
        publisher = ""
        if getattr(entry, "source", None):
            try:
                publisher = entry.source.get("title","")
            except Exception:
                pass
        rows.append({
            "date": dt,
            "company": company,
            "title": entry.get("title","").strip(),
            "url": entry.get("link",""),
            "publisher": publisher or "Official-domain search",
        })
    return rows

def map_value_chain(title):
    t = (title or "").lower()
    steps = []
    def add(step):
        if step not in steps:
            steps.append(step)
    if any(k in t for k in ["quote","quotation","pricing","rate","booking","procurement","commercial"]):
        add("Booking & pricing")
    if any(k in t for k in ["document","compliance","paperwork","invoice"]):
        add("Docs & compliance")
    if any(k in t for k in ["warehouse","wms","consolidation","inventory","fulfillment","fulfilment"]):
        add("Collection & consolidation")
    if any(k in t for k in ["customs","tariff","duty","clearance","brokerage"]):
        add("Customs clearance (origin)")
        add("Customs clearance (dest.)")
    if any(k in t for k in ["security","inspection","screening","handling"]):
        add("Security & handling")
    if any(k in t for k in ["air freight","ocean freight","sea freight","capacity","routing","route","eta","shipment","network"]):
        add("Air / ocean transport")
    if any(k in t for k in ["delivery","trucking","truck","last mile","distribution"]):
        add("Decons. & delivery")
    if any(k in t for k in ["audit","settlement","billing","payment","reconciliation"]):
        add("Audit & settlement")
    if any(k in t for k in ["agentic ai","ai strategy","artificial intelligence strategy","digital transformation"]):
        return VALUE_CHAIN_STEPS[1:]
    return steps or ["Air / ocean transport"]

@st.cache_data(ttl=86400, show_spinner=False)
def live_official_news():
    rows = []
    for company, query in OFFICIAL_SEARCHES.items():
        rows.extend(fetch_official(query, company))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["value_chain"] = df["title"].apply(map_value_chain)
    df["age_days"] = (pd.Timestamp.now(tz="UTC") - df["date"]).dt.total_seconds() / 86400
    return df.sort_values("date", ascending=False).drop_duplicates("title")

# Header
st.markdown(
    f"""
    <div class="hero">
      <div>
        <div class="hero-title">CEVA AI Competitor Intelligence</div>
        <div class="hero-sub">Real-time updates. Verified sources. Actionable insights.</div>
      </div>
      <div class="hero-updated">Last checked<br><b>{datetime.now().strftime("%d %b %Y • %H:%M")}</b></div>
    </div>
    """,
    unsafe_allow_html=True,
)

logo_html = '<div class="logo-strip">'
for company in COMPETITORS:
    if company in LOGOS:
        logo_html += f'<div class="logo-cell"><img src="{LOGOS[company]}" alt="{company}"></div>'
    else:
        logo_html += f'<div class="logo-cell">{company}</div>'
logo_html += "</div>"
st.markdown(logo_html, unsafe_allow_html=True)

verified = pd.DataFrame(VERIFIED)
verified["date"] = pd.to_datetime(verified["date"])
today = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
verified["age_days"] = (today - verified["date"]).dt.days

with st.sidebar:
    st.markdown("## Filters")
    search = st.text_input("Search", placeholder="Initiatives, technologies, keywords…")
    selected_comp = st.multiselect("Competitor", COMPETITORS, default=COMPETITORS)
    selected_tech = st.multiselect("Technology", sorted(verified["technology"].unique().tolist()))
    selected_stage = st.multiselect("Deployment stage", sorted(verified["stage"].unique().tolist()))
    priority = st.selectbox("Priority", ["All","Priority","Neutral"])
    period = st.radio("Date range", ["Last 7 days","Last 30 days","Last 90 days","Last 12 months","All 2026"], index=1)
    if st.button("Refresh sources now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Official-source discovery refreshes automatically every 24 hours.")

st.markdown('<div class="valuechain-title">FREIGHT VALUE CHAIN — click a step to filter the news and insights</div>', unsafe_allow_html=True)
selected_step = st.radio("Freight value chain", VALUE_CHAIN_STEPS, horizontal=True, label_visibility="collapsed")

days_map = {"Last 7 days":7,"Last 30 days":30,"Last 90 days":90,"Last 12 months":365,"All 2026":9999}
max_days = days_map[period]

view = verified[(verified["company"].isin(selected_comp)) & (verified["age_days"] <= max_days)].copy()
if selected_step != "All steps":
    view = view[view["value_chain"].apply(lambda x: selected_step in x)]
if selected_tech:
    view = view[view["technology"].isin(selected_tech)]
if selected_stage:
    view = view[view["stage"].isin(selected_stage)]
if priority != "All":
    view = view[view["priority"] == priority]
if search:
    view = view[
        view["initiative"].str.contains(search, case=False, na=False)
        | view["technology"].str.contains(search, case=False, na=False)
        | view["evidence"].str.contains(search, case=False, na=False)
        | view["company"].str.contains(search, case=False, na=False)
    ]
view = view.sort_values("date", ascending=False)

recent30 = verified[verified["age_days"] <= 30]
active_stages = {
    "Launched","Scaling","Scaling capability","Global rollout",
    "Enhanced production service","Commercial operation","Scaled multi-use-case deployment",
}
active_share = verified["stage"].isin(active_stages).mean()

kpi_cols = st.columns(5)
kpi_data = [
    ("Verified AI initiatives", len(verified), False),
    ("Competitors monitored", verified["company"].nunique(), False),
    ("In deployment or live", f"{active_share:.0%}", False),
    ("Freight value-chain steps", 9, False),
    ("New in last 30 days", len(recent30), True),
]
for col, (label, value, red_flag) in zip(kpi_cols, kpi_data):
    cls = "kpi red" if red_flag else "kpi"
    col.markdown(f'<div class="{cls}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)

st.markdown("")
tab1, tab2, tab3 = st.tabs(["AI Initiatives & News","Live official-source watcher","Competitor analysis"])

with tab1:
    step_label = selected_step if selected_step != "All steps" else "all value-chain steps"
    st.markdown(f"### Verified initiatives — {step_label}")
    st.caption(f"{len(view)} result(s) • {period} • most recent first")
    if view.empty:
        st.info("No verified initiatives match the current filters. Expand the date range or choose another step.")
    else:
        for _, row in view.iterrows():
            cls = "priority" if row["priority"] == "Priority" else "normal"
            imp_cls = "priority" if row["priority"] == "Priority" else ""
            fresh = '<span class="tag tag-red">NEW</span>' if row["age_days"] <= 30 else ""
            logo = LOGOS.get(row["company"])
            company_html = (
                f'<img src="{logo}" style="height:19px;max-width:105px;object-fit:contain;vertical-align:middle;margin-right:8px;">'
                if logo else f"<b>{row['company']}</b>"
            )
            chain_tags = "".join(f'<span class="tag">{s}</span>' for s in row["value_chain"])
            st.markdown(
                f"""
                <div class="news-card {cls}">
                  <div>{fresh}{company_html}<span class="tag">{row['stage']}</span></div>
                  <div class="news-title">{row['initiative']}</div>
                  <div class="news-meta">{row['date'].strftime('%d %b %Y')} • {row['source']} • {row['source_type']}</div>
                  <div>{row['evidence']}</div>
                  <div style="margin-top:7px;"><b style="color:{BLUE};">Metric:</b> {row['metric']}</div>
                  <div style="margin-top:7px;">{chain_tags}</div>
                  <div class="implication {imp_cls}"><b>CEVA implication:</b> {row['ceva']}</div>
                  <div style="margin-top:8px;"><a href="{row['url']}" target="_blank"><b>Open official source ↗</b></a></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

with tab2:
    st.markdown("### Live official-source watcher")
    st.caption("Fresh discovery layer. Important items should be validated against the original linked source before executive use.")
    with st.spinner("Checking official-source feeds…"):
        live = live_official_news()
    if live.empty:
        st.warning("Live feeds are temporarily unavailable. Verified intelligence remains available in the first tab.")
    else:
        live = live[(live["age_days"] <= max_days) & (live["company"].isin(selected_comp))]
        if selected_step != "All steps":
            live = live[live["value_chain"].apply(lambda x: selected_step in x)]
        if search:
            live = live[live["title"].str.contains(search, case=False, na=False)]
        st.caption(f"{len(live)} headline(s) match the current filters.")
        for _, row in live.head(50).iterrows():
            steps = " • ".join(row["value_chain"])
            st.markdown(
                f"""
                <div class="news-card normal">
                  <span class="badge-green">LIVE SOURCE WATCH</span>
                  <div class="news-title"><a href="{row['url']}" target="_blank">{row['title']}</a></div>
                  <div class="news-meta">{row['date'].strftime('%d %b %Y')} • {row['company']} • {row['publisher']}</div>
                  <div style="font-size:.8rem;color:{MUTED};">Mapped value chain: {steps}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

with tab3:
    st.markdown("### Competitor signals")
    comp = view.groupby("company").agg(
        initiatives=("initiative","count"),
        priority=("priority", lambda x: int((x == "Priority").sum())),
        technologies=("technology","nunique"),
    ).reset_index()
    if comp.empty:
        st.info("No data for the current filters.")
    else:
        chart = alt.Chart(comp).mark_bar(color=BLUE).encode(
            x=alt.X("initiatives:Q", title="Verified initiatives"),
            y=alt.Y("company:N", sort="-x", title=""),
            tooltip=["company","initiatives","priority","technologies"],
        ).properties(height=250)
        st.altair_chart(chart, use_container_width=True)

        tech = view.groupby("technology").size().reset_index(name="initiatives").sort_values("initiatives", ascending=False)
        chart2 = alt.Chart(tech).mark_bar(color=RED).encode(
            x=alt.X("initiatives:Q", title="Initiatives"),
            y=alt.Y("technology:N", sort="-x", title=""),
            tooltip=["technology","initiatives"],
        ).properties(height=300)
        st.altair_chart(chart2, use_container_width=True)

        lead = comp.sort_values(["initiatives","priority"], ascending=False).iloc[0]["company"]
        st.markdown("#### Strategic readout")
        st.write(f"**{lead}** has the highest number of verified initiatives in the current filtered view.")
        if selected_step != "All steps":
            st.write(f"This comparison is filtered specifically to **{selected_step}**.")
        st.write("Prioritise moves that alter forwarding economics, customer experience, speed of execution or control over data.")

st.divider()
st.caption("Primary sources are prioritised. The live watcher is a discovery layer and should be validated against the underlying source.")
