import streamlit as st
from html import escape

from config import APP_TITLE, TAGLINE
from core.db import init_db, list_reports, scan_count
from modules import dashboard, report, scanner, segregation

st.set_page_config(page_title=APP_TITLE, page_icon="♻️", layout="wide")
init_db()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
html,body,[class*="css"] {font-family:'DM Sans',sans-serif;color-scheme:light}
.stApp,[data-testid="stAppViewContainer"] {background:linear-gradient(145deg,#f3f8f3,#fbfcfa 54%,#eef6f0);color:#163a2b}
[data-testid="stHeader"] {background:rgba(246,250,246,.9)}
.stApp h1,.stApp h2,.stApp h3,.stApp h4 {color:#163a2b!important;font-family:'Manrope',sans-serif;letter-spacing:-.025em}
.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stWidgetLabel"],.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stRadio"] label,.stApp [data-testid="stCheckbox"] label,.stApp [data-testid="stToggle"] label,section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] label {color:#294d3b!important}
section[data-testid="stSidebar"] {background:#edf5ee;border-right:1px solid #dce9de}
input,textarea,[data-baseweb="select"]>div {background:#fff!important;color:#173c2b!important;border-radius:10px!important}
[data-baseweb="select"] *,[data-testid="stFileUploader"] section *, .stApp [data-testid="stNumberInput"] button {color:#173c2b!important}
.hero {padding:2.1rem 2.35rem;border-radius:24px;background:radial-gradient(circle at 88% 12%,#45a66f 0,transparent 28%),linear-gradient(115deg,#123d2b,#1b6844);color:#fff;margin-bottom:1rem;box-shadow:0 18px 45px #123d2b1c}
.hero h1 {color:#fff!important;font-size:2.55rem;margin:0}.hero p {color:#d8eee0!important;font-size:1.05rem;margin:.45rem 0 0}
.eyebrow {text-transform:uppercase;letter-spacing:.14em;font-size:.72rem;font-weight:700;color:#c1e2ce;margin-bottom:.6rem}
.section-kicker {text-transform:uppercase;letter-spacing:.12em;font-size:.72rem;font-weight:700;color:#56806a;margin-bottom:.45rem}
.panel,.action-card {background:#fff;border:1px solid #e1ebe2;border-radius:18px;padding:1.1rem 1.2rem;box-shadow:0 8px 26px #183d2810}
.action-card {min-height:126px}.action-card h3 {font-size:1rem;margin:.3rem 0}.action-card p,.panel p {color:#526b5b!important}.action-icon {font-size:1.55rem}
.signal {border-radius:16px;padding:1.2rem 1.3rem;background:#e9f4ec;border:1px solid #d5e8d9}.signal strong {color:#17613a;font-size:1.05rem}.signal p {margin:.35rem 0 0;color:#486453!important}
.muted {color:#63766b;font-size:.9rem}
.wv-table-wrap {overflow-x:auto;background:#fff;border:1px solid #e0eae1;border-radius:14px;box-shadow:0 6px 20px #183d2808}
.wv-table {width:100%;border-collapse:collapse;font-size:.9rem}.wv-table th {text-align:left;padding:12px 14px;background:#edf5ee;color:#365c45;font-size:.76rem;text-transform:uppercase;letter-spacing:.06em;white-space:nowrap}.wv-table td {padding:12px 14px;border-top:1px solid #edf2ed;color:#294d3b}.wv-table tr:hover td {background:#f8fbf8}
.wv-badge {display:inline-block;padding:4px 9px;border-radius:99px;font-size:.78rem;font-weight:700;white-space:nowrap}.wv-badge.high,.wv-badge.reported {color:#a93830;background:#ffedea}.wv-badge.medium,.wv-badge.in-progress {color:#8a6212;background:#fff5dc}.wv-badge.low,.wv-badge.resolved {color:#237244;background:#e8f5eb}
div[data-testid="stMetric"] {background:#fff;border:1px solid #e1ebe2;padding:14px 16px;border-radius:15px;box-shadow:0 5px 18px #183d2808}
div[data-testid="stMetricLabel"] p {color:#5a7563!important;font-size:.83rem}div[data-testid="stMetricValue"] {color:#173c2b!important}
</style>
""", unsafe_allow_html=True)

PAGES = ["Home", "AI Waste Scanner", "Smart Segregation", "Report Waste", "Impact Dashboard"]

def navigate(target):
    st.session_state.navigation = target

with st.sidebar:
    st.markdown("## ♻️ WasteVision")
    st.caption("FIELD OPERATIONS · WASTE INTELLIGENCE")
    page = st.radio("Workspace", PAGES, key="navigation", label_visibility="collapsed")
    st.divider()
    st.markdown("**DEMO CONTROLS**")
    demo_mode = st.toggle("Use sample detections", value=False, help="Illustrative detections are never model predictions.")
    threshold = st.slider("Model confidence", 0.05, 0.80, 0.20, 0.05, help="Lower values include less certain candidates.")
    st.caption("Model results depend on the weights and photo quality.")

if page == "Home":
    reports = list_reports()
    open_reports = [row for row in reports if row["status"] != "Resolved"]
    urgent = sorted([row for row in open_reports if row["priority"] == "High"],key=lambda row:int(row.get("priority_score",0)),reverse=True)
    st.markdown('<div class="hero"><div class="eyebrow">COMMUNITY CLEANUP · OPERATIONS DESK</div><h1>Turn waste signals into action.</h1><p>Scan what you see. Sort it correctly. Route cleanup where it matters.</p></div>',unsafe_allow_html=True)
    metrics = st.columns(4)
    metrics[0].metric("Open cleanup reports",len(open_reports))
    metrics[1].metric("High priority",len(urgent))
    metrics[2].metric("Issues resolved",sum(row["status"]=="Resolved" for row in reports))
    metrics[3].metric("Scans logged",scan_count())
    st.markdown("<div class='section-kicker'>CHOOSE YOUR NEXT MOVE</div>",unsafe_allow_html=True)
    columns=st.columns(4)
    actions=[("📷","Scan a waste photo","Identify known waste objects and get disposal steps.","AI Waste Scanner"),("📍","Report a hotspot","Score cleanup urgency and put a location in the queue.","Report Waste"),("🧭","Find a sorting route","Type an item description for disposal guidance.","Smart Segregation"),("📊","Review community impact","See the response queue, trends, and hotspot map.","Impact Dashboard")]
    for col,(icon,title,description,target) in zip(columns,actions):
        with col:
            st.markdown(f'<div class="action-card"><div class="action-icon">{icon}</div><h3>{title}</h3><p>{description}</p></div>',unsafe_allow_html=True)
            st.button(f"Open {title} →",key=f"go_{target}",use_container_width=True,on_click=navigate,args=(target,))
    left,right=st.columns([1.45,1])
    with left:
        st.markdown("<div class='section-kicker'>RESPONSE SIGNAL</div>",unsafe_allow_html=True)
        if urgent:
            next_row=urgent[0]
            score=next_row.get("priority_score",0)
            score_text=f" · Estimate {score}/26" if score else ""
            st.markdown(f'<div class="signal"><strong>🚨 Start with {escape(next_row["location"])}</strong><p>{next_row["priority"]} priority{score_text} · {next_row["item_count"]} detected items · {next_row["status"]}</p></div>',unsafe_allow_html=True)
        elif open_reports:
            next_row=open_reports[0]
            st.markdown(f'<div class="signal"><strong>Next report to review: {escape(next_row["location"])}</strong><p>{next_row["priority"]} priority · {next_row["item_count"]} items · {next_row["status"]}</p></div>',unsafe_allow_html=True)
        else:
            st.markdown('<div class="signal"><strong>All clear</strong><p>No open reports are waiting. Run a scan or log a new community observation.</p></div>',unsafe_allow_html=True)
    with right:
        resolved=sum(row["status"]=="Resolved" for row in reports)
        st.markdown(f'<div class="panel"><div class="section-kicker">COMMUNITY PULSE</div><h3>{resolved} of {len(reports)} reports resolved</h3><p>Priority scores are triage estimates, not official hazard assessments.</p></div>',unsafe_allow_html=True)
    if demo_mode:
        st.info("Sample detections are enabled. Results created in this mode are labeled demo data.")
elif page == "AI Waste Scanner":
    scanner.render(demo_mode,threshold)
elif page == "Smart Segregation":
    segregation.render()
elif page == "Report Waste":
    report.render(demo_mode,threshold)
else:
    dashboard.render()

st.markdown("<div class='muted' style='text-align:center;padding:1.5rem 0'>♻️ WasteVision AI · Detections come from the model; accuracy depends on the model and image.</div>",unsafe_allow_html=True)
