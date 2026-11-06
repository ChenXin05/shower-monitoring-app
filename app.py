import importlib
import sqlite3
from datetime import datetime
import streamlit as st
import model
import controller as ctrl_module

importlib.reload(model)
importlib.reload(ctrl_module)

st.set_page_config(
    page_title="Shower Monitor App",
    page_icon="🚿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

controller = ctrl_module.ShowerController()


def ensure_exact_report_seed():
    """Ensures User #1 (Alex) has the exact 6 sessions shown in Figure 4.7"""
    with sqlite3.connect(model.DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM USER")
        if cur.fetchone()["cnt"] == 0:
            cur.execute("INSERT INTO USER (age, health_conditions, target_duration) VALUES ('28', 'None', 10.0)")
            conn.commit()

        cur.execute("SELECT timestamp FROM SHOWER_SESSION WHERE user_id = 1 LIMIT 1")
        row = cur.fetchone()
        if not row or ("Today" not in str(row["timestamp"]) and "Mar" not in str(row["timestamp"])):
            cur.execute("DELETE FROM RECOMMENDATION WHERE session_id IN (SELECT session_id FROM SHOWER_SESSION WHERE user_id = 1)")
            cur.execute("DELETE FROM SHOWER_SESSION WHERE user_id = 1")
            exact_sessions = [
                (10.0, 38.0, 62, "Mar 7 · 8:00 AM", "Right at the recommended limit.", "Good"),
                (16.0, 41.0, 100, "Mar 8 · 6:50 AM", "Extended hot shower may dry your skin.", "Warning"),
                (6.0, 36.0, 38, "Mar 8 · 9:30 PM", "Short and gentle — great for your skin.", "Good"),
                (9.0, 37.0, 56, "Yesterday · 7:05 AM", "Well within healthy range.", "Good"),
                (14.0, 42.0, 88, "Yesterday · 8:15 PM", "Too long and too hot for skin comfort.", "Warning"),
                (8.0, 38.0, 62, "Today · 7:42 AM", "Ideal duration and temperature.", "Good"),
            ]
            for dur, temp, use_lvl, ts_label, adv, cat in exact_sessions:
                cur.execute(
                    "INSERT INTO SHOWER_SESSION (user_id, duration, water_temp, usage_level, timestamp) VALUES (1, ?, ?, ?, ?)",
                    (dur, temp, use_lvl, ts_label)
                )
                sid = cur.lastrowid
                cur.execute(
                    "INSERT INTO RECOMMENDATION (session_id, advice_text, category) VALUES (?, ?, ?)",
                    (sid, adv, cat)
                )
            conn.commit()


ensure_exact_report_seed()

if "logged_in_uid" not in st.session_state:
    st.session_state.logged_in_uid = 1
if "user_names" not in st.session_state:
    st.session_state.user_names = {1: "Alex"}
if "active_screen" not in st.session_state:
    st.session_state.active_screen = "Dashboard"
if "sim_duration" not in st.session_state:
    st.session_state.sim_duration = 8.1
if "sim_temp" not in st.session_state:
    st.session_state.sim_temp = 38.0

# ==============================================================================
# ULTIMATE CONTRAST & DROPDOWN FIX CSS
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Hide Streamlit Chrome */
[data-testid="stSidebar"], [data-testid="collapsedControl"], header[data-testid="stHeader"], footer {
    display: none !important;
}

/* Desktop Backdrop */
.stApp {
    background-color: #0B0F19 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Phone Screen Container */
.block-container,
[data-testid="stAppViewBlockContainer"],
[data-testid="stMainBlockContainer"] {
    max-width: 430px !important;
    background-color: #F8FAFC !important;
    border-radius: 40px !important;
    border: 9px solid #1E293B !important;
    padding: 28px 20px 24px 20px !important;
    margin: 16px auto !important;
    box-shadow: 0 30px 70px rgba(0, 0, 0, 0.65) !important;
}

/* FORCE ALL TEXT INSIDE PHONE TO HIGH-CONTRAST DARK SLATE (#0F172A) */
p, span, label, div, h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"] p,
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"] p {
    color: #0F172A !important;
}

/* Expander Styling */
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 20px !important;
    margin-top: 12px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05) !important;
}
[data-testid="stExpander"] details,
[data-testid="stExpander"] summary,
[data-testid="stExpanderDetails"] {
    background-color: #FFFFFF !important;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #0284C7 !important;
    font-weight: 700 !important;
    font-size: 14.5px !important;
}

/* Input Fields (Sliders, Selectboxes, NumberInputs, TextInputs) */
[data-baseweb="input"], [data-baseweb="input"] > div, [data-baseweb="select"] > div {
    background-color: #F1F5F9 !important;
    border: 1px solid #94A3B8 !important;
    border-radius: 12px !important;
}
[data-baseweb="input"] input, [data-baseweb="select"] div {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    font-weight: 600 !important;
}

/* CRITICAL FIX: SELECTBOX DROPDOWN POPUP MENU (Forces white background and dark text) */
div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"], [role="listbox"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.15) !important;
}
[role="option"], [role="option"] div, [role="option"] span {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    font-weight: 500 !important;
}
[role="option"]:hover, [role="option"]:focus, [aria-selected="true"] {
    background-color: #E2E8F0 !important;
    color: #0F172A !important;
}

/* Buttons Styling */
div.stButton > button[kind="primary"] {
    background-color: #0284C7 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 16px !important;
    font-weight: 700 !important;
}
div.stButton > button[kind="primary"] p,
div.stButton > button[kind="primary"] span {
    color: #FFFFFF !important;
}

div.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 16px !important;
    font-weight: 600 !important;
}
div.stButton > button[kind="secondary"] p,
div.stButton > button[kind="secondary"] span {
    color: #0F172A !important;
}
</style>
""", unsafe_allow_html=True)

current_uid = st.session_state.logged_in_uid
current_user = controller.db.get_user(current_uid)
display_name = st.session_state.user_names.get(current_uid, f"User #{current_uid}")

# ==============================================================================
# SCREEN 1: DASHBOARD (FIGURE 4.6)
# ==============================================================================
if st.session_state.active_screen == "Dashboard":
    dur_val = st.session_state.sim_duration
    temp_val = st.session_state.sim_temp

    res = controller.process_shower_session(dur_val, temp_val, save_to_db=False)
    fis = res["fis"]
    target_dur = float(current_user["target_duration"])

    mins = int(dur_val)
    secs = int(round((dur_val - mins) * 60))
    if secs == 60:
        mins += 1
        secs = 0
    dur_str = f"{mins}:{secs:02d}"

    rem_min_float = max(0.0, target_dur - dur_val)
    r_m = int(rem_min_float)
    r_s = int(round((rem_min_float - r_m) * 60))
    if dur_val <= target_dur:
        rem_str = f"{r_m}:{r_s:02d} left of {int(target_dur)} min"
    else:
        over_m = int(dur_val - target_dur)
        over_s = int(round(((dur_val - target_dur) - over_m) * 60))
        rem_str = f"{over_m}:{over_s:02d} over {int(target_dur)} min"

    litres_display = int(round(dur_val * 5.93))
    usage_pct = min(100, int(round((dur_val / 13.0) * 100)))

    circumference = 540.35
    progress_ratio = min(1.0, dur_val / target_dur)
    dash_offset = round(circumference * (1.0 - progress_ratio), 2)
    ring_stroke = "#0284C7" if fis["overall_status"] == "Good" else "#D97706"
    bar_fill = "#15803D" if usage_pct <= 75 else "#D97706"

    temp_word = "Warm" if fis["dom_temp"] == "Moderate" else ("Cool" if fis["dom_temp"] == "Low" else "Hot")

    if 7.5 <= dur_val <= 10.0 and temp_val < 40.0:
        adv_title = "Tip: Keep it under 10 minutes"
        adv_body = "You are close to the recommended limit. Long, hot showers strip natural oils — finish soon to protect your skin barrier."
    elif dur_val < 7.5 and temp_val < 40.0:
        adv_title = "Great habit: Healthy & Eco-friendly"
        adv_body = "Your shower duration and warm water temperature are well within the ideal clinical range to preserve natural skin moisture."
    else:
        adv_title = "Warning: Exceeding safe thermal limit"
        adv_body = res["recommendations"][0]["advice_text"]

    dashboard_html = f"""<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;">
<div>
<div style="color:#475569 !important; font-size:14.5px; font-weight:500; margin-bottom:2px;">Good morning, {display_name}</div>
<div style="color:#0F172A !important; font-size:25px; font-weight:700; letter-spacing:-0.3px;">Shower Monitor</div>
</div>
<div style="background-color:#DCFCE7; color:#15803D !important; font-size:13px; font-weight:700; padding:6px 14px; border-radius:999px; display:inline-flex; align-items:center; gap:6px; margin-top:4px;">
<span style="font-size:10px; color:#15803D !important;">●</span> <span style="color:#15803D !important;">Live</span>
</div>
</div>
<div style="background-color:#FFFFFF; border:1px solid #CBD5E1; border-radius:26px; padding:24px 16px; text-align:center; margin-bottom:14px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">
<div style="position:relative; width:204px; height:204px; margin:0 auto;">
<svg width="204" height="204" viewBox="0 0 210 210" style="transform:rotate(-90deg);">
<circle cx="105" cy="105" r="86" stroke="#E2E8F0" stroke-width="15" fill="none" />
<circle cx="105" cy="105" r="86" stroke="{ring_stroke}" stroke-width="15" fill="none" stroke-dasharray="{circumference}" stroke-dashoffset="{dash_offset}" stroke-linecap="round" />
</svg>
<div style="position:absolute; top:0; left:0; width:204px; height:204px; display:flex; flex-direction:column; align-items:center; justify-content:center;">
<span style="color:#64748B !important; font-size:11px; font-weight:700; letter-spacing:0.08em; margin-bottom:2px;">SHOWER DURATION</span>
<span style="color:#0F172A !important; font-size:42px; font-weight:700; line-height:1.1; margin-bottom:4px;">{dur_str}</span>
<span style="color:#475569 !important; font-size:13px; font-weight:600;">{rem_str}</span>
</div>
</div>
</div>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:14px;">
<div style="background-color:#FFFFFF; border:1px solid #CBD5E1; border-radius:22px; padding:16px 15px; text-align:left; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">
<div style="width:38px; height:38px; border-radius:50%; background-color:#E0F2FE; display:flex; align-items:center; justify-content:center; margin-bottom:10px;">
<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>
</div>
<div style="color:#64748B !important; font-size:13px; font-weight:600; margin-bottom:3px;">Water Temperature</div>
<div style="color:#0F172A !important; font-size:26px; font-weight:700; line-height:1.15; margin-bottom:6px;">{temp_val:.0f}°C</div>
<div style="color:#334155 !important; font-size:13.5px; font-weight:600;">{temp_word}</div>
</div>
<div style="background-color:#FFFFFF; border:1px solid #CBD5E1; border-radius:22px; padding:16px 15px; text-align:left; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">
<div style="width:38px; height:38px; border-radius:50%; background-color:#DCFCE7; display:flex; align-items:center; justify-content:center; margin-bottom:10px;">
<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#15803D" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
</div>
<div style="color:#64748B !important; font-size:13px; font-weight:600; margin-bottom:3px;">Usage Level</div>
<div style="color:#0F172A !important; font-size:26px; font-weight:700; line-height:1.15; margin-bottom:6px;">{usage_pct}%</div>
<div style="width:100%; height:6px; background-color:#E2E8F0; border-radius:999px; overflow:hidden; margin:7px 0;">
<div style="width:{usage_pct}%; height:100%; background-color:{bar_fill}; border-radius:999px;"></div>
</div>
<div style="color:#334155 !important; font-size:13.5px; font-weight:600;">{litres_display} L used</div>
</div>
</div>
<div style="background-color:#FEF9C3; border:1px solid #FDE047; border-radius:22px; padding:16px 15px; display:flex; gap:13px; align-items:flex-start; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">
<div style="width:40px; height:40px; min-width:40px; border-radius:50%; background-color:#FEF08A; display:flex; align-items:center; justify-content:center; margin-top:2px;">
<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#854D0E" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
</div>
<div>
<div style="color:#854D0E !important; font-size:11px; font-weight:800; letter-spacing:0.06em; text-transform:uppercase; margin-bottom:2px;">HEALTH ADVICE</div>
<div style="color:#0F172A !important; font-size:15px; font-weight:700; margin-bottom:3px;">{adv_title}</div>
<div style="color:#334155 !important; font-size:13.5px; font-weight:500; line-height:1.42;">{adv_body}</div>
</div>
</div>"""
    st.markdown(dashboard_html, unsafe_allow_html=True)

    with st.expander("🚿 Tap to Adjust / Log Shower (UC-02)"):
        new_dur = st.slider("Duration (minutes)", 1.0, 20.0, float(st.session_state.sim_duration), 0.1)
        new_temp = st.slider("Water Temperature (°C)", 28.0, 45.0, float(st.session_state.sim_temp), 0.5)

        if new_dur != st.session_state.sim_duration or new_temp != st.session_state.sim_temp:
            st.session_state.sim_duration = new_dur
            st.session_state.sim_temp = new_temp
            st.rerun()

        if st.button("💾 Complete & Save to History", type="primary", use_container_width=True):
            now_label = f"Today · {datetime.now().strftime('%I:%M %p').lstrip('0')}"
            short_advice = res["recommendations"][0]["advice_text"]
            if new_dur <= 6.5 and new_temp <= 37.5:
                short_advice = "Short and gentle — great for your skin."
            elif new_dur <= 10.0 and new_temp <= 39.0:
                short_advice = "Ideal duration and temperature."
            elif new_dur > 10.0 and new_temp >= 40.0:
                short_advice = "Too long and too hot for skin comfort."
            elif new_dur > 10.0:
                short_advice = "Extended hot shower may dry your skin."
            elif new_temp >= 40.0:
                short_advice = "Water too hot; risk of thermal stress."

            controller.db.insert_session_and_recommendations(
                current_uid,
                round(new_dur, 1),
                round(new_temp, 1),
                usage_pct,
                [{"advice_text": short_advice, "category": fis["overall_status"]}],
                timestamp=now_label
            )
            st.success("Session saved! Tap 'History' below to view.")

# ==============================================================================
# SCREEN 2: RECOMMENDATION HISTORY (FIGURE 4.7)
# ==============================================================================
elif st.session_state.active_screen == "History":
    sessions = controller.db.get_user_sessions_with_recommendations(current_uid)
    total_cnt = len(sessions)
    good_cnt = sum(1 for s in sessions if s["status_badge"] == "Good")

    cards_html = ""
    for s in sessions:
        is_good = (s["status_badge"] == "Good")
        if is_good:
            icon_bg = "#DCFCE7"
            pill_bg = "#DCFCE7"
            pill_col = "#15803D"
            svg_icon = '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#15803D" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/></svg>'
        else:
            icon_bg = "#FEF9C3"
            pill_bg = "#FEF9C3"
            pill_col = "#854D0E"
            svg_icon = '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#854D0E" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'

        ts_parts = str(s["timestamp"]).split("·")
        if len(ts_parts) == 2:
            ts_html = f'<span style="font-weight:700; color:#0F172A !important;">{ts_parts[0].strip()}</span> <span style="color:#64748B !important; font-weight:600;">· {ts_parts[1].strip()}</span>'
        else:
            ts_html = f'<span style="font-weight:700; color:#0F172A !important;">{s["timestamp"]}</span>'

        cards_html += f"""<div style="background-color:#FFFFFF; border:1px solid #CBD5E1; border-radius:20px; padding:15px; margin-bottom:11px; display:flex; justify-content:space-between; align-items:flex-start; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">
<div style="display:flex; gap:13px; align-items:flex-start;">
<div style="width:40px; height:40px; min-width:40px; border-radius:50%; background-color:{icon_bg}; display:flex; align-items:center; justify-content:center; margin-top:3px;">{svg_icon}</div>
<div>
<div style="font-size:15px; margin-bottom:4px;">{ts_html}</div>
<div style="color:#64748B !important; font-size:13px; font-weight:600; margin-bottom:5px; display:flex; align-items:center; gap:12px;">
<span style="color:#475569 !important;">🕒 {s['duration']:.0f} min</span>
<span style="color:#475569 !important;">🌡️ {s['water_temp']:.0f}°C</span>
</div>
<div style="color:#334155 !important; font-size:13.5px; font-weight:500;">{s['advice_text']}</div>
</div>
</div>
<span style="background-color:{pill_bg}; color:{pill_col} !important; font-size:12px; font-weight:700; padding:4px 11px; border-radius:999px; white-space:nowrap;">{s['status_badge']}</span>
</div>"""

    history_html = f"""<div style="color:#0F172A !important; font-size:25px; font-weight:700; margin-bottom:4px; letter-spacing:-0.3px;">Recommendation History</div>
<div style="color:#475569 !important; font-size:14.5px; font-weight:600; margin-bottom:18px;">{good_cnt} of {total_cnt} recent sessions were skin-healthy.</div>
{cards_html}"""
    st.markdown(history_html, unsafe_allow_html=True)

    if total_cnt == 0:
        st.info("No sessions logged yet. Go to Dashboard to log your first shower!")

# ==============================================================================
# SCREEN 3: IN-APP USER PROFILE & ACCOUNT SWITCHER (UC-01)
# ==============================================================================
elif st.session_state.active_screen == "Profile":
    sessions = controller.db.get_user_sessions_with_recommendations(current_uid)
    personal_mode = "Cold-Start Baseline (<3 sessions)" if len(sessions) < 3 else f"Content-Based Active ({len(sessions)} sessions)"

    profile_html = f"""<div style="color:#0F172A !important; font-size:25px; font-weight:700; margin-bottom:4px; letter-spacing:-0.3px;">User Profile</div>
<div style="color:#475569 !important; font-size:14.5px; font-weight:600; margin-bottom:16px;">Personalised health & water settings (UC-01)</div>
<div style="background-color:#FFFFFF; border:1px solid #CBD5E1; border-radius:22px; padding:18px 16px; display:flex; align-items:center; gap:14px; margin-bottom:14px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">
<div style="width:52px; height:52px; min-width:52px; border-radius:50%; background:linear-gradient(135deg, #0284C7, #0369A1); color:#FFFFFF !important; font-size:20px; font-weight:700; display:flex; align-items:center; justify-content:center;">
<span style="color:#FFFFFF !important;">{display_name[0].upper()}</span>
</div>
<div>
<div style="font-size:17px; font-weight:700; color:#0F172A !important;">
<span style="color:#0F172A !important;">{display_name}</span>
<span style="font-size:12.5px; color:#64748B !important; font-weight:600;"> (ID #{current_uid})</span>
</div>
<div style="font-size:13.5px; color:#334155 !important; font-weight:500; margin-top:3px;">
<span style="color:#334155 !important;">Age: </span><strong style="color:#0F172A !important;">{current_user['age']}</strong>
<span style="color:#334155 !important;"> &nbsp;•&nbsp; Condition: </span><strong style="color:#0F172A !important;">{current_user['health_conditions']}</strong>
</div>
<div style="font-size:12.5px; color:#15803D !important; font-weight:700; margin-top:4px;">● {personal_mode}</div>
</div>
</div>"""
    st.markdown(profile_html, unsafe_allow_html=True)

    with st.expander("✏️ Edit Health Profile & Target Limit", expanded=True):
        upd_age = st.number_input("Age (Years)", 5, 110, int(current_user["age"]) if str(current_user["age"]).isdigit() else 28)
        cond_list = ["None", "Hypertension", "Arrhythmia", "Eczema / Atopic Dermatitis"]
        c_idx = cond_list.index(current_user["health_conditions"]) if current_user["health_conditions"] in cond_list else 0
        upd_cond = st.selectbox("Clinical / Skin Condition", cond_list, index=c_idx)
        upd_target = st.slider("Personal Target Duration (min)", 5.0, 15.0, float(current_user["target_duration"]), 0.5)

        if st.button("💾 Save Profile Changes", type="primary", use_container_width=True):
            controller.db.update_user(current_uid, upd_age, upd_cond, upd_target)
            st.success("Profile updated in local SQLite!")
            st.rerun()

    with st.expander("🔄 Switch Account / Sign Up New User"):
        with sqlite3.connect(model.DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            all_users = [dict(r) for r in conn.execute("SELECT * FROM USER ORDER BY user_id ASC").fetchall()]

        u_map = {
            u["user_id"]: f"{st.session_state.user_names.get(u['user_id'], 'User #'+str(u['user_id']))} ({u['age']}yo, {u['health_conditions']})"
            for u in all_users
        }
        u_keys = list(u_map.keys())
        cur_idx = u_keys.index(current_uid) if current_uid in u_keys else 0
        sel_uid = st.selectbox("Switch Active Profile", options=u_keys, format_func=lambda x: u_map[x], index=cur_idx)
        if sel_uid != current_uid:
            st.session_state.logged_in_uid = sel_uid
            st.rerun()

        st.markdown('<hr style="border:none; border-top:1px solid #CBD5E1; margin:12px 0;">', unsafe_allow_html=True)
        st.caption("Register New Profile (Demonstrates Cold-Start Fallback)")
        new_name = st.text_input("Display Name", value="Sarah")
        col_a, col_b = st.columns(2)
        new_age = col_a.number_input("New User Age", 5, 110, 68)
        new_cond = col_b.selectbox("Condition", ["None", "Hypertension", "Arrhythmia", "Eczema / Atopic Dermatitis"], index=1)
        if st.button("✨ Create & Login New User", type="primary", use_container_width=True):
            with sqlite3.connect(model.DB_NAME) as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO USER (age, health_conditions, target_duration) VALUES (?, ?, ?)",
                    (str(new_age), new_cond, 10.0)
                )
                conn.commit()
                new_id = cur.lastrowid
                st.session_state.user_names[new_id] = new_name
                st.session_state.logged_in_uid = new_id
                st.rerun()

# ==============================================================================
# IN-APP 3-TAB BOTTOM NAVIGATION BAR (DASHBOARD | HISTORY | PROFILE)
# ==============================================================================
st.markdown('<div style="margin-top: 14px; border-top: 1px solid #CBD5E1; padding-top: 10px;"></div>', unsafe_allow_html=True)
nav_c1, nav_c2, nav_c3 = st.columns(3)
with nav_c1:
    t1 = "primary" if st.session_state.active_screen == "Dashboard" else "secondary"
    if st.button("🏠 Dashboard", use_container_width=True, type=t1):
        st.session_state.active_screen = "Dashboard"
        st.rerun()
with nav_c2:
    t2 = "primary" if st.session_state.active_screen == "History" else "secondary"
    if st.button("🕒 History", use_container_width=True, type=t2):
        st.session_state.active_screen = "History"
        st.rerun()
with nav_c3:
    t3 = "primary" if st.session_state.active_screen == "Profile" else "secondary"
    if st.button("👤 Profile", use_container_width=True, type=t3):
        st.session_state.active_screen = "Profile"
        st.rerun()