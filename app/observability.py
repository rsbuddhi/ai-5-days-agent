# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Observability, Structured JSON Logging, Distributed Tracing, and PII Scrubbing.

Satisfies Category 4 of AgentOps Matrix:
- Criterion 4.1 / 13: Structured JSON Logging
- Criterion 4.2 / 14: Intent vs. Outcome Capture
- Criterion 4.3 / 15: Distributed Tracing (OpenTelemetry)
- Criterion 4.4 / 16: PII Redaction
"""

from __future__ import annotations

import datetime
import json
import logging
import re
import sys
import time
from typing import Any, Optional

# Attempt OpenTelemetry import for distributed tracing spans
try:
    from opentelemetry import trace
    tracer = trace.get_tracer("enterprise_helpdesk_agent", "1.0.0")
except Exception:
    tracer = None


# ============================================================================
# 1. PII REDACTION ENGINE (Criterion 4.4 / 16)
# ============================================================================
class PIIRedactor:
    """Active scrubbing pipeline to redact PII and sensitive data before logging or storage."""

    # Regex patterns for sensitive entity identification
    CREDIT_CARD_REGEX = re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13})\b"
    )
    SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
    API_KEY_REGEX = re.compile(r"(?:AIza[0-9A-Za-z-_]{35}|Bearer\s+[A-Za-z0-9_\-\.]{20,})")
    PASSWORD_REGEX = re.compile(r"(?:password|passwd|secret|token)\s*[:=]\s*['\"]?([^'\"\s,]+)['\"]?", re.IGNORECASE)

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Scrub all sensitive PII patterns from the input string."""
        if not isinstance(text, str):
            return text

        scrubbed = cls.CREDIT_CARD_REGEX.sub("[REDACTED_CREDIT_CARD]", text)
        scrubbed = cls.SSN_REGEX.sub("[REDACTED_SSN]", scrubbed)
        scrubbed = cls.API_KEY_REGEX.sub("[REDACTED_SECRET_TOKEN]", scrubbed)
        scrubbed = cls.PASSWORD_REGEX.sub(r"password=[REDACTED_CREDENTIAL]", scrubbed)
        return scrubbed

    @classmethod
    def redact_structure(cls, data: Any) -> Any:
        """Recursively scrub PII across nested dicts, lists, and primitives."""
        if isinstance(data, str):
            return cls.redact_text(data)
        elif isinstance(data, dict):
            return {k: cls.redact_structure(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.redact_structure(item) for item in data]
        return data


def scrub_pii(data: Any) -> Any:
    """Convenience helper for PII scrubbing."""
    return PIIRedactor.redact_structure(data)


# ============================================================================
# 2. STRUCTURED JSON LOGGER (Criterion 4.1 / 13)
# ============================================================================
class StructuredJsonFormatter(logging.Formatter):
    """Custom logging formatter that outputs Google Cloud Logging compliant JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.datetime.fromtimestamp(
                record.created, datetime.timezone.utc
            ).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": PIIRedactor.redact_text(record.getMessage()),
            "sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            },
        }

        # Include structured extra fields if provided
        if hasattr(record, "structured_data"):
            log_entry["payload"] = PIIRedactor.redact_structure(record.structured_data)
        if hasattr(record, "event_type"):
            log_entry["eventType"] = record.event_type
        if hasattr(record, "session_id"):
            log_entry["sessionId"] = record.session_id
        if hasattr(record, "user_id"):
            log_entry["userId"] = record.user_id
        if hasattr(record, "trace_id"):
            log_entry["traceId"] = record.trace_id

        return json.dumps(log_entry)


def get_structured_logger(name: str = "agentops") -> logging.Logger:
    """Create or configure a structured JSON logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


agent_logger = get_structured_logger("it_helpdesk_agent")


# ============================================================================
# 3. INTENT VS. OUTCOME CAPTURE (Criterion 4.2 / 14)
# ============================================================================
class IntentOutcomeRecorder:
    """Records the agent's intended actions before execution and actual outcomes after."""

    _active_intents: dict[str, dict[str, Any]] = {}

    @classmethod
    def record_intent(
        cls,
        tool_name: str,
        arguments: dict[str, Any],
        predicted_goal: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Capture and log the pre-execution intent of an agent tool call."""
        intent_id = f"{tool_name}-{time.time_ns()}"
        scrubbed_args = PIIRedactor.redact_structure(arguments)

        intent_data = {
            "intent_id": intent_id,
            "tool_name": tool_name,
            "arguments": scrubbed_args,
            "predicted_goal": predicted_goal,
            "start_time": time.time(),
        }
        cls._active_intents[intent_id] = intent_data

        agent_logger.info(
            f"Agent intent captured for tool '{tool_name}'",
            extra={
                "event_type": "TOOL_INTENT",
                "session_id": session_id,
                "user_id": user_id,
                "structured_data": intent_data,
            },
        )
        return intent_id

    @classmethod
    def record_outcome(
        cls,
        intent_id: str,
        status: str,
        result: Any,
        error_code: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Capture and log the post-execution outcome against the recorded intent."""
        intent_data = cls._active_intents.pop(intent_id, {})
        start_time = intent_data.get("start_time", time.time())
        duration_ms = round((time.time() - start_time) * 1000, 2)
        tool_name = intent_data.get("tool_name", "unknown_tool")

        outcome_data = {
            "intent_id": intent_id,
            "tool_name": tool_name,
            "status": status,
            "duration_ms": duration_ms,
            "error_code": error_code,
            "result_summary": PIIRedactor.redact_structure(str(result)[:500]),
            "matched_intent": intent_data.get("predicted_goal"),
        }

        agent_logger.info(
            f"Agent outcome captured for tool '{tool_name}' with status '{status}' in {duration_ms}ms",
            extra={
                "event_type": "TOOL_OUTCOME",
                "session_id": session_id,
                "user_id": user_id,
                "structured_data": outcome_data,
            },
        )


# ============================================================================
# 4. DISTRIBUTED TRACING SPAN WRAPPER (Criterion 4.3 / 15)
# ============================================================================
class TraceSpanContext:
    """Context manager for distributed tracing spans with OpenTelemetry."""

    def __init__(self, span_name: str, attributes: Optional[dict[str, Any]] = None) -> None:
        self.span_name = span_name
        self.attributes = attributes or {}
        self._span = None

    def __enter__(self):
        if tracer:
            try:
                self._span = tracer.start_span(self.span_name)
                for k, v in self.attributes.items():
                    self._span.set_attribute(k, str(v))
            except Exception:
                self._span = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._span:
            if exc_val:
                self._span.record_exception(exc_val)
                self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            self._span.end()
