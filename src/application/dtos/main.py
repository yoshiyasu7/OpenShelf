from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, Field


class QueryFilterParams(BaseModel):
    limit: int = Field(10, ge=1, le=100, description="Max results (1-100, default: 10)")
    offset: int = Field(0, ge=0, description="Results to skip")
    name_query: str | None = Field(None, description="Search by name (partial match)")


QueryFilterParamsDep = Annotated[QueryFilterParams, Depends()]
