import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_event_emitter, get_orchestrator
from app.api.schemas import EventItem, GeneratedFileInfo, TaskEventsResponse, TaskRequest, TaskResponse
from app.orchestrator import Orchestrator, ProgressEventEmitter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=None, status_code=status.HTTP_200_OK)
def create_task(
    request: TaskRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> TaskResponse:
    """
    Executes a user task through SOAR's core orchestration pipeline.
    Dispatches to direct answer, code execution, or multi-step agent mode with
    adaptive local model routing.
    """
    task_text = request.task.strip()
    if not task_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task prompt must not be empty or whitespace.",
        )

    try:
        result: Dict[str, Any] = orchestrator.process_task(
            task=task_text,
            run_id=request.run_id,
            model_id=request.model,
            attached_file_ids=request.attached_file_ids,
        )

        run_id = result.get("run_id", "")
        task_status = result.get("status", "completed")
        answer = result.get("response", "")
        execution_mode = result.get("execution_mode", "direct_answer")
        citations = result.get("citations", [])
        model_meta = result.get("model", {})
        actual_model = model_meta.get("actual") if isinstance(model_meta, dict) else str(model_meta)

        events = result.get("events", [])

        raw_generated = result.get("generated_files", [])
        if not isinstance(raw_generated, list):
            logger.warning("Ignoring malformed generated_files payload: %r", raw_generated)
            raw_generated = []
        generated_files = [
            GeneratedFileInfo(
                file_id=f["file_id"],
                filename=f["filename"],
                mime_type=f.get("mime_type"),
            )
            for f in raw_generated
            if isinstance(f, dict) and f.get("file_id") and f.get("filename")
        ]

        response = TaskResponse(
            run_id=run_id,
            status=task_status,
            answer=str(answer or ""),
            model=actual_model or "unknown",
            execution_mode=execution_mode,
            citations=citations,
            model_details=model_meta if isinstance(model_meta, dict) else None,
            events=events,
            generated_files=generated_files,
        )
        # Return a plain JSON-compatible object so FastAPI/Starlette does not
        # perform a second validation pass after the route has completed.
        return response.model_dump() if hasattr(response, "model_dump") else response.dict()

    except ValueError as e:
        logger.warning(f"Validation error during task processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Error during task processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task execution failed: {str(e)}",
        )


@router.get("/{run_id}/events", response_model=TaskEventsResponse)
def get_task_events(
    run_id: str,
    emitter: ProgressEventEmitter = Depends(get_event_emitter),
) -> TaskEventsResponse:
    """
    Retrieves chronological execution progress checkpoints for a specific run_id.
    """
    if not run_id or not run_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="run_id must be a non-empty string.",
        )

    events_list = emitter.get_events_for_run(run_id.strip())
    if not events_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No progress events found for run ID '{run_id}'.",
        )

    parsed_items = [
        EventItem(
            event_id=e["event_id"],
            run_id=e.get("run_id"),
            stage=e["stage"],
            status=e["status"],
            message=e["message"],
            timestamp=e["timestamp"],
            metadata=e.get("metadata", {}),
        )
        for e in events_list
    ]

    return TaskEventsResponse(
        run_id=run_id,
        events=parsed_items,
    )
