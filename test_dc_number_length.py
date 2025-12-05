#!/usr/bin/env python3
"""
Test DC number length to ensure it fits within 16 character limit
"""

# Test all possible combinations

test_cases = [
    # (company, facility, hub, expected_prefix_length, description)
    ("AK", "AH", None, 6, "AK + DC + AH (no hub)"),
    ("AK", "SG", None, 6, "AK + DC + SG (no hub)"),
    ("AK", "HYD", None, 7, "AK + DC + HYD (no hub)"),
    ("AK", "HYD", "NCH", 10, "AK + DC + HYD + NCH (with hub)"),
    ("AK", "HYD", "BAL", 10, "AK + DC + HYD + BAL (with hub)"),
    ("AK", "HYD", "BVG", 10, "AK + DC + HYD + BVG (with hub)"),
    ("BD", "HYD", "NCH", 10, "BD + DC + HYD + NCH (with hub)"),
    ("SB", "HYD", "NCH", 10, "SB + DC + HYD + NCH (with hub)"),
]

print("=" * 70)
print("DC NUMBER LENGTH VERIFICATION")
print("=" * 70)
print("\nFormat: {Company}DC{Facility}{Hub}{Sequence}")
print("Sequence digits: 6 (range: 1 to 999,999)")
print("Max total length: 16 characters")
print()

all_passed = True
max_length = 0
max_case = None

for company, facility, hub, expected_prefix_len, description in test_cases:
    if hub:
        prefix = f"{company}DC{facility}{hub}"
    else:
        prefix = f"{company}DC{facility}"
    
    # Simulate with max sequence (999999)
    dc_number = f"{prefix}999999"
    length = len(dc_number)
    
    status = "✅" if length <= 16 else "❌"
    if length > 16:
        all_passed = False
    
    if length > max_length:
        max_length = length
        max_case = description
    
    print(f"{status} {description:40s} | Example: {dc_number:20s} | Length: {length:2d}")
    
    # Verify prefix length
    if len(prefix) != expected_prefix_len:
        print(f"   ⚠️  Warning: Expected prefix length {expected_prefix_len}, got {len(prefix)}")

print()
print("=" * 70)

if all_passed:
    print("✅ ALL TESTS PASSED - All DC numbers fit within 16 characters!")
else:
    print("❌ SOME TESTS FAILED - Some DC numbers exceed 16 characters!")

print(f"\n📊 Statistics:")
print(f"   Longest DC number: {max_length} chars ({max_case})")
print(f"   Character limit: 16")
print(f"   Margin: {16 - max_length} chars")

print()
print("=" * 70)

