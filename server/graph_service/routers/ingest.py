import asyncio
import logging
from contextlib import asynccontextmanager
from functools import partial

from fastapi import APIRouter, FastAPI, status
from graphiti_core.nodes import EpisodeType  # type: ignore
from graphiti_core.utils.maintenance.graph_data_operations import clear_data  # type: ignore

from graph_service.dto import AddEntityNodeRequest, AddMessagesRequest, Message, Result
from graph_service.zep_graphiti import ZepGraphitiDep, ZepGraphiti, get_entity_types_for_context
from graph_service.config import get_settings

logger = logging.getLogger(__name__)


class AsyncWorker:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.task = None
        self.graphiti_client = None  # Persistent client for background jobs

    async def initialize_client(self):
        """Create a persistent graphiti client for background jobs"""
        settings = get_settings()
        self.graphiti_client = ZepGraphiti(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )
        if settings.openai_base_url is not None:
            self.graphiti_client.llm_client.config.base_url = settings.openai_base_url
        if settings.openai_api_key is not None:
            self.graphiti_client.llm_client.config.api_key = settings.openai_api_key
        if settings.model_name is not None:
            self.graphiti_client.llm_client.model = settings.model_name
        logger.info("Background worker graphiti client initialized")

    async def worker(self):
        print("Worker loop starting...", flush=True)
        while True:
            try:
                job = await self.queue.get()
                print(f'Processing job (remaining queue: {self.queue.qsize()})', flush=True)
                try:
                    await job()
                    logger.info("Job completed successfully")
                except Exception as e:
                    logger.error(f"Job failed with error: {e}", exc_info=True)
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break

    async def start(self):
        await self.initialize_client()
        self.task = asyncio.create_task(self.worker())

    async def stop(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        while not self.queue.empty():
            self.queue.get_nowait()
        if self.graphiti_client:
            await self.graphiti_client.close()
            logger.info("Background worker graphiti client closed")


async_worker = AsyncWorker()


# NOTE: Worker lifecycle is managed in main.py app lifespan
router = APIRouter()


@router.post('/messages', status_code=status.HTTP_202_ACCEPTED)
async def add_messages(
    request: AddMessagesRequest,
):
    # Use the worker's persistent graphiti client instead of request-scoped dependency
    graphiti = async_worker.graphiti_client
    if graphiti is None:
        return Result(message='Worker not initialized', success=False)

    async def add_messages_task(m: Message, group_id: str):
        # Get entity types for healthcare ML context
        entity_types = get_entity_types_for_context("healthcare_ml")

        # Build source description with file_name and cloudflare_stream_id if provided
        source_desc = m.source_description
        metadata_parts = []
        if m.file_name:
            metadata_parts.append(f"file:{m.file_name}")
        if m.cloudflare_stream_id:
            metadata_parts.append(f"cfstream:{m.cloudflare_stream_id}")
        if metadata_parts:
            source_desc = f"[{';'.join(metadata_parts)}] {source_desc}".strip()

        # Use the worker's persistent client
        # NOTE: Don't pass uuid to add_episode - in graphiti_core, passing a uuid
        # means you want to UPDATE an existing episode. For new episodes, let
        # graphiti_core generate the uuid automatically.
        await async_worker.graphiti_client.add_episode(
            group_id=group_id,
            name=m.name,
            episode_body=f'{m.role or ""}({m.role_type}): {m.content}',
            reference_time=m.timestamp,
            source=EpisodeType.message,
            source_description=source_desc,
            entity_types=entity_types,
        )

    for m in request.messages:
        await async_worker.queue.put(partial(add_messages_task, m, request.group_id))

    return Result(message='Messages added to processing queue', success=True)


@router.post('/entity-node', status_code=status.HTTP_201_CREATED)
async def add_entity_node(
    request: AddEntityNodeRequest,
    graphiti: ZepGraphitiDep,
):
    node = await graphiti.save_entity_node(
        uuid=request.uuid,
        group_id=request.group_id,
        name=request.name,
        summary=request.summary,
    )
    return node


@router.delete('/entity-edge/{uuid}', status_code=status.HTTP_200_OK)
async def delete_entity_edge(uuid: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_entity_edge(uuid)
    return Result(message='Entity Edge deleted', success=True)


@router.delete('/group/{group_id}', status_code=status.HTTP_200_OK)
async def delete_group(group_id: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_group(group_id)
    return Result(message='Group deleted', success=True)


@router.delete('/episode/{uuid}', status_code=status.HTTP_200_OK)
async def delete_episode(uuid: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_episodic_node(uuid)
    return Result(message='Episode deleted', success=True)


@router.post('/clear', status_code=status.HTTP_200_OK)
async def clear(
    graphiti: ZepGraphitiDep,
):
    await clear_data(graphiti.driver)
    await graphiti.build_indices_and_constraints()
    return Result(message='Graph cleared', success=True)
