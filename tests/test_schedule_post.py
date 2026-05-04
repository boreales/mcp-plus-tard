from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.models import SchedulePostResponse
from app.tools import schedule_post


async def test_schedule_post_nominal(mock_client):
    mock_client.schedule_post.return_value = SchedulePostResponse(
        success=True, post_id=456, message="Post created successfully"
    )

    result = await schedule_post(
        mock_client,
        provider="facebook",
        page_id="123456789",
        planned_at="2026-05-01T10:00:00Z",
        text="Hello world",
    )

    mock_client.schedule_post.assert_awaited_once()
    payload = mock_client.schedule_post.await_args.args[0]
    assert payload.provider.value == "facebook"
    assert payload.page_id == "123456789"
    assert payload.text == "Hello world"
    assert payload.image_posts is None

    assert "456" in result
    assert "facebook" in result
    assert "123456789" in result
    assert "01/05/2026" in result


async def test_schedule_post_with_images(mock_client):
    mock_client.schedule_post.return_value = SchedulePostResponse(
        success=True, post_id=789, message="ok"
    )

    result = await schedule_post(
        mock_client,
        provider="instagram",
        page_id="ig_123",
        planned_at="2026-05-01T10:00:00Z",
        text="Photo",
        image_posts=["https://x/1.jpg", "https://x/2.jpg"],
    )

    payload = mock_client.schedule_post.await_args.args[0]
    assert payload.image_posts == ["https://x/1.jpg", "https://x/2.jpg"]
    assert "2 média" in result


async def test_schedule_post_rejects_unknown_provider(mock_client):
    with pytest.raises(ValueError):
        await schedule_post(
            mock_client,
            provider="myspace",
            page_id="x",
            planned_at="2026-05-01T10:00:00Z",
            text="Hello",
        )

    mock_client.schedule_post.assert_not_called()


@pytest.mark.parametrize("status", [400, 401, 502])
async def test_schedule_post_propagates_http_errors(mock_client, status):
    mock_client.schedule_post.side_effect = HTTPException(status_code=status, detail="x")

    with pytest.raises(HTTPException) as exc_info:
        await schedule_post(
            mock_client,
            provider="facebook",
            page_id="123",
            planned_at="2026-05-01T10:00:00Z",
            text="Hello",
        )

    assert exc_info.value.status_code == status
