"""Dependency aliases for query filter params bound to FastAPI."""

from typing import Annotated

from fastapi import Depends

from src.application.dtos.main import QueryFilterParams

QueryFilterParamsDep = Annotated[QueryFilterParams, Depends()]
