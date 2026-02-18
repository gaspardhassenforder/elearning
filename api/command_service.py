from typing import Any, Dict, List, Optional

from loguru import logger
from surreal_commands import get_command_status, submit_command
import surreal_commands


class CommandService:
    """Generic service layer for command operations"""

    @staticmethod
    async def submit_command_job(
        module_name: str,  # Actually app_name for surreal-commands
        command_name: str,
        command_args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Submit a generic command job for background processing"""
        logger.info(f"Submitting command: {module_name}.{command_name}")
        logger.debug(f"Command args keys: {list(command_args.keys())}")
        try:
            # Ensure command modules are imported before submitting
            # This is needed because submit_command validates against local registry
            try:
                import commands.podcast_commands  # noqa: F401
                logger.debug("Command modules imported successfully")
            except ImportError as import_err:
                logger.error("Failed to import command modules: {}", str(import_err))
                raise ValueError("Command modules not available")

            # surreal-commands expects: submit_command(app_name, command_name, args)
            logger.debug(f"Calling submit_command({module_name}, {command_name}, ...)")
            cmd_id = submit_command(
                module_name,  # This is actually the app name (e.g., "open_notebook")
                command_name,  # Command name (e.g., "process_text")
                command_args,  # Input data
            )
            # Convert RecordID to string if needed
            if not cmd_id:
                logger.error("submit_command returned None/empty job_id")
                raise ValueError("Failed to get cmd_id from submit_command")
            cmd_id_str = str(cmd_id)
            logger.info(
                f"Command job submitted successfully: {cmd_id_str} for {module_name}.{command_name}"
            )
            return cmd_id_str

        except Exception as e:
            logger.error("Failed to submit command job {}.{}: {}", module_name, command_name, str(e))
            logger.exception(e)
            raise

    @staticmethod
    async def get_command_status(job_id: str) -> Dict[str, Any]:
        """Get status of any command job"""
        logger.debug(f"Getting status for job: {job_id}")
        try:
            # Ensure job_id has the command: prefix required by surreal_commands
            full_job_id = job_id if job_id.startswith("command:") else f"command:{job_id}"
            status = await get_command_status(full_job_id)
            status_str = status.status if status else "unknown"
            logger.debug(f"Job {job_id} status: {status_str}")

            # Fetch progress directly from the command record.
            # CommandResult doesn't include a progress field, but we write one
            # via _update_command_progress() during podcast generation.
            progress = None
            try:
                from open_notebook.database.repository import repo_query
                cmd_data = await repo_query(
                    "SELECT progress FROM $cmd_id",
                    {"cmd_id": full_job_id},
                )
                if cmd_data and isinstance(cmd_data, list) and len(cmd_data) > 0:
                    progress = cmd_data[0].get("progress")
            except Exception:
                pass

            return {
                "job_id": job_id,
                "status": status_str,
                "result": status.result if status else None,
                "error_message": getattr(status, "error_message", None)
                if status
                else None,
                "created": str(status.created)
                if status and hasattr(status, "created") and status.created
                else None,
                "updated": str(status.updated)
                if status and hasattr(status, "updated") and status.updated
                else None,
                "progress": progress,
            }
        except Exception as e:
            logger.error("Failed to get command status for job {}: {}", job_id, str(e))
            raise

    @staticmethod
    async def list_command_jobs(
        module_filter: Optional[str] = None,
        command_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List command jobs with optional filtering"""
        # This will be implemented with proper SurrealDB queries
        # For now, return empty list as this is foundation phase
        return []

    @staticmethod
    async def cancel_command_job(job_id: str) -> bool:
        """Cancel a running command job"""
        logger.info(f"Cancelling job: {job_id}")
        try:
            # Best-effort: use whatever cancellation hook surreal-commands exposes.
            # Different versions may name this differently.
            cancel_candidates = [
                "cancel_command_job",
                "cancel_command",
                "cancel_job",
                "stop_command",
                "stop_job",
                "abort_command",
                "abort_job",
            ]

            cancel_fn = None
            for name in cancel_candidates:
                candidate = getattr(surreal_commands, name, None)
                if callable(candidate):
                    cancel_fn = candidate
                    logger.debug(f"Found cancellation function: {name}")
                    break

            if cancel_fn is None:
                logger.warning(
                    "surreal-commands cancellation API not found; cannot cancel job"
                )
                return False

            # Support both sync + async cancellation functions.
            logger.debug(f"Calling cancellation function for job {job_id}")
            result = cancel_fn(job_id)
            if hasattr(result, "__await__"):
                result = await result

            success = bool(result) if result is not None else True
            if success:
                logger.info(f"Successfully cancelled job: {job_id}")
            else:
                logger.warning(f"Cancellation returned false for job: {job_id}")
            return success
        except Exception as e:
            logger.error("Failed to cancel command job {}: {}", job_id, str(e))
            logger.exception(e)
            raise
