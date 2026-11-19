import streamlit as st
import time
from agent import handle_lead, run_followups, generate_reply_card
import data

st.set_page_config(
    page_title="ServiceFlow • Instant Home Services AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom modern CSS styling
st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 12px 18px;
        text-align: center;
    }
    .badge-quoted { background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px; }
    .badge-booked { background: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px; }
    .badge-human { background: #fef3c7; color: #b45309; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px; }
    .badge-callback { background: #f3e8ff; color: #7e22ce; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px; }
    .badge-junk { background: #fee2e2; color: #b91c1c; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px; }
    .result-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #2563eb;
        border-radius: 10px;
        padding: 20px;
        margin-top: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .sample-btn {
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Fetch latest stats
stats = data.get_stats()
prof_counts = stats.get("prof_counts", {})

# -------------------------------------------------------------------------
# 1. SIDEBAR: PROFESSION FILTER WITH COUNTS
# -------------------------------------------------------------------------
st.sidebar.title("⚡ ServiceFlow")
st.sidebar.caption("Instant Dispatch & Lead Recovery Agent")

prof_emojis = {
    "All": "🌐",
    "plumber": "🔧",
    "electrician": "⚡",
    "carpenter": "🪚",
    "painter": "🎨",
    "ac_technician": "❄️",
    "home_cleaner": "🧹",
    "pest_control": "🐜",
    "appliance_repair": "📱",
}

sidebar_options = ["All"] + list(data.CATALOG.keys())
sidebar_labels = []
for p in sidebar_options:
    count = stats["total"] if p == "All" else prof_counts.get(p, 0)
    emoji = prof_emojis.get(p, "🛠️")
    name = "All Services" if p == "All" else data.CATALOG[p]["title"]
    sidebar_labels.append(f"{emoji} {name} ({count})")

selected_idx = st.sidebar.radio(
    "Filter by Profession:",
    range(len(sidebar_options)),
    format_func=lambda i: sidebar_labels[i],
)
selected_profession = sidebar_options[selected_idx]

st.sidebar.divider()
st.sidebar.markdown("### ⚙️ Engine Settings")
st.sidebar.info("**Gemini 3.5 Flash Lite**\nSingle-call parsing + pure Python instant quoting.")

# -------------------------------------------------------------------------
# 2. TOP STATS ROW
# -------------------------------------------------------------------------
st.title("⚡ Multi-Profession Lead Recovery Agent")
st.caption("Auto-qualifies incoming requests, matches top-rated local technicians, and quotes live prices instantly.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Inquiries", stats["total"])
col2.metric("Confirmed Bookings", stats["booked"])
col3.metric("Needs Human Review", stats["needs_human"])
col4.metric("Avg Process Time", f"{stats['avg_time']}s" if stats['avg_time'] > 0 else "Instant")

st.divider()

# -------------------------------------------------------------------------
# 3. MAIN TABS: "NEW LEAD" & "ALL LEADS"
# -------------------------------------------------------------------------
tab_new, tab_all = st.tabs(["📥 New Lead Intake", "📋 All Leads & Follow-ups"])

# -------------------------------------------------------------------------
# TAB 1: NEW LEAD
# -------------------------------------------------------------------------
with tab_new:
    st.subheader("Simulate Incoming Customer Message")
    st.write("Click any quick sample button or type your own custom message below:")

    # Quick sample buttons
    sample_cols = st.columns(3)
    sample_msg = None
    if sample_cols[0].button("🚰 Tap Leak (Sec 45, Gurugram)"):
        sample_msg = "My kitchen tap is leaking badly, need someone today in Gurugram Sector 45"
    if sample_cols[1].button("⚡ Switchboard Sparks (Dwarka)"):
        sample_msg = "Bhaiya short circuit ho gaya switchboard me sparks aa rahe hain, Dwarka me urgent koi bhej do"
    if sample_cols[2].button("❄️ AC Not Cooling (Sector 56)"):
        sample_msg = "My split AC is blowing warm air and not cooling at all in Sector 56, need servicing today"

    sample_cols2 = st.columns(3)
    if sample_cols2[0].button("🐜 Pest Control (DLF Phase 2)"):
        sample_msg = "Need cockroach and termite gel treatment for my 3BHK flat in DLF Phase 2"
    if sample_cols2[1].button("❓ Vague Message"):
        sample_msg = "Hello, I need some repair work done at my house"
    if sample_cols2[2].button("🚫 Spam / Junk"):
        sample_msg = "CONGRATULATIONS! You won a ₹50,000 cash prize! Claim at bit.ly/spam-gift"

    # Message input box
    default_text = sample_msg if sample_msg else ""
    message_input = st.text_area(
        "Incoming customer message (WhatsApp / SMS / Web):",
        value=default_text,
        height=90,
        placeholder="e.g. My washing machine is vibrating loudly in DLF Phase 1, need someone tomorrow morning",
    )

    # Process lead action
    if st.button("🚀 Process Lead", type="primary"):
        if not message_input.strip():
            st.warning("Please enter or select a customer message first.")
        else:
            with st.spinner("Classifying intent with Gemini Flash Lite..."):
                details, status, card, elapsed = handle_lead(message_input)

            # Store result in session state so interactive buttons (Book, Callback, Hinglish) stay active
            st.session_state["current_lead"] = {
                "message": message_input,
                "details": details,
                "status": status,
                "card": card,
                "elapsed": elapsed,
                "hinglish": False,
                "selected_provider_id": card["provider_id"] if card else None,
            }

    # Render Current Lead Result
    if "current_lead" in st.session_state and st.session_state["current_lead"]:
        lead_state = st.session_state["current_lead"]
        details = lead_state["details"]
        status = lead_state["status"]
        card = lead_state["card"]
        elapsed = lead_state["elapsed"]

        # Speed badge
        st.markdown(f"#### ⚡ Processed in **{elapsed} seconds** (1 Gemini Call + Local Match)")

        # Case 1: Junk
        if status == "junk":
            st.error("🚨 **Guardrail Triggered: Junk / Spam Detected**")
            st.write("This inquiry was classified as spam or nonsensical text. **No automated reply was generated** to protect provider bandwidth.")
            st.json(details)

        # Case 2: Needs Human Review
        elif status == "needs_human":
            st.warning("⚠️ **Flagged for Human Review: Status 'needs_human'**")
            st.write("The request was vague, out of scope, or fell below confidence threshold (0.6). Routed to support staff.")
            st.json(details)

        # Case 3: Error
        elif status == "error":
            st.error(f"❌ Processing Error: {details.get('error')}")

        # Case 4: Quoted (Success Card)
        elif status == "quoted" and card:
            # Interactive toggle for Hinglish
            c_head1, c_head2 = st.columns([3, 1])
            with c_head1:
                st.success(f"✅ Lead Successfully Quoted for **{card['profession_title']}**")
            with c_head2:
                hinglish_toggle = st.toggle("🇮🇳 Reply in Hinglish", value=lead_state.get("hinglish", False))
                if hinglish_toggle != lead_state.get("hinglish", False):
                    lead_state["hinglish"] = hinglish_toggle
                    # Re-render card text with instant template (0 AI call)
                    lang = "hinglish" if hinglish_toggle else "english"
                    current_prov = data.get_provider_by_id(card["profession"], lead_state["selected_provider_id"]) or card
                    new_card = generate_reply_card(
                        card["profession"], card["job_type"], card["urgency"],
                        details.get("location", "unknown"), current_prov,
                        card["available_at_location"], language=lang
                    )
                    new_card["lead_id"] = card.get("lead_id")
                    lead_state["card"] = new_card
                    card = new_card

            # --- THE CARD UI ---
            st.markdown(f"""
            <div class="result-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 18px; font-weight: 700; color: #1e293b;">
                        {prof_emojis.get(card['profession'], '🛠️')} {card['profession_title']} &bull; {card['job_title']}
                    </span>
                    <span style="background: {'#fef2f2' if card['urgency'] in ['emergency', 'today'] else '#f1f5f9'}; color: {'#dc2626' if card['urgency'] in ['emergency', 'today'] else '#475569'}; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px;">
                        {('🚨 URGENT: ' if card['urgency'] in ['emergency', 'today'] else '📅 ') + card['urgency'].upper()}
                    </span>
                </div>
                <div style="font-size: 15px; margin-bottom: 8px;">
                    <strong>👤 Matched Specialist:</strong> {card['provider_name']} &nbsp;|&nbsp; 
                    <span style="color: #f59e0b; font-weight: 600;">⭐ {card['provider_rating']}</span> &nbsp;|&nbsp; 
                    <span>{card['provider_exp']} Years Experience</span>
                </div>
                <div style="font-size: 14px; margin-bottom: 8px;">
                    <strong>📍 Location Availability:</strong> {card['location_display']}
                </div>
                <div style="font-size: 15px; margin-bottom: 8px; color: #047857; font-weight: 700;">
                    💰 Price Range: ₹{card['price_min']} - ₹{card['price_max']} <span style="font-size: 13px; color: #64748b; font-weight: normal;">(+ ₹{card['visiting_charge']} fixed visiting fee)</span>
                </div>
                <div style="font-size: 14px; margin-bottom: 12px; color: #2563eb;">
                    ⏱️ <strong>Estimated Arrival:</strong> {card['arrival_est']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.write("")
            # Interactive Slot Booking Buttons
            st.markdown("##### 📅 Available Slots for Today & Tomorrow (Click to Book):")
            slot_cols = st.columns(len(card["slots"]))
            for idx, slot_time in enumerate(card["slots"]):
                if slot_cols[idx].button(f"📌 Book {slot_time}", key=f"book_slot_{idx}"):
                    if card.get("lead_id"):
                        data.book_lead_slot(card["lead_id"], slot_time, card["provider_id"])
                        st.balloons()
                        st.success(f"🎉 **Slot Confirmed!** Booked with {card['provider_name']} for **{slot_time}**. Follow-ups stopped.")
                        lead_state["status"] = "booked"

            # Alternative Provider Selector
            st.write("")
            with st.expander("🔄 Choose a different service provider"):
                all_provs = data.PROVIDERS.get(card["profession"], [])
                prov_names = [f"{p['name']} (⭐ {p['rating']}, {p['experience_years']} yrs exp)" for p in all_provs]
                selected_prov_idx = st.selectbox(
                    "Switch provider for this job:",
                    range(len(all_provs)),
                    format_func=lambda i: prov_names[i],
                )
                if st.button("Apply New Provider"):
                    new_p = all_provs[selected_prov_idx]
                    lead_state["selected_provider_id"] = new_p["id"]
                    if card.get("lead_id"):
                        data.update_lead_provider(card["lead_id"], new_p["id"], new_p["name"])
                    lang = "hinglish" if lead_state.get("hinglish") else "english"
                    new_card = generate_reply_card(
                        card["profession"], card["job_type"], card["urgency"],
                        details.get("location", "unknown"), new_p,
                        True, language=lang
                    )
                    new_card["lead_id"] = card.get("lead_id")
                    lead_state["card"] = new_card
                    st.rerun()

            # Request Callback Button
            st.write("")
            c_btn1, c_btn2 = st.columns([1, 3])
            if c_btn1.button("📞 Request a Callback"):
                if card.get("lead_id"):
                    data.request_callback(card["lead_id"])
                    st.info("📞 **Callback Requested!** Our support desk has been notified to call the customer.")
                    lead_state["status"] = "callback_requested"

            # Formatted Customer Message Preview
            with st.expander("📱 WhatsApp / SMS Ready Message Preview"):
                st.code(card["summary_text"], language="markdown")


# -------------------------------------------------------------------------
# TAB 2: ALL LEADS & FOLLOW-UPS
# -------------------------------------------------------------------------
with tab_all:
    st.subheader(f"All Recorded Inquiries ({'All' if selected_profession == 'All' else data.CATALOG.get(selected_profession, {}).get('title', selected_profession)})")

    # Follow-up Action
    c_f1, c_f2 = st.columns([2, 1])
    with c_f1:
        st.write("Simulate 1 day passing to trigger automated follow-up nudges for unbooked quoted leads:")
    with c_f2:
        if st.button("⏩ Fast-forward 1 Day (Send Follow-ups)", type="primary"):
            with st.spinner("Generating templated follow-ups..."):
                sent = run_followups()
            if not sent:
                st.info("No leads currently need a follow-up.")
            else:
                for lid, f_text in sent:
                    st.success(f"**Follow-up sent for Lead #{lid}:** {f_text}")

    st.write("")
    leads = data.get_leads_by_profession(selected_profession)

    if not leads:
        st.info("No leads found for this filter.")
    else:
        for l in leads:
            status_val = l.get('status') or 'quoted'
            status_class = f"badge-{status_val}"
            profession = l.get('profession')

            if isinstance(profession, str) and profession.strip():
                clean_prof = profession.strip()
                prof_title = data.CATALOG.get(clean_prof, {}).get('title') or clean_prof.title()
            else:
                prof_title = "Unknown"

            status_text = status_val.replace('_', ' ').upper()
            location_text = l.get('location') or 'Unknown'

            with st.expander(f"Lead #{l['id']} • {prof_title} • Status: {status_text} • {location_text}"):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**Customer Message:** *\"{l.get('message', '')}\"*")
                    st.write(f"**Job Type:** `{l.get('job_type')}` | **Urgency:** `{l.get('urgency')}` | **Score:** `{l.get('lead_score')}`")
                    if l.get('provider_name'):
                        st.write(f"**Assigned Provider:** {l['provider_name']}")
                    if l.get('booked_slot'):
                        st.success(f"**Booked Slot:** 📌 {l['booked_slot']}")
                    if l.get('reply'):
                        st.info(f"**Agent Reply:**\n\n{l['reply']}")
                with col_b:
                    st.markdown(f"<span class='{status_class}'>{status_text}</span>", unsafe_allow_html=True)
                    st.write(f"⏱️ **Process Time:** {l.get('processing_time', 0.0)}s")
                    st.write(f"📬 **Follow-ups:** {l.get('followups_sent', 0)} / 3")
                    st.caption(f"Created: {l.get('created_at', 'Just now')}")