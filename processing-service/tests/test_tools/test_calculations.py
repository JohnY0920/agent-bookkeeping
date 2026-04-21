import pytest
from app.tools.calculations import (
    calculate_cca,
    calculate_amortization,
    calculate_gst,
    calculate_itc,
    calculate_tax_payable,
    calculate_sbd,
)


class TestCalculateCCA:
    async def test_class10_basic(self):
        result = await calculate_cca(cca_class=10, ucc_opening=10000.0)
        assert result["cca_amount"] == pytest.approx(3000.0)
        assert result["ucc_closing"] == pytest.approx(7000.0)
        assert result["rate"] == pytest.approx(0.30)

    async def test_class10_first_year_aiip(self):
        # First year: 30% on existing UCC + 1.5×30% = 45% on net additions
        result = await calculate_cca(
            cca_class=10, ucc_opening=0.0, additions=10000.0, is_first_year=True
        )
        assert result["cca_amount"] == pytest.approx(4500.0)  # 10000 * 0.30 * 1.5
        assert result["ucc_closing"] == pytest.approx(5500.0)

    async def test_class1_buildings(self):
        result = await calculate_cca(cca_class=1, ucc_opening=500000.0)
        assert result["cca_amount"] == pytest.approx(20000.0)  # 4%
        assert result["rate"] == pytest.approx(0.04)

    async def test_cca_cannot_exceed_ucc(self):
        result = await calculate_cca(cca_class=12, ucc_opening=100.0)  # 100% rate
        assert result["cca_amount"] == pytest.approx(100.0)
        assert result["ucc_closing"] == pytest.approx(0.0)

    async def test_unknown_class_returns_error(self):
        result = await calculate_cca(cca_class=99, ucc_opening=1000.0)
        assert "error" in result

    async def test_with_dispositions(self):
        result = await calculate_cca(
            cca_class=8, ucc_opening=10000.0, additions=2000.0, dispositions=3000.0
        )
        # net additions = -1000, ucc_before = 9000
        assert result["ucc_before_cca"] == pytest.approx(9000.0)
        assert result["cca_amount"] == pytest.approx(1800.0)  # 9000 * 20%

    async def test_class14_straight_line_returns_error(self):
        result = await calculate_cca(cca_class=14, ucc_opening=10000.0)
        assert "error" in result


class TestCalculateAmortization:
    async def test_basic_straight_line(self):
        result = await calculate_amortization(cost=60000.0, useful_life_years=5)
        assert result["annual_amortization"] == pytest.approx(12000.0)
        assert result["period_amortization"] == pytest.approx(12000.0)

    async def test_partial_year(self):
        result = await calculate_amortization(
            cost=60000.0, useful_life_years=5, months_in_service=6
        )
        assert result["period_amortization"] == pytest.approx(6000.0)

    async def test_with_salvage(self):
        result = await calculate_amortization(
            cost=55000.0, salvage_value=5000.0, useful_life_years=5
        )
        assert result["annual_amortization"] == pytest.approx(10000.0)


class TestCalculateGST:
    async def test_default_5_percent(self):
        result = await calculate_gst(amount=100.0)
        assert result["gst_amount"] == pytest.approx(5.0)
        assert result["total_with_gst"] == pytest.approx(105.0)

    async def test_hst_ontario(self):
        result = await calculate_gst(amount=100.0, rate=0.13)
        assert result["gst_amount"] == pytest.approx(13.0)

    async def test_rounding(self):
        result = await calculate_gst(amount=33.33)
        assert result["gst_amount"] == pytest.approx(1.67)  # 33.33 * 0.05 = 1.6665 → 1.67


class TestCalculateITC:
    async def test_full_itc_eligible(self):
        result = await calculate_itc(expense_amount=1000.0, expense_type="office_supplies")
        assert result["restriction_rate"] == pytest.approx(1.0)
        assert result["itc_eligible"] == pytest.approx(50.0)
        assert result["itc_restricted"] == pytest.approx(0.0)

    async def test_meals_50_percent(self):
        result = await calculate_itc(expense_amount=200.0, expense_type="meals_entertainment")
        assert result["restriction_rate"] == pytest.approx(0.5)
        assert result["itc_eligible"] == pytest.approx(5.0)   # 200 * 5% = 10 GST, 50% = 5
        assert result["itc_restricted"] == pytest.approx(5.0)

    async def test_personal_zero_itc(self):
        result = await calculate_itc(expense_amount=500.0, expense_type="personal")
        assert result["itc_eligible"] == pytest.approx(0.0)
        assert result["itc_restricted"] == pytest.approx(25.0)

    async def test_club_dues_zero_itc(self):
        result = await calculate_itc(expense_amount=1200.0, expense_type="club_dues")
        assert result["itc_eligible"] == pytest.approx(0.0)


class TestCalculateTaxPayable:
    async def test_ccpc_sbd_eligible(self):
        # $400K income, all ABI, CCPC — all under $500K limit
        result = await calculate_tax_payable(
            taxable_income=400000.0, province="ON", is_ccpc=True
        )
        # Federal: 400000 * 9% = 36000
        assert result["federal_tax"] == pytest.approx(36000.0)
        assert result["sbd_eligible_amount"] == pytest.approx(400000.0)

    async def test_non_ccpc_general_rate(self):
        result = await calculate_tax_payable(
            taxable_income=100000.0, province="ON", is_ccpc=False
        )
        # Federal: 100000 * 15% = 15000 (no SBD)
        assert result["federal_tax"] == pytest.approx(15000.0)
        assert result["sbd_eligible_amount"] == pytest.approx(0.0)

    async def test_income_over_business_limit(self):
        result = await calculate_tax_payable(
            taxable_income=700000.0,
            province="ON",
            is_ccpc=True,
            active_business_income=700000.0,
            business_limit=500000.0,
        )
        # SBD on first 500K @ 9%, general rate on remaining 200K @ 15%
        assert result["federal_tax"] == pytest.approx(500000 * 0.09 + 200000 * 0.15)

    async def test_effective_rate_calculation(self):
        result = await calculate_tax_payable(taxable_income=100000.0, province="ON", is_ccpc=True)
        assert result["effective_rate"] > 0


class TestCalculateSBD:
    async def test_ccpc_under_limit(self):
        result = await calculate_sbd(active_business_income=300000.0)
        assert result["sbd_amount"] == pytest.approx(300000 * 0.19)
        assert result["sbd_eligible"] == pytest.approx(300000.0)

    async def test_ccpc_over_limit(self):
        result = await calculate_sbd(active_business_income=700000.0, business_limit=500000.0)
        assert result["sbd_eligible"] == pytest.approx(500000.0)

    async def test_not_ccpc(self):
        result = await calculate_sbd(active_business_income=300000.0, is_ccpc=False)
        assert result["sbd_amount"] == pytest.approx(0.0)
