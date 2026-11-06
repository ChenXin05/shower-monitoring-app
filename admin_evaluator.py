import sqlite3
import pandas as pd
import streamlit as st
import model
from controller import ShowerController

st.set_page_config(
    page_title="Examiner Evaluation & SQLite Inspector",
    page_icon="🧪",
    layout="wide"
)

controller = ShowerController()

st.title("🧪 FYP Project II — Algorithm Evaluation & SQLite 3NF Inspector")
st.caption("Backend evaluation console for demonstrating Rubric criteria (FIS Logic, Monte Carlo Simulation, Input Validation, and 3NF Database Structure).")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Section 4.5: FIS Lab & Rubric Metrics",
    "🎲 Section 3.2.2: Monte Carlo Synthetic Data",
    "🗄️ Section 4.2: Live SQLite 3NF DB Viewer",
    "🛡️ Section 4.4: Input Validation & DB Reset"
])

with tab1:
    st.subheader("Algorithm Evaluation Metrics (Section 4.5)")
    metrics = controller.evaluate_algorithm_metrics()
    c1, c2, c3 = st.columns(3)
    c1.metric("Classification Accuracy", f"{metrics['classification_accuracy_pct']}%", "Matches Clinical Benchmarks")
    c2.metric("Average Response Latency", f"{metrics['avg_response_time_ms']} ms", "< 50 ms Target (NFR3)")
    c3.metric("Rule Coverage Matrix", f"{metrics['rule_coverage_pct']}%", "All 9 Fuzzy Rules + Edge Cases")

    st.markdown("#### 9-State Fuzzy Rule Coverage & Edge-Case Verification Matrix")
    st.dataframe(pd.DataFrame(metrics["matrix_details"]), use_container_width=True)

with tab2:
    st.subheader("Monte Carlo Gaussian Synthetic Data Generator (Section 3.2.2 / Figure 3.2)")
    col1, col2, col3 = st.columns(3)
    n_sim = col1.number_input("Number of Synthetic Sessions", 5, 50, 15)
    mean_d = col2.number_input("Gaussian Mean Duration (min)", 5.0, 18.0, 9.5)
    mean_t = col3.number_input("Gaussian Mean Temperature (°C)", 34.0, 43.0, 38.5)

    if st.button("🎲 Run Monte Carlo Stress Test (Preview)", type="primary"):
        sim_data = controller.generate_monte_carlo_synthetic_data(
            n_samples=int(n_sim), mean_dur=float(mean_d), mean_temp=float(mean_t), save_to_db=False
        )
        rows = [
            {
                "Duration (min)": r["duration"],
                "Water Temp (°C)": r["water_temp"],
                "Litres (L)": r["litres_used"],
                "Fuzzy Duration": r["fis"]["dom_duration"],
                "Fuzzy Temp": r["fis"]["dom_temp"],
                "Centroid Risk Score": r["fis"]["centroid_score"],
                "Classification": r["fis"]["overall_status"],
                "Latency (ms)": r["latency_ms"]
            }
            for r in sim_data
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

with tab3:
    st.subheader("SQLite 3NF Relational Database Inspector (`shower_monitor.db`)")
    if st.button("🔄 Refresh Database Tables"):
        st.rerun()

    with sqlite3.connect(model.DB_NAME) as conn:
        u_df = pd.read_sql_query("SELECT * FROM USER", conn)
        s_df = pd.read_sql_query("SELECT * FROM SHOWER_SESSION ORDER BY session_id DESC", conn)
        r_df = pd.read_sql_query("SELECT * FROM RECOMMENDATION ORDER BY rec_id DESC", conn)

    st.markdown("**1. `USER` Table (Primary Key: `user_id`)**")
    st.dataframe(u_df, use_container_width=True)
    st.markdown("**2. `SHOWER_SESSION` Table (Primary Key: `session_id`, Foreign Key: `user_id`)**")
    st.dataframe(s_df, use_container_width=True)
    st.markdown("**3. `RECOMMENDATION` Table (Primary Key: `rec_id`, Foreign Key: `session_id`)**")
    st.dataframe(r_df, use_container_width=True)

with tab4:
    st.subheader("DFD 1.0 Input Sanitisation & Exception Handling Test (Section 4.4)")
    vc1, vc2 = st.columns(2)
    raw_d = vc1.text_input("Test Raw Duration Input", value="-5")
    raw_t = vc2.text_input("Test Raw Temperature Input", value="abc")
    if st.button("Verify Controller Validation"):
        ok, msg = controller.validate_inputs(raw_d, raw_t)
        if ok:
            st.success(msg)
        else:
            st.error(f"Intercepted Illegal Input: {msg}")

    st.divider()
    st.subheader("Admin Database Reset")
    st.caption("Resets `shower_monitor.db` back to the exact 6 sessions in Figure 4.7 (`image_1f03ee.png`).")
    if st.button("⚠️ Reset Database to Original Report State", type="primary"):
        with sqlite3.connect(model.DB_NAME) as conn:
            conn.execute("DELETE FROM RECOMMENDATION")
            conn.execute("DELETE FROM SHOWER_SESSION")
            conn.execute("DELETE FROM USER")
            conn.execute("DELETE FROM sqlite_sequence")
            conn.commit()
        st.success("Database cleared! Refresh the User Mobile App (`app.py`) to re-seed the 6 original sessions.")