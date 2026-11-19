import os
import json
import time
from typing import Literal
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
import data

load_dotenv()

# Read model configuration; default to the ultra-fast flash-lite model
API_KEY = os.getenv("GEMINI_API_KEY")
raw_model = os.getenv("MODEL", "gemini-3.5-flash-lite")
MODEL_NAME = raw_model.strip().lower().replace(" ", "-") if raw_model else "gemini-3.5-flash-lite"

client = genai.Client(api_key=API_KEY) if API_KEY else genai.Client()


# -------------------------------------------------------------------------
# 1. RETRY MECHANISM FOR THE SINGLE QUALIFIER CALL
# -------------------------------------------------------------------------
def call_gemini_with_retry(fn, max_retries=3, delay_seconds=1.5):
    """Retries a Gemini call if transient rate limits or 503 errors occur."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            err_str = str(e).lower()
            if ("503" in err_str or "unavailable" in err_str or "429" in err_str) and attempt < max_retries - 1:
                time.sleep(delay_seconds * (attempt + 1))
                continue
            raise e


# -------------------------------------------------------------------------
# 2. SINGLE GEMINI CALL: LEAD QUALIFIER
# -------------------------------------------------------------------------
class LeadQualifierOutput(BaseModel):
    profession: Literal[
        "plumber",
        "electrician",
        "carpenter",
        "painter",
        "ac_technician",
        "home_cleaner",
        "pest_control",
        "appliance_repair",
        "unknown",
    ]
    job_type: str
    urgency: Literal["emergency", "today", "this_week", "flexible"]
    location: str
    lead_score: Literal["hot", "warm", "junk"]
    confidence: float
    customer_language: Literal["english", "hinglish", "hindi"]


def qualify_lead(message: str) -> dict:
    """Uses exactly ONE Gemini call to parse and qualify customer intent."""
    prompt = (
        "You are an AI intake dispatcher for an on-demand home service platform in Delhi NCR / Gurugram.\n"
        "Classify the incoming customer message into strict JSON with the following rules:\n"
        "- profession: Must be one of 'plumber', 'electrician', 'carpenter', 'painter', 'ac_technician', "
        "'home_cleaner', 'pest_control', 'appliance_repair', or 'unknown'.\n"
        "- job_type: The specific issue (e.g., 'leak_repair', 'tap_replacement', 'ac_servicing', "
        "'short_circuit_repair', 'cockroach_control', etc., or 'unknown').\n"
        "- urgency: 'emergency' (flooding, sparking, gas leak), 'today', 'this_week', or 'flexible'.\n"
        "- location: Extracted Gurugram sector, Delhi NCR area (e.g. 'Sector 45', 'Dwarka', 'Noida'), or 'unknown'.\n"
        "- lead_score: 'hot' (urgent/ready to book), 'warm' (asking for price/info), or 'junk' (spam, greeting with no request, gibberish).\n"
        "- confidence: Float from 0.0 to 1.0 reflecting confidence.\n"
        "- customer_language: 'english', 'hinglish', or 'hindi'.\n\n"
        f"Customer message: \"{message}\""
    )

    def _call():
        return client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LeadQualifierOutput,
                temperature=0.1,
            ),
        )

    response = call_gemini_with_retry(_call)
    raw_text = response.text.strip() if response.text else "{}"
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

    return json.loads(raw_text)


# -------------------------------------------------------------------------
# 3. FAST TEMPLATE-BASED CARD & REPLY GENERATOR (ZERO AI LATENCY)
# -------------------------------------------------------------------------
def generate_reply_card(
    profession: str,
    job_type: str,
    urgency: str,
    location: str,
    provider: dict,
    available_at_location: bool,
    language: str = "english",
) -> dict:
    """Builds a structured reply card entirely in Python using verified catalog data."""
    prof_info = data.CATALOG.get(profession, {})
    jobs = prof_info.get("jobs", {})

    # Best-match job details
    job_info = jobs.get(job_type)
    if not job_info:
        # Match closest job key or fallback to first
        for k, v in jobs.items():
            if k in job_type or job_type in k:
                job_info = v
                job_type = k
                break
        if not job_info:
            first_key = list(jobs.keys())[0] if jobs else "general"
            job_info = jobs.get(first_key, {"title": "General Inspection", "min": 500, "max": 1500})
            job_type = first_key

    min_p = job_info.get("min", 500)
    max_p = job_info.get("max", 1500)
    visiting_charge = prof_info.get("visiting_charge", 199)
    prof_title = prof_info.get("title", profession.title())
    job_title = job_info.get("title", job_type.replace("_", " ").title())

    # Arrival estimate for urgent queries
    arrival_est = "Within 45-60 minutes" if urgency in ["emergency", "today"] else "Scheduled arrival on selected slot"

    # Up to 3 available slots
    slots = provider.get("slots", [])[:3]

    # Location text
    loc_display = location.title() if location and location != "unknown" else "your sector"
    avail_status = f"Yes ({loc_display})" if available_at_location else f"No (Nearest alternative serving: {provider['areas'][0]})"

    # Generate message text for English and Hinglish templates
    if language == "hinglish":
        summary_text = (
            f"Namaste! Aapke {job_title} ke liye humne top-rated {prof_title} "
            f"**{provider['name']}** (⭐ {provider['rating']}, {provider['experience_years']} saal ka anubhav) ko select kiya hai.\n\n"
            f"📍 **Aapki location par service:** {avail_status}\n"
            f"💰 **Estimated Price:** ₹{min_p} - ₹{max_p} (+ ₹{visiting_charge} visiting charge)\n"
            f"⏱️ **Arrival:** {arrival_est}\n\n"
            f"Kripya apna preferred slot select karke booking confirm karein:"
        )
    else:
        summary_text = (
            f"Hello! For your {job_title}, we have matched you with certified {prof_title} "
            f"**{provider['name']}** (⭐ {provider['rating']}, {provider['experience_years']} yrs exp).\n\n"
            f"📍 **Available at your location:** {avail_status}\n"
            f"💰 **Estimated Price Range:** ₹{min_p} - ₹{max_p} (+ ₹{visiting_charge} visiting charge)\n"
            f"⏱️ **Estimated Arrival:** {arrival_est}\n\n"
            f"Please select your preferred appointment slot below to confirm your booking:"
        )

    return {
        "profession": profession,
        "profession_title": prof_title,
        "job_type": job_type,
        "job_title": job_title,
        "price_min": min_p,
        "price_max": max_p,
        "visiting_charge": visiting_charge,
        "provider_name": provider.get("name", ""),
        "provider_id": provider.get("id", ""),
        "provider_rating": provider.get("rating", 4.8),
        "provider_exp": provider.get("experience_years", 5),
        "available_at_location": available_at_location,
        "location_display": avail_status,
        "urgency": urgency,
        "arrival_est": arrival_est,
        "slots": slots,
        "summary_text": summary_text,
    }


# -------------------------------------------------------------------------
# 4. MAIN LEAD DISPATCHER (1 AI CALL + INSTANT LOCAL LOGIC)
# -------------------------------------------------------------------------
def handle_lead(message: str, force_language: str | None = None) -> tuple[dict, str, dict | None, float]:
    """Processes an incoming customer lead end-to-end:
    1. Makes exactly ONE Gemini call to classify the lead.
    2. Applies safety guardrails (junk -> no reply; low confidence/unknown -> needs_human).
    3. Matches local service providers by location.
    4. Builds card & reply instantly from templates.
    5. Saves to leads.db and tracks elapsed processing time.

    Returns:
        (details_dict, status, card_dict_or_None, processing_time_seconds)
    """
    start_time = time.time()

    try:
        # Step 1: Single Gemini Qualifier call
        details = qualify_lead(message)

        profession = details.get("profession", "unknown").lower().replace(" ", "_")
        job_type = details.get("job_type", "unknown").lower().replace(" ", "_")
        urgency = details.get("urgency", "today").lower()
        location = details.get("location", "unknown")
        lead_score = details.get("lead_score", "warm").lower()
        confidence = float(details.get("confidence", 0.0))
        customer_lang = force_language or details.get("customer_language", "english")

        # Step 2: Guardrail A - Junk leads get no reply
        if lead_score == "junk":
            status = "junk"
            elapsed = round(time.time() - start_time, 2)
            data.save_lead({
                "message": message,
                "profession": profession,
                "job_type": job_type,
                "location": location,
                "urgency": urgency,
                "lead_score": lead_score,
                "confidence": confidence,
                "status": status,
                "reply": "",
                "processing_time": elapsed,
            })
            return details, status, None, elapsed

        # Step 2: Guardrail B - Unknown profession or low confidence (< 0.6)
        if confidence < 0.6 or profession == "unknown" or profession not in data.CATALOG:
            status = "needs_human"
            elapsed = round(time.time() - start_time, 2)
            data.save_lead({
                "message": message,
                "profession": profession,
                "job_type": job_type,
                "location": location,
                "urgency": urgency,
                "lead_score": lead_score,
                "confidence": confidence,
                "status": status,
                "reply": "",
                "processing_time": elapsed,
            })
            return details, status, None, elapsed

        # Step 3: Match service provider by location
        match_result = data.match_provider(profession, location)
        provider = match_result["provider"]
        available_at_loc = match_result["available_at_location"]

        # Step 4: Build response card with 0 AI latency
        card = generate_reply_card(
            profession=profession,
            job_type=job_type,
            urgency=urgency,
            location=location,
            provider=provider,
            available_at_location=available_at_loc,
            language=customer_lang,
        )

        status = "quoted"
        elapsed = round(time.time() - start_time, 2)

        lead_id = data.save_lead({
            "message": message,
            "profession": profession,
            "job_type": job_type,
            "location": location,
            "urgency": urgency,
            "lead_score": lead_score,
            "confidence": confidence,
            "provider_name": provider["name"],
            "provider_id": provider["id"],
            "status": status,
            "reply": card["summary_text"],
            "processing_time": elapsed,
        })
        card["lead_id"] = lead_id

        return details, status, card, elapsed

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        error_details = {"error": str(e), "message": message}
        return error_details, "error", None, elapsed


# -------------------------------------------------------------------------
# 5. TEMPLATE-BASED FOLLOW-UPS (ZERO AI CALLS, INSTANT)
# -------------------------------------------------------------------------
def run_followups() -> list:
    """Sends progressive follow-up messages based on templates:
    - Follow-up 1: Gentle nudge
    - Follow-up 2: Reminder of quote & slots
    - Follow-up 3: Last check-in before releasing slot
    """
    pending = data.get_leads_needing_followup()
    results = []

    for lead in pending:
        lead_id = lead["id"]
        stage = lead["followups_sent"] + 1
        prof_title = data.CATALOG.get(lead["profession"], {}).get("title", "Service")
        provider = lead["provider_name"] or "our certified specialist"

        if stage == 1:
            msg = (
                f"Hi there! Just a gentle check-in regarding your {prof_title} inquiry. "
                f"{provider} has open slots today if you'd still like assistance!"
            )
        elif stage == 2:
            msg = (
                f"Reminder: Your price estimate for {prof_title} is still active. "
                f"Would you like us to hold an appointment slot with {provider}?"
            )
        else:
            msg = (
                f"Final check-in: We are releasing reserved slots for your {prof_title} request. "
                f"Feel free to reply if you'd still like to schedule or request a callback anytime!"
            )

        data.mark_followup_sent(lead_id)
        results.append((lead_id, msg))

    return results
