"""
Async Workflow Engine Example

This example demonstrates how to use the async workflow execution engine
to run Snakemake workflows without blocking.
"""

import asyncio
from pathlib import Path

from backend.services.snakemake.workflow_engine import (
    WorkflowExecutionEngine,
    WorkflowProgress,
    WorkflowStatus,
    get_workflow_engine,
    shutdown_workflow_engine,
)


async def progress_callback(progress: WorkflowProgress):
    """Callback function to receive progress updates."""
    print(f"[Progress] {progress.status.value}: {progress.progress_percentage:.1f}% "
          f"({progress.completed_jobs}/{progress.total_jobs} jobs)")

    if progress.messages:
        print(f"[Message] {progress.messages[-1]}")


async def main():
    """Main example function."""
    print("=" * 60)
    print("Async Workflow Engine Example")
    print("=" * 60)

    # Initialize the workflow engine
    print("\n1. Initializing workflow engine...")
    engine = await get_workflow_engine(max_concurrent_jobs=4)
    print("   Engine initialized!")

    # Register progress callback
    engine.add_progress_callback(progress_callback)

    # Create a sample Snakefile
    print("\n2. Creating sample workflow...")
    with tempfile.TemporaryDirectory() as tmpdir:
        workflow_dir = Path(tmpdir)
        snakefile = workflow_dir / "Snakefile"

        snakefile.write_text("""
rule all:
    input: "output.txt"

rule generate:
    output: "output.txt"
    shell: "echo 'Hello from async workflow!' > {output} && sleep 2"
""")
        print(f"   Created: {snakefile}")

        # Execute the workflow
        print("\n3. Executing workflow...")
        workflow_id = await engine.execute_workflow(
            workflow_path=snakefile,
            workdir=workflow_dir,
            dry_run=False,
            jobs=1,
        )
        print(f"   Workflow ID: {workflow_id}")

        # Monitor progress
        print("\n4. Monitoring progress...")
        while True:
            progress = await engine.get_workflow_status(workflow_id)
            if not progress:
                print("   Workflow not found!")
                break

            if progress.status in (
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.CANCELLED,
            ):
                print(f"\n   Workflow finished with status: {progress.status.value}")
                print(f"   Duration: {progress.duration_seconds:.2f}s")
                break

            await asyncio.sleep(0.5)

        # Check final status
        final_progress = await engine.get_workflow_status(workflow_id)
        if final_progress:
            print(f"\n5. Final Status:")
            print(f"   Status: {final_progress.status.value}")
            print(f"   Jobs: {final_progress.completed_jobs}/{final_progress.total_jobs}")
            print(f"   Messages: {len(final_progress.messages)}")

    # Shutdown
    print("\n6. Shutting down...")
    await shutdown_workflow_engine()
    print("   Done!")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    import tempfile
    asyncio.run(main())
