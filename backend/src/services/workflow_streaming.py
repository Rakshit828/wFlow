from enum import Enum
from typing import Dict, TypeAlias, Any, AsyncGenerator, TypeVar, TypedDict
import asyncio
from temporalio.client import Client
from temporalio.contrib.workflow_streams import (
    WorkflowStreamClient,
    TopicHandle,
)
from loguru import logger


NodeResultType: TypeAlias = Dict[str, Any]

class WorkflowRunStatus:
    pass 

class WorkflowStatusResultType(TypedDict):
    status: WorkflowRunStatus


T = TypeVar("T")


class StreamingChannels(str, Enum):
    NODE_RESULT_CHANNEL = (
        "NODE_RESULT_CHANNEL"  # Channel for recieving every nodes ouputs.
    )
    WORKFLOW_STATUS_CHANNEL = "WORKFLOW_STATUS_CHANNEL"


OUTPUT_MAP: Dict[StreamingChannels, NodeResultType] = {
    StreamingChannels.NODE_RESULT_CHANNEL: NodeResultType,
    StreamingChannels.WORKFLOW_STATUS_CHANNEL: WorkflowStatusResultType,
}


async def workflow_listener(
    temporal_client: Client, workflow_id: str
) -> AsyncGenerator[Any, None]:
    stream_client = WorkflowStreamClient.create(
        client=temporal_client, workflow_id=workflow_id
    )

    lock: asyncio.Lock = asyncio.Lock()

    topic_handlers = [
        stream_client.topic(name=topic.value, type=OUTPUT_MAP[topic])
        for topic in StreamingChannels
    ]

    async def consume(topic_handle: TopicHandle):
        async for item in topic_handle.subscribe():
            logger.info(f"Raw data is : {item.data}")

            async with lock:
                await queue.put(item.data)

    queue = asyncio.Queue()

    tasks = [asyncio.create_task(consume(handler)) for handler in topic_handlers]

    logger.info(f"THe tasks are : {len(tasks)}")

    terminate: bool = False

    try:
        while True:
            if terminate:
                logger.info(f"Workflow completed. Closing Connection...")
                break
            data = await queue.get()

            if data.get("status") == WorkflowRunStatus.COMPLETED:
                terminate = True

            yield f"data: {data}\n\n"

        return
    finally:
        for t in tasks:
            t.cancel()

        lock = None
        queue = None
