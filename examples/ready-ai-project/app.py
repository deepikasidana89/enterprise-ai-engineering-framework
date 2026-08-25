"""Illustrative AI service with explicit engineering controls."""

import logging

from opentelemetry import trace
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("ready-ai-project")


class Question(BaseModel):
    text: str = Field(min_length=1, max_length=500)


def policy_check(answer: str) -> str:
    """Apply an output guardrail before returning model content."""
    return sanitize_output(answer)


def sanitize_output(answer: str) -> str:
    return answer.strip()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
def call_model(question: Question, client) -> str:
    with tracer.start_as_current_span("model_call"):
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": question.text}],
            timeout=10,
        )
        answer = response.choices[0].message.content or ""
        logger.info("AI interaction completed")
        return policy_check(answer)
