import sqlite3
import json
import time

# -------------------------------------------------------------------------
# 1. PROFESSIONS, JOBS & VISITING CHARGES (INR)
# -------------------------------------------------------------------------
CATALOG = {
    "plumber": {
        "title": "Plumber",
        "visiting_charge": 199,
        "jobs": {
            "leak_repair": {"title": "Pipe / Tap Leak Repair", "min": 800, "max": 2500},
            "drain_cleaning": {"title": "Drain & Clog Cleaning", "min": 500, "max": 1500},
            "tap_replacement": {"title": "Tap & Mixer Replacement", "min": 300, "max": 900},
            "water_heater_install": {"title": "Geyser / Water Heater Install", "min": 3000, "max": 7000},
        },
    },
    "electrician": {
        "title": "Electrician",
        "visiting_charge": 149,
        "jobs": {
            "short_circuit_repair": {"title": "Short Circuit & Tripping Repair", "min": 600, "max": 1800},
            "wiring_installation": {"title": "Home Wiring & Re-wiring", "min": 1200, "max": 4500},
            "switchboard_repair": {"title": "Switchboard & Socket Repair", "min": 350, "max": 950},
            "fan_installation": {"title": "Ceiling Fan / Exhaust Install", "min": 250, "max": 600},
        },
    },
    "carpenter": {
        "title": "Carpenter",
        "visiting_charge": 199,
        "jobs": {
            "door_lock_repair": {"title": "Door Lock & Handle Repair", "min": 400, "max": 1200},
            "furniture_assembly": {"title": "Bed / Table Furniture Assembly", "min": 800, "max": 2500},
            "cupboard_repair": {"title": "Wardrobe & Drawer Hinge Repair", "min": 900, "max": 2800},
            "wood_polishing": {"title": "Wood Sanding & Polishing", "min": 1500, "max": 5000},
        },
    },
    "painter": {
        "title": "Painter",
        "visiting_charge": 199,
        "jobs": {
            "wall_touchup": {"title": "Wall Patch & Touchup Painting", "min": 800, "max": 2200},
            "room_painting": {"title": "Single Room Interior Painting", "min": 3500, "max": 9000},
            "waterproofing": {"title": "Ceiling Seepage & Waterproofing", "min": 2500, "max": 8000},
            "stencil_art": {"title": "Accent Wall & Stencil Texture", "min": 1800, "max": 4500},
        },
    },
    "ac_technician": {
        "title": "AC Technician",
        "visiting_charge": 249,
        "jobs": {
            "ac_servicing": {"title": "Split / Window AC Deep Cleaning", "min": 599, "max": 1299},
            "gas_refill": {"title": "AC Gas Leakage & Refill", "min": 1800, "max": 3200},
            "cooling_issue": {"title": "Low Cooling & Coil Diagnosis", "min": 799, "max": 2199},
            "compressor_repair": {"title": "Compressor & Capacitor Replacement", "min": 2500, "max": 6500},
        },
    },
    "home_cleaner": {
        "title": "Home Cleaner",
        "visiting_charge": 99,
        "jobs": {
            "deep_cleaning": {"title": "Full House Deep Cleaning", "min": 2199, "max": 5499},
            "bathroom_cleaning": {"title": "Intense Bathroom Cleaning", "min": 599, "max": 1499},
            "kitchen_cleaning": {"title": "Degreasing Kitchen Deep Clean", "min": 999, "max": 2499},
            "sofa_shampooing": {"title": "Sofa & Upholstery Shampooing", "min": 799, "max": 1899},
        },
    },
    "pest_control": {
        "title": "Pest Control",
        "visiting_charge": 149,
        "jobs": {
            "cockroach_control": {"title": "Cockroach & Ant Gel Treatment", "min": 899, "max": 1999},
            "termite_treatment": {"title": "Wood & Wall Termite Shield", "min": 2500, "max": 6500},
            "bedbug_treatment": {"title": "Two-Visit Bedbug Eradication", "min": 1499, "max": 3499},
            "rodent_control": {"title": "Rat & Rodent Repellent Traps", "min": 1199, "max": 2499},
        },
    },
    "appliance_repair": {
        "title": "Appliance Repair",
        "visiting_charge": 199,
        "jobs": {
            "washing_machine_repair": {"title": "Front/Top Load Washing Machine", "min": 600, "max": 2200},
            "refrigerator_repair": {"title": "Single/Double Door Refrigerator", "min": 750, "max": 2800},
            "microwave_repair": {"title": "Microwave Magnetron & Heating", "min": 450, "max": 1600},
            "ro_water_purifier": {"title": "RO Water Purifier Filter & Motor", "min": 499, "max": 1599},
        },
    },
}

# -------------------------------------------------------------------------
# 2. SERVICE PROVIDERS PER PROFESSION
# -------------------------------------------------------------------------
PROVIDERS = {
    "plumber": [
        {
            "id": "plumber_1",
            "name": "Ramesh Sharma",
            "rating": 4.9,
            "experience_years": 9,
            "areas": ["Sector 14", "Sector 29", "Sector 45", "DLF Phase 1", "DLF Phase 4", "Gurugram", "Dwarka"],
            "slots": ["Today 2:30 PM", "Today 5:00 PM", "Tomorrow 10:00 AM", "Tomorrow 3:00 PM"],
        },
        {
            "id": "plumber_2",
            "name": "Vikram Singh",
            "rating": 4.8,
            "experience_years": 6,
            "areas": ["Sector 56", "Sector 57", "Sohna Road", "Golf Course Road", "Cyber City", "Vasant Kunj"],
            "slots": ["Today 4:00 PM", "Tomorrow 11:30 AM", "Tomorrow 2:00 PM", "Tomorrow 5:30 PM"],
        },
        {
            "id": "plumber_3",
            "name": "Sunil Yadav",
            "rating": 4.7,
            "experience_years": 11,
            "areas": ["Sector 31", "Sushant Lok", "DLF Phase 2", "DLF Phase 3", "South Extension", "Noida Sector 62"],
            "slots": ["Today 3:30 PM", "Tomorrow 9:00 AM", "Tomorrow 1:00 PM"],
        },
    ],
    "electrician": [
        {
            "id": "electrician_1",
            "name": "Anil Verma",
            "rating": 4.9,
            "experience_years": 8,
            "areas": ["Sector 45", "Sector 56", "DLF Phase 3", "Golf Course Road", "Gurugram", "Dwarka"],
            "slots": ["Today 2:00 PM", "Today 4:30 PM", "Tomorrow 10:00 AM", "Tomorrow 4:00 PM"],
        },
        {
            "id": "electrician_2",
            "name": "Mohd. Rizwan",
            "rating": 4.8,
            "experience_years": 10,
            "areas": ["Sector 14", "Sector 29", "DLF Phase 1", "Cyber City", "Vasant Kunj", "Saket"],
            "slots": ["Today 3:00 PM", "Tomorrow 11:00 AM", "Tomorrow 2:30 PM"],
        },
        {
            "id": "electrician_3",
            "name": "Pradeep Kumar",
            "rating": 4.7,
            "experience_years": 5,
            "areas": ["Sohna Road", "Sector 57", "Sushant Lok", "Noida Sector 62", "South Extension"],
            "slots": ["Today 5:00 PM", "Tomorrow 9:30 AM", "Tomorrow 3:30 PM"],
        },
    ],
    "carpenter": [
        {
            "id": "carpenter_1",
            "name": "Harish Mistry",
            "rating": 4.9,
            "experience_years": 12,
            "areas": ["DLF Phase 1", "DLF Phase 2", "Sector 29", "Sector 45", "Gurugram", "South Extension"],
            "slots": ["Today 3:00 PM", "Tomorrow 10:00 AM", "Tomorrow 2:00 PM"],
        },
        {
            "id": "carpenter_2",
            "name": "Kuldeep Jangid",
            "rating": 4.8,
            "experience_years": 7,
            "areas": ["Sector 56", "Sector 57", "Sohna Road", "Golf Course Road", "Dwarka", "Vasant Kunj"],
            "slots": ["Today 4:30 PM", "Tomorrow 11:30 AM", "Tomorrow 4:00 PM"],
        },
    ],
    "painter": [
        {
            "id": "painter_1",
            "name": "Manoj Tiwari",
            "rating": 4.9,
            "experience_years": 10,
            "areas": ["DLF Phase 4", "Sector 45", "Sector 56", "Cyber City", "Gurugram", "Dwarka"],
            "slots": ["Today 4:00 PM", "Tomorrow 10:00 AM", "Tomorrow 2:00 PM"],
        },
        {
            "id": "painter_2",
            "name": "Dharmendra Pal",
            "rating": 4.7,
            "experience_years": 6,
            "areas": ["Sector 14", "Sector 29", "Sohna Road", "Sushant Lok", "Noida Sector 62"],
            "slots": ["Today 5:30 PM", "Tomorrow 11:00 AM", "Tomorrow 3:30 PM"],
        },
    ],
    "ac_technician": [
        {
            "id": "ac_1",
            "name": "Imran Khan",
            "rating": 4.9,
            "experience_years": 9,
            "areas": ["Sector 45", "Sector 56", "DLF Phase 1", "DLF Phase 5", "Gurugram", "Noida Sector 62"],
            "slots": ["Today 2:00 PM", "Today 4:30 PM", "Tomorrow 10:30 AM", "Tomorrow 3:00 PM"],
        },
        {
            "id": "ac_2",
            "name": "Deepak Gupta",
            "rating": 4.8,
            "experience_years": 7,
            "areas": ["Sector 14", "Sector 29", "Sohna Road", "Cyber City", "Dwarka", "Vasant Kunj"],
            "slots": ["Today 3:15 PM", "Tomorrow 11:00 AM", "Tomorrow 2:00 PM", "Tomorrow 5:00 PM"],
        },
    ],
    "home_cleaner": [
        {
            "id": "cleaner_1",
            "name": "Sunita & Team",
            "rating": 4.9,
            "experience_years": 6,
            "areas": ["DLF Phase 1", "DLF Phase 4", "Sector 45", "Golf Course Road", "Gurugram", "Dwarka"],
            "slots": ["Today 3:00 PM", "Tomorrow 9:00 AM", "Tomorrow 1:30 PM"],
        },
        {
            "id": "cleaner_2",
            "name": "Pooja Cleaners",
            "rating": 4.8,
            "experience_years": 5,
            "areas": ["Sector 14", "Sector 56", "Sohna Road", "Sushant Lok", "South Extension"],
            "slots": ["Today 4:30 PM", "Tomorrow 10:30 AM", "Tomorrow 3:00 PM"],
        },
    ],
    "pest_control": [
        {
            "id": "pest_1",
            "name": "Rajesh Kumar (SafeShield)",
            "rating": 4.9,
            "experience_years": 11,
            "areas": ["DLF Phase 2", "Sector 29", "Sector 45", "Sohna Road", "Gurugram", "Dwarka"],
            "slots": ["Today 2:30 PM", "Tomorrow 10:00 AM", "Tomorrow 2:30 PM"],
        },
        {
            "id": "pest_2",
            "name": "Sanjay Bansal (PestGuard)",
            "rating": 4.8,
            "experience_years": 8,
            "areas": ["Sector 14", "Sector 56", "DLF Phase 3", "Cyber City", "Noida Sector 62"],
            "slots": ["Today 5:00 PM", "Tomorrow 11:30 AM", "Tomorrow 4:00 PM"],
        },
    ],
    "appliance_repair": [
        {
            "id": "appliance_1",
            "name": "Naresh Chawla",
            "rating": 4.9,
            "experience_years": 13,
            "areas": ["Sector 45", "Sector 56", "DLF Phase 1", "Sohna Road", "Gurugram", "Dwarka"],
            "slots": ["Today 2:00 PM", "Today 4:30 PM", "Tomorrow 10:00 AM", "Tomorrow 3:00 PM"],
        },
        {
            "id": "appliance_2",
            "name": "Mukesh Sharma",
            "rating": 4.8,
            "experience_years": 7,
            "areas": ["Sector 14", "Sector 29", "DLF Phase 4", "Cyber City", "Vasant Kunj"],
            "slots": ["Today 3:30 PM", "Tomorrow 11:00 AM", "Tomorrow 2:00 PM"],
        },
    ],
}


# -------------------------------------------------------------------------
# 3. LOCATION MATCHING ENGINE
# -------------------------------------------------------------------------
def match_provider(profession: str, location: str) -> dict:
    """Finds the best provider in the customer's area. If none covers the exact area,
    selects the highest-rated nearby provider as an alternative.
    """
    clean_prof = profession.lower().replace(" ", "_").strip()
    providers = PROVIDERS.get(clean_prof, [])
    if not providers:
        return {"matched": False, "provider": None, "available_at_location": False, "note": "No providers available"}

    clean_loc = (location or "").lower().strip()

    # Try matching location to provider service areas
    matched_providers = []
    if clean_loc and clean_loc != "unknown":
        for p in providers:
            for area in p["areas"]:
                if area.lower() in clean_loc or clean_loc in area.lower():
                    matched_providers.append(p)
                    break

    if matched_providers:
        # Pick the highest rated in that area
        best = max(matched_providers, key=lambda x: x["rating"])
        return {
            "matched": True,
            "provider": best,
            "available_at_location": True,
            "area_served": clean_loc.title(),
            "note": f"Directly covers {clean_loc.title()}",
            "all_providers": providers,
        }

    # If no direct match or location is unknown, pick the highest-rated provider overall
    fallback = max(providers, key=lambda x: x["rating"])
    return {
        "matched": True,
        "provider": fallback,
        "available_at_location": False,
        "area_served": fallback["areas"][0],
        "note": f"Closest specialist: {fallback['name']} (covers nearby {fallback['areas'][0]})",
        "all_providers": providers,
    }


def get_provider_by_id(profession: str, provider_id: str) -> dict | None:
    """Finds a provider by their unique ID."""
    clean_prof = profession.lower().replace(" ", "_").strip()
    for p in PROVIDERS.get(clean_prof, []):
        if p["id"] == provider_id:
            return p
    return None


def book_slot(provider_id: str, slot: str) -> bool:
    """Removes a booked slot from the live provider list."""
    for prof, p_list in PROVIDERS.items():
        for p in p_list:
            if p["id"] == provider_id:
                if slot in p["slots"]:
                    p["slots"].remove(slot)
                    return True
    return False


# -------------------------------------------------------------------------
# 4. SQLITE DATABASE SETUP & HELPERS
# -------------------------------------------------------------------------
db = sqlite3.connect("leads.db", check_same_thread=False)

db.execute("""CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT,
    profession TEXT,
    job_type TEXT,
    location TEXT,
    urgency TEXT,
    lead_score TEXT,
    confidence REAL,
    provider_name TEXT,
    provider_id TEXT,
    booked_slot TEXT,
    status TEXT,
    reply TEXT,
    followups_sent INTEGER DEFAULT 0,
    processing_time REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")
db.commit()

# Ensure any existing leads table gets upgraded with missing columns seamlessly
existing_cols = [c[1] for c in db.execute("PRAGMA table_info(leads)").fetchall()]
required_cols = {
    "profession": "TEXT",
    "job_type": "TEXT",
    "location": "TEXT",
    "urgency": "TEXT",
    "lead_score": "TEXT",
    "confidence": "REAL",
    "provider_name": "TEXT",
    "provider_id": "TEXT",
    "booked_slot": "TEXT",
    "processing_time": "REAL DEFAULT 0.0",
    "created_at": "TEXT",
}
for col_name, col_def in required_cols.items():
    if col_name not in existing_cols:
        db.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_def}")
db.commit()


def save_lead(data_dict: dict) -> int:
    """Saves a lead into the SQLite database."""
    cur = db.execute(
        """INSERT INTO leads (
            message, profession, job_type, location, urgency,
            lead_score, confidence, provider_name, provider_id,
            booked_slot, status, reply, followups_sent, processing_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data_dict.get("message", ""),
            data_dict.get("profession", "unknown"),
            data_dict.get("job_type", "unknown"),
            data_dict.get("location", "unknown"),
            data_dict.get("urgency", "low"),
            data_dict.get("lead_score", "warm"),
            data_dict.get("confidence", 0.0),
            data_dict.get("provider_name", ""),
            data_dict.get("provider_id", ""),
            data_dict.get("booked_slot", ""),
            data_dict.get("status", "quoted"),
            data_dict.get("reply", ""),
            data_dict.get("followups_sent", 0),
            data_dict.get("processing_time", 0.0),
        ),
    )
    db.commit()
    return cur.lastrowid


def book_lead_slot(lead_id: int, slot: str, provider_id: str) -> bool:
    """Marks a lead as booked, locks in the slot, and removes it from the provider."""
    book_slot(provider_id, slot)
    db.execute(
        "UPDATE leads SET status = 'booked', booked_slot = ? WHERE id = ?",
        (slot, lead_id),
    )
    db.commit()
    return True


def request_callback(lead_id: int) -> bool:
    """Updates lead status to callback_requested."""
    db.execute(
        "UPDATE leads SET status = 'callback_requested' WHERE id = ?",
        (lead_id,),
    )
    db.commit()
    return True


def update_lead_provider(lead_id: int, new_provider_id: str, new_provider_name: str):
    """Updates the assigned provider for a lead."""
    db.execute(
        "UPDATE leads SET provider_id = ?, provider_name = ? WHERE id = ?",
        (new_provider_id, new_provider_name, lead_id),
    )
    db.commit()


def get_leads_by_profession(profession: str = "All") -> list:
    """Fetches leads filtered by profession or All."""
    if not profession or profession == "All":
        cur = db.execute("SELECT * FROM leads ORDER BY id DESC")
    else:
        clean_prof = profession.lower().replace(" ", "_")
        cur = db.execute("SELECT * FROM leads WHERE profession = ? ORDER BY id DESC", (clean_prof,))

    cols = [col[0] for col in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_stats() -> dict:
    """Calculates top-level operational statistics."""
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM leads")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leads WHERE status = 'booked'")
    booked = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leads WHERE status = 'needs_human'")
    needs_human = cur.fetchone()[0]

    cur.execute("SELECT AVG(processing_time) FROM leads WHERE processing_time > 0")
    avg_row = cur.fetchone()[0]
    avg_time = round(avg_row, 2) if avg_row else 0.0

    # Counts by profession for sidebar
    cur.execute("SELECT profession, COUNT(*) FROM leads GROUP BY profession")
    prof_counts = dict(cur.fetchall())

    return {
        "total": total,
        "booked": booked,
        "needs_human": needs_human,
        "avg_time": avg_time,
        "prof_counts": prof_counts,
    }


def get_leads_needing_followup() -> list:
    """Fetches leads that are quoted (not booked or closed) with < 3 follow-ups."""
    cur = db.execute("""
        SELECT id, message, profession, job_type, provider_name, followups_sent, location
        FROM leads
        WHERE status = 'quoted' AND followups_sent < 3
    """)
    cols = [col[0] for col in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def mark_followup_sent(lead_id: int):
    """Increments the follow-up counter."""
    db.execute("UPDATE leads SET followups_sent = followups_sent + 1 WHERE id = ?", (lead_id,))
    db.commit()
