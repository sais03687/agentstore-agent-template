"""Example agent — the smallest thing that is still honest.

Two functions are required. The platform imports both when the container starts,
so a package missing either cannot run at all:

    run_agent     — called for every inbound message
    resume_agent  — called when a decision you waited on comes back

Everything else here is replaceable. What is worth keeping is the shape: ask the
model for a named JSON structure, check you got it, and say so when you did not.
"""
import json
import os
from typing import Any, Callable

from langchain_openai import ChatOpenAI
from platform_llm import StructuredLLM, has_any

AGENT_NAME = os.environ.get("AGENT_NAME", "Example Agent")

# The platform injects these. It pays for the calls; your code never holds a
# provider key of its own.
llm = ChatOpenAI(
    model=os.environ["LLM_MODEL"],
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
    temperature=0,
)
structured = StructuredLLM(model=os.environ["LLM_MODEL"])

ANSWER_SCHEMA = {
    "name": "answer",
    "schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "unsure_about": {
                "type": "array",
                "items": {"type": "string"},
                "description": "anything the message did not say that you had to work around",
            },
        },
        "required": ["answer", "unsure_about"],
        "additionalProperties": False,
    },
}

# The field names are in the prompt as well as the schema on purpose: the schema
# only reaches the model on anthropic/* models. Everything else is asked for
# plain JSON, which guarantees valid JSON and nothing about your field names —
# ask without saying them and the model picks its own.
PROMPT = """Answer this message.

Answer with JSON in exactly this shape, using exactly these field names:

{{
  "answer": "the reply, in plain sentences",
  "unsure_about": ["anything the message did not say that you had to work around"]
}}

Do not state anything the message does not support. If you cannot answer, say
so in "answer" rather than guessing.

MESSAGE:
{message}
"""


async def run_agent(
    content: str,
    context: dict[str, Any],
    **tools: Callable,
) -> dict[str, Any]:
    """Called for every inbound message.

    `content` is the message text. Everything about the message — sender,
    subject, thread_id — is in `context`.

    `**tools` is how the platform passes what you asked for. Name the ones you
    want as keyword arguments instead and you get exactly those: approve_fn and
    resolve_fn for human approval, graph_fn for Microsoft 365, contribute_fn /
    search_fn / use_fn for shared learning, and the file and verification
    helpers. See the creator docs for the full list.
    """
    message = (content or "").strip()
    if not message:
        return {
            "action": "reply_email",
            "text": "There was no text in that message, so there is nothing for me to "
                    "answer. Send it again with the question in the body.",
            "needs_approval": False,
        }

    raw = await structured.ainvoke(
        llm, PROMPT.format(message=message[:12000]), timeout=120, schema=ANSWER_SCHEMA
    )
    try:
        parsed = json.loads(raw.content) if isinstance(raw.content, str) else raw.content
    except (json.JSONDecodeError, TypeError):
        parsed = None

    # An object carrying none of the fields you asked for is an unreadable
    # answer, not an empty one. Reporting it as a result is how a parsing
    # failure turns into a confident wrong answer.
    if not has_any(parsed, ("answer", "unsure_about")):
        return {
            "action": "reply_email",
            "text": "I could not read a clean answer back from the model for that "
                    "message, so I have not guessed at one. Send it again and I will retry.",
            "needs_approval": False,
        }

    return {
        "action": "reply_email",
        "text": parsed.get("answer") or "I do not have an answer for that.",
        # Up to three things the reader should check. They are shown with the
        # reply, and they are the difference between an answer and a claim.
        "check": list(parsed.get("unsure_about") or [])[:3],
        "needs_approval": False,
    }


async def resume_agent(thread_id: str, resolution: dict, **tools: Callable) -> dict:
    """Called when a decision this run was waiting on comes back.

    Required even in an agent that never pauses, because the platform imports it
    at startup. A buyer's policy can queue outbound mail for approval regardless
    of what the agent asked for, so this can be reached without you queuing
    anything yourself.
    """
    status = str((resolution or {}).get("status", "")).upper()
    if status in ("APPROVED", "EDITED"):
        return {"action": "none"}
    return {
        "action": "reply_email",
        "text": "That was not approved, so I have not sent anything further.",
        "needs_approval": False,
    }
