from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Provider(StrEnum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    THREADS = "threads"
    BLUESKY = "bluesky"
    GOOGLE = "google"
    # The API exposes Google My Business as "googlemybusiness" in user
    # responses but expects "google" as the provider for POST /api/post.
    GOOGLE_MY_BUSINESS = "googlemybusiness"


class HydraResource(BaseModel):
    """Base for an API Platform single-resource payload.

    If the response only carries `@id` (IRI like `/api/accounts/42`) and
    no plain `id` field, derive `id` from the last IRI segment.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _id_from_iri(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("id") and isinstance(
            data.get("@id"), str
        ):
            iri = data["@id"]
            if "/" in iri:
                return {**data, "id": iri.rsplit("/", 1)[-1]}
        return data


class SchedulePostRequest(BaseModel):
    """Body sent to POST /api/post.

    Aliases match the API field names (camelCase).
    """

    model_config = ConfigDict(populate_by_name=True)

    provider: Provider
    planned_at: datetime = Field(alias="plannedAt")
    page_id: str = Field(alias="pageId")
    text: str | None = None
    image_posts: list[Any] | None = Field(default=None, alias="imagePosts")
    tiktok_params: dict[str, Any] | None = Field(default=None, alias="tiktokParams")
    twitter_params: dict[str, Any] | None = Field(default=None, alias="twitterParams")


class SchedulePostResponse(BaseModel):
    success: bool
    post_id: int
    message: str | None = None
