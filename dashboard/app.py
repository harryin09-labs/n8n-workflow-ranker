"""
Streamlit Dashboard for n8n Workflow Intelligence & Ranking System.
"""

import sys
import os
from pathlib import Path

# Ensure project root is in sys.path when running via streamlit run dashboard/app.py
ROOT_DIR = str(Path(__file__).parent.parent.resolve())
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import json
from database.db import fetch_all, fetch_one, init_db
from agents.recommendation import RecommendationEngine
from agents.ranking import RankingAgent

st.set_page_config(
    page_title="n8n Workflow Intelligence & Ranking System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database if needed
init_db()

rec_engine = RecommendationEngine()
ranking_agent = RankingAgent()

# Custom Header
st.markdown("""
<div style="background: linear-gradient(135deg, #FF6D5A 0%, #EA4C89 100%); padding: 22px; border-radius: 12px; color: white; margin-bottom: 20px;">
    <h1 style="margin: 0; color: white;">⚡ n8n Workflow Intelligence & Ranking System</h1>
    <p style="margin: 6px 0 0 0; font-size: 1.1em; opacity: 0.95;">
        Autonomous discovery, 12-dimension deterministic scoring, Daily-Life Practicality analysis, security audits, duplicate detection, and evidence-based recommendations.
    </p>
</div>
""", unsafe_allow_html=True)

# Navigation
tabs = st.tabs([
    "📊 Overview & Metrics",
    "🌟 Daily-Life Automations",
    "🏆 Leaderboards & Rankings",
    "💎 Hidden Gems",
    "🔍 Workflow Explorer",
    "📑 Workflow Detail Audit",
    "💡 Recommendation Engine",
    "👥 Duplicate Intelligence"
])

# TAB 1: OVERVIEW & ANALYTICS
with tabs[0]:
    st.subheader("System Health & Catalog Metrics")
    
    total_disc = fetch_one("SELECT COUNT(*) as count FROM discovery_records")["count"]
    total_analyzed = fetch_one("SELECT COUNT(*) as count FROM workflows")["count"]
    avg_score = fetch_one("SELECT AVG(overall_score) as avg_score FROM workflows")["avg_score"] or 0.0
    avg_daily_life = fetch_one("SELECT AVG(daily_life_practicality_score) as avg_score FROM workflows")["avg_score"] or 0.0
    total_ai = fetch_one("SELECT COUNT(*) as count FROM workflows WHERE ai_score IS NOT NULL")["count"]
    total_free = fetch_one("SELECT COUNT(*) as count FROM workflows WHERE cost_class = 'FREE'")["count"]
    total_gems = fetch_one("SELECT COUNT(*) as count FROM workflows WHERE hidden_gem_score >= 7.0")["count"]

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    col1.metric("Discovered", f"{total_disc:,}")
    col2.metric("Analyzed", f"{total_analyzed:,}")
    col3.metric("Avg Overall Score", f"{avg_score:.2f} / 10")
    col4.metric("Avg Daily-Life Score", f"{avg_daily_life:.2f} / 10")
    col5.metric("AI Workflows", f"{total_ai:,}")
    col6.metric("100% Free", f"{total_free:,}")
    col7.metric("Hidden Gems", f"{total_gems:,}")

    st.markdown("---")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.write("##### Daily-Life Practicality Distribution")
        daily_df = pd.DataFrame(fetch_all("SELECT daily_life_practicality_label as Label, COUNT(*) as Count FROM workflows GROUP BY daily_life_practicality_label"))
        if not daily_df.empty:
            st.bar_chart(daily_df.set_index("Label"))
        else:
            st.info("No workflow data yet.")

    with c2:
        st.write("##### Complexity Distribution")
        comp_df = pd.DataFrame(fetch_all("SELECT complexity as Level, COUNT(*) as Count FROM workflows GROUP BY complexity"))
        if not comp_df.empty:
            st.bar_chart(comp_df.set_index("Level"))
        else:
            st.info("No workflow data yet.")

    with c3:
        st.write("##### Cost Classification")
        cost_df = pd.DataFrame(fetch_all("SELECT cost_class as Cost, COUNT(*) as Count FROM workflows GROUP BY cost_class"))
        if not cost_df.empty:
            st.bar_chart(cost_df.set_index("Cost"))
        else:
            st.info("No workflow data yet.")

    with c4:
        st.write("##### Rating Labels Breakdown")
        rat_df = pd.DataFrame(fetch_all("SELECT rating_label as Rating, COUNT(*) as Count FROM workflows GROUP BY rating_label"))
        if not rat_df.empty:
            st.bar_chart(rat_df.set_index("Rating"))
        else:
            st.info("No workflow data yet.")

# TAB 2: DAILY-LIFE AUTOMATIONS
with tabs[1]:
    st.subheader("🌟 Top Daily-Life Automations & Practical Workflows")
    st.write("Ranked primarily by **Practical Use in Daily Life Score** (15% weight) — measuring genuine everyday usefulness, frequency, and time saved in normal personal or professional routines.")
    
    daily_life_count = fetch_one(
        "SELECT COUNT(*) as total FROM workflows WHERE status = 'active'"
    )["total"]
    dl_page_size = st.slider("Results per page", 10, 50, 25, key="dl_page_size")
    dl_total_pages = max(1, (daily_life_count + dl_page_size - 1) // dl_page_size)
    dl_page = st.number_input("Page", 1, dl_total_pages, 1, key="dl_page")
    dl_offset = (dl_page - 1) * dl_page_size
    
    daily_life_workflows = fetch_all(
        """
        SELECT workflow_id, title, problem_it_solves, canonical_url, creator_name,
               daily_life_practicality_score, daily_life_practicality_label, daily_life_use_frequency,
               overall_score, rating_label, complexity, cost_class, confidence_score, views
        FROM workflows
        WHERE status = 'active'
        ORDER BY daily_life_practicality_score DESC, overall_score DESC
        LIMIT ? OFFSET ?
        """,
        (dl_page_size, dl_offset)
    )
    
    if daily_life_workflows:
        for idx, wf in enumerate(daily_life_workflows, 1):
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #e2e8f0; border-left: 6px solid #10B981; padding: 16px; border-radius: 8px; margin-bottom: 16px; background: #ffffff;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <h3 style="margin: 0 0 6px 0; color: #1E293B;">#{idx} {wf['title']}</h3>
                        <span style="background: #ECFDF5; color: #059669; font-weight: bold; padding: 4px 10px; border-radius: 20px; font-size: 0.9em;">
                            Daily Practicality: {wf['daily_life_practicality_score']:.1f} / 10 ({wf['daily_life_practicality_label']})
                        </span>
                    </div>
                    <p style="margin: 4px 0 10px 0; font-size: 1.05em; color: #334155; font-style: italic;">
                        🎯 <b>Problem It Solves:</b> {wf['problem_it_solves'] or 'Automates recurring task.'}
                    </p>
                    <p style="margin: 0 0 8px 0; font-size: 0.9em; color: #64748B;">
                        <b>Overall Score:</b> {wf['overall_score']:.2f}/10 ({wf['rating_label']}) | 
                        <b>Frequency:</b> {wf['daily_life_use_frequency']} | 
                        <b>Complexity:</b> {wf['complexity']} | 
                        <b>Cost:</b> {wf['cost_class']} | 
                        <b>Confidence:</b> {wf['confidence_score']:.0f}%
                    </p>
                    <a href="{wf['canonical_url']}" target="_blank" style="color: #059669; font-weight: bold; text-decoration: none; font-size: 0.9em;">🔗 View on n8n.io &rarr;</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No daily life workflows indexed yet.")

# TAB 3: HIDDEN GEMS — specially curated high-quality low-visibility workflows
with tabs[3]:
    st.subheader("💎 Hidden Gems — Underappreciated, High-Quality Workflows")
    st.write("These workflows score well across all quality dimensions but have **low visibility** — perfect for discovering valuable automations the community hasn't widely adopted yet.")
    
    gem_count = fetch_one("SELECT COUNT(*) as cnt FROM workflows WHERE hidden_gem_score >= 7.0 AND status = 'active'")["cnt"]
    st.info(f"**{gem_count} Hidden Gems** identified across the catalog, picked by a combined score of quality vs. view count.")
    
    gem_pages = fetch_one("SELECT CEIL(COUNT(*)/25.0) as total FROM workflows WHERE hidden_gem_score >= 7.0 AND status = 'active'")["total"] or 1
    gem_page = st.number_input("Page", 1, int(max(gem_pages, 1)), 1, key="gem_page")
    gem_offset = (gem_page - 1) * 25
    
    gems = fetch_all("""
        SELECT workflow_id, title, problem_it_solves, views, overall_score,
               daily_life_practicality_score, daily_life_use_frequency,
               hidden_gem_score, node_count, canonical_url, creator_name,
               cost_class, complexity, rating_label
        FROM workflows
        WHERE hidden_gem_score >= 7.0 AND status = 'active'
        ORDER BY hidden_gem_score DESC, views ASC
        LIMIT 25 OFFSET ?
    """, (gem_offset,))
    
    if gems:
        for idx, gem in enumerate(gems, start=1 + (gem_page-1)*25):
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #e2e8f0; border-left: 6px solid #7C3AED; padding: 16px; border-radius: 8px; margin-bottom: 16px; background: #ffffff;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <h3 style="margin: 0 0 6px 0; color: #1E293B;">#<span style="color: #7C3AED;">{idx}</span> ✨ {gem['title']}</h3>
                        <span style="background: #F5F3FF; color: #6D28D9; font-weight: bold; padding: 4px 10px; border-radius: 20px; font-size: 0.9em;">
                            Gem Score: {gem['hidden_gem_score']:.1f} ⭐ | Views: {gem['views']:,}
                        </span>
                    </div>
                    <p style="margin: 4px 0 10px 0; font-size: 1.05em; color: #334155; font-style: italic;">
                        🎯 <b>Problem It Solves:</b> {gem['problem_it_solves'] or 'Description unavailable'}
                    </p>
                    <p style="margin: 0 0 8px 0; font-size: 0.9em; color: #64748B;">
                        <b>Overall Score:</b> {gem['overall_score']:.2f}/10 ({gem['rating_label']}) |
                        <b>Daily-Life:</b> {gem['daily_life_practicality_score']:.1f}/10 ({gem['daily_life_use_frequency']}) |
                        <b>Nodes:</b> {gem['node_count']} |
                        <b>Cost:</b> {gem['cost_class']} |
                        <b>Complexity:</b> {gem['complexity']} |
                        <b>By:</b> {gem['creator_name'] or 'Unknown'}
                    </p>
                    <a href="{gem['canonical_url']}" target="_blank" style="color: #6D28D9; font-weight: bold; text-decoration: none; font-size: 0.9em;">🔗 View on n8n.io &rarr;</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No hidden gems found on this page.")

# TAB 2 (cont): LEADERBOARDS & RANKINGS
with tabs[2]:
    st.subheader("Curated Leaderboards & Multi-Category Rankings")
    
    rankings_available = [
        ("top_overall", "🏆 Top Overall Workflows"),
        ("top_daily_life", "🌟 Most Practical for Daily Life"),
        ("most_practical", "⚡ Most Practical Overall"),
        ("best_quick_wins", "🌱 Best Quick Wins (Beginner + High Value)"),
        ("hidden_gems", "💎 Hidden Gems (High Quality, Low Views)"),
        ("best_roi_value", "📈 Best ROI / Value Score"),
        ("top_ai_agents", "🤖 Top AI Agents"),
        ("top_rag", "📚 Top RAG & Vector Knowledge"),
        ("top_completely_free", "💚 Top 100% Free (Zero API Cost)"),
        ("top_mostly_free", "🌿 Top Mostly Free"),
        ("top_self_hosted", "🏠 Top Self-Hostable"),
        ("top_privacy_friendly", "🛡️ Top Privacy-Friendly"),
        ("top_business_automation", "💼 Top Business Automation"),
        ("top_sales", "🤝 Top Sales & CRM"),
        ("top_marketing", "📢 Top Marketing & Social"),
        ("top_customer_support", "🎧 Top Customer Support"),
        ("top_document_automation", "📄 Top Document Automation"),
        ("top_appointment_booking", "📅 Top Appointment Booking"),
        ("top_developer_workflows", "💻 Top Developer Workflows"),
        ("top_gmail", "✉️ Top Gmail Workflows"),
        ("top_google_sheets", "📊 Top Google Sheets Workflows"),
        ("top_google_drive", "📁 Top Google Drive Workflows"),
        ("top_telegram", "💬 Top Telegram Workflows"),
        ("top_slack", "🗣️ Top Slack Workflows"),
        ("top_postgres", "🐘 Top PostgreSQL Workflows"),
        ("best_security", "🔒 Top Security Rated"),
        ("best_documentation", "📖 Best Documentation"),
    ]

    selected_list = st.selectbox(
        "Select Ranking Leaderboard:",
        options=[r[0] for r in rankings_available],
        format_func=lambda x: next((r[1] for r in rankings_available if r[0] == x), x)
    )

    leaderboard_data = ranking_agent.get_ranking_list(selected_list, limit=20)
    
    if leaderboard_data:
        display_data = []
        for row in leaderboard_data:
            display_data.append({
                "Rank": f"#{row['rank_position']}",
                "Score": f"{row['score_value']:.2f} ⭐",
                "Daily-Life Score": f"{row.get('daily_life_practicality_score') or 0.0:.1f} / 10",
                "Frequency": row.get("daily_life_use_frequency") or "Weekly",
                "Title": row["title"],
                "Problem It Solves": row.get("problem_it_solves") or "N/A",
                "Complexity": row["complexity"],
                "Cost": row["cost_class"],
                "Confidence": f"{row['confidence_score']:.0f}%",
                "URL": row["canonical_url"],
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)
    else:
        st.info("No rankings cached for this category yet. Run ranking agent to populate.")

# TAB 4: WORKFLOW EXPLORER
with tabs[4]:
    st.subheader("Filter, Search, and Explore Workflows")
    
    f1, f2, f3, f4, f5 = st.columns(5)
    with f1:
        min_s = st.slider("Min Overall Score", 0.0, 10.0, 0.0, 0.1)
    with f2:
        min_daily = st.slider("Min Daily-Life Score", 0.0, 10.0, 0.0, 0.1)
    with f3:
        comp_filter = st.selectbox("Complexity", ["ALL", "BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT"])
    with f4:
        cost_filter = st.selectbox("Cost Class", ["ALL", "FREE", "MOSTLY_FREE", "LOW_COST", "PAID", "EXPENSIVE"])
    with f5:
        search_kw = st.text_input("Search Keyword / Integration", "")

    query = "SELECT * FROM workflows WHERE overall_score >= ? AND daily_life_practicality_score >= ?"
    params = [min_s, min_daily]

    if comp_filter != "ALL":
        query += " AND complexity = ?"
        params.append(comp_filter)
    if cost_filter != "ALL":
        query += " AND cost_class = ?"
        params.append(cost_filter)
    if search_kw.strip():
        query += " AND (title LIKE ? OR description LIKE ? OR problem_it_solves LIKE ?)"
        params.extend([f"%{search_kw}%", f"%{search_kw}%", f"%{search_kw}%"])

    # Database-backed pagination
    count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
    total_count = fetch_one(count_query, tuple(params))["total"]
    
    page_size = st.slider("Results per page", 10, 100, 25, key="page_size")
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    page = st.number_input("Page", 1, total_pages, 1, key="page_num")
    
    offset = (page - 1) * page_size
    query += f" ORDER BY overall_score DESC LIMIT ? OFFSET ?"
    results = fetch_all(query, tuple(params + [page_size, offset]))

    st.write(f"Found **{total_count:,}** workflows matching filters (Page {page}/{total_pages}):")
    if results:
        table_rows = []
        for r in results:
            table_rows.append({
                "ID": r["workflow_id"],
                "Title": r["title"],
                "Problem It Solves": r.get("problem_it_solves") or "N/A",
                "Overall Score": f"{r['overall_score']:.2f}",
                "Daily-Life Score": f"{r.get('daily_life_practicality_score') or 0.0:.1f}",
                "Frequency": r.get("daily_life_use_frequency") or "Weekly",
                "Rating": r["rating_label"],
                "Complexity": r["complexity"],
                "Cost": r["cost_class"],
                "Security": f"{r['security_score']:.1f}",
                "Value": f"{r['value_score']:.1f}",
                "Views": f"{r['views']:,}",
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No workflows found matching the specified criteria.")

# TAB 5: WORKFLOW DETAIL VIEW
with tabs[5]:
    st.subheader("Comprehensive Workflow Audit & Deep Dive")
    
    all_workflows = fetch_all("SELECT workflow_id, title, overall_score FROM workflows ORDER BY overall_score DESC")
    
    if all_workflows:
        wf_choices = {f"#{w['workflow_id']} - {w['title']} ({w['overall_score']:.2f} ⭐)": w["workflow_id"] for w in all_workflows}
        selected_key = st.selectbox("Select Workflow to Audit:", options=list(wf_choices.keys()))
        selected_id = wf_choices[selected_key]
        
        wf = fetch_one("SELECT * FROM workflows WHERE workflow_id = ?", (selected_id,))
        nodes = fetch_all("SELECT * FROM workflow_nodes WHERE workflow_id = ?", (selected_id,))
        integrations = fetch_all("SELECT * FROM workflow_integrations WHERE workflow_id = ?", (selected_id,))
        evidence = fetch_all("SELECT * FROM score_evidence WHERE workflow_id = ? ORDER BY weight DESC", (selected_id,))
        penalties = fetch_all("SELECT * FROM penalties WHERE workflow_id = ?", (selected_id,))
        sec_findings = fetch_all("SELECT * FROM security_findings WHERE workflow_id = ?", (selected_id,))

        # Top Mandatory Summary Box
        st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 18px; margin-bottom: 20px;">
            <h2 style="margin: 0 0 10px 0; color: #0F172A;">{wf['title']}</h2>
            <div style="background: #EFF6FF; border-left: 4px solid #3B82F6; padding: 10px 14px; border-radius: 4px; margin-bottom: 12px;">
                <b style="color: #1D4ED8;">🎯 Problem It Solves:</b>
                <span style="font-size: 1.05em; color: #1E293B;"> {wf.get('problem_it_solves') or 'Automates recurring task.'}</span>
            </div>
            <p style="margin: 0; color: #475569;">
                <b>Canonical URL:</b> <a href="{wf['canonical_url']}" target="_blank">{wf['canonical_url']}</a> | 
                <b>Creator:</b> {wf['creator_name'] or 'Unknown'} (@{wf['creator_username'] or 'unknown'}) | 
                <b>Views:</b> {wf['views']:,}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Top Badges Summary
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        m1.metric("Overall Score", f"{wf['overall_score']:.2f} / 10", wf["rating_label"])
        m2.metric("Daily Practicality", f"{wf.get('daily_life_practicality_score') or 0.0:.1f} / 10", wf.get("daily_life_use_frequency") or "Weekly")
        m3.metric("Confidence", f"{wf['confidence_score']:.0f}%")
        m4.metric("Value Score", f"{wf['value_score']:.1f} / 10")
        m5.metric("Security Score", f"{wf['security_score']:.1f} / 10", wf['security_risk_level'])
        m6.metric("Complexity", wf["complexity"])
        m7.metric("Cost Class", wf["cost_class"])

        if wf.get("description"):
            with st.expander("📝 Full Description & Overview", expanded=True):
                st.write(wf["description"])

        # Score Breakdown & Evidence Table
        st.write("#### 📊 12-Dimension Evidence-Based Scoring Breakdown")
        if evidence:
            ev_df = pd.DataFrame([{
                "Criterion": e["criterion"].replace("_", " ").title(),
                "Raw Score": f"{e['raw_score']:.1f} / 10",
                "Weight": f"{e['weight']*100:.0f}%",
                "Weighted Score": f"{e['weighted_score']:.2f}",
                "Evidence": e["evidence"],
                "Reasoning": e["reasoning"],
                "Confidence": f"{e['confidence']:.0f}%",
                "Type": e["evidence_type"],
            } for e in evidence])
            st.dataframe(ev_df, use_container_width=True, hide_index=True)

        if penalties:
            st.write("#### ⚠️ Penalties Deducted")
            for p in penalties:
                st.warning(f"**{p['penalty_type']} (-{p['penalty_amount']} pts):** {p['evidence']}")

        # Security Findings
        st.write("#### 🛡️ Security Audit Findings")
        if sec_findings:
            for sf in sec_findings:
                risk = sf["risk_level"]
                color = "red" if risk in ("HIGH", "CRITICAL") else "orange" if risk == "MEDIUM" else "green"
                st.markdown(f"- **[{risk}] {sf['finding_type']}:** {sf['description']}\n  - *Recommendation:* {sf['recommendation']}")
        else:
            st.success("✅ Clean security scan: No embedded credentials or dangerous injection patterns detected.")

        # Architecture & Nodes
        st.write("#### 🧩 Workflow Topology & Integrations")
        st.write(f"**Integrations ({len(integrations)}):** {', '.join([i['integration_name'] for i in integrations]) or 'None'}")
        
        if nodes:
            node_table = pd.DataFrame([{
                "Node Name": n["node_name"],
                "Type": n["node_type_normalized"],
                "Category": n["node_category"],
                "Trigger?": "⚡ Yes" if n["is_trigger"] else "No",
                "AI?": "🤖 Yes" if n["is_ai"] else "No",
                "Credentials": n["credentials_needed"] or "None"
            } for n in nodes])
            st.dataframe(node_table, use_container_width=True, hide_index=True)
            
    else:
        st.info("No workflows indexed yet. Run supervisor pipeline first.")

# TAB 6: RECOMMENDATION ENGINE
with tabs[6]:
    st.subheader("💡 Natural Language Recommendation Engine")
    st.write("Ask natural-language questions to discover the best evidence-backed workflows for your specific automation use case.")

    example_queries = [
        "Best n8n workflow for everyday use",
        "Best daily-life automations",
        "Best free Telegram AI agent",
        "Best Gmail workflow without OpenAI",
        "Best Google Sheets workflow using Gemini",
        "Best self-hosted RAG workflow",
        "Best beginner workflow",
        "Best appointment booking automation",
        "Best workflow with no paid API",
    ]
    
    col_ex1, col_ex2 = st.columns([1, 3])
    with col_ex1:
        st.write("**Try Example Queries:**")
        for eq in example_queries[:5]:
            if st.button(eq, key=f"ex_{eq}"):
                st.session_state["query_input"] = eq
                
    with col_ex2:
        user_q = st.text_input("Enter your automation goal or question:", value=st.session_state.get("query_input", "Best daily-life automations"))
        submit_btn = st.button("Get Evidence-Backed Recommendations 🚀", type="primary")

    if user_q and (submit_btn or "query_input" in st.session_state):
        recs = rec_engine.recommend(user_q, limit=5)
        st.write(f"### Top Recommendations for: *\"{user_q}\"*")
        
        if recs:
            for i, r in enumerate(recs, start=1):
                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #e2e8f0; border-left: 6px solid #FF6D5A; padding: 18px; border-radius: 8px; margin-bottom: 16px; background: #ffffff;">
                        <h3 style="margin: 0 0 6px 0; color: #0F172A;">#{i} {r['workflow_name']}</h3>
                        <div style="background: #FFF7ED; border-left: 4px solid #F97316; padding: 8px 12px; border-radius: 4px; margin-bottom: 10px;">
                            <b style="color: #C2410C;">🎯 Problem It Solves:</b>
                            <span> {r['problem_it_solves']}</span>
                        </div>
                        <p style="margin: 0 0 10px 0; color: #475569; font-size: 0.95em;">
                            <b>Overall Score:</b> {r['overall_score']} / 10 ({r['rating_label']}) | 
                            <b>Practical Use in Daily Life:</b> {r['daily_life_practicality_score']} / 10 ({r['daily_life_use_frequency']}) | 
                            <b>Confidence:</b> {r['confidence']}% | 
                            <b>Cost:</b> {r['cost']} | 
                            <b>Complexity:</b> {r['complexity']} | 
                            <b>Integrations:</b> {', '.join(r['integrations'])}
                        </p>
                        <p style="margin: 0 0 10px 0; background: #F0FDF4; border-left: 4px solid #22C55E; padding: 8px 12px; border-radius: 4px; color: #166534;">
                            💡 <b>Why Recommended:</b> {r['why_recommended']}
                        </p>
                        <div style="display: flex; gap: 20px; margin-top: 10px;">
                            <div style="flex: 1;">
                                <b style="color: #166534;">✅ Strengths:</b>
                                <ul>{"".join([f"<li>{s}</li>" for s in r['strengths']])}</ul>
                            </div>
                            <div style="flex: 1;">
                                <b style="color: #991B1B;">⚠️ Considerations:</b>
                                <ul>{"".join([f"<li>{w}</li>" for w in r['weaknesses']])}</ul>
                            </div>
                        </div>
                        <a href="{r['original_url']}" target="_blank" style="text-decoration: none; font-weight: bold; color: #EA4C89;">🔗 Open Template on n8n.io &rarr;</a>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No matching workflows found for this specific query. Try relaxing constraints.")

# TAB 7: DUPLICATE INTELLIGENCE
with tabs[7]:
    st.subheader("Multi-Layer Duplicate & Variant Intelligence")
    st.write("Identifies exact structural duplicates, near-duplicates, and creative variants across the template catalog using graph hashing and similarity layers.")
    
    dup_rows = fetch_all(
        """
        SELECT d.duplicate_type, d.similarity_score, d.similarity_reason,
               w1.workflow_id as id1, w1.title as title1, w1.overall_score as score1,
               w2.workflow_id as id2, w2.title as title2, w2.overall_score as score2
        FROM duplicates d
        JOIN workflows w1 ON d.workflow_id = w1.workflow_id
        JOIN workflows w2 ON d.duplicate_of_id = w2.workflow_id
        ORDER BY d.similarity_score DESC
        """
    )
    
    if dup_rows:
        st.write(f"Detected **{len(dup_rows)}** duplicate / variant relationships:")
        d_table = pd.DataFrame([{
            "Type": r["duplicate_type"],
            "Similarity": f"{r['similarity_score']*100:.0f}%",
            "Template A": f"#{r['id1']} {r['title1']} ({r['score1']:.1f}⭐)",
            "Template B": f"#{r['id2']} {r['title2']} ({r['score2']:.1f}⭐)",
            "Reason": r["similarity_reason"]
        } for r in dup_rows])
        st.dataframe(d_table, use_container_width=True, hide_index=True)
    else:
        st.info("No duplicates detected in the current workflow batch.")
