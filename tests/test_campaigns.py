"""Campaign endpoint tests."""

from datetime import date


async def test_create_list_and_get_campaign(client) -> None:
    payload = {
        "name": "Launch Campaign",
        "advertiser": "Contoso",
        "budget": 12000,
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
    }

    create_response = await client.post("/campaigns", json=payload)
    assert create_response.status_code == 201
    created_campaign = create_response.json()
    assert created_campaign["name"] == payload["name"]
    assert created_campaign["advertiser"] == payload["advertiser"]

    list_response = await client.get("/campaigns")
    assert list_response.status_code == 200
    campaigns = list_response.json()
    assert len(campaigns) == 1
    assert campaigns[0]["id"] == created_campaign["id"]

    get_response = await client.get(f"/campaigns/{created_campaign['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["budget"] == float(payload["budget"])


async def test_create_campaign_rejects_invalid_dates(client) -> None:
    response = await client.post(
        "/campaigns",
        json={
            "name": "Broken Campaign",
            "advertiser": "Contoso",
            "budget": 1000,
            "start_date": "2026-03-31",
            "end_date": "2026-03-01",
        },
    )

    assert response.status_code == 422
    assert "end_date" in response.text


async def test_health_check(client) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
