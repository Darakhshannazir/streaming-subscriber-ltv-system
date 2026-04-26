import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(
    page_title="Streaming Subscriber LTV & Retention Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

API     = "https://darakhshannazir-netflix-streaming-subscriber-ltv-api.hf.space"
RED     = "#E50914"
RED_DIM = "#B20710"
DARK    = "#141414"
DGRAY   = "#2D2D2D"
MGRAY   = "#564D4D"
LGRAY   = "#AAAAAA"
WHITE   = "#FFFFFF"

# ── Netflix curtain ───────────────────────────────────────────────
if 'curtain_shown' not in st.session_state:
    st.session_state.curtain_shown = False

if not st.session_state.curtain_shown:
    ph = st.empty()
    ph.markdown(f"""
    <style>
    #co{{position:fixed;inset:0;z-index:9999;display:flex;
         align-items:center;justify-content:center;overflow:hidden}}
    .cl,.cr{{position:absolute;top:0;width:50%;height:100%;background:{DARK}}}
    .cl{{left:0;transform-origin:left;
         animation:co 1.8s cubic-bezier(.77,0,.18,1) .8s forwards}}
    .cr{{right:0;transform-origin:right;
         animation:co 1.8s cubic-bezier(.77,0,.18,1) .8s forwards}}
    @keyframes co{{0%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}}}
    .clog{{position:relative;z-index:10000;text-align:center;
           animation:lf 2.6s ease forwards}}
    @keyframes lf{{
        0%{{opacity:0;transform:scale(.8)}}
        30%{{opacity:1;transform:scale(1.05)}}
        70%{{opacity:1;transform:scale(1)}}
        100%{{opacity:0}}}}
    .cn{{font-size:120px;font-weight:900;color:{RED};
         font-family:Georgia,serif;letter-spacing:-4px;line-height:1;
         text-shadow:0 0 60px rgba(229,9,20,.8),0 0 120px rgba(229,9,20,.4)}}
    .ct{{font-size:18px;font-weight:500;color:{WHITE};letter-spacing:3px;
         text-transform:uppercase;margin-top:16px;font-family:Inter,sans-serif}}
    </style>
    <div id="co">
      <div class="cl"></div><div class="cr"></div>
      <div class="clog">
        <div class="cn">N</div>
        <div class="ct">Subscriber Intelligence</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(2.8)
    ph.empty()
    st.session_state.curtain_shown = True

# ── CSS ───────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif}}

[data-testid="stAppViewContainer"]{{
    background:linear-gradient(-45deg,#f9f9f9,#fff5f5,#ffffff,#fdf0f0);
    background-size:400% 400%;animation:bgShift 14s ease infinite}}
@keyframes bgShift{{
    0%{{background-position:0% 50%}}
    50%{{background-position:100% 50%}}
    100%{{background-position:0% 50%}}}}

[data-testid="stSidebar"]{{
    background:{DARK}!important;border-right:2px solid {RED}}}
[data-testid="stSidebar"] *{{color:{WHITE}!important}}
[data-testid="stSidebar"] .stRadio label{{
    font-size:15px!important;font-weight:500!important;
    padding:12px 0!important;letter-spacing:.03em;transition:color .2s}}
[data-testid="stSidebar"] .stRadio label:hover{{color:{RED}!important}}

[data-testid="metric-container"]{{
    background:{WHITE};border:1px solid #EBEBEB;
    border-top:3px solid {RED};border-radius:8px;
    padding:14px!important;box-shadow:0 2px 12px rgba(0,0,0,.06);
    transition:transform .2s,box-shadow .2s}}
[data-testid="metric-container"]:hover{{
    transform:translateY(-2px);
    box-shadow:0 6px 20px rgba(229,9,20,.1)}}
[data-testid="metric-container"] label{{
    font-size:11px!important;color:{MGRAY}!important;
    text-transform:uppercase;letter-spacing:.07em;font-weight:500!important}}
[data-testid="metric-container"] [data-testid="stMetricValue"]{{
    font-size:26px!important;font-weight:700!important;color:{DARK}!important}}

h1,h2,h3{{color:{DARK}!important}}
h1{{border-left:4px solid {RED};padding-left:14px;font-size:24px!important}}
h3{{font-size:16px!important;margin-bottom:4px!important}}

.fn{{font-size:14px;color:#555;line-height:1.8;padding:10px 16px;
     border-left:3px solid {RED};background:#FFF8F8;
     border-radius:0 6px 6px 0;margin-top:8px}}
.ins{{font-size:14px;color:{DARK};line-height:1.7;padding:10px 16px;
      border-left:3px solid #CCCCCC;background:#F5F5F5;
      border-radius:0 6px 6px 0;margin:8px 0}}
.sec-hdr{{margin:18px 0 6px;padding-bottom:8px;border-bottom:1px solid #EBEBEB}}
.sec-hdr h3{{margin:0!important}}
.sec-hdr small{{color:{LGRAY};font-size:13px;display:block;margin-top:3px}}

.ph{{background:{DARK};border-radius:12px;margin-bottom:0;
     overflow:hidden;display:flex;gap:0;min-height:120px}}
.ph-left{{flex:1;padding:24px 28px 20px;position:relative;z-index:1}}
.ph-right{{width:320px;flex-shrink:0;position:relative;
           overflow:hidden;background:{DARK}}}
.browse-track{{
    display:flex;gap:4px;padding:4px;height:100%;
    animation:browseScroll 25s linear infinite}}
.browse-track:hover{{animation-play-state:paused}}
@keyframes browseScroll{{
    0%{{transform:translateX(0)}}
    100%{{transform:translateX(-50%)}}}}
.mc{{flex-shrink:0;width:110px;border-radius:4px;overflow:hidden;
     position:relative;transition:transform .3s;cursor:pointer}}
.mc:hover{{transform:scale(1.12);z-index:10}}
.mc-img{{width:100%;height:100%;display:flex;flex-direction:column;
         justify-content:flex-end;padding:6px 4px}}
.mc-t{{font-size:8.5px;font-weight:700;color:{WHITE};line-height:1.2;
       text-shadow:0 1px 4px rgba(0,0,0,.9)}}
.mc-g{{font-size:7px;color:rgba(255,255,255,.65);margin-top:1px}}
.ph-overlay{{position:absolute;inset:0;
             background:linear-gradient(90deg,{DARK} 0%,
             rgba(20,20,20,.2) 55%,transparent 100%);
             pointer-events:none;z-index:5}}
.red-orb{{position:absolute;bottom:-20px;right:-20px;
          width:100px;height:100px;
          background:radial-gradient(circle,rgba(229,9,20,.35),
          transparent 65%);border-radius:50%;
          animation:orbPulse 3s ease-in-out infinite;z-index:4}}
@keyframes orbPulse{{
    0%,100%{{transform:scale(1);opacity:.5}}
    50%{{transform:scale(1.3);opacity:1}}}}
.ph h2{{color:{WHITE}!important;border:none;padding:0;margin:0;font-size:22px}}
.ph p{{color:#CCC;margin:8px 0 0;font-size:14px;line-height:1.65;max-width:600px}}
.ph-tag{{display:inline-block;background:{RED};color:{WHITE};
         font-size:10px;font-weight:600;padding:3px 10px;
         border-radius:20px;margin-top:12px;letter-spacing:.06em;
         text-transform:uppercase}}
.div{{border:none;border-top:1px solid #EBEBEB;margin:20px 0}}
.plan-card{{background:{WHITE};border:1px solid #EBEBEB;
            border-left:4px solid {RED};border-radius:0 8px 8px 0;
            padding:12px 16px;margin-bottom:10px}}
.biz-card{{background:{WHITE};border:1px solid #EBEBEB;
           border-radius:10px;padding:14px 16px;margin-bottom:10px}}
.biz-tag{{display:inline-block;font-size:10px;font-weight:600;
          padding:2px 8px;border-radius:20px;margin-bottom:8px;
          text-transform:uppercase;letter-spacing:.06em}}
@keyframes tickerScroll{{
    0%{{transform:translateX(0)}}100%{{transform:translateX(-50%)}}}}
@keyframes glow{{
    0%,100%{{text-shadow:0 0 20px rgba(229,9,20,.4)}}
    50%{{text-shadow:0 0 50px rgba(229,9,20,1),
         0 0 80px rgba(229,9,20,.5)}}}}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────
def fetch(endpoint, params=""):
    try:
        r = requests.get(
            f"{API}/{endpoint}{params}", timeout=60)
        return endpoint, r.json()
    except:
        return endpoint, {}

@st.cache_data(ttl=300)
def load_all_page1():
    endpoints = [
        ("segments",""),("winback","?top_n=50"),
        ("funnel",""),("cohorts",""),
        ("content-retention",""),("km-curves",""),
        ("feature-importance","")
    ]
    results = {}
    with ThreadPoolExecutor(max_workers=7) as ex:
        futures = {ex.submit(fetch,ep,p):ep for ep,p in endpoints}
        for f in as_completed(futures):
            ep, data = f.result()
            results[ep] = data
    return results

@st.cache_data(ttl=300)
def load_winback():
    try:
        return requests.get(
            f"{API}/winback?top_n=50", timeout=60).json()
    except:
        return []

def post_score(payload):
    for attempt in range(3):
        try:
            r = requests.post(
                f"{API}/score", json=payload, timeout=60)
            return r.json()
        except requests.exceptions.Timeout:
            if attempt < 2:
                st.toast(f"API waking up, retry {attempt+1}/3...")
                time.sleep(8)
    st.warning(
        "API timed out. Open the health URL in browser to wake it, "
        "then try again.")
    return None

def chart(fig, height=300):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=12, color=DARK),
        margin=dict(l=10,r=10,t=36,b=10),
        xaxis=dict(showgrid=False, zeroline=False,
                   linecolor="#EBEBEB"),
        yaxis=dict(showgrid=True, gridcolor="#F2F2F2",
                   zeroline=False),
        title_font=dict(size=13, color=DARK)
    )
    return fig

def fn(text):
    st.markdown(f'<div class="fn">{text}</div>',
                unsafe_allow_html=True)

def ins(text):
    st.markdown(f'<div class="ins">{text}</div>',
                unsafe_allow_html=True)

def sec(title, subtitle=""):
    sub = f"<small>{subtitle}</small>" if subtitle else ""
    st.markdown(
        f'<div class="sec-hdr"><h3>{title}</h3>{sub}</div>',
        unsafe_allow_html=True)

def make_movie_cards():
    movies = [
        ("Midnight Protocol","Thriller",
         f"linear-gradient(160deg,#3a0000,#1a0808,{DARK})"),
        ("Echoes","Sci-Fi",
         f"linear-gradient(160deg,#000833,#080818,{DARK})"),
        ("The Inheritance","Drama",
         f"linear-gradient(160deg,#1a0020,#0f000f,{DARK})"),
        ("Cipher","Crime",
         f"linear-gradient(160deg,#001a08,#000f05,{DARK})"),
        ("Wild Meridian","Doc",
         f"linear-gradient(160deg,#1a1200,#0f0a00,{DARK})"),
        ("Flash Point","Action",
         f"linear-gradient(160deg,#2a0500,#1a0000,{DARK})"),
        ("Dark Waters","Mystery",
         f"linear-gradient(160deg,#00081a,#00050f,{DARK})"),
        ("The Signal","Thriller",
         f"linear-gradient(160deg,#1a0a2a,#0f0018,{DARK})"),
        ("Lost Meridian","Drama",
         f"linear-gradient(160deg,#1a0800,#0f0500,{DARK})"),
        ("Zero Hour","Action",
         f"linear-gradient(160deg,#1a0000,#0f0000,{DARK})"),
        ("The Archive","Sci-Fi",
         f"linear-gradient(160deg,#00001a,#00000f,{DARK})"),
        ("Night Watch","Crime",
         f"linear-gradient(160deg,#001a10,#000f08,{DARK})"),
        ("Fractured","Thriller",
         f"linear-gradient(160deg,#2a0a00,#1a0500,{DARK})"),
        ("The Breach","Action",
         f"linear-gradient(160deg,#1a0005,#0f0003,{DARK})"),
        ("Phantom Line","Sci-Fi",
         f"linear-gradient(160deg,#001020,#000810,{DARK})"),
        ("Blood Meridian","Drama",
         f"linear-gradient(160deg,#200008,#100005,{DARK})"),
    ]
    all_movies = movies * 2
    cards = ""
    for title, genre, grad in all_movies:
        cards += f"""
        <div class="mc" style="background:{grad};height:150px">
            <div style="position:absolute;top:0;left:0;right:0;
                        height:2px;background:{RED};opacity:.7"></div>
            <div class="mc-img">
                <div class="mc-t">{title}</div>
                <div class="mc-g">{genre}</div>
            </div>
        </div>"""
    return cards

def page_header(title, subtitle, tag):
    cards = make_movie_cards()
    st.markdown(f"""
    <div class="ph">
        <div class="ph-left">
            <h2>{title}</h2>
            <p>{subtitle}</p>
            <span class="ph-tag">{tag}</span>
        </div>
        <div class="ph-right">
            <div class="browse-track">{cards}</div>
            <div class="ph-overlay"></div>
            <div class="red-orb"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def ticker(page_name=""):
    items_by_page = {
        "Subscriber Intelligence": [
            ("Netflix churn rate Q3 2024",        "2.17% record low"),
            ("New subscriber acquisition cost",   "5-7x more than retention"),
            ("Netflix recommendations",           "drive 80% of content watched"),
            ("Netflix saves via recommendations", "$1B+ annually"),
            ("Prime Video churn benchmark",       "3.7%, Paramount+ 4.94%"),
            ("iLTV vs naive overstatement",       "Netflix reports 2-3x in WWW 22"),
            ("Markov chain parameters",           "beta=0.99/month, T=24 months"),
        ],
        "Lifetime Value Prediction Model": [
            ("XGBoost churn model AUC",   "0.79 on held-out test set"),
            ("Top churn signal",          "Days since last watch — highest SHAP importance"),
            ("Naive LTV flaw",            "ignores counterfactual rejoin revenue"),
            ("iLTV approach",             "inspired by Badri & Tran, Netflix WWW 22"),
            ("p(rejoin) range",           "5% to 45% based on genre affinity"),
            ("Plan upgrade churn effect", "reduces risk by 8-12%"),
        ],
        "Customer Win-back Intelligence": [
            ("B-1 state",               "highest p(rejoin), act within 1 cycle"),
            ("Win-back score formula",  "iLTV x p(rejoin)"),
            ("Optimal discount range",  "10-25% calibrated to price elasticity"),
            ("Recent vs long churners", "2-3x higher rejoin rate in B-1"),
            ("Netflix win-back window", "personalised offer within 30 days"),
            ("Campaign efficiency",     "80% factor applied to ROI"),
        ]
    }
    items_list = items_by_page.get(
        page_name, list(items_by_page.values())[0])
    items = " &nbsp;&nbsp; | &nbsp;&nbsp; ".join([
        f"<span style='color:{LGRAY};font-size:12px'>{k}:</span> "
        f"<span style='color:{WHITE};font-weight:600;"
        f"font-size:12px'>{v}</span>"
        for k, v in items_list
    ])
    double = f"{items} &nbsp;&nbsp; | &nbsp;&nbsp; {items}"
    st.markdown(f"""
    <div style='background:{DARK};border-top:1px solid #222;
                border-bottom:2px solid {RED};padding:7px 0;
                overflow:hidden;margin-bottom:18px'>
        <div style='display:flex;align-items:center'>
            <div style='background:{RED};color:{WHITE};font-size:10px;
                        font-weight:700;padding:4px 14px;
                        letter-spacing:.1em;text-transform:uppercase;
                        white-space:nowrap;flex-shrink:0'>LIVE</div>
            <div style='overflow:hidden;flex:1;padding-left:16px'>
                <div style='display:inline-block;white-space:nowrap;
                            animation:tickerScroll 40s linear infinite'>
                    {double}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='padding:14px 0 22px;text-align:center'>
        <div style='font-size:58px;font-weight:900;color:{RED};
                    font-family:Georgia,serif;letter-spacing:-2px;
                    line-height:1;animation:glow 3s ease-in-out infinite'>N</div>
        <div style='font-size:13px;font-weight:600;color:{WHITE};
                    margin-top:8px;letter-spacing:.4px'>
            Streaming Subscriber</div>
        <div style='font-size:11px;color:{LGRAY};letter-spacing:.3px'>
            LTV & Retention Intelligence</div>
    </div>
    <div style='font-size:11px;color:#555;padding:8px 10px;
                background:#1A1A1A;border-radius:6px;margin-bottom:18px;
                line-height:1.8;border-left:2px solid {RED}'>
        Incremental LTV methodology<br>
        <span style='color:{RED};font-weight:500'>
            Inspired by Badri & Tran, Netflix, WWW 22</span><br>
        XGBoost, Markov chain, Kaplan-Meier
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("", [
        "Subscriber Intelligence",
        "Lifetime Value Prediction Model",
        "Customer Win-back Intelligence"
    ], label_visibility="collapsed")

    st.markdown(f"""
    <hr style='border-color:#222;margin:16px 0'>
    <div style='font-size:11px;color:#444;line-height:2'>
        <div>Data: MovieLens 25M</div>
        <div>Model: XGBoost, AUC 0.79</div>
        <div>Survival: Kaplan-Meier</div>
        <div>API: Hugging Face Spaces</div>
        <div style='margin-top:8px;color:{RED};font-weight:500'>
            Live scoring enabled</div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# PAGE 1 — SUBSCRIBER INTELLIGENCE
# ════════════════════════════════════════════════════════════════
if page == "Subscriber Intelligence":

    page_header(
        "Subscriber Intelligence",
        "A full-picture view of where subscribers sit in their "
        "lifecycle, what signals predict their departure, and how "
        "acquisition channel and content preferences shape long-term "
        "incremental value. Powered by real-time iLTV scoring across "
        "three Markov states.",
        "Inspired by Netflix WWW 22 methodology"
    )

    with st.spinner("Loading subscriber data..."):
        data = load_all_page1()

    segments = pd.DataFrame(data.get("segments", []))
    funnel   = pd.DataFrame(
        data.get("funnel", {}).get('stages', []))
    cohorts  = pd.DataFrame(data.get("cohorts", []))
    content  = pd.DataFrame(data.get("content-retention", []))
    km       = data.get("km-curves", {})
    fi       = pd.DataFrame(data.get("feature-importance", []))

    if segments.empty:
        st.error("Could not load data. Please refresh.")
        st.stop()

    total    = segments['count'].sum()
    avg_iltv = round(
        (segments['avg_iltv']*segments['count']).sum()/total, 2)
    avg_churn= round(
        (segments['avg_churn']*segments['count']).sum()/total*100, 1)
    off_mask = segments['markov_state'].isin(
        ['off_service_long','off_service_recent'])
    rev_risk = round(
        (segments[off_mask]['avg_iltv']*
         segments[off_mask]['count']).sum(), 0)
    on_count = int(segments[
        segments['markov_state']=='on_service']['count'].iloc[0])
    arpu     = round(avg_iltv/24, 2)
    mrr      = round(arpu*on_count, 0)

    ticker("Subscriber Intelligence")

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Active subscribers",    f"{on_count:,}")
    k2.metric("MRR (estimated)",       f"${mrr:,.0f}")
    k3.metric("ARPU",                  f"${arpu}/mo")
    k4.metric("Avg iLTV",             f"${avg_iltv}")
    k5.metric("Avg churn probability", f"{avg_churn}%")
    k6.metric("Revenue at risk",       f"${rev_risk:,.0f}")

    fn(
        "ARPU = avg iLTV / 24-month horizon (proxy from Markov model). "
        "MRR = ARPU x active subscribers. "
        "iLTV = V(on-service) - V(counterfactual off-service). "
        "Revenue at risk = total iLTV of all off-service subscribers."
    )

    st.markdown("<hr class='div'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([0.85, 1.05, 1.2])

    with col1:
        sec("Subscriber lifecycle funnel",
            "Sequential stages, each a strict subset of the previous")
        if not funnel.empty:
            colors_f = [DARK,DGRAY,MGRAY,RED_DIM,RED,RED,RED_DIM]
            fig_f = go.Figure(go.Funnel(
                y            = funnel['stage'].tolist(),
                x            = funnel['pct'].tolist(),
                textinfo     = "percent initial",
                textposition = (["inside"] * (len(funnel)-3)
                                + ["outside", "inside", "outside"]),
                textfont     = dict(size=11,family="Inter",
                                    color=(
                                        [WHITE]*(len(funnel)-3)
                                        + [DARK, WHITE, DARK]
                                    )),
                marker       = dict(
                    color=colors_f[:len(funnel)],
                    line=dict(width=1,color=WHITE)),
                connector    = dict(line=dict(color="#DDD",width=0.5))
            ))
            fig_f.update_layout(
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=80,t=10,b=10),
                font=dict(family="Inter",size=12)
            )
            st.plotly_chart(fig_f, use_container_width=True)
        fn(
            "Engaged = watch_freq > 0.1. "
            "Loyal = tenure > 12mo, active, not churned. "
            "At risk = active but churn_prob > 50%."
        )

    with col2:
        sec("Markov state distribution",
            "Current billing cycle state for all subscribers")
        state_map = {
            'on_service'        : 'On-service',
            'off_service_recent': 'Off-service (recent)',
            'off_service_long'  : 'Off-service (long-term)'
        }
        segments['label']     = segments['markov_state'].map(state_map)
        segments['color_bar'] = [DARK, RED, RED_DIM]

        fig_m = go.Figure()
        for _, row in segments.iterrows():
            fig_m.add_trace(go.Bar(
                x            = [row['label']],
                y            = [row['count']],
                name         = row['label'],
                marker_color = row['color_bar'],
                text         = [f"{row['count']:,}, "
                                f"${row['avg_iltv']:.0f} iLTV"],
                textposition = 'outside',
                textfont     = dict(color=DARK,size=12,family='Inter')
            ))
        fig_m = chart(fig_m.update_layout(
            title      = "Subscribers by Markov state",
            showlegend = False,
            yaxis_title= "Subscribers",
            xaxis_title= "",
            yaxis      = dict(
                showgrid=True,gridcolor="#F2F2F2",
                range=[0,segments['count'].max()*1.35])
        ), height=300)
        st.plotly_chart(fig_m, use_container_width=True)
        fn(
            "Markov states (inspired by Netflix WWW 22): "
            "Aₙ = on-service n billing cycles. "
            "B₋ⱼ = off-service j cycles. "
            "p(Aₙ→B₋₁) = churn. p(B₋ⱼ→Aₙ) = rejoin."
        )
        ins(
            "Off-service recent (B₋₁) has the highest p(rejoin). "
            "Target within 1 billing cycle for maximum win-back ROI."
        )

    with col3:
        sec("Kaplan-Meier retention curves",
            "Survival probability by acquisition channel")
        if km:
            fig_km = go.Figure()
            km_styles = {
                'organic'    :dict(color=DARK,   dash='solid',width=2.5),
                'paid_social':dict(color=MGRAY,  dash='dash', width=2),
                'bundle'     :dict(color=RED_DIM,dash='dot',  width=2),
                'trial'      :dict(color=RED,    dash='solid',width=2.5)
            }
            for channel, cdata in km.items():
                s = km_styles.get(channel,
                    dict(color=LGRAY,dash='solid',width=1.5))
                if isinstance(cdata,dict) and 'timeline' in cdata:
                    fig_km.add_trace(go.Scatter(
                        x    = cdata['timeline'],
                        y    = cdata['survival'],
                        name = channel.replace('_',' ').title(),
                        line = dict(color=s['color'],
                                    dash=s['dash'],
                                    width=s['width']),
                        mode = 'lines'
                    ))
            fig_km = chart(fig_km.update_layout(
                title       = "Retention by acquisition channel",
                xaxis_title = "Tenure (years, normalised 0-5)",
                yaxis_title = "Proportion still subscribed",
                legend      = dict(orientation="h",y=1.12,x=0,
                                   font=dict(size=11))
            ), height=300)
            st.plotly_chart(fig_km, use_container_width=True)
        else:
            st.info("Retention curves loading...")
        ins(
            "Organic retains longest. "
            "Trial churns fastest — discount-driven acquisition "
            "produces weaker long-term cohorts."
        )
        fn(
            "S(t) = product(1 - d_i/n_i). "
            "95% CI: Var(S(t)) = S(t)^2 x sum(d_i/n_i(n_i-d_i)). "
            "Tenure rescaled from MovieLens 1995-2019 to 0-5yr."
        )

    st.markdown("<hr class='div'>", unsafe_allow_html=True)

    col4, col5, col6 = st.columns([1, 1, 1.1])

    with col4:
        sec("What drives churn?",
            "SHAP feature importance from XGBoost churn model")
        if not fi.empty:
            labels = {
                'last_active_days'    :'Days since last watch',
                'watch_frequency'     :'Watch frequency',
                'genre_affinity_score':'Genre affinity',
                'rating_std'          :'Rating consistency',
                'avg_rating'          :'Avg content rating',
                'plan_encoded'        :'Plan tier',
                'total_ratings'       :'Total watches',
                'genre_encoded'       :'Genre preference',
                'acq_encoded'         :'Acquisition channel'
            }
            fi['label'] = fi['feature'].map(labels).fillna(fi['feature'])
            fi_s = fi.sort_values('importance')
            fi_s['col'] = fi_s['importance'].apply(
                lambda x: RED
                if x > fi_s['importance'].median()
                else LGRAY
            )
            fig_fi = go.Figure(go.Bar(
                x            = fi_s['importance'],
                y            = fi_s['label'],
                orientation  = 'h',
                marker_color = fi_s['col'],
                text         = fi_s['importance'].round(2),
                textposition = 'outside',
                textfont     = dict(size=12,color=DARK)
            ))
            fig_fi = chart(fig_fi.update_layout(
                title       = "SHAP importance (XGBoost churn model)",
                xaxis_title = "Mean |SHAP value|"
            ), height=300)
            st.plotly_chart(fig_fi, use_container_width=True)
        ins(
            "Recency dominates — days since last watch "
            "outweighs all other signals combined."
        )
        fn(
            "SHAP = marginal contribution of each feature. "
            "XGBoost, AUC = 0.79, 15,998 subscribers."
        )

    with col5:
        sec("Cohort revenue analysis",
            "iLTV and churn by acquisition channel and plan tier")

        valid_plans    = ['Basic','Standard','Premium']
        valid_channels = ['organic','paid_social','bundle','trial']
        color_iltv  = {'Basic':LGRAY,'Standard':MGRAY,'Premium':RED}
        color_churn = {'Basic':RED,  'Standard':MGRAY,'Premium':LGRAY}

        cohorts_clean = cohorts.copy()
        cohorts_clean['plan_tier'] = (
            cohorts_clean['plan_tier'].astype(str).str.strip())
        cohorts_clean['acq_channel'] = (
            cohorts_clean['acq_channel'].astype(str).str.strip())
        cohorts_clean = cohorts_clean[
            cohorts_clean['plan_tier'].isin(valid_plans) &
            cohorts_clean['acq_channel'].isin(valid_channels)
        ].copy()

        tab1, tab2 = st.tabs(
            ["iLTV by cohort","Churn rate by cohort"])

        with tab1:
            fig_c1 = go.Figure()
            for plan in valid_plans:
                d = cohorts_clean[cohorts_clean['plan_tier']==plan]
                if not d.empty:
                    fig_c1.add_trace(go.Bar(
                        name         = plan,
                        x            = d['acq_channel'],
                        y            = d['avg_iltv'],
                        marker_color = color_iltv[plan]
                    ))
            fig_c1.update_layout(barmode='group')
            fig_c1 = chart(fig_c1.update_layout(
                title      = "Avg iLTV by channel and plan tier",
                yaxis_title= "Avg iLTV ($)",
                xaxis_title= "",
                legend     = dict(orientation="h",y=1.1,
                                  font=dict(size=11),
                                  title=dict(text=""))
            ), height=255)
            st.plotly_chart(fig_c1, use_container_width=True)

        with tab2:
            fig_c2 = go.Figure()
            for plan in valid_plans:
                d = cohorts_clean[cohorts_clean['plan_tier']==plan]
                if not d.empty:
                    fig_c2.add_trace(go.Bar(
                        name         = plan,
                        x            = d['acq_channel'],
                        y            = d['churn_rate'],
                        marker_color = color_churn[plan]
                    ))
            fig_c2.update_layout(barmode='group')
            fig_c2 = chart(fig_c2.update_layout(
                title      = "Churn rate by channel and plan tier",
                yaxis_title= "Churn rate",
                xaxis_title= "",
                legend     = dict(orientation="h",y=1.1,
                                  font=dict(size=11),
                                  title=dict(text=""))
            ), height=255)
            st.plotly_chart(fig_c2, use_container_width=True)

        ins(
            "Trial + Basic: highest churn (32%), lowest iLTV ($50). "
            "Organic + Premium: lowest churn (6%), highest iLTV ($271)."
        )
        fn(
            "iLTV computed analytically via Markov chain. "
            "r = 1%/month, T = 24 months."
        )

    with col6:
        sec("Content genre: tenure vs iLTV",
            "Bubble size = subscribers, color = churn rate")
        if not content.empty:
            content['size_s'] = (
                content['count']/content['count'].max()*55
            ).clip(lower=14)
            fig_g = px.scatter(
                content,
                x        = 'avg_tenure',
                y        = 'avg_iltv',
                size     = 'size_s',
                color    = 'avg_churn',
                text     = 'top_genre',
                color_continuous_scale = [[0,DARK],[0.5,MGRAY],[1,RED]],
                size_max = 50,
                labels   = {
                    'avg_tenure':'Avg tenure (months)',
                    'avg_iltv'  :'Avg iLTV ($)',
                    'avg_churn' :'Churn rate'
                }
            )
            fig_g.update_traces(
                textposition = 'top center',
                textfont     = dict(size=13, color=DARK)
            )
            fig_g = chart(fig_g.update_layout(
                title                    = "Genre: tenure vs iLTV",
                coloraxis_colorbar_title = 'Churn rate',
                yaxis_range              = [50, 110],
                xaxis_range              = [100, 205]
            ), height=300)
            st.plotly_chart(fig_g, use_container_width=True)
        ins(
            "Action: highest iLTV ($93). "
            "Comedy: longest tenure but higher churn."
        )
        fn(
            "Bubble size = subscriber count. "
            "Color = churn rate (dark = low, red = high). "
            "Observational, not causal."
        )

# ════════════════════════════════════════════════════════════════
# PAGE 2 — LIFETIME VALUE PREDICTION MODEL
# ════════════════════════════════════════════════════════════════
elif page == "Lifetime Value Prediction Model":

    page_header(
        "Lifetime Value Prediction Model",
        "Adjust a subscriber's streaming behaviour signals and watch "
        "the Markov chain compute their incremental LTV in real time. "
        "iLTV corrects naive LTV by subtracting the counterfactual "
        "revenue earned even if the subscriber churned, via p(rejoin). "
        "Outputs feed into acquisition, engagement, retention, "
        "and revenue decisions.",
        "Inspired by Badri & Tran, Netflix WWW 22"
    )

    col_in, col_out = st.columns([1, 1.3])

    with col_in:
        sec("Streaming behaviour signals",
            "Inputs to XGBoost churn classifier and Markov iLTV formula")

        with st.expander("Watch activity", expanded=True):
            watch_frequency  = st.slider(
                "Watch frequency (0 = inactive, 1 = power user)",
                0.0, 1.0, 0.4, 0.01)
            last_active_days = st.slider(
                "Recency: days since last watch (normalised 0-1)",
                0.0, 1.0, 0.1, 0.01)
            total_ratings    = st.slider(
                "Total content interactions",
                10, 500, 150)

        with st.expander("Content preferences", expanded=True):
            genre_affinity = st.slider(
                "Genre affinity: % of watches in top genre",
                0.0, 100.0, 60.0, 1.0)
            avg_rating = st.slider(
                "Avg content rating given", 1.0, 5.0, 3.8, 0.1)
            rating_std = st.slider(
                "Rating consistency (lower = more consistent)",
                0.0, 2.0, 0.9, 0.1)
            genre = st.selectbox("Top genre",
                ["Action","Comedy","Drama","Thriller",
                 "Sci-fi","Documentary"])
            genre_encoded = {
                "Action":0,"Comedy":1,"Drama":2,
                "Thriller":3,"Sci-fi":4,"Documentary":5}[genre]

        with st.expander("Subscription signals", expanded=True):
            plan = st.selectbox("Plan tier",
                                ["Basic","Standard","Premium"])
            channel = st.selectbox("Acquisition channel",
                ["organic","paid_social","bundle","trial"])
            plan_encoded = {"Basic":1,"Standard":2,"Premium":3}[plan]
            plan_price   = {
                "Basic":9.99,"Standard":15.49,"Premium":22.99}[plan]
            acq_encoded  = {
                "organic":0,"paid_social":1,
                "bundle":2,"trial":3}[channel]

    with col_out:
        sec("Scoring output",
            "Results from POST /score via Markov chain + XGBoost")

        payload = {
            "total_ratings"       : total_ratings,
            "avg_rating"          : avg_rating,
            "rating_std"          : rating_std,
            "last_active_days"    : last_active_days,
            "watch_frequency"     : watch_frequency,
            "genre_affinity_score": genre_affinity,
            "genre_encoded"       : genre_encoded,
            "plan_encoded"        : plan_encoded,
            "acq_encoded"         : acq_encoded,
            "plan_price"          : plan_price
        }

        with st.spinner("Scoring..."):
            r = post_score(payload)
        if r is None:
            st.stop()

        churn_prob     = r['churn_probability']
        iltv           = r['iltv']
        naive_ltv      = r['naive_ltv']
        state          = r['markov_state']
        signal         = r['campaign_signal']
        risk           = r['churn_risk']
        p_rejoin       = r['p_rejoin']
        overstate      = round(naive_ltv/iltv,1) if iltv>0 else 1.0
        counterfactual = round(naive_ltv - iltv, 2)

        state_label = {
            "on_service"         :"On-service (active)",
            "off_service_recent" :"Off-service, recent",
            "off_service_long"   :"Off-service, long-term"
        }.get(state, state)

        ticker("Lifetime Value Prediction Model")

        s1,s2,s3 = st.columns(3)
        s1.metric("Incremental LTV",   f"${iltv:.2f}",
                  help="Revenue truly lost if subscriber never acquired")
        s2.metric("Naive LTV",         f"${naive_ltv:.2f}",
                  delta=f"Overstates by {overstate}x",
                  delta_color="inverse")
        s3.metric("Churn probability", f"{churn_prob:.1%}")

        s4,s5,s6 = st.columns(3)
        s4.metric("Markov state",  state_label)
        s5.metric("p(rejoin)",     f"{p_rejoin:.1%}",
                  help="If churned, probability of returning")
        s6.metric("Risk level",    risk.upper())

        cf_label_pos   = ('outside' if counterfactual < naive_ltv*0.15
                          else 'inside')
        cf_label_color = WHITE if cf_label_pos == 'inside' else DARK

        fig_ltv = go.Figure()
        fig_ltv.add_trace(go.Bar(
            x            = ["Incremental LTV",
                             "Counterfactual\n(would earn anyway)"],
            y            = [iltv, counterfactual],
            marker_color = [RED, MGRAY],
            text         = [f"${iltv:.2f}", f"${counterfactual:.2f}"],
            textposition = ['inside', cf_label_pos],
            insidetextanchor = 'middle',
            textfont     = dict(
                size=14, family="Inter",
                color=[WHITE, cf_label_color]),
            width        = [0.4, 0.4]
        ))
        fig_ltv.add_hline(
            y                   = naive_ltv,
            line_dash           = "dot",
            line_color          = DARK,
            line_width          = 2,
            annotation_text     = (
                f"Naive LTV: ${naive_ltv:.2f} "
                f"— overstates by {overstate}x"),
            annotation_position = "top right",
            annotation_font     = dict(size=12, color=DARK)
        )
        fig_ltv.update_layout(
            height        = 250,
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor  = "rgba(0,0,0,0)",
            margin        = dict(l=10,r=10,t=50,b=10),
            title         = dict(
                text="LTV decomposition: what naive LTV misses",
                font=dict(size=13,color=DARK)),
            showlegend    = False,
            yaxis         = dict(
                showgrid=True,gridcolor="#F2F2F2",
                title="Value ($)",zeroline=False,
                range=[0, naive_ltv*1.4]),
            xaxis         = dict(showgrid=False),
            font          = dict(family="Inter",size=12)
        )
        st.plotly_chart(fig_ltv, use_container_width=True)

        fn(
            f"iLTV = V(on-service) - V(counterfactual). "
            f"V = sum_t(beta^t x p_retain^t x price). "
            f"V_off = sum_t(beta^t x p_still_off x p_rejoin x price). "
            f"beta=0.99, T=24mo, p(rejoin)={p_rejoin:.3f}. "
            f"Naive overstates by {overstate}x. "
            f"(Inspired by Badri & Tran, Netflix WWW 22, eq 2.13)"
        )

        biz_actions = {
            "Win-back discount": {
                "Acquisition": (
                    "Re-acquisition via discount is 5-7x cheaper "
                    "than new subscriber acquisition. Assess CAC "
                    "vs win-back cost before launching."),
                "Engagement": (
                    "Identify the last watched title. Use it as "
                    "the personalised hook in win-back communication."),
                "Retention": (
                    f"Send discount within B-1 window (first billing "
                    f"cycle post-churn). Use 15-25% tiers calibrated "
                    f"to price elasticity."),
                "Revenue": (
                    f"Expected ROI = iLTV x p(rejoin) = "
                    f"${iltv*p_rejoin:.2f}. Net of 20% discount cost.")
            },
            "Personalised recommendation": {
                "Acquisition": (
                    "Engagement dropping but not yet churned. "
                    "No new acquisition action needed."),
                "Engagement": (
                    "Surface a title in their top genre via push "
                    "notification. Netflix recommendations drive "
                    "80% of content watched."),
                "Retention": (
                    "Act before recency exceeds 14 days. Churn risk "
                    "escalates sharply after 2 weeks of inactivity."),
                "Revenue": (
                    "Preventing churn here preserves full iLTV. "
                    "Cost of personalised nudge is near zero.")
            },
            "Upsell to Standard": {
                "Acquisition": (
                    "Low churn risk confirms successful onboarding. "
                    "Acquisition channel performed well."),
                "Engagement": (
                    "Heavy Basic user — Standard HD and 2-screen "
                    "access directly matches usage pattern."),
                "Retention": (
                    "Plan upgrade reduces churn risk by 8-12%. "
                    "Higher plan = higher switching cost."),
                "Revenue": (
                    f"Upgrade value: ${15.49-9.99:.2f}/mo. "
                    f"Annual uplift: ${(15.49-9.99)*12:.2f}.")
            },
            "Upsell to Premium": {
                "Acquisition": (
                    "Loyal Standard subscriber. Highest LTV ceiling "
                    "if converted to Premium."),
                "Engagement": (
                    "4K and 4 simultaneous screens directly serves "
                    "multi-device households."),
                "Retention": (
                    "Premium subscribers have the lowest churn rate "
                    "(6%). Upgrade reinforces loyalty."),
                "Revenue": (
                    f"Upgrade value: ${22.99-15.49:.2f}/mo. "
                    f"Annual uplift: ${(22.99-15.49)*12:.2f}.")
            },
            "Loyalty reward": {
                "Acquisition": (
                    "Organic, high-value subscriber. "
                    "No acquisition action needed."),
                "Engagement": (
                    "Early access to new releases in top genre "
                    "reinforces the viewing habit."),
                "Retention": (
                    "Surprise loyalty reward costs under 5% of iLTV "
                    "but significantly lowers churn risk."),
                "Revenue": (
                    "Retention cost is minimal. Preserving this "
                    "subscriber's full iLTV is the priority.")
            },
            "Watch reminder": {
                "Acquisition": (
                    "Recency dropping. Monitor for early churn signal."),
                "Engagement": (
                    "Send personalised continue-watching or new-season "
                    "alert. Drives 80% of Netflix views."),
                "Retention": (
                    "Act within 7 days. Churn probability doubles "
                    "after 14 days without a session."),
                "Revenue": (
                    "Early intervention is low cost and high return. "
                    "Prevents escalation to win-back territory.")
            }
        }
        biz = biz_actions.get(signal, {
            "Acquisition":"Monitor.",
            "Engagement" :"Monitor.",
            "Retention"  :"Monitor.",
            "Revenue"    :"Monitor."
        })
        biz_colors = {
            "Acquisition":DARK,"Engagement":MGRAY,
            "Retention"  :RED_DIM,"Revenue":RED
        }

        st.markdown(f"""
        <div style='background:{WHITE};border:1px solid #EBEBEB;
                    border-top:3px solid {RED};
                    border-radius:0 0 10px 10px;
                    padding:12px 18px;margin:12px 0'>
            <div style='font-size:10px;color:{LGRAY};
                        text-transform:uppercase;
                        letter-spacing:.08em;margin-bottom:4px'>
                Recommended action</div>
            <div style='font-size:16px;font-weight:700;
                        color:{DARK}'>{signal}</div>
        </div>
        """, unsafe_allow_html=True)

        b1, b2 = st.columns(2)
        for i,(unit,text) in enumerate(biz.items()):
            col = b1 if i%2==0 else b2
            color = biz_colors.get(unit,DARK)
            col.markdown(f"""
            <div class="biz-card">
                <span class="biz-tag"
                      style='background:{color};color:{WHITE}'>
                    {unit}</span>
                <div style='font-size:13px;color:#333;
                            line-height:1.65'>{text}</div>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# PAGE 3 — CUSTOMER WIN-BACK INTELLIGENCE
# ════════════════════════════════════════════════════════════════
elif page == "Customer Win-back Intelligence":

    page_header(
        "Customer Win-back Intelligence",
        "Subscribers who have left, ranked by how much revenue we "
        "recover if they return. Win-back score = iLTV x p(rejoin), "
        "prioritising those who are both high-value and statistically "
        "likely to return within the next billing cycle. Short-term "
        "targets (B-1 state) have the highest conversion probability.",
        "Markov off-service states B-1 through B-m"
    )

    with st.spinner("Loading win-back data..."):
        df_wb = pd.DataFrame(load_winback())

    if df_wb.empty:
        st.error("Could not load win-back data. Please refresh.")
        st.stop()

    short  = df_wb[df_wb['markov_state']=='off_service_recent']
    long_  = df_wb[df_wb['markov_state']=='off_service_long']
    st_iltv= round(short['iltv'].sum(),0)
    lt_iltv= round(long_['iltv'].sum(),0)
    avg_wb = round(df_wb['winback_score'].mean(),1)
    top_g  = df_wb['top_genre'].mode()[0]
    total_r= round((df_wb['iltv']*df_wb['p_rejoin']).sum(),0)

    ticker("Customer Win-back Intelligence")

    w1,w2,w3,w4,w5 = st.columns(5)
    w1.metric("Short-term recoverable", f"${st_iltv:,.0f}",
              help="B-1: churned 1 cycle ago, highest p(rejoin)")
    w2.metric("Long-term recoverable",  f"${lt_iltv:,.0f}",
              help="B-j (j>2): lower p(rejoin), larger pool")
    w3.metric("Expected total recovery",f"${total_r:,.0f}",
              help="Sum of iLTV x p(rejoin) across all candidates")
    w4.metric("Avg win-back score",     f"{avg_wb}",
              help="iLTV x p(rejoin): composite priority score")
    w5.metric("Top genre at risk",      top_g)

    fn(
        "Win-back score = iLTV x p(rejoin). "
        "Short-term = B-1 (churned 1 cycle ago). "
        "Long-term = B-j where j > 2 cycles. "
        "p(rejoin) = clip(0.15 + genre_affinity x 0.001, 0.05, 0.45). "
        "Optimal discount: 25% if churn_prob > 70%, "
        "15% if > 50%, 10% otherwise."
    )

    st.markdown("<hr class='div'>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.7, 1])

    with col1:
        sec("Win-back target list",
            "Sorted by win-back score, highest priority first")

        f1,f2 = st.columns(2)
        with f1:
            state_filter = st.multiselect(
                "Filter by Markov state",
                options=df_wb['markov_state'].unique().tolist(),
                default=df_wb['markov_state'].unique().tolist(),
                format_func=lambda x: x.replace('_',' ').title()
            )
        with f2:
            plan_filter = st.multiselect(
                "Filter by plan tier",
                options=df_wb['plan_tier'].unique().tolist(),
                default=df_wb['plan_tier'].unique().tolist()
            )

        filtered = df_wb[
            (df_wb['markov_state'].isin(state_filter)) &
            (df_wb['plan_tier'].isin(plan_filter))
        ].copy()
        filtered['discount'] = filtered['churn_prob'].apply(
            lambda p:'25%' if p>.7 else '15%' if p>.5 else '10%')
        filtered['roi'] = (
            filtered['iltv']*filtered['p_rejoin']*0.8).round(2)

        st.dataframe(
            filtered[[
                'userId','markov_state','iltv','p_rejoin',
                'winback_score','plan_tier','top_genre',
                'discount','roi'
            ]].rename(columns={
                'userId'       :'Subscriber',
                'markov_state' :'State',
                'iltv'         :'iLTV ($)',
                'p_rejoin'     :'p(rejoin)',
                'winback_score':'Win-back score',
                'plan_tier'    :'Plan',
                'top_genre'    :'Genre',
                'discount'     :'Optimal discount',
                'roi'          :'Expected ROI ($)'
            }).sort_values('Win-back score',ascending=False),
            use_container_width=True, height=360
        )
        fn(
            "Expected ROI = iLTV x p(rejoin) x 0.8 "
            "(80% campaign efficiency). "
            "Discount: maximise E[revenue] = "
            "p(rejoin|discount) x iLTV - discount_cost."
        )

    with col2:
        sec("Revenue by plan tier")

        plan_order   = ['Premium','Standard','Basic']
        plan_summary = df_wb.groupby('plan_tier').agg(
            count    =('userId',       'count'),
            avg_iltv =('iltv',         'mean'),
            avg_wb   =('winback_score','mean')
        ).round(1).reset_index()
        plan_summary = plan_summary.set_index(
            'plan_tier').reindex(
            [p for p in plan_order
             if p in plan_summary.index]
        ).reset_index()

        plan_colors = {
            'Premium':RED,'Standard':MGRAY,'Basic':LGRAY}
        for _, row in plan_summary.iterrows():
            bc = plan_colors.get(row['plan_tier'],LGRAY)
            st.markdown(f"""
            <div class="plan-card" style='border-left-color:{bc}'>
                <div style='font-size:13px;font-weight:600;
                            color:{DARK}'>{row['plan_tier']} plan</div>
                <div style='display:flex;gap:20px;margin-top:8px'>
                    <div>
                        <div style='font-size:10px;color:{LGRAY};
                            text-transform:uppercase'>Count</div>
                        <div style='font-size:22px;font-weight:700;
                            color:{bc}'>{int(row['count'])}</div>
                    </div>
                    <div>
                        <div style='font-size:10px;color:{LGRAY};
                            text-transform:uppercase'>Avg iLTV</div>
                        <div style='font-size:22px;font-weight:700;
                            color:{DARK}'>${row['avg_iltv']:.0f}</div>
                    </div>
                    <div>
                        <div style='font-size:10px;color:{LGRAY};
                            text-transform:uppercase'>WB score</div>
                        <div style='font-size:22px;font-weight:700;
                            color:{DARK}'>{row['avg_wb']:.1f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        sec("Expected monthly revenue recovery",
            "iLTV x p(rejoin) / 24 months, by Markov state")

        recovery = df_wb.groupby('markov_state').apply(
            lambda x: round(
                (x['iltv']*x['p_rejoin']/24).sum(),1)
        ).reset_index()
        recovery.columns = ['state','monthly_recovery']
        recovery['state'] = (
            recovery['state'].str.replace('_',' ').str.title())

        fig_rec = go.Figure(go.Bar(
            x            = recovery['state'],
            y            = recovery['monthly_recovery'],
            marker_color = [RED, RED_DIM],
            text         = recovery['monthly_recovery'].apply(
                lambda x: f"${x:.0f}/mo"),
            textposition = 'outside',
            textfont     = dict(size=13,color=DARK)
        ))
        fig_rec.update_layout(
            height=200,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor ="rgba(0,0,0,0)",
            margin=dict(l=10,r=10,t=20,b=10),
            yaxis=dict(
                showgrid=True,gridcolor="#F2F2F2",
                title="$/month",zeroline=False,
                range=[0,recovery['monthly_recovery'].max()*1.35]),
            xaxis=dict(showgrid=False),
            font=dict(family="Inter",size=12,color=DARK),
            showlegend=False
        )
        st.plotly_chart(fig_rec, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        sec("Top genres at risk")

        genre_counts = (
            df_wb['top_genre'].value_counts().reset_index())
        genre_counts.columns = ['genre','count']
        max_c = genre_counts['count'].max()

        for _, row in genre_counts.iterrows():
            bar_w = int(row['count']/max_c*100)
            st.markdown(f"""
            <div style='display:flex;align-items:center;
                        gap:10px;margin-bottom:8px'>
                <div style='font-size:13px;color:{DARK};
                            min-width:90px;font-weight:500'>
                    {row['genre']}</div>
                <div style='flex:1;background:#F2F2F2;
                            border-radius:3px;height:7px'>
                    <div style='background:{RED};width:{bar_w}%;
                                height:7px;border-radius:3px'></div>
                </div>
                <div style='font-size:13px;font-weight:600;
                            color:{DARK};min-width:24px'>
                    {row['count']}</div>
            </div>
            """, unsafe_allow_html=True)

        fn(
            "Win-back score = iLTV x p(rejoin). "
            "Genre at risk = top genre of off-service pool. "
            "Use genre as content hook in win-back messaging."
        )

