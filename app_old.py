import streamlit as st
from agent import handle_lead, run_followups
import data

# Page setup
st.set_page_config(page_title="Lead Recovery Agent", page_icon="🔧")
st.title("🔧 Plumbing Lead Recovery Agent")
st.write(
    "Paste a customer message. The agent will understand it, quote real prices using tools, "
    "offer free time slots, and later follow up if the customer goes quiet."
)

# Text box for incoming lead
message = st.text_area(
    "Incoming customer message",
    placeholder="e.g. my kitchen tap is leaking badly, need someone today in Gurugram",
    height=110,
)

# Button to process the lead
if st.button("Process lead", type="primary"):
    if not message.strip():
        st.warning("Please type a message first.")
    else:
        with st.spinner("The agent is analyzing the message and looking up prices..."):
            details, status, reply = handle_lead(message)

        st.subheader("1. What the agent understood")
        st.json(details)

        st.subheader("2. Status")
        st.write(f"Status: **{status}**")

        st.subheader("3. Reply to the customer")
        if reply:
            st.info(reply)
        elif status == "junk":
            st.warning("No reply sent (lead identified as junk/spam).")
        elif status == "needs_human":
            st.warning("Flagged for human review (confidence below threshold or unknown job type).")
        else:
            st.write("No automated reply.")

st.divider()

# Follow-up simulation button
st.subheader("Follow-up Automation")
st.write("Simulate 1 day passing to trigger follow-up messages for quoted leads.")

if st.button("Fast-forward 1 day (send follow-ups)"):
    with st.spinner("Writing follow-up messages..."):
        sent = run_followups()

    if not sent:
        st.info("No leads need a follow-up right now.")
    else:
        for lead_id, text in sent:
            st.success(f"**Follow-up sent for Lead #{lead_id}:**\n\n{text}")

st.divider()

# Table showing all leads in the database
st.subheader("All leads so far")
rows = data.get_all_leads()
if rows:
    st.table(rows)
else:
    st.write("No leads yet.")
