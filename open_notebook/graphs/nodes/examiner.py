"""Background Examiner — independently evaluates learner progress after each exchange.

Runs as a background task after the main chat response is streamed. Uses a cheaper/faster
model to assess whether the learner's latest response demonstrates understanding of any
incomplete learning objectives. Results are pushed to an asyncio.Queue for the SSE
generator to relay as `objective_checked` events.

Conservative grading: only marks passed if the learner's response demonstrates the
SPECIFIC competency described in the objective, not just general topic awareness.
"""

import asyncio
import json
from typing import Optional

from loguru import logger

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.domain.learner_objective_progress import (
    LearnerObjectiveProgress,
    ProgressStatus,
    CompletedVia,
)
from open_notebook.utils import extract_text_from_response

EXAMINER_PROMPT = """You are a strict learning assessment examiner. Your job is to determine
whether a learner has demonstrated understanding of specific learning objectives based on
their latest conversation exchange.

## Rules
- Be CONSERVATIVE. Only mark an objective as passed if the learner's response clearly
  demonstrates the SPECIFIC competency described in the objective text.
- General topic awareness is NOT sufficient. The learner must show understanding of the
  specific skill, concept, or ability described.
- If unsure, mark as NOT passed. False negatives are acceptable; false positives are not.
- Base your assessment ONLY on what the learner said (user_message), not on what the AI
  teacher said.

## Objectives to evaluate
{objectives_json}

## Latest exchange
**Learner said:** {user_message}

**AI teacher responded:** {ai_response}

## Output format
Return a JSON array. For each objective, include:
- "objective_id": the objective's record ID
- "passed": true or false
- "evidence": brief explanation of why passed or not (1-2 sentences)

Return ONLY the JSON array, no other text.
"""


async def evaluate_exchange(
    user_message: str,
    ai_response: str,
    objectives_with_status: list[dict],
    user_id: str,
    notebook_id: str,
    result_queue: Optional[asyncio.Queue] = None,
) -> list[dict]:
    """Evaluate whether the latest exchange demonstrates learning objective mastery.

    Args:
        user_message: The learner's latest message
        ai_response: The AI teacher's response
        objectives_with_status: List of dicts with id, text, status, order
        user_id: Learner's user ID
        notebook_id: Notebook/module record ID
        result_queue: Optional queue to push results for SSE relay.
            Push None sentinel when done.

    Returns:
        List of dicts with objective_id, passed, evidence for objectives that passed
    """
    results = []

    try:
        # Filter to incomplete objectives only
        incomplete = [
            o for o in objectives_with_status
            if o.get("status") != "completed"
        ]

        if not incomplete:
            logger.debug("All objectives complete — skipping examiner")
            if result_queue:
                await result_queue.put(None)
            return results

        # Skip if learner message is too short to demonstrate understanding
        if len(user_message.strip()) < 20:
            logger.debug("Learner message too short for objective assessment")
            if result_queue:
                await result_queue.put(None)
            return results

        # Fetch full LearningObjective objects for richer grading context
        try:
            full_objectives = await LearningObjective.get_for_notebook(notebook_id)
            full_obj_map = {str(o.id): o for o in full_objectives}
        except Exception as e:
            logger.warning("Failed to load full objectives: {}", str(e))
            full_obj_map = {}

        # Build objectives JSON for the prompt
        objectives_for_prompt = []
        for obj in incomplete:
            obj_id = str(obj.get("id", ""))
            full_obj = full_obj_map.get(obj_id)
            entry = {
                "objective_id": obj_id,
                "text": obj.get("text", ""),
                "source_refs": full_obj.source_refs if full_obj else [],
            }
            objectives_for_prompt.append(entry)

        prompt = EXAMINER_PROMPT.format(
            objectives_json=json.dumps(objectives_for_prompt, indent=2),
            user_message=user_message[:2000],  # Truncate for token budget
            ai_response=ai_response[:2000],
        )

        # Use a cheaper/faster model for grading
        model = await provision_langchain_model(
            prompt, model_id=None, default_type="chat", max_tokens=1024
        )
        response = await model.ainvoke(prompt)
        raw_text = extract_text_from_response(response.content).strip()

        # Parse JSON response — handle markdown code fences
        if raw_text.startswith("```"):
            # Strip ```json ... ``` wrapper
            lines = raw_text.split("\n")
            raw_text = "\n".join(
                l for l in lines if not l.strip().startswith("```")
            )

        assessments = json.loads(raw_text)

        if not isinstance(assessments, list):
            logger.warning("Examiner returned non-list response: {}", type(assessments))
            if result_queue:
                await result_queue.put(None)
            return results

        # Process passed objectives
        for assessment in assessments:
            if not assessment.get("passed"):
                continue

            objective_id = assessment.get("objective_id", "")
            evidence = assessment.get("evidence", "")

            try:
                # Create progress record
                await LearnerObjectiveProgress.create(
                    user_id=user_id,
                    objective_id=objective_id,
                    status=ProgressStatus.COMPLETED,
                    completed_via=CompletedVia.CONVERSATION,
                    evidence=evidence,
                )

                # Count totals for the SSE event
                total_completed = await LearnerObjectiveProgress.count_completed_for_notebook(
                    user_id=user_id, notebook_id=notebook_id
                )
                total_objectives = await LearningObjective.count_for_notebook(notebook_id)
                all_complete = total_completed >= total_objectives

                # Find objective text
                obj_text = ""
                for o in objectives_with_status:
                    if str(o.get("id")) == objective_id:
                        obj_text = o.get("text", "")
                        break

                event_data = {
                    "objective_id": objective_id,
                    "objective_text": obj_text,
                    "evidence": evidence,
                    "total_completed": total_completed,
                    "total_objectives": total_objectives,
                    "all_complete": all_complete,
                }
                results.append(event_data)

                if result_queue:
                    await result_queue.put(event_data)

                logger.info(
                    "Examiner: objective {} passed ({}/{})",
                    objective_id, total_completed, total_objectives,
                )

            except Exception as e:
                logger.error(
                    "Error saving examiner result for objective {}: {}",
                    objective_id, str(e),
                )

    except json.JSONDecodeError as e:
        logger.warning("Examiner response was not valid JSON: {}", str(e))
    except Exception as e:
        logger.error("Examiner evaluation failed: {}", str(e), exc_info=True)

    # Signal completion
    if result_queue:
        await result_queue.put(None)

    return results
