from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.post import HydraResource


class Account(HydraResource):
    id: str
    name: str
    account_id: str = Field(alias="accountId")


class AccountsResponse(BaseModel):
    """API Platform Hydra collection: items live in `hydra:member` (v1)
    or `member` (v2 / API Platform 3.2+)."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    accounts: list[Account] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _read_hydra_member(cls, data: Any) -> Any:
        if isinstance(data, dict) and "accounts" not in data:
            members = data.get("hydra:member") or data.get("member") or []
            return {**data, "accounts": members}
        return data
