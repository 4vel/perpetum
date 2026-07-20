from typing import List

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(min_length=2, max_length=400)


class Source(BaseModel):
    id: int
    title: str
    url: str
    domain: str
    snippet: str


class Offer(BaseModel):
    id: str
    name: str
    description: str
    url: str
    image_url: str = ""


class AskResponse(BaseModel):
    query: str
    answer: str
    sources: List[Source]
    offers: List[Offer] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    search_configured: bool
    llm_configured: bool


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=500)
