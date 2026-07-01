from decimal import Decimal, ROUND_HALF_UP


def calculate_price_floor(our_cost, min_margin_percent):
    """
    Calculate the minimum price we can charge while
    maintaining our required profit margin.

    Example:
        cost = 15.00, min_margin = 20%
        floor = 15.00 * 1.20 = 18.00
    """
    cost = Decimal(str(our_cost))
    margin = Decimal(str(min_margin_percent)) / Decimal("100")
    floor = cost * (1 + margin)

    return floor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_target_price(competitor_prices, undercut_percent=2.0):
    """
    Given a list of competitor prices, find the lowest one
    and undercut it by undercut_percent.

    Returns None if no valid competitor prices provided.
    """
    if not competitor_prices:
        return None

    valid_prices = [p for p in competitor_prices if p and p > 0]

    if not valid_prices:
        return None

    lowest = Decimal(str(min(valid_prices)))
    undercut = Decimal(str(undercut_percent)) / Decimal("100")
    target = lowest * (1 - undercut)

    return target.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def decide_optimal_price(our_cost, min_margin_percent, max_price,
                          current_price, competitor_prices,
                          undercut_percent=2.0):
    """
    Core pricing decision function.
    Returns a dict with the recommended price and full reasoning.
    """
    result = {
        "recommended_price": None,
        "price_floor": None,
        "target_price": None,
        "lowest_competitor": None,
        "decision_reason": None,
        "action_needed": False,
    }

    floor = calculate_price_floor(our_cost, min_margin_percent)
    result["price_floor"] = float(floor)

    target = calculate_target_price(competitor_prices, undercut_percent)

    if target is None:
        result["decision_reason"] = "No valid competitor prices available. Keeping current price."
        result["recommended_price"] = float(current_price)
        return result

    result["target_price"] = float(target)
    result["lowest_competitor"] = float(min(competitor_prices))

    if target < floor:
        result["recommended_price"] = float(floor)
        result["decision_reason"] = (
            f"Target £{target} is below margin floor £{floor}. "
            f"Setting price to floor."
        )

    elif max_price and target > Decimal(str(max_price)):
        result["recommended_price"] = float(max_price)
        result["decision_reason"] = (
            f"Target £{target} exceeds max price £{max_price}. "
            f"Setting price to ceiling."
        )

    else:
        result["recommended_price"] = float(target)
        result["decision_reason"] = (
            f"Target £{target} is within acceptable range "
            f"(floor: £{floor}, max: £{max_price or 'none'}). Using target."
        )

    current = Decimal(str(current_price))
    recommended = Decimal(str(result["recommended_price"]))

    result["action_needed"] = abs(recommended - current) >= Decimal("0.01")

    return result