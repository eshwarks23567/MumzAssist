"""
MumzAssist — Customer Service Triage Agent
Mumzworld brand-matched UI · clean, minimalistic, no unclosed-div tricks.
Run: python -m streamlit run app.py
"""

import os
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

st.set_page_config(
    page_title="MumzAssist · CS Triage",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Reset & base */
html, body, [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif !important; }
[data-testid="stHeader"] { display: none; }
.block-container {
  padding: 0 2.5rem 2rem !important;
  max-width: 1080px !important;
}

/* ── Header ── */
.mw-header {
  margin: 0 -2.5rem;
  background: #fff;
  border-bottom: 1px solid #f0eff5;
  padding: 14px 2.5rem;
  display: flex; align-items: center; justify-content: space-between;
}
.mw-logo { display: flex; align-items: center; gap: 8px; }
.mw-logo-ring {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, #e91e8c, #f06292);
  display: flex; align-items: center; justify-content: center; font-size: 15px;
}
.mw-logo-word { font-size: 21px; font-weight: 800; color: #1a1f36; letter-spacing: -.4px; }
.mw-logo-word em { color: #e91e8c; font-style: normal; }
.mw-cs-badge {
  font-size: 10.5px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase;
  color: #be185d; background: #fce4f3; border: 1px solid #f5a8d8;
  border-radius: 20px; padding: 3px 11px;
}

/* ── Pink hero ── */
.mw-hero {
  margin: 0 -2.5rem;
  background: linear-gradient(120deg, #e91e8c 0%, #ec407a 50%, #f48fb1 100%);
  padding: 20px 2.5rem 18px;
}
.mw-hero h2 {
  margin: 0 0 3px; font-size: 18px; font-weight: 700; color: #fff;
}
.mw-hero p { margin: 0; font-size: 12.5px; color: rgba(255,255,255,.82); }

/* ── Section label ── */
.mw-sec {
  font-size: 10px; font-weight: 700; letter-spacing: .09em;
  text-transform: uppercase; color: #b0a8bc; margin: 0 0 8px;
}

/* ── White card ── */
.mw-card {
  background: #fff; border: 1px solid #ede9f4;
  border-radius: 12px; padding: 16px 18px;
  box-shadow: 0 1px 3px rgba(180,60,140,.06);
}

/* ── Metric pills ── */
.mw-pills { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0; }
.mw-pill {
  flex: 1; min-width: 88px;
  background: #fff; border: 1.5px solid #f0e8f8;
  border-radius: 10px; padding: 10px 14px; text-align: center;
  box-shadow: 0 1px 3px rgba(233,30,140,.05);
}
.mw-pill-lbl {
  font-size: 9.5px; font-weight: 700; letter-spacing: .08em;
  text-transform: uppercase; color: #d63384; margin-bottom: 4px;
}
.mw-pill-val { font-size: 14px; font-weight: 700; color: #1a1f36; }

/* ── Urgency bar ── */
.mw-urg {
  border-radius: 8px; padding: 10px 15px;
  font-size: 13px; font-weight: 500; margin: 0 0 16px;
  display: flex; align-items: flex-start; gap: 9px; line-height: 1.45;
}
.mw-urg-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
.mw-u1 { background:#f0fdf4; border:1.5px solid #bbf7d0; color:#15803d; }
.mw-u1 .mw-urg-dot { background:#22c55e; }
.mw-u2 { background:#f7fde8; border:1.5px solid #d9f99d; color:#4d7c0f; }
.mw-u2 .mw-urg-dot { background:#84cc16; }
.mw-u3 { background:#fffbeb; border:1.5px solid #fde68a; color:#b45309; }
.mw-u3 .mw-urg-dot { background:#eab308; }
.mw-u4 { background:#fff7ed; border:1.5px solid #fed7aa; color:#c2410c; }
.mw-u4 .mw-urg-dot { background:#f97316; }
.mw-u5 { background:#fff1f2; border:1.5px solid #fecdd3; color:#be123c; }
.mw-u5 .mw-urg-dot { background:#f43f5e; }

/* ── Escalation ── */
.mw-esc {
  background:#fff1f2; border:1.5px solid #fecdd3; border-radius:10px;
  padding:14px 16px; margin-bottom:16px;
  display:flex; align-items:flex-start; gap:11px;
}
.mw-esc-icon { font-size:17px; flex-shrink:0; }
.mw-esc-title {
  font-size:10px; font-weight:700; letter-spacing:.07em;
  text-transform:uppercase; color:#e11d48; margin-bottom:3px;
}
.mw-esc-body { font-size:13px; color:#9f1239; line-height:1.5; }

/* ── Tags ── */
.mw-tag {
  display:inline-flex; align-items:center; gap:4px;
  padding:3px 10px; border-radius:20px; font-size:11.5px; font-weight:500;
  margin:2px 3px 2px 0; white-space:nowrap;
}
.t-order   { background:#fce4f3; border:1px solid #f5a8d8; color:#be185d; }
.t-product { background:#dcfce7; border:1px solid #86efac; color:#15803d; }
.t-date    { background:#fef9c3; border:1px solid #fde047; color:#a16207; }
.t-amount  { background:#ede9fe; border:1px solid #c4b5fd; color:#6d28d9; }
.t-person  { background:#f0f9ff; border:1px solid #bae6fd; color:#0369a1; }
.t-tool    { background:#fdf4ff; border:1px solid #e9d5ff; color:#7e22ce; }

/* ── Action badge ── */
.mw-action {
  display:inline-block; padding:4px 13px; border-radius:20px;
  font-size:11.5px; font-weight:600;
  background:#fce4f3; border:1.5px solid #f5a8d8; color:#be185d;
}

/* ── Grounding ── */
.mw-ok  { color:#16a34a; font-size:12px; font-weight:600; }
.mw-warn{ color:#dc2626; font-size:12px; font-weight:600; }

/* ── Maya chat bubble ── */
.maya-row { display:flex; align-items:flex-start; gap:10px; }
.maya-av {
  width:34px; height:34px; border-radius:50%; flex-shrink:0;
  background:linear-gradient(135deg,#e91e8c,#f06292);
  display:flex; align-items:center; justify-content:center; font-size:14px;
}
.maya-av-sup { background:linear-gradient(135deg,#9333ea,#c026d3); }
.maya-name { font-size:10.5px; font-weight:600; color:#9ca3af; margin-bottom:4px; }
.maya-bubble {
  background:#f3f4f6; border-radius:2px 12px 12px 12px;
  padding:13px 16px; font-size:14px; color:#1a1f36; line-height:1.75;
}
.maya-bubble-ar {
  background:#f3f4f6; border-radius:12px 2px 12px 12px;
  padding:13px 16px; font-size:14.5px; color:#1a1f36;
  line-height:1.9; direction:rtl; text-align:right;
}
.maya-bubble-sup {
  background:#fdf4ff; border:1px solid #e9d5ff; border-radius:2px 12px 12px 12px;
  padding:13px 16px; font-size:14px; color:#1a1f36; line-height:1.75;
}

/* ── Loading dots ── */
@keyframes mw-bounce {
  0%,80%,100% { transform:scale(.55); opacity:.35; }
  40%         { transform:scale(1);   opacity:1; }
}
.mw-loader {
  display:flex; flex-direction:column; align-items:center;
  justify-content:center; padding:64px 0; gap:14px;
}
.mw-dots { display:flex; gap:8px; }
.mw-dot  {
  width:10px; height:10px; border-radius:50%;
  animation:mw-bounce 1.3s ease-in-out infinite;
}
.mw-dot:nth-child(1){ background:#e91e8c; }
.mw-dot:nth-child(2){ background:#f06292; animation-delay:.18s; }
.mw-dot:nth-child(3){ background:#f8bbd9; animation-delay:.36s; }
.mw-loader-lbl { font-size:12.5px; color:#9ca3af; font-weight:500; letter-spacing:.03em; }

/* ── Skeleton shimmer ── */
@keyframes mw-shimmer {
  0%   { background-position:-500px 0; }
  100% { background-position: 500px 0; }
}
.mw-skel {
  border-radius:5px; height:15px;
  background:linear-gradient(90deg,#f3f3f3 25%,#e8e8e8 50%,#f3f3f3 75%);
  background-size:500px 100%; animation:mw-shimmer 1.4s infinite;
  margin-bottom:8px;
}

/* ── Streamlit widget overrides ── */
/* Textarea */
.stTextArea textarea {
  background:#fff !important;
  border:1.5px solid #e5e7eb !important;
  border-radius:10px !important; color:#1a1f36 !important;
  font-size:13.5px !important; line-height:1.6 !important;
  box-shadow:none !important;
}
.stTextArea textarea:focus {
  border-color:#e91e8c !important;
  box-shadow:0 0 0 3px rgba(233,30,140,.1) !important;
}
.stTextArea label { color:#6b7280 !important; font-size:12.5px !important; font-weight:500 !important; }

/* Primary button */
div[data-testid="stButton"] button[kind="primary"],
.stButton > button[kind="primary"] {
  background:#e91e8c !important; border:none !important;
  border-radius:8px !important; color:#fff !important;
  font-size:13px !important; font-weight:600 !important;
  padding:9px 24px !important; letter-spacing:.02em;
  box-shadow:0 2px 8px rgba(233,30,140,.25) !important;
  transition:background .18s !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover { background:#c2185b !important; }

/* Radio */
div[data-testid="stRadio"] label span { font-size:12.5px !important; color:#374151 !important; }
div[data-testid="stRadio"] [aria-checked="true"] > div:first-child {
  background:#e91e8c !important; border-color:#e91e8c !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background:transparent !important;
  border-bottom:1.5px solid #f0eff5 !important; gap:0;
}
.stTabs [data-baseweb="tab"] {
  background:transparent !important; color:#9ca3af !important;
  font-size:12.5px !important; font-weight:500 !important;
  padding:8px 18px !important; border-radius:0 !important;
}
.stTabs [aria-selected="true"] {
  color:#e91e8c !important;
  border-bottom:2px solid #e91e8c !important;
}

/* Basic Expander Styling */
details[data-testid="stExpander"] { border:1px solid #f0eff5 !important; border-radius:10px !important; margin-top: 10px !important; }

hr { border:none !important; border-top:1px solid #f0eff5 !important; margin:18px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mw-header">
  <div class="mw-logo">
    <div class="mw-logo-ring">🌸</div>
    <div class="mw-logo-word">mumz<em>world</em></div>
  </div>
  <span class="mw-cs-badge">MumzAssist · CS Triage</span>
</div>
""", unsafe_allow_html=True)

# ── Hero strip ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mw-hero">
  <h2>MumzAssist</h2>
  <p>English &amp; Arabic · AI-powered</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Input section ─────────────────────────────────────────────────────────────
CATEGORIZED_EXAMPLES = {
    "🔄 Returns": {
        "Return request (EN)":        "I want to return the stroller from order MW-10021. It arrived but it's not what I expected.",
        "Outside window (EN)":        "I bought a baby monitor 3 months ago (order MW-10067) and want to return it. I know it's been a while.",
        "Non-returnable formula (AR)":"هل حليب أبتاميل عندكم؟ وهل يمكن إرجاعه لو ما ناسبني؟",
        "Damaged item (AR)":          "وصل الكرسي مكسور! الطلب MW-10115. هذا غير مقبول، دفعت 1650 درهم وجاء مكسور. أريد استرداد كامل فوراً.",
    },
    "📦 Orders": {
        "Order tracking (AR)":        "مرحباً، طلبت كرسي سيارة وما وصل لحد الآن. رقم الطلب MW-10045. وين طلبي؟",
        "Missing item (EN)":          "My order MW-10320 was marked delivered but I never received it. Please help.",
        "Wrong item (EN)":            "I received the wrong product in order MW-10402. I ordered a Maxi-Cosi but got a different brand.",
    },
    "🛍️ Products": {
        "Product inquiry (EN)":       "Do you have the Cybex Gazelle stroller in stock? What's the price?",
        "Formula question (AR)":      "هل يتوفر حليب أبتاميل بروفيوتيورا رقم 1 عندكم؟ وما هو السعر؟",
        "Stroller comparison (EN)":   "What's the difference between the UPPAbaby Vista and the Bugaboo Fox? Which is better for newborns?",
    },
    "⚠️ Safety": {
        "Safety escalation (EN)":     "My 8-month-old swallowed part of a toy I bought from you. What should I do?",
        "Car seat concern (EN)":      "The car seat latch in order MW-10265 feels very loose. Is it safe to use?",
        "Product recall (EN)":        "I saw a news article about a recall on Graco strollers. Does this affect my order MW-10589?",
        "ابتلاع جزء من لعبة (AR)":    "طفلي عمره 9 أشهر ابتلع قطعة صغيرة من لعبة اشتريتها منكم اليوم. ماذا أفعل الآن؟",
        "كرسي سيارة غير آمن (AR)":   "مشبك كرسي السيارة في طلب MW-10265 يبدو مفكوكاً جداً. هل هو آمن للاستخدام؟",
        "استدعاء منتج (AR)":          "قرأت خبراً عن استدعاء عربات Graco. هل يؤثر هذا على طلبي رقم MW-10589؟",
    },
    "💬 Other": {
        "Positive feedback (EN)":     "Just wanted to say the Philips Avent bottles I ordered were perfect! Thank you Mumzworld!",
        "Ambiguous message":          "help",
        "Discount request (EN)":      "Can I get a discount on the Nuna Leaf baby seat? It's for my second child.",
        "تقييم إيجابي (AR)":          "أريد أن أشكركم على زجاجات فيليبس أفنت، وصلت بسرعة وكانت ممتازة! شكراً موميز وورلد!",
        "رسالة غامضة (AR)":           "مساعدة",
        "طلب خصم (AR)":               "هل يمكنني الحصول على خصم على كرسي Nuna Leaf؟ هذا لطفلي الثاني.",
    },
}

col_msg, col_ex = st.columns([3, 1], gap="large")

with col_ex:
    st.markdown('<p class="mw-sec">Quick Examples</p>', unsafe_allow_html=True)

    category = st.radio(
        "category",
        list(CATEGORIZED_EXAMPLES.keys()),
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:11px;color:#b0a8bc;margin:0 0 4px">— {category.split(" ", 1)[1]} —</p>', unsafe_allow_html=True)

    examples_in_cat = CATEGORIZED_EXAMPLES[category]
    selected = st.radio(
        "example",
        list(examples_in_cat.keys()),
        index=None,
        label_visibility="collapsed",
    )

with col_msg:
    default = examples_in_cat[selected] if selected else ""
    message = st.text_area(
        "Customer message (English or Arabic)",
        value=default,
        height=130,
        placeholder="Paste or type a customer message…",
    )

    # Mode selection
    st.markdown('<p class="mw-sec">Triage Mode</p>', unsafe_allow_html=True)
    mode = st.radio(
        "Select Triage Mode",
        ["Flash", "Balanced", "Pro"],
        index=1,
        label_visibility="collapsed",
        horizontal=True,
        help="Flash: Fastest, lower accuracy. Balanced: Optimized for general use. Pro: High accuracy, handles complex cases."
    ).lower()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    btn_col, meta_col = st.columns([1, 4])
    with btn_col:
        run = st.button("Triage →", type="primary", use_container_width=True)
    
    with meta_col:
        provider = os.getenv("PROVIDER", "openrouter")
        # Local lookup for model name to display in UI
        from src.agent import MODES as AGENT_MODES
        model = AGENT_MODES[mode]["models"][0]
        
        st.markdown(
            f'<p style="margin:10px 0 0;font-size:11px;color:#b0a8bc">'
            f'<span style="color:#e91e8c">●</span> &nbsp;{mode.title()} Mode &nbsp;·&nbsp; {model}</p>',
            unsafe_allow_html=True,
        )

st.markdown("<hr>", unsafe_allow_html=True)

# ── Result area ───────────────────────────────────────────────────────────────
result_slot = st.empty()

if run:
    if not message.strip():
        st.warning("Please enter a customer message.")
        st.stop()

    _STEP_LABELS = {
        "scanning": ("Scanning message…",        "Detecting intent and data needs"),
        "fetching": ("Fetching order & product data…", "Looking up real-time Mumzworld data"),
        "thinking": ("Maya is thinking…",        "Generating grounded reply"),
    }

    def _loader_html(step: str) -> str:
        label, sub = _STEP_LABELS.get(step, ("Processing…", ""))
        return f"""
        <div class="mw-loader">
          <div class="mw-dots">
            <div class="mw-dot"></div><div class="mw-dot"></div><div class="mw-dot"></div>
          </div>
          <div class="mw-loader-lbl">{label}</div>
          <div style="font-size:11.5px;color:#b0a8bc;margin-top:4px">{sub}</div>
          <div style="width:340px;margin-top:20px">
            <div class="mw-skel" style="width:60%"></div>
            <div class="mw-skel" style="width:88%"></div>
            <div class="mw-skel" style="width:44%"></div>
          </div>
        </div>"""

    loader_slot = result_slot.empty()
    loader_slot.markdown(_loader_html("scanning"), unsafe_allow_html=True)

    def _on_step(step: str) -> None:
        loader_slot.markdown(_loader_html(step), unsafe_allow_html=True)

    try:
        from src.agent import triage
        t0 = time.time()
        result, meta = triage(message, mode=mode, on_step=_on_step)
        elapsed = time.time() - t0
    except Exception as exc:
        result_slot.error(f"Error: {exc}")
        st.stop()

    # ── Render ────────────────────────────────────────────────────────────────
    with result_slot.container():

        # Escalation
        if result.should_escalate:
            st.markdown(f"""
            <div class="mw-esc">
              <div class="mw-esc-icon">🚨</div>
              <div>
                <div class="mw-esc-title">Escalate to human agent</div>
                <div class="mw-esc-body">{result.escalation_reason}</div>
              </div>
            </div>""", unsafe_allow_html=True)

        # Metric pills
        SENT_COLOR = {
            "positive": "#16a34a", "neutral": "#6b7280",
            "negative": "#d97706", "very_negative": "#dc2626",
        }
        sc = SENT_COLOR.get(result.sentiment, "#6b7280")

        st.markdown(f"""
        <div class="mw-pills">
          <div class="mw-pill">
            <div class="mw-pill-lbl">Language</div>
            <div class="mw-pill-val">{result.message_language.upper()}</div>
          </div>
          <div class="mw-pill">
            <div class="mw-pill-lbl">Intent</div>
            <div class="mw-pill-val" style="font-size:12.5px">{result.intent.replace('_',' ').title()}</div>
          </div>
          <div class="mw-pill">
            <div class="mw-pill-lbl">Urgency</div>
            <div class="mw-pill-val">{result.urgency}<span style="font-size:10px;color:#9ca3af;font-weight:400">/5</span></div>
          </div>
          <div class="mw-pill">
            <div class="mw-pill-lbl">Confidence</div>
            <div class="mw-pill-val">{result.confidence:.0%}</div>
          </div>
          <div class="mw-pill">
            <div class="mw-pill-lbl">Sentiment</div>
            <div class="mw-pill-val" style="font-size:12.5px;color:{sc}">{result.sentiment.replace('_',' ').title()}</div>
          </div>
          <div class="mw-pill">
            <div class="mw-pill-lbl">Time</div>
            <div class="mw-pill-val" style="font-size:12.5px;color:#9ca3af">{elapsed:.1f}s</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Urgency bar
        URG_LABELS = {1:"Low",2:"Slightly Elevated",3:"Moderate",4:"High",5:"Critical"}
        u = result.urgency
        st.markdown(f"""
        <div class="mw-urg mw-u{u}">
          <div class="mw-urg-dot"></div>
          <div><strong>Urgency {u} — {URG_LABELS[u]}:</strong> &nbsp;{result.urgency_reasoning}</div>
        </div>""", unsafe_allow_html=True)

        # Action + entities row
        ca, ce = st.columns(2, gap="medium")

        with ca:
            action = result.suggested_action.replace("_", " ").title()
            tools_html = " ".join(
                f'<span class="mw-tag t-tool">⚙ {t}</span>' for t in result.tools_used
            ) or '<span style="font-size:12px;color:#9ca3af">No tools called</span>'
            grounded = (
                '<span class="mw-ok">✓ Grounded on live data</span>'
                if result.grounded_on_data
                else '<span class="mw-warn">⚠ Heuristic reply</span>'
            )
            st.markdown(f"""
            <p class="mw-sec">Action &amp; Tools</p>
            <div class="mw-card">
              <div style="margin-bottom:9px"><span class="mw-action">{action}</span></div>
              <div style="margin-bottom:7px">{tools_html}</div>
              {grounded}
            </div>""", unsafe_allow_html=True)

        with ce:
            ent = result.extracted_entities
            tags = []
            for x in ent.order_ids:    tags.append(f'<span class="mw-tag t-order">⊞ {x}</span>')
            for x in ent.product_names: tags.append(f'<span class="mw-tag t-product">· {x}</span>')
            for x in ent.dates_mentioned: tags.append(f'<span class="mw-tag t-date">◷ {x}</span>')
            if ent.amount_mentioned:   tags.append(f'<span class="mw-tag t-amount">◈ {ent.amount_mentioned}</span>')
            if ent.customer_name:      tags.append(f'<span class="mw-tag t-person">◎ {ent.customer_name}</span>')
            body = "".join(tags) or '<span style="font-size:12px;color:#9ca3af">None detected</span>'
            st.markdown(f"""
            <p class="mw-sec">Extracted Entities</p>
            <div class="mw-card" style="min-height:86px">{body}</div>""", unsafe_allow_html=True)

        # Maya replies
        st.markdown('<p class="mw-sec" style="margin-top:4px">Suggested Reply · Maya</p>', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Customer language", "English — supervisor copy"])

        with tab1:
            lang = result.message_language
            lang_label = {"en": "English", "ar": "Arabic", "mixed": "Mixed — replied in customer's language"}.get(lang, lang)
            bubble = "maya-bubble-ar" if lang == "ar" else "maya-bubble"
            st.markdown(f"""
            <p style="font-size:11px;color:#9ca3af;margin:10px 0 10px">{lang_label}</p>
            <div class="maya-row">
              <div class="maya-av">🌸</div>
              <div style="flex:1;min-width:0">
                <div class="maya-name">Maya · MumzAssist</div>
                <div class="{bubble}">{result.suggested_reply_original_language}</div>
              </div>
            </div>""", unsafe_allow_html=True)

        with tab2:
            st.markdown(f"""
            <p style="font-size:11px;color:#9ca3af;margin:10px 0 10px">For supervisor / QA review — always in English</p>
            <div class="maya-row">
              <div class="maya-av maya-av-sup">🌸</div>
              <div style="flex:1;min-width:0">
                <div class="maya-name">Maya · Supervisor copy</div>
                <div class="maya-bubble-sup">{result.suggested_reply_english}</div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        with st.expander("Raw JSON output"):
            st.json(result.model_dump())
