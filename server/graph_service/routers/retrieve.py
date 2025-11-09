from datetime import datetime, timezone

from fastapi import APIRouter, status

from graph_service.dto import (
    GetMemoryRequest,
    GetMemoryResponse,
    Message,
    SearchQuery,
    SearchResults,
)
from graph_service.zep_graphiti import ZepGraphitiDep, get_fact_result_from_edge

router = APIRouter()

@router.post('/search', status_code=status.HTTP_200_OK)
async def search(query: SearchQuery, graphiti: ZepGraphitiDep):
    relevant_edges = await graphiti.search(
        group_ids=query.group_ids,
        query=query.query,
        num_results=query.max_facts,
    )
    facts = [get_fact_result_from_edge(edge) for edge in relevant_edges]
    return SearchResults(
        facts=facts,
    )


@router.get('/entity-edge/{uuid}', status_code=status.HTTP_200_OK)
async def get_entity_edge(uuid: str, graphiti: ZepGraphitiDep):
    entity_edge = await graphiti.get_entity_edge(uuid)
    return get_fact_result_from_edge(entity_edge)


@router.get('/episodes/{group_id}', status_code=status.HTTP_200_OK)
async def get_episodes(group_id: str, last_n: int, graphiti: ZepGraphitiDep):
    episodes = await graphiti.retrieve_episodes(
        group_ids=[group_id], last_n=last_n, reference_time=datetime.now(timezone.utc)
    )
    return episodes


@router.post('/get-memory', status_code=status.HTTP_200_OK)
async def get_memory(
    request: GetMemoryRequest,
    graphiti: ZepGraphitiDep,
):
    combined_query = compose_query_from_messages(request.messages)
    result = await graphiti.search(
        group_ids=[request.group_id],
        query=combined_query,
        num_results=request.max_facts,
    )
    facts = [get_fact_result_from_edge(edge) for edge in result]
    return GetMemoryResponse(facts=facts)


def compose_query_from_messages(messages: list[Message]):
    combined_query = ''
    for message in messages:
        combined_query += f'{message.role_type or ""}({message.role or ""}): {message.content}\n'
    return combined_query


# Graph visualization endpoints compatible with Zep format
@router.get('/graph/{group_id}/nodes', status_code=status.HTTP_200_OK)
async def get_graph_nodes(group_id: str, graphiti: ZepGraphitiDep):
    """Get all nodes for a specific group_id"""
    nodes = await graphiti.get_all_nodes_by_group(group_id)
    from graph_service.zep_graphiti import transform_entity_node_to_zep_node
    return [transform_entity_node_to_zep_node(node) for node in nodes]


@router.get('/graph/{group_id}/edges', status_code=status.HTTP_200_OK) 
async def get_graph_edges(group_id: str, graphiti: ZepGraphitiDep):
    """Get all edges for a specific group_id"""
    edges = await graphiti.get_all_edges_by_group(group_id)
    from graph_service.zep_graphiti import transform_entity_edge_to_zep_edge
    return [transform_entity_edge_to_zep_edge(edge) for edge in edges]


@router.get('/graph/{group_id}/triplets', status_code=status.HTTP_200_OK)
async def get_graph_triplets(group_id: str, graphiti: ZepGraphitiDep):
    """Get all graph triplets (nodes + edges) for a specific group_id in Zep-compatible format"""
    triplets = await graphiti.get_graph_triplets(group_id)
    from graph_service.dto.retrieve import GraphTripletsResponse
    return GraphTripletsResponse(triplets=triplets)
