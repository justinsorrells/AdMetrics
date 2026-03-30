"""Reporting endpoint tests."""


async def _create_campaign_with_metrics(client, name: str, advertiser: str, metrics: list[dict]) -> int:
    campaign_response = await client.post(
        "/campaigns",
        json={
            "name": name,
            "advertiser": advertiser,
            "budget": 15000,
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
        },
    )
    campaign_id = campaign_response.json()["id"]
    for metric in metrics:
        response = await client.post(f"/campaigns/{campaign_id}/metrics", json=metric)
        assert response.status_code == 201
    return campaign_id


async def test_campaign_report_aggregates_totals_and_best_day(client) -> None:
    campaign_id = await _create_campaign_with_metrics(
        client,
        "Report Campaign",
        "Adventure Co",
        [
            {
                "date": "2026-03-01",
                "impressions": 1000,
                "clicks": 100,
                "spend": 120.0,
                "conversions": 10,
            },
            {
                "date": "2026-03-02",
                "impressions": 2000,
                "clicks": 160,
                "spend": 150.0,
                "conversions": 22,
            },
        ],
    )

    response = await client.get(f"/campaigns/{campaign_id}/report?as_of_date=2026-03-02")
    assert response.status_code == 200
    report = response.json()
    assert report["report_start_date"] == "2026-03-01"
    assert report["report_end_date"] == "2026-03-31"
    assert report["days_in_report"] == 31
    assert report["days_with_data"] == 2
    assert report["total_impressions"] == 3000
    assert report["total_clicks"] == 260
    assert report["total_spend"] == 270.0
    assert report["total_conversions"] == 32
    assert report["ctr"] == 0.0867
    assert report["cpa"] == 8.44
    assert report["best_performing_day"]["date"] == "2026-03-02"
    assert len(report["daily_breakdown"]) == 31
    assert report["daily_breakdown"][0]["ctr"] == 0.1
    assert report["pacing"]["as_of_date"] == "2026-03-02"
    assert report["pacing"]["spend_to_date"] == 270.0
    assert report["pacing"]["projected_total_spend"] == 4185.0
    assert report["pacing"]["pacing_status"] == "underpacing"


async def test_campaign_report_handles_empty_metrics(client) -> None:
    campaign_response = await client.post(
        "/campaigns",
        json={
            "name": "Empty Campaign",
            "advertiser": "Adventure Co",
            "budget": 15000,
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
        },
    )
    campaign_id = campaign_response.json()["id"]

    response = await client.get(f"/campaigns/{campaign_id}/report?as_of_date=2026-03-15")
    assert response.status_code == 200
    report = response.json()
    assert report["total_impressions"] == 0
    assert report["ctr"] == 0.0
    assert report["cpa"] is None
    assert report["best_performing_day"] is None
    assert len(report["daily_breakdown"]) == 31
    assert report["daily_breakdown"][0]["date"] == "2026-03-01"
    assert report["daily_breakdown"][0]["spend"] == 0.0
    assert report["pacing"]["spend_to_date"] == 0.0
    assert report["pacing"]["pacing_status"] == "underpacing"


async def test_campaign_report_supports_date_ranges_and_zero_filled_trends(client) -> None:
    campaign_id = await _create_campaign_with_metrics(
        client,
        "Filtered Campaign",
        "Adventure Co",
        [
            {
                "date": "2026-03-01",
                "impressions": 1000,
                "clicks": 100,
                "spend": 120.0,
                "conversions": 10,
            },
            {
                "date": "2026-03-02",
                "impressions": 800,
                "clicks": 80,
                "spend": 90.0,
                "conversions": 8,
            },
            {
                "date": "2026-03-04",
                "impressions": 600,
                "clicks": 60,
                "spend": 70.0,
                "conversions": 12,
            },
        ],
    )

    response = await client.get(
        f"/campaigns/{campaign_id}/report?"
        "start_date=2026-03-02&end_date=2026-03-04&as_of_date=2026-03-04"
    )
    assert response.status_code == 200
    report = response.json()

    assert report["report_start_date"] == "2026-03-02"
    assert report["report_end_date"] == "2026-03-04"
    assert report["days_in_report"] == 3
    assert report["days_with_data"] == 2
    assert report["total_impressions"] == 1400
    assert report["total_clicks"] == 140
    assert report["total_spend"] == 160.0
    assert report["total_conversions"] == 20
    assert report["ctr"] == 0.1
    assert report["cpa"] == 8.0
    assert report["best_performing_day"]["date"] == "2026-03-04"
    assert len(report["daily_breakdown"]) == 3
    assert report["daily_breakdown"][1]["date"] == "2026-03-03"
    assert report["daily_breakdown"][1]["impressions"] == 0
    assert report["daily_breakdown"][1]["spend"] == 0.0


async def test_campaign_report_rejects_non_overlapping_date_range(client) -> None:
    campaign_id = await _create_campaign_with_metrics(
        client,
        "Range Campaign",
        "Adventure Co",
        [
            {
                "date": "2026-03-01",
                "impressions": 1000,
                "clicks": 100,
                "spend": 120.0,
                "conversions": 10,
            }
        ],
    )

    response = await client.get(
        f"/campaigns/{campaign_id}/report?start_date=2026-02-01&end_date=2026-02-10"
    )
    assert response.status_code == 400
    assert "does not overlap" in response.text


async def test_compare_reports_returns_metric_winners(client) -> None:
    campaign_a = await _create_campaign_with_metrics(
        client,
        "Campaign A",
        "Adventure Co",
        [
            {
                "date": "2026-03-01",
                "impressions": 1000,
                "clicks": 60,
                "spend": 120.0,
                "conversions": 6,
            }
        ],
    )
    campaign_b = await _create_campaign_with_metrics(
        client,
        "Campaign B",
        "Adventure Co",
        [
            {
                "date": "2026-03-01",
                "impressions": 1200,
                "clicks": 84,
                "spend": 100.0,
                "conversions": 9,
            }
        ],
    )

    response = await client.get(
        f"/reports/compare?a={campaign_a}&b={campaign_b}"
        "&start_date=2026-03-01&end_date=2026-03-01&as_of_date=2026-03-01"
    )
    assert response.status_code == 200
    comparison = response.json()
    assert comparison["overall_winner"] == "campaign_b"
    assert comparison["campaign_a"]["report_start_date"] == "2026-03-01"
    assert comparison["campaign_b"]["pacing"]["as_of_date"] == "2026-03-01"
    assert len(comparison["campaign_a"]["daily_breakdown"]) == 1

    ctr_row = next(row for row in comparison["comparisons"] if row["metric"] == "ctr")
    spend_row = next(row for row in comparison["comparisons"] if row["metric"] == "spend")
    assert ctr_row["winner"] == "campaign_b"
    assert spend_row["winner"] == "campaign_b"


async def test_compare_reports_requires_distinct_campaigns(client) -> None:
    campaign_id = await _create_campaign_with_metrics(
        client,
        "Campaign Solo",
        "Adventure Co",
        [
            {
                "date": "2026-03-01",
                "impressions": 1000,
                "clicks": 60,
                "spend": 120.0,
                "conversions": 6,
            }
        ],
    )

    response = await client.get(f"/reports/compare?a={campaign_id}&b={campaign_id}")
    assert response.status_code == 400
    assert "different campaign IDs" in response.text
