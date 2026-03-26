#!/usr/bin/env python3
"""
Local test for Pune (PUN) DC sequence number generation.
Uses LocalSequenceGenerator only — does NOT touch GitHub or Google Sheets.
"""

import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.dc_sequence_manager import DCSequenceManager, LocalSequenceGenerator

PASS = "✅ PASS"
FAIL = "❌ FAIL"

def make_manager_with_local_gen(initial_sequences: dict) -> DCSequenceManager:
    """Build a DCSequenceManager wired to a temp LocalSequenceGenerator."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(initial_sequences, f)
        tmp_path = f.name

    manager = DCSequenceManager.__new__(DCSequenceManager)
    manager.generator = LocalSequenceGenerator(state_file=tmp_path)
    manager.company_codes = {'AMOLAKCHAND': 'AK', 'BODEGA': 'BD', 'SOURCINGBEE': 'SB'}
    manager.facility_codes = {
        'Sutlej/Gomati': 'SG',
        'Arihant': 'AH',
        'Vikrant': 'AH',
        'FC-Hyderabad': 'HYD',
        'Hyderabad': 'HYD',
        'FC-Pune': 'PUN',
        'Pune': 'PUN',
    }
    manager.telangana_hubs = ['ATP', 'BAL', 'BVG', 'KMP', 'NCH', 'SAN', 'SGR']
    manager.pune_hubs = ['TLW', 'PSL']
    manager.reserved_numbers = {}
    return manager, tmp_path


def run_tests():
    print("=" * 60)
    print("PUNE DC SEQUENCE — LOCAL TEST")
    print("=" * 60)

    results = []

    # ── Test 1: Facility code mapping ────────────────────────────
    print("\n── Test 1: Facility code mapping")
    manager, tmp = make_manager_with_local_gen({'bddcpuntlw_seq': 0, 'bddcpunpsl_seq': 0})
    for name, expected in [('FC-Pune', 'PUN'), ('Pune', 'PUN'), ('FC-Hyderabad', 'HYD')]:
        got = manager.facility_codes.get(name)
        ok = got == expected
        print(f"  {PASS if ok else FAIL}  facility_codes['{name}'] = '{got}' (expected '{expected}')")
        results.append(ok)
    os.unlink(tmp)

    # ── Test 2: Hub code extraction ───────────────────────────────
    print("\n── Test 2: Hub code extraction")
    manager, tmp = make_manager_with_local_gen({'bddcpuntlw_seq': 0, 'bddcpunpsl_seq': 0})
    for hub_value, expected in [('PUN_TLW', 'TLW'), ('PUN_PSL', 'PSL'), ('HYD_NCH', 'NCH')]:
        got = manager._extract_hub_code(hub_value)
        ok = got == expected
        print(f"  {PASS if ok else FAIL}  _extract_hub_code('{hub_value}') = '{got}' (expected '{expected}')")
        results.append(ok)
    os.unlink(tmp)

    # ── Test 3: First DC for BDDCPUNTLW = 000001 ─────────────────
    print("\n── Test 3: First DC number — BDDCPUNTLW (starts at 0)")
    manager, tmp = make_manager_with_local_gen({'bddcpuntlw_seq': 0, 'bddcpunpsl_seq': 0})
    dc = manager.generate_dc_number('BODEGA', 'FC-Pune', 'PUN_TLW')
    expected = 'BDDCPUNTLW000001'
    ok = dc == expected
    print(f"  {PASS if ok else FAIL}  generate_dc_number('BODEGA','FC-Pune','PUN_TLW') = '{dc}' (expected '{expected}')")
    results.append(ok)
    os.unlink(tmp)

    # ── Test 4: First DC for BDDCPUNPSL = 000001 ─────────────────
    print("\n── Test 4: First DC number — BDDCPUNPSL (starts at 0)")
    manager, tmp = make_manager_with_local_gen({'bddcpuntlw_seq': 0, 'bddcpunpsl_seq': 0})
    dc = manager.generate_dc_number('BODEGA', 'Pune', 'PUN_PSL')
    expected = 'BDDCPUNPSL000001'
    ok = dc == expected
    print(f"  {PASS if ok else FAIL}  generate_dc_number('BODEGA','Pune','PUN_PSL') = '{dc}' (expected '{expected}')")
    results.append(ok)
    os.unlink(tmp)

    # ── Test 5: Sequence increments correctly ─────────────────────
    print("\n── Test 5: Sequential increment (000001 → 000002 → 000003)")
    manager, tmp = make_manager_with_local_gen({'bddcpuntlw_seq': 0})
    dcs = [manager.generate_dc_number('BODEGA', 'FC-Pune', 'PUN_TLW') for _ in range(3)]
    expected_seq = ['BDDCPUNTLW000001', 'BDDCPUNTLW000002', 'BDDCPUNTLW000003']
    ok = dcs == expected_seq
    print(f"  {PASS if ok else FAIL}  Generated: {dcs}")
    results.append(ok)
    os.unlink(tmp)

    # ── Test 6: reserve_dc_number also works ─────────────────────
    print("\n── Test 6: reserve_dc_number produces correct format")
    manager, tmp = make_manager_with_local_gen({'bddcpuntlw_seq': 0})
    dc = manager.reserve_dc_number('BODEGA', 'FC-Pune', 'PUN_TLW')
    expected = 'BDDCPUNTLW000001'
    ok = dc == expected
    print(f"  {PASS if ok else FAIL}  reserve_dc_number('BODEGA','FC-Pune','PUN_TLW') = '{dc}' (expected '{expected}')")
    results.append(ok)
    os.unlink(tmp)

    # ── Test 7: HYD still works (no regression) ──────────────────
    print("\n── Test 7: HYD regression — BDDCHYDNCH still works")
    manager, tmp = make_manager_with_local_gen({'bddchydnch_seq': 755})
    dc = manager.generate_dc_number('BODEGA', 'FC-Hyderabad', 'HYD_NCH')
    expected = 'BDDCHYDNCH000756'
    ok = dc == expected
    print(f"  {PASS if ok else FAIL}  generate_dc_number('BODEGA','FC-Hyderabad','HYD_NCH') = '{dc}' (expected '{expected}')")
    results.append(ok)
    os.unlink(tmp)

    # ── Test 8: DC number length ≤ 16 chars ───────────────────────
    print("\n── Test 8: DC number length ≤ 16 characters")
    manager, tmp = make_manager_with_local_gen({'bddcpuntlw_seq': 0, 'bddcpunpsl_seq': 0})
    for hub in ['PUN_TLW', 'PUN_PSL']:
        dc = manager.generate_dc_number('BODEGA', 'FC-Pune', hub)
        ok = len(dc) <= 16
        print(f"  {PASS if ok else FAIL}  '{dc}' length = {len(dc)} (max 16)")
        results.append(ok)
    os.unlink(tmp)

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULT: {passed}/{total} tests passed")
    if passed == total:
        print("✅ All tests passed — safe to push to GitHub")
    else:
        print("❌ Some tests failed — review before pushing")
    print("=" * 60)

    return passed == total


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
