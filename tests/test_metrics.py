"""Metric ingestion tests."""


async def _create_campaign(client) -> int:
    response = await client.post(
        "/campaigns",
        json={
            "name": "Metrics Campaign",
            "advertiser": "Fabrikam",
            "budget": 8000,
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
        },
    )
    return response.json()["id"]


async def test_ingest_metric_row(client) -> None:
    campaign_id = await _create_campaign(client)
    response = await client.post(
        f"/campaigns/{campaign_id}/metrics",
        json={
            "date": "2026-03-05",
            "impressions": 10000,
            "clicks": 420,
            "spend": 315.25,
            "conversions": 40,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["campaign_id"] == campaign_id
    assert body["clicks"] == 420


async def test_ingest_metric_rejects_duplicate_dates(client) -> None:
    campaign_id = await _create_campaign(client)
    payload = {
        "date": "2026-03-05",
        "impressions": 10000,
        "clicks": 420,
        "spend": 315.25,
        "conversions": 40,
    }

    first_response = await client.post(f"/campaigns/{campaign_id}/metrics", json=payload)
    second_response = await client.post(f"/campaigns/{campaign_id}/metrics", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


async def test_ingest_metric_rejects_out_of_range_date(client) -> None:
    campaign_id = await _create_campaign(client)
    response = await client.post(
        f"/campaigns/{campaign_id}/metrics",
        json={
            "date": "2026-04-01",
            "impressions": 10000,
            "clicks": 420,
            "spend": 315.25,
            "conversions": 40,
        },
    )

    assert response.status_code == 400
    assert "date range" in response.text


async def test_ingest_metric_validates_clicks_and_conversions(client) -> None:
    campaign_id = await _create_campaign(client)
    response = await client.post(
        f"/campaigns/{campaign_id}/metrics",
        json={
            "date": "2026-03-05",
            "impressions": 200,
            "clicks": 250,
            "spend": 50.0,
            "conversions": 10,
        },
    )

    assert response.status_code == 422
    assert "clicks" in response.text
