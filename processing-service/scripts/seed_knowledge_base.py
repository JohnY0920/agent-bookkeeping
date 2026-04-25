"""
Seed the knowledge_base table with CRA/ITA guidance.

Run from processing-service directory:
    PYTHONPATH=. python scripts/seed_knowledge_base.py

Requires: DATABASE_URL and MISTRAL_API_KEY env vars (or .env file).
"""
import asyncio
import os
import sys

os.environ.setdefault("DATABASE_URL", "postgresql://dev:dev@localhost:5432/architect_ledger")
os.environ.setdefault("MISTRAL_API_KEY", os.environ.get("MISTRAL_API_KEY", "placeholder"))
os.environ.setdefault("CLAUDE_API_KEY", "placeholder")

KNOWLEDGE_ENTRIES = [
    # CCA Classes
    {
        "source": "CCA_CLASSES",
        "section": "ITA Schedule II",
        "title": "CCA Class 1 — Non-residential buildings",
        "content": "Class 1 includes most buildings acquired after 1987. CCA rate: 4% declining balance. Eligible for the accelerated investment incentive (AIIP) for additions after November 20, 2018.",
    },
    {
        "source": "CCA_CLASSES",
        "section": "ITA Schedule II",
        "title": "CCA Class 8 — Miscellaneous tangible capital property",
        "content": "Class 8 includes furniture, fixtures, office equipment, machinery not in other classes. CCA rate: 20% declining balance. Includes photocopiers, electronic cash registers, and most office equipment.",
    },
    {
        "source": "CCA_CLASSES",
        "section": "ITA Schedule II",
        "title": "CCA Class 10 — Motor vehicles and computer hardware",
        "content": "Class 10 includes general-purpose motor vehicles and pre-2018 computer hardware. CCA rate: 30% declining balance. Passenger vehicles with cost >$36,000 (2024 limit) are subject to capital cost limits under ITA s.13(7)(g).",
    },
    {
        "source": "CCA_CLASSES",
        "section": "ITA Schedule II",
        "title": "CCA Class 10.1 — Passenger vehicles exceeding cost limit",
        "content": "Class 10.1 applies to passenger vehicles costing more than $36,000 (2024 threshold). Each vehicle is a separate class. CCA rate: 30%. Only the $36,000 limit is depreciable. No terminal loss on disposition.",
    },
    {
        "source": "CCA_CLASSES",
        "section": "ITA Schedule II",
        "title": "CCA Class 12 — Small tools and cutlery",
        "content": "Class 12 includes tools costing less than $500, cutlery, and linen. CCA rate: 100% (fully deductible in year of acquisition). AIIP does not apply — already 100% rate.",
    },
    {
        "source": "CCA_CLASSES",
        "section": "ITA Schedule II",
        "title": "CCA Class 14 — Patents and franchises with limited life",
        "content": "Class 14 includes patents, franchises, concessions, or licences with a limited legal life. Amortized on a straight-line basis over the remaining legal life of the property. No AIIP multiplier.",
    },
    {
        "source": "CCA_CLASSES",
        "section": "ITA Schedule II",
        "title": "CCA Class 50 — Computer equipment post-2011",
        "content": "Class 50 includes general-purpose computer hardware and systems software acquired after March 18, 2007. CCA rate: 55% declining balance. Eligible for AIIP for additions after November 20, 2018.",
    },
    {
        "source": "CCA_CLASSES",
        "section": "ITA Schedule II",
        "title": "CCA Class 53 — Manufacturing and processing machinery post-2015",
        "content": "Class 53 includes manufacturing and processing machinery and equipment acquired after 2015 and before 2026. CCA rate: 50% declining balance. Eligible for immediate expensing under AIIP rules.",
    },
    # AIIP Rules
    {
        "source": "ITA",
        "section": "ITA s.13(1)(b)",
        "title": "Accelerated Investment Incentive Property (AIIP)",
        "content": "For eligible additions after November 20, 2018, the first-year CCA deduction is calculated on 1.5x the normal UCC base (effectively suspending the half-year rule and adding an additional 50% deduction). For Class 14.1 and manufacturing classes, a 3x multiplier applies for property acquired before 2024. The AIIP phases out for property acquired in 2027 and later.",
    },
    # ITC Rules
    {
        "source": "ITC_RULES",
        "section": "ETA s.169(1)",
        "title": "General ITC eligibility",
        "content": "An ITC may be claimed where a registrant acquires or imports property or a service for use in the course of commercial activities. The ITC is equal to the tax paid or payable multiplied by the extent of commercial use. The registrant must hold sufficient documentation (invoice, receipt) to support the claim.",
    },
    {
        "source": "ITC_RULES",
        "section": "ETA s.67.1 / ITA s.67.1",
        "title": "Meals and entertainment — 50% ITC restriction",
        "content": "Only 50% of GST/HST paid on meals and entertainment expenses is claimable as an ITC (ETA s.67.1). This parallels the income tax deduction limit (ITA s.67.1). Common categories subject to the restriction: restaurant meals, bar tabs, client entertainment events, tickets to shows or sports events. The full expense is not allowed; receipts must identify the nature of the expense.",
    },
    {
        "source": "ITC_RULES",
        "section": "ETA s.170(1)",
        "title": "Personal expenses — no ITC",
        "content": "No ITC may be claimed on property or services acquired for personal consumption or use. If a shareholder or employee uses a company-purchased item personally, the ITC must be prorated or eliminated. Common personal expenses improperly claiming ITC: personal clothing, personal groceries, personal vacations. CRA will reassess ITCs on personal expenses with interest and penalties.",
    },
    {
        "source": "ITC_RULES",
        "section": "ETA s.201",
        "title": "Passenger vehicle ITC limit",
        "content": "The ITC for passenger vehicles is limited based on the $36,000 capital cost limit (2024). The deductible portion of a $50,000 vehicle is $36,000/$50,000 = 72%. This applies to both the GST/HST paid on purchase and the CCA deduction claimed.",
    },
    {
        "source": "ITC_RULES",
        "section": "ETA s.177",
        "title": "Non-registrant suppliers — no ITC",
        "content": "No ITC is claimable on purchases from suppliers who are not registered for GST/HST (small suppliers with annual revenue <$30,000). If an invoice does not show a GST/HST registration number (RT number), the ITC cannot be claimed. This is a common CRA audit adjustment.",
    },
    # Small Business Deduction
    {
        "source": "ITA",
        "section": "ITA s.125",
        "title": "Small Business Deduction (SBD) — federal",
        "content": "Canadian-Controlled Private Corporations (CCPCs) may claim the SBD on active business income earned in Canada. The federal SBD rate is 9% (reducing the general 15% rate to 6% net federal tax). The SBD is available on the lesser of: (a) income from active business in Canada, (b) taxable income, and (c) the SBD limit ($500,000 federally for 2024). Associated corporations must share the SBD limit. The SBD is phased out when taxable capital exceeds $10M.",
    },
    {
        "source": "ITA",
        "section": "ITA s.256",
        "title": "Associated corporations — SBD limit sharing",
        "content": "Two corporations are associated if one controls the other, they are both controlled by the same person or group, or one is controlled by a person related to the controller of the other. Associated corporations must share the $500,000 SBD limit. If $300,000 is allocated to Corp A, Corp B can only claim SBD on $200,000 of active business income.",
    },
    # Shareholder Loans
    {
        "source": "ITA",
        "section": "ITA s.15(2)",
        "title": "Shareholder loan inclusion rule",
        "content": "Where a corporation makes a loan to a shareholder (or a person connected with a shareholder), the loan amount is included in the shareholder's income in the year received, UNLESS the loan is repaid within one year after the end of the corporation's fiscal year in which the loan was made. The s.15(2) inclusion applies to any debit balance in a shareholder loan account that exceeds one year. Interest must be charged at the CRA prescribed rate or higher to avoid a benefit under ITA s.80.4.",
    },
    # GST Rates
    {
        "source": "ETA",
        "section": "ETA Schedule VI / VII",
        "title": "Zero-rated vs exempt supplies",
        "content": "Zero-rated supplies (taxed at 0%): basic groceries, prescription drugs, exports, most agricultural products. ITCs are claimable on inputs used to make zero-rated supplies. Exempt supplies: residential rent, most health care services, child care, financial services, educational services. NO ITCs on inputs for exempt supplies. Mixed-use (making both taxable and exempt supplies) requires proration of ITCs under ETA s.141.01.",
    },
    {
        "source": "ETA",
        "section": "ETA s.165",
        "title": "HST rates by province (2024)",
        "content": "Federal GST rate: 5%. HST rates: Ontario 13%, Nova Scotia 15%, New Brunswick 15%, Prince Edward Island 15%, Newfoundland & Labrador 15%. PST-registered provinces (BC, SK, MB) charge 5% GST plus separate PST (not claimable as ITC). Alberta, Yukon, NWT, Nunavut: 5% GST only, no provincial sales tax.",
    },
    # T2 Corporate Tax
    {
        "source": "ITA",
        "section": "ITA s.123",
        "title": "Federal corporate income tax rates",
        "content": "General federal corporate rate: 15% (38% basic rate minus 10% provincial abatement minus 13% general rate reduction). Small business rate (CCPC eligible for SBD): 9% net federal on income up to $500,000 limit. Investment income in a CCPC: 38.67% federal rate (includes 30.67% refundable tax).",
    },
    # T1 Personal Tax
    {
        "source": "ITA",
        "section": "ITA s.118",
        "title": "Basic personal amount and non-refundable credits",
        "content": "Basic personal amount (2024): $15,705. This credit reduces federal tax at the lowest marginal rate (15%). Additional personal credits: CPP employee contributions (T4 box 16), EI premiums (T4 box 18), Canada employment amount ($1,433), RRSP deduction limit per NOA. Non-refundable credits do not generate a refund if they exceed tax payable.",
    },
    {
        "source": "ITA",
        "section": "ITA s.146",
        "title": "RRSP deduction rules",
        "content": "RRSP contributions are deductible up to 18% of prior year earned income, minus the pension adjustment (PA) on the T4, subject to the annual dollar limit ($31,560 for 2024). Unused room carries forward indefinitely. Over-contributions above $2,000 are subject to a 1%/month penalty tax. Contributions must be made in the calendar year or within 60 days after year-end.",
    },
    # CRA Audit Risk
    {
        "source": "CRA_GUIDE",
        "section": "CRA audit triggers",
        "title": "Common personal expense CRA audit triggers",
        "content": "CRA commonly audits: (1) Meals & entertainment >2% of gross revenue; (2) Home office claims without T2200; (3) Vehicle expenses with high personal-use ratio; (4) Cash-intensive businesses; (5) Large year-over-year income fluctuations (>40%); (6) Shareholder loans with debit balances; (7) Non-arm's length transactions; (8) Unreported income suggested by net worth assessments.",
    },
]


async def seed():
    import asyncpg
    import json

    url = os.environ["DATABASE_URL"]

    async def init(conn):
        await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
        await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")

    pool = await asyncpg.create_pool(url, min_size=1, max_size=2, init=init)

    from app.tools.knowledge import add_knowledge_entry

    existing = await pool.fetchval("SELECT COUNT(*) FROM knowledge_base")
    if existing > 0:
        print(f"Knowledge base already has {existing} entries. Skipping.")
        await pool.close()
        return

    print(f"Seeding {len(KNOWLEDGE_ENTRIES)} knowledge base entries...")
    for i, entry in enumerate(KNOWLEDGE_ENTRIES, 1):
        try:
            result = await add_knowledge_entry(**entry)
            print(f"  [{i}/{len(KNOWLEDGE_ENTRIES)}] {entry['title'][:60]} → {result['id']}")
        except Exception as e:
            print(f"  [{i}] ERROR: {entry['title'][:60]} — {e}")

    await pool.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
