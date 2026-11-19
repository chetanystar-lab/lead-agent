import time
from agent import handle_lead

test_cases = [
    ("1. Plumber (Clear)", "My kitchen sink drain is blocked and overflowing in Gurugram Sector 14, need urgent help."),
    ("2. Electrician (Hinglish)", "Bhaiya short circuit ho gaya hai switchboard me aur sparks aa rahe hain, Dwarka me koi bhej do."),
    ("3. AC Technician (Urgent)", "My split AC is blowing warm air and not cooling at all in Sector 56."),
    ("4. Pest Control", "Need cockroach and ant gel treatment for my 2BHK apartment in DLF Phase 2."),
    ("5. Vague", "Hello, I need some repair work done at my home."),
    ("6. Out of Scope", "Can you deliver groceries and cook dinner for my family tonight?"),
    ("7. Spam", "CONGRATULATIONS! Claim your ₹50,000 cash prize instantly at bit.ly/spam-gift!"),
]

print("=" * 70)
print("RUNNING MULTI-PROFESSION BENCHMARK SUITE")
print("=" * 70)

total_start = time.time()
for name, msg in test_cases:
    t0 = time.time()
    details, status, card, elapsed = handle_lead(msg)
    
    print(f"\n[{name}] -> {elapsed}s | Status: {status}")
    print(f"  Profession: {details.get('profession')} | Job: {details.get('job_type')} | Loc: {details.get('location')}")
    if card:
        print(f"  Matched: {card['provider_name']} (⭐ {card['provider_rating']}) | Price: ₹{card['price_min']}-₹{card['price_max']} + ₹{card['visiting_charge']} visiting")
        print(f"  Location Match: {card['location_display']} | Arrival: {card['arrival_est']}")
    else:
        print(f"  Guardrail triggered: No automated quote sent ({status})")

total_duration = round(time.time() - total_start, 2)
print("\n" + "=" * 70)
print(f"COMPLETED ALL 7 TESTS IN {total_duration}s TOTAL!")
print("=" * 70)
