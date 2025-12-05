from datetime import datetime, timezone

from pydantic import BaseModel, Field

from graph_service.dto.common import Message


class SearchQuery(BaseModel):
    group_ids: list[str] | None = Field(
        None, description='The group ids for the memories to search'
    )
    query: str
    max_facts: int = Field(default=10, description='The maximum number of facts to retrieve')


class FactResult(BaseModel):
    uuid: str
    name: str
    fact: str
    valid_at: datetime | None
    invalid_at: datetime | None
    created_at: datetime
    expired_at: datetime | None

    class Config:
        json_encoders = {datetime: lambda v: v.astimezone(timezone.utc).isoformat()}


class SearchResults(BaseModel):
    facts: list[FactResult]


class GetMemoryRequest(BaseModel):
    group_id: str = Field(..., description='The group id of the memory to get')
    max_facts: int = Field(default=10, description='The maximum number of facts to retrieve')
    center_node_uuid: str | None = Field(
        ..., description='The uuid of the node to center the retrieval on'
    )
    messages: list[Message] = Field(
        ..., description='The messages to build the retrieval query from '
    )


class GetMemoryResponse(BaseModel):
    facts: list[FactResult] = Field(..., description='The facts that were retrieved from the graph')


class VideoSource(BaseModel):
    file_name: str
    cloudflare_stream_id: str | None = None


# Zep-compatible DTOs for graph visualization
class Node(BaseModel):
    uuid: str
    name: str
    summary: str | None = None
    labels: list[str] | None = None
    attributes: dict | None = None
    source_files: list[str] | None = None  # List of source file names
    video_sources: list[VideoSource] | None = None  # Video sources with playback info
    created_at: str
    updated_at: str


class Edge(BaseModel):
    uuid: str
    source_node_uuid: str
    target_node_uuid: str
    type: str
    name: str
    fact: str | None = None
    episodes: list[str] | None = None
    source_files: list[str] | None = None  # List of source file names extracted from episodes
    video_sources: list[VideoSource] | None = None  # Video sources with playback info
    created_at: str
    updated_at: str
    valid_at: str | None = None
    expired_at: str | None = None
    invalid_at: str | None = None


class RawTriplet(BaseModel):
    sourceNode: Node
    edge: Edge
    targetNode: Node


class GraphTripletsResponse(BaseModel):
    triplets: list[RawTriplet]
