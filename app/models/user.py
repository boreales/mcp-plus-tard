from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.post import Provider


class ApiKeyInfo(BaseModel):
    created_at: datetime | None = None
    expires_at: datetime | None = None
    last_used_at: datetime | None = None


class ValidateApiKeyResponse(BaseModel):
    valid: bool
    api_key: ApiKeyInfo | None = None


class ProviderSubAccount(BaseModel):
    """A sub-account exposed under a provider (e.g. a Facebook page)."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    name: str
    type: str | None = None


class UserProvider(BaseModel):
    """A social provider connected to a user (Facebook, LinkedIn, ...)."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: int
    provider: Provider
    provider_id: str | None = Field(default=None, alias="providerId")
    username: str | None = None
    accounts: list[ProviderSubAccount] = []


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: int
    email: str | None = None
    language: str | None = None
    is_subscribed: bool | None = None
    providers: list[UserProvider] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RegisterUserResponse(BaseModel):
    success: bool
    user: User
    oauth_url: str


class GetUserResponse(BaseModel):
    success: bool
    user: User


class OAuthUrlResponse(BaseModel):
    success: bool
    user_id: int
    oauth_url: str
