from pricing_engine import decide_optimal_price

print("=== Test 1: Normal case — competitor above floor ===")
r = decide_optimal_price(15.00, 20.0, 45.00, 29.99, [51.77, 53.74, 50.10])
print(f"Recommended: £{r['recommended_price']} | Reason: {r['decision_reason']}\n")

print("=== Test 2: Competitor below our floor ===")
r = decide_optimal_price(15.00, 20.0, 45.00, 29.99, [16.00, 17.50])
print(f"Recommended: £{r['recommended_price']} | Reason: {r['decision_reason']}\n")

print("=== Test 3: Target exceeds max price ceiling ===")
r = decide_optimal_price(15.00, 20.0, 45.00, 29.99, [55.00, 60.00])
print(f"Recommended: £{r['recommended_price']} | Reason: {r['decision_reason']}\n")

print("=== Test 4: No competitor prices available ===")
r = decide_optimal_price(15.00, 20.0, 45.00, 29.99, [])
print(f"Recommended: £{r['recommended_price']} | Reason: {r['decision_reason']}\n")