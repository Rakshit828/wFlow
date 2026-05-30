import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from loguru import logger
from src.workflows.workflow import DynamicWorkflow
from src.workflows.nodes import NODES_MAP
from src.db.mongo_db import MongoClient





async def run_worker():
    """
    Start the Temporal worker.

    This worker will:
    1. Connect to the Temporal server
    2. Register the DynamicWorkflow and execute_node_activity
    3. Listen for and process workflow tasks and activity tasks
    """

    # Create a Temporal client
    mongo = MongoClient("mongodb://localhost:27017")
    await mongo.get_database("wflow_db")
    await mongo.init_beanie_odm()


    client = await Client.connect(
        "localhost:7233",  # Default Temporal server address
        namespace="default",  # Change to your namespace if needed
    )

    logger.info("Successfully connected to Temporal server")

    # Create a worker for the specified task queue
    worker = Worker(
        client,
        task_queue="default",  # Change to your task queue name if needed
        workflows=[DynamicWorkflow],
        activities=[node.fn for node in NODES_MAP.values()],
    )

    logger.info("Worker registered with workflows and activities")

    # Run the worker
    try:
        logger.info("Starting Temporal worker...")
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
    except Exception as e:
        logger.error(f"Worker encountered an error: {e}", exc_info=True)
        raise


def main():
    """Main entry point for the worker."""
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
