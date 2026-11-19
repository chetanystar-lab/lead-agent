from agent import handle_lead

# Test incoming customer message
message = "my kitchen tap is leaking badly, need someone today in Gurugram Sector 45"

print("=" * 60)
print(f"PROCESSING LEAD: \"{message}\"")
print("=" * 60)

details, status, card, elapsed = handle_lead(message)

print(f"\n⚡ Response Time: {elapsed} seconds")
print(f"Status        : {status}")
print(f"Profession    : {details.get('profession')}")
print(f"Job Type      : {details.get('job_type')}")
print(f"Location      : {details.get('location')}")
print(f"Urgency       : {details.get('urgency')}")
print(f"Lead Score    : {details.get('lead_score')}")
print(f"Confidence    : {details.get('confidence')}")

if card:
    print("\n--- NEW SHORT CARD REPLY ---")
    print(f"Provider      : {card['provider_name']} (⭐ {card['provider_rating']}, {card['provider_exp']} yrs exp)")
    print(f"Available     : {card['location_display']}")
    print(f"Price Range   : ₹{card['price_min']} - ₹{card['price_max']} (+ ₹{card['visiting_charge']} visiting)")
    print(f"Est. Arrival  : {card['arrival_est']}")
    print(f"Available Slots: {', '.join(card['slots'])}")
    print("\nFormatted WhatsApp/SMS Message:")
    print(card['summary_text'])

print("=" * 60)
