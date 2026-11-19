import os
import json
import time
from typing import Literal
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
import data

# Load environment variables from .env file
load_dotenv()

# Read configuration from .env; default to the fastest, most reliable model
API_KEY = os.getenv("GEMINI_API_KEY")
raw_model = os.getenv("MODEL", "gemini-3.5-flash-lite")
MODEL_NAME = raw_model.strip().lower().replace(" ", "-") if raw_model else "gemini-3.5-flash-lite"

# Initialize Gemini client
client = genai.Client(api_key=API_KEY) if API_KEY else genai.Client()


# -------------------------------------------------------------
# 5. RETRY & RESILIENCE: Retries on 503/rate limits with fallback
# -------------------------------------------------------------
def call_gemini_with_retry(fn, max_retries=3, delay_seconds=1.5):
    """Retries a Gemini call up to 3 times with a short pause if transient errors occur."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            err_str = str(e).lower()
            # If 503 unavailable or rate limited, wait briefly and retry
            if ("503" in err_str or "unavailable" in err_str or "429" in err_str) and attempt < max_retries - 1:
                time.sleep(delay_seconds * (attempt + 1))
                continue
            raise e


# -------------------------------------------------------------
# 2. TOOLS FOR GEMINI: Functions Gemini calls to fetch live data
# -------------------------------------------------------------
def lookup_price(job_type: str) -> dict:
    """Look up the official price range in INR for a plumbing job type.
    Allowed job types: leak_repair, drain_cleaning, tap_replacement, water_heater_install.
    """
    return data.get_price(job_type)


def list_free_slots() -> list:
    """Get the list of currently available appointment time slots for plumbing."""
    return data.get_free_slots()


# -------------------------------------------------------------
# 1. QUALIFIER: Understands lead details and returns JSON
# -------------------------------------------------------------
class LeadQualification(BaseModel):
    job_type: Literal[
        "leak_repair",
        "drain_cleaning",
        "tap_replacement",
        "water_heater_install",
        "unknown",
    ]
    urgency: str
    location: str
    lead_score: Literal["hot", "warm", "junk"]
    confidence: float


def qualify_lead(message: str) -> dict:
    """Asks Gemini to analyze customer message and return structured JSON."""
    prompt = (
        "You are an assistant for a local plumbing business in India.\n"
        "Analyze the following incoming customer message and classify it:\n"
        "- job_type: one of 'leak_repair', 'drain_cleaning', 'tap_replacement', 'water_heater_install', or 'unknown'.\n"
        "- urgency: customer's timeline (e.g. 'today', 'emergency', 'this week', 'low').\n"
        "- location: customer location or city mentioned (or 'unknown').\n"
        "- lead_score: 'hot' (urgent/ready to book), 'warm' (interested/inquiring), or 'junk' (spam, greeting with no request, unrelated).\n"
        "- confidence: a float from 0.0 to 1.0 indicating confidence in this classification.\n\n"
        f"Customer message: \"{message}\""
    )

    def _call():
        return client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LeadQualification,
                temperature=0.1,
            ),
        )

    response = call_gemini_with_retry(_call)
    raw_text = response.text.strip() if response.text else "{}"

    # Remove markdown code formatting if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

    return json.loads(raw_text)


# -------------------------------------------------------------
# 2. QUOTER: Uses Gemini function calling with the two tools
# -------------------------------------------------------------
def quote_lead(message: str, job_type: str) -> str:
    """Uses Gemini with function calling to look up real prices and free slots,
    then writes a friendly quote message.
    """
    prompt = (
        f"Customer message: \"{message}\"\n"
        f"Identified job type: \"{job_type}\"\n\n"
        "Instructions:\n"
        "1. Immediately call 'lookup_price' to find the official price range in INR.\n"
        "2. Immediately call 'list_free_slots' to find currently available appointment slots.\n"
        "3. Write a short, friendly quote message for the customer (ready for WhatsApp/SMS).\n\n"
        "Rules:\n"
        "- Prices MUST come strictly from the lookup_price tool. Never invent prices.\n"
        "- State the exact INR price range (e.g. ₹800 - ₹2500).\n"
        "- Suggest the available appointment slots so the customer can pick one."
    )

    def _call():
        chat = client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                tools=[lookup_price, list_free_slots],
                temperature=0.2,
            ),
        )
        return chat.send_message(prompt)

    response = call_gemini_with_retry(_call)
    return response.text.strip() if response.text else ""


# -------------------------------------------------------------
# 4. SAFETY RULES & MAIN LEAD HANDLER
# -------------------------------------------------------------
def handle_lead(message: str):
    """Processes an incoming customer lead end-to-end:
    1. Qualifies the lead with Gemini.
    2. Applies safety rules:
       - Junk leads get no reply.
       - Confidence < 0.6 or unknown job_type becomes status 'needs_human'.
    3. If valid, uses Gemini tools to generate an accurate price quote and slot options.
    4. Saves to database and returns (details, status, reply).
    """
    try:
        # Step 1: Qualify lead
        details = qualify_lead(message)
        job_type = details.get("job_type", "").strip().lower().replace(" ", "_")
        lead_score = details.get("lead_score", "").strip().lower()
        confidence = float(details.get("confidence", 0.0))

        # Step 4: Safety rule A - junk leads get no reply
        if lead_score == "junk":
            status = "junk"
            reply = ""
            data.save_lead(message, details, status, reply)
            return details, status, reply

        # Step 4: Safety rule B - confidence < 0.6 or unknown job_type becomes "needs_human"
        if confidence < 0.6 or job_type == "unknown" or job_type not in data.PRICES:
            status = "needs_human"
            reply = ""
            data.save_lead(message, details, status, reply)
            return details, status, reply

        # Step 2: Quoter using Gemini function calling
        reply = quote_lead(message, job_type)
        status = "quoted"
        data.save_lead(message, details, status, reply)
        return details, status, reply

    except Exception as e:
        error_details = {"error": str(e), "message": message}
        return error_details, "error", f"Error processing lead: {str(e)}"


# -------------------------------------------------------------
# 3. FOLLOW-UP WRITER: Gentle nudge -> Reminder -> Last check-in
# -------------------------------------------------------------
def run_followups() -> list:
    """Finds leads with status 'quoted' and fewer than 3 follow-ups,
    and writes the appropriate follow-up message using Gemini:
    - Follow-up 1: gentle nudge
    - Follow-up 2: reminder
    - Follow-up 3: last check-in
    """
    pending = data.get_leads_needing_followup()
    results = []

    for lead_id, original_message, followups_sent in pending:
        followup_stage = followups_sent + 1

        if followup_stage == 1:
            stage_instruction = (
                "Write a gentle nudge asking if they still need help with their plumbing issue. "
                "Keep it polite and short (1-2 sentences, WhatsApp style)."
            )
        elif followup_stage == 2:
            stage_instruction = (
                "Write a friendly reminder about their plumbing quote and available appointment slots. "
                "Ask which time works best for them (1-2 sentences)."
            )
        else:
            stage_instruction = (
                "Write a courteous 'last check-in' note. Let them know this is the final check-in "
                "before releasing the slot reservation, and ask if they'd like to proceed (1-2 sentences)."
            )

        prompt = (
            f"Original customer inquiry: \"{original_message}\"\n"
            f"Follow-up number: {followup_stage} of 3\n"
            f"Goal: {stage_instruction}"
        )

        def _call(p=prompt):
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=p,
                config=types.GenerateContentConfig(temperature=0.3),
            )

        response = call_gemini_with_retry(_call)
        followup_text = response.text.strip() if response.text else ""

        data.mark_followup_sent(lead_id)
        results.append((lead_id, followup_text))

    return results
