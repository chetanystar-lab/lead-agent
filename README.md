# ⚡ ServiceFlow: Multi-Profession Lead Recovery Agent
**Hackathon Project: Track D (Sales, Growth and Revenue Agents)**

An ultra-fast, high-converting AI Dispatch and Lead Recovery Agent for on-demand home services in Delhi NCR & Gurugram. 

---

## 🚀 Key Improvements & Architecture

1. **⚡ Ultra-Fast Single Gemini Call:**
   - **Only 1 AI Call per lead:** The **Qualifier** classifies the customer inquiry into structured JSON (`profession`, `job_type`, `urgency`, `location`, `lead_score`, `confidence`, `customer_language`) using `gemini-3.5-flash-lite`.
   - **Zero AI Latency for Quotes & Follow-ups:** Price calculation, provider matching, card generation, and follow-ups are computed **instantly in pure Python** from deterministic templates and database records.
   - **Response Time:** Drops from 15–20s down to **~1.5 to 2.5 seconds** per lead.

2. **🛠️ 8 Professions & Verified Provider Catalog (`data.py`):**
   - **Professions:** Plumber, Electrician, Carpenter, Painter, AC Technician, Home Cleaner, Pest Control, Appliance Repair.
   - Each with 3–4 specific job types, INR price ranges, and fixed visiting fees.
   - 2 to 3 service providers per profession with real ratings (⭐ 4.7–4.9), experience years, open slots for today/tomorrow, and covered NCR sectors (Gurugram Sectors, DLF Phases, Cyber City, Dwarka, Noida, etc.).
   - **Location Matching Engine:** Automatically pairs customers with the highest-rated technician directly covering their sector, or surfaces the closest top-rated alternative.

3. **💳 Clean Card Reply Format:**
   - Profession & Job Type badge
   - Matched Specialist: Name, Star rating, Years of experience
   - Location Availability: Yes/No with sector confirmation
   - Estimated Price Range in INR + fixed visiting fee
   - Estimated arrival time for urgent emergencies ("Within 45–60 minutes")
   - Next 3 open time slots with interactive **"Book this slot"** buttons
   - Interactive options: **"Request a callback"**, **"Choose a different provider"**, and **"Reply in Hinglish"** toggle.

4. **🛡️ Strict Guardrails:**
   - Junk / Spam inquiries are filtered out with zero automated reply.
   - Vague requests or low confidence (< 0.6) are routed to `needs_human`.
   - 100% of prices and slots originate strictly from verified company data in `data.py`.

5. **🖥️ Modern Dashboard UI (`app.py`):**
   - Sidebar service catalog with live lead counters and instant profession filtering.
   - Top metrics bar (Total Inquiries, Booked, Needs Human, Average Speed).
   - Quick one-click sample buttons to test without typing.
   - Tab 1: Interactive New Lead Intake & Card Booking.
   - Tab 2: All Leads Explorer with status badges & 1-day follow-up fast-forwarding.

---

## 🧪 Testing

### 1. Test Lead Agent Pipeline
Verify single-call qualification, provider matching, and sub-2-second speed:
```powershell
python test_agent.py
```

### 2. Run Comprehensive Multi-Profession Test Suite
Tests clear, Hinglish, urgent, vague, out-of-scope, and spam scenarios:
```powershell
python test_suite.py
```

---

## 🖥️ Running the Web Dashboard

Launch the Streamlit app:
```powershell
streamlit run app.py
```
Open your browser at: *[(http://localhost:8000/)** (or http://localhost:8501).
