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

    response = await client.get(f"/campaigns/{campaign_id}/report")
    assert response.status_code == 200
    report = response.json()
    assert report["total_impressions"] == 3000
    assert report["total_clicks"] == 260
    assert report["total_spend"] == 270.0
    assert report["total_conversions"] == 32
    assert report["ctr"] == 0.0867
    assert report["cpa"] == 8.44
    assert report["best_performing_day"]["date"] == "2026-03-02"


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

    response = await client.get(f"/campaigns/{campaign_id}/report")
    assert response.status_code == 200
    report = response.json()
    assert report["total_impressions"] == 0
    assert report["ctr"] == 0.0
    assert report["cpa"] is None
    assert report["best_performing_day"] is None


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

    response = await client.get(f"/reports/compare?a={campaign_a}&b={campaign_b}")
    assert response.status_code == 200
    comparison = response.json()
    assert comparison["overall_winner"] == "campaign_b"

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
