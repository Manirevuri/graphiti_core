import logging
from typing import Annotated

from fastapi import Depends, HTTPException
from graphiti_core import Graphiti  # type: ignore
from graphiti_core.edges import EntityEdge  # type: ignore
from graphiti_core.errors import EdgeNotFoundError, GroupsEdgesNotFoundError, NodeNotFoundError
from graphiti_core.llm_client import LLMClient  # type: ignore
from graphiti_core.nodes import EntityNode, EpisodicNode  # type: ignore

from pydantic import BaseModel, Field
from graph_service.config import ZepEnvDep
from graph_service.dto import FactResult
from graph_service.dto.retrieve import Node, Edge, RawTriplet


# Dynamic Entity Type Definitions for better categorization
class Person(BaseModel):
    """A human person mentioned in the conversation."""
    first_name: str | None = Field(None, description='First name of the person')
    last_name: str | None = Field(None, description='Last name of the person')
    occupation: str | None = Field(None, description='Job or profession of the person')
    role: str | None = Field(None, description='Professional role or title')


class Organization(BaseModel):
    """A company, institution, or organized group."""
    organization_type: str | None = Field(None, description='Type of organization (company, NGO, etc.)')
    industry: str | None = Field(None, description='Industry or sector')
    location: str | None = Field(None, description='Geographic location')


class Technology(BaseModel):
    """Software, programming languages, tools, or technical systems."""
    category: str | None = Field(None, description='Type of technology (language, framework, tool)')
    version: str | None = Field(None, description='Version if applicable')
    purpose: str | None = Field(None, description='Primary use case or purpose')


class Concept(BaseModel):
    """Abstract concepts, ideas, methodologies, or processes."""
    domain: str | None = Field(None, description='Field or domain this concept belongs to')
    complexity: str | None = Field(None, description='Complexity level (simple, moderate, complex)')


class MedicalConcept(BaseModel):
    """Healthcare and medical-related concepts."""
    medical_domain: str | None = Field(None, description='Medical specialty or domain')
    patient_related: bool | None = Field(None, description='Whether directly related to patient care')


class Regulation(BaseModel):
    """Legal regulations, standards, and compliance requirements."""
    regulatory_body: str | None = Field(None, description='Organization that enforces this regulation')
    scope: str | None = Field(None, description='Geographic or industry scope')
    compliance_level: str | None = Field(None, description='Required compliance level')


# Dynamic entity type registry
def get_entity_types_for_context(context: str = "healthcare_ml") -> dict[str, type[BaseModel]]:
    """
    Get entity types dynamically based on context.
    This allows different entity schemas for different domains.
    """
    if context == "healthcare_ml":
        return {
            'Person': Person,
            'Organization': Organization, 
            'Technology': Technology,
            'Concept': Concept,
            'MedicalConcept': MedicalConcept,
            'Regulation': Regulation,
        }
    elif context == "general":
        return {
            'Person': Person,
            'Organization': Organization,
            'Technology': Technology,
            'Concept': Concept,
        }
    else:
        # Default minimal set
        return {
            'Person': Person,
            'Organization': Organization,
        }

logger = logging.getLogger(__name__)


class ZepGraphiti(Graphiti):
    def __init__(self, uri: str, user: str, password: str, llm_client: LLMClient | None = None):
        super().__init__(uri, user, password, llm_client)

    async def save_entity_node(self, name: str, uuid: str, group_id: str, summary: str = ''):
        new_node = EntityNode(
            name=name,
            uuid=uuid,
            group_id=group_id,
            summary=summary,
        )
        await new_node.generate_name_embedding(self.embedder)
        await new_node.save(self.driver)
        return new_node

    async def get_entity_edge(self, uuid: str):
        try:
            edge = await EntityEdge.get_by_uuid(self.driver, uuid)
            return edge
        except EdgeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e

    async def delete_group(self, group_id: str):
        try:
            edges = await EntityEdge.get_by_group_ids(self.driver, [group_id])
        except GroupsEdgesNotFoundError:
            logger.warning(f'No edges found for group {group_id}')
            edges = []

        nodes = await EntityNode.get_by_group_ids(self.driver, [group_id])

        episodes = await EpisodicNode.get_by_group_ids(self.driver, [group_id])

        for edge in edges:
            await edge.delete(self.driver)

        for node in nodes:
            await node.delete(self.driver)

        for episode in episodes:
            await episode.delete(self.driver)

    async def delete_entity_edge(self, uuid: str):
        try:
            edge = await EntityEdge.get_by_uuid(self.driver, uuid)
            await edge.delete(self.driver)
        except EdgeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e

    async def delete_episodic_node(self, uuid: str):
        try:
            episode = await EpisodicNode.get_by_uuid(self.driver, uuid)
            await episode.delete(self.driver)
        except NodeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e

    async def get_all_nodes_by_group(self, group_id: str) -> list[EntityNode]:
        """Get all EntityNodes for a specific group_id"""
        try:
            nodes = await EntityNode.get_by_group_ids(self.driver, [group_id])
            return nodes
        except Exception as e:
            logger.error(f"Error fetching nodes for group {group_id}: {e}")
            return []

    async def get_all_edges_by_group(self, group_id: str) -> list[EntityEdge]:
        """Get all EntityEdges for a specific group_id"""
        try:
            edges = await EntityEdge.get_by_group_ids(self.driver, [group_id])
            return edges
        except GroupsEdgesNotFoundError:
            logger.warning(f"No edges found for group {group_id}")
            return []
        except Exception as e:
            logger.error(f"Error fetching edges for group {group_id}: {e}")
            return []

    async def get_graph_triplets(self, group_id: str) -> list[RawTriplet]:
        """Get all graph triplets (nodes + edges) for a specific group_id in Zep-compatible format"""
        # Get all nodes and edges for the group
        nodes = await self.get_all_nodes_by_group(group_id)
        edges = await self.get_all_edges_by_group(group_id)
        
        # Transform to triplets
        triplets = create_triplets_from_nodes_and_edges(nodes, edges)
        return triplets


async def get_graphiti(settings: ZepEnvDep):
    client = ZepGraphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    if settings.openai_base_url is not None:
        client.llm_client.config.base_url = settings.openai_base_url
    if settings.openai_api_key is not None:
        client.llm_client.config.api_key = settings.openai_api_key
    if settings.model_name is not None:
        client.llm_client.model = settings.model_name

    try:
        yield client
    finally:
        await client.close()


async def initialize_graphiti(settings: ZepEnvDep):
    client = ZepGraphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await client.build_indices_and_constraints()


def get_fact_result_from_edge(edge: EntityEdge):
    return FactResult(
        uuid=edge.uuid,
        name=edge.name,
        fact=edge.fact,
        valid_at=edge.valid_at,
        invalid_at=edge.invalid_at,
        created_at=edge.created_at,
        expired_at=edge.expired_at,
    )


def classify_entity_type(name: str, summary: str = "") -> str:
    """Classify entity type based on name and summary for better visualization"""
    name_lower = name.lower()
    summary_lower = summary.lower()
    
    # People/Person names (check this FIRST to avoid false positives)
    if any(indicator in summary_lower for indicator in ['dr. ', 'doctor ', 'engineer', 'software engineer', 'professional']):
        return "Person"
    # Check for person name patterns (First Last, or single professional names)
    if (name.count(' ') == 1 and name[0].isupper() and 
        not any(tech in name_lower for tech in ['model', 'analytics', 'data', 'system', 'computer'])):
        return "Person"
    
    # Technologies/Tools 
    if any(tech in name_lower for tech in ['python', 'scikit-learn', 'pandas', 'tensorflow', 'pytorch', 'sql', 'api']):
        return "Technology"
    if any(indicator in summary_lower for indicator in ['programming language', 'library', 'framework', 'python library']):
        return "Technology"
    
    # Companies/Organizations
    if any(indicator in summary_lower for indicator in ['company', 'organization', 'corp', 'client', 'firm']):
        return "Organization"
    if name_lower.endswith('corp') or name_lower.endswith('inc') or name_lower.endswith('ltd'):
        return "Organization"
    
    # Regulations/Standards
    if any(reg in name_lower for reg in ['hipaa', 'gdpr', 'regulation', 'standard', 'compliance']):
        return "Regulation"
    
    # Medical/Health concepts
    if any(medical in name_lower for medical in ['patient', 'diabetes', 'hospitalization', 'health']):
        return "Medical"
    
    # Concepts/Abstract (check this last to avoid false matches)
    if any(concept in name_lower for concept in ['model', 'analytics', 'data', 'privacy', 'algorithm']):
        return "Concept"
    if any(indicator in summary_lower for indicator in ['concept', 'approach', 'method', 'process', 'consideration']):
        return "Concept"
    
    # Default fallback
    return "Entity"


def transform_entity_node_to_zep_node(entity_node: EntityNode) -> Node:
    """Transform Graphiti EntityNode to Zep-compatible Node format with enhanced categorization"""
    # Classify the entity type for better visualization
    entity_type = classify_entity_type(entity_node.name, entity_node.summary or "")
    
    # Create enhanced labels (ensure no duplicates)
    enhanced_labels = [entity_type]
    if entity_node.labels and entity_node.labels != ["Entity"]:
        # Only add labels that aren't already in the list
        for label in entity_node.labels:
            if label not in enhanced_labels:
                enhanced_labels.append(label)
    
    return Node(
        uuid=entity_node.uuid,
        name=entity_node.name,
        summary=entity_node.summary or "",
        labels=enhanced_labels,
        attributes={
            **(entity_node.attributes or {}),
            "entity_type": entity_type,
            "original_labels": entity_node.labels
        },
        created_at=entity_node.created_at.isoformat(),
        updated_at=entity_node.created_at.isoformat(),  # Graphiti doesn't track updated_at separately
    )


def transform_entity_edge_to_zep_edge(entity_edge: EntityEdge) -> Edge:
    """Transform Graphiti EntityEdge to Zep-compatible Edge format"""
    return Edge(
        uuid=entity_edge.uuid,
        source_node_uuid=entity_edge.source_node_uuid,
        target_node_uuid=entity_edge.target_node_uuid,
        type="",  # Graphiti doesn't have explicit edge types
        name=entity_edge.name,
        fact=entity_edge.fact,
        episodes=entity_edge.episodes,
        created_at=entity_edge.created_at.isoformat(),
        updated_at=entity_edge.created_at.isoformat(),  # Graphiti doesn't track updated_at separately
        valid_at=entity_edge.valid_at.isoformat() if entity_edge.valid_at else None,
        expired_at=entity_edge.expired_at.isoformat() if entity_edge.expired_at else None,
        invalid_at=entity_edge.invalid_at.isoformat() if entity_edge.invalid_at else None,
    )


def create_triplets_from_nodes_and_edges(nodes: list[EntityNode], edges: list[EntityEdge]) -> list[RawTriplet]:
    """Create triplets by combining nodes and edges, similar to Zep's logic"""
    # Create a lookup map for nodes by UUID
    node_map = {node.uuid: node for node in nodes}
    
    # Create triplets from edges
    triplets = []
    connected_node_ids = set()
    
    for edge in edges:
        source_node = node_map.get(edge.source_node_uuid)
        target_node = node_map.get(edge.target_node_uuid)
        
        if source_node and target_node:
            # Track connected nodes
            connected_node_ids.add(source_node.uuid)
            connected_node_ids.add(target_node.uuid)
            
            triplets.append(RawTriplet(
                sourceNode=transform_entity_node_to_zep_node(source_node),
                edge=transform_entity_edge_to_zep_edge(edge),
                targetNode=transform_entity_node_to_zep_node(target_node),
            ))
    
    # Handle isolated nodes (nodes without edges)
    for node in nodes:
        if node.uuid not in connected_node_ids:
            # Create a virtual self-referencing edge for isolated nodes
            virtual_edge = Edge(
                uuid=f"isolated-node-{node.uuid}",
                source_node_uuid=node.uuid,
                target_node_uuid=node.uuid,
                type="_isolated_node_",
                name="",
                fact=None,
                episodes=None,
                created_at=node.created_at.isoformat(),
                updated_at=node.created_at.isoformat(),
                valid_at=None,
                expired_at=None,
                invalid_at=None,
            )
            
            zep_node = transform_entity_node_to_zep_node(node)
            triplets.append(RawTriplet(
                sourceNode=zep_node,
                edge=virtual_edge,
                targetNode=zep_node,
            ))
    
    return triplets


ZepGraphitiDep = Annotated[ZepGraphiti, Depends(get_graphiti)]
