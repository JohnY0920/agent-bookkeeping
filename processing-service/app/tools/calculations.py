from decimal import Decimal, ROUND_HALF_UP

# CCA rates by class per Income Tax Act
CCA_RATES: dict[int, Decimal | None] = {
    1: Decimal("0.04"),    # Buildings
    8: Decimal("0.20"),    # Furniture, fixtures
    10: Decimal("0.30"),   # Motor vehicles, computer hardware
    12: Decimal("1.00"),   # Small tools (<$500)
    14: None,              # Patents/franchises — straight-line over life
    43: Decimal("0.30"),   # Manufacturing equipment
    44: Decimal("0.25"),   # Patents
    45: Decimal("0.45"),   # Computer equipment (post-Mar 2007)
    46: Decimal("0.30"),   # Data network infrastructure
    50: Decimal("0.55"),   # Computer equipment (post-2011)
    53: Decimal("0.50"),   # Manufacturing equipment (post-2015)
    54: Decimal("0.30"),   # Zero-emission vehicles
}

PROVINCIAL_RATES: dict[str, dict[str, Decimal]] = {
    "ON": {"small": Decimal("0.032"), "general": Decimal("0.115")},
    "BC": {"small": Decimal("0.02"),  "general": Decimal("0.12")},
    "AB": {"small": Decimal("0.02"),  "general": Decimal("0.08")},
    "QC": {"small": Decimal("0.03"),  "general": Decimal("0.115")},
    "SK": {"small": Decimal("0.02"),  "general": Decimal("0.12")},
    "MB": {"small": Decimal("0.00"),  "general": Decimal("0.12")},
    "NS": {"small": Decimal("0.025"), "general": Decimal("0.14")},
    "NB": {"small": Decimal("0.025"), "general": Decimal("0.14")},
    "PE": {"small": Decimal("0.01"),  "general": Decimal("0.16")},
    "NL": {"small": Decimal("0.03"),  "general": Decimal("0.15")},
}


async def calculate_cca(
    cca_class: int,
    ucc_opening: float,
    additions: float = 0.0,
    dispositions: float = 0.0,
    is_first_year: bool = False,
) -> dict:
    """Calculate Capital Cost Allowance per ITA regulations."""
    rate = CCA_RATES.get(cca_class)
    if rate is None:
        return {
            "error": f"CCA class {cca_class} requires straight-line calculation. Provide asset life."
        }

    ucc = Decimal(str(ucc_opening))
    add = Decimal(str(additions))
    disp = Decimal(str(dispositions))

    net_additions = add - disp
    ucc_before_cca = ucc + net_additions

    # Accelerated Investment Incentive Property (AIIP): first-year gets 1.5× rate on net additions
    if is_first_year and net_additions > 0:
        cca_on_existing = (ucc * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        cca_on_new = (net_additions * rate * Decimal("1.5")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        cca_amount = cca_on_existing + cca_on_new
    else:
        cca_amount = (ucc_before_cca * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # CCA cannot exceed UCC
    if cca_amount > ucc_before_cca:
        cca_amount = ucc_before_cca

    ucc_closing = ucc_before_cca - cca_amount

    return {
        "cca_class": cca_class,
        "rate": float(rate),
        "ucc_opening": float(ucc),
        "additions": float(add),
        "dispositions": float(disp),
        "ucc_before_cca": float(ucc_before_cca),
        "cca_amount": float(cca_amount),
        "ucc_closing": float(ucc_closing),
        "is_first_year": is_first_year,
        "calculation_reference": f"ITA Class {cca_class}, {float(rate) * 100}% declining balance",
    }


async def calculate_amortization(
    cost: float,
    salvage_value: float = 0.0,
    useful_life_years: int = 5,
    months_in_service: int = 12,
) -> dict:
    """Straight-line amortization for intangible assets."""
    cost_d = Decimal(str(cost))
    salvage_d = Decimal(str(salvage_value))
    life = Decimal(str(useful_life_years))
    months = Decimal(str(months_in_service))

    annual = (cost_d - salvage_d) / life
    period = (annual * months / 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "cost": float(cost_d),
        "salvage_value": float(salvage_d),
        "useful_life_years": useful_life_years,
        "months_in_service": months_in_service,
        "annual_amortization": float(annual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "period_amortization": float(period),
        "calculation_reference": "Straight-line amortization",
    }


async def calculate_gst(amount: float, rate: float = 0.05) -> dict:
    """Calculate GST on an amount. Default 5% federal rate."""
    gst = (Decimal(str(amount)) * Decimal(str(rate))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return {
        "base_amount": amount,
        "gst_rate": rate,
        "gst_amount": float(gst),
        "total_with_gst": float(Decimal(str(amount)) + gst),
        "calculation_reference": "Excise Tax Act, Part IX",
    }


async def calculate_itc(
    expense_amount: float,
    expense_type: str,
    gst_rate: float = 0.05,
) -> dict:
    """
    Calculate Input Tax Credit eligibility.
    Applies CRA ITC restriction rules: meals at 50%, personal/club at 0%.
    """
    RESTRICTIONS: dict[str, Decimal] = {
        "meals_entertainment": Decimal("0.50"),
        "personal": Decimal("0.00"),
        "club_dues": Decimal("0.00"),
    }

    amount = Decimal(str(expense_amount))
    rate = Decimal(str(gst_rate))
    gst_paid = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    restriction = RESTRICTIONS.get(expense_type, Decimal("1.00"))
    itc_eligible = (gst_paid * restriction).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    ref = "ETA s.169"
    if restriction < Decimal("1.00"):
        ref = "ETA s.169, ITA s.67.1 (meals)" if "meal" in expense_type else "ETA s.169 (restricted)"

    return {
        "expense_amount": expense_amount,
        "expense_type": expense_type,
        "gst_paid": float(gst_paid),
        "restriction_rate": float(restriction),
        "itc_eligible": float(itc_eligible),
        "itc_restricted": float(gst_paid - itc_eligible),
        "calculation_reference": ref,
    }


async def calculate_tax_payable(
    taxable_income: float,
    province: str = "ON",
    is_ccpc: bool = True,
    active_business_income: float | None = None,
    business_limit: float = 500000.0,
) -> dict:
    """
    Calculate corporate tax payable.
    Federal: 38% base − 10% abatement − 19% SBD (on first $500K for CCPC) = 9%
    General rate: 38% − 10% − 13% general reduction = 15%
    """
    income = Decimal(str(taxable_income))
    abi = Decimal(str(active_business_income or taxable_income))
    limit = Decimal(str(business_limit))

    sbd_eligible = min(abi, limit) if is_ccpc else Decimal("0")
    federal_tax = (sbd_eligible * Decimal("0.09") + max(income - sbd_eligible, Decimal("0")) * Decimal("0.15")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    prov = PROVINCIAL_RATES.get(province, PROVINCIAL_RATES["ON"])
    provincial_tax = (
        sbd_eligible * prov["small"]
        + max(income - sbd_eligible, Decimal("0")) * prov["general"]
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    total_tax = federal_tax + provincial_tax

    return {
        "taxable_income": float(income),
        "sbd_eligible_amount": float(sbd_eligible),
        "federal_tax": float(federal_tax),
        "provincial_tax": float(provincial_tax),
        "total_tax": float(total_tax),
        "effective_rate": float((total_tax / income * 100).quantize(Decimal("0.01"))) if income > 0 else 0,
        "province": province,
        "is_ccpc": is_ccpc,
        "calculation_reference": "ITA s.123, s.124, s.125, provincial rates",
    }


async def calculate_sbd(
    active_business_income: float,
    business_limit: float = 500000.0,
    is_ccpc: bool = True,
) -> dict:
    """Calculate Small Business Deduction amount (ITA s.125)."""
    if not is_ccpc:
        return {
            "sbd_amount": 0.0,
            "calculation_reference": "ITA s.125 — not eligible (not CCPC)",
        }

    abi = Decimal(str(active_business_income))
    limit = Decimal(str(business_limit))
    sbd_eligible = min(abi, limit)
    # SBD rate is 19% of eligible income (reduces federal rate from 28% to 9%)
    sbd_amount = (sbd_eligible * Decimal("0.19")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "active_business_income": float(abi),
        "business_limit": float(limit),
        "sbd_eligible": float(sbd_eligible),
        "sbd_amount": float(sbd_amount),
        "calculation_reference": "ITA s.125 — Small Business Deduction",
    }
