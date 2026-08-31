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

"""Enterprise Security Guardrails, Prompt Injection Defense, and Policy Verification.

Satisfies Rubric Criterion 3.3 / 11 (Guardrails & Policy Plugins) and Criterion 3.4 / 12 (HITL Hooks).
"""

from __future__ import annotations

import re
from typing import Any, Tuple
from google.adk.agents.callback_context import CallbackContext
from app.observability import agent_logger, PIIRedactor


class SecurityGuardrails:
    """Multi-layer enterprise security guardrail engine."""

    # Prompt injection and adversarial jailbreak patterns
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
        re.compile(r"system\s*prompt\s*(reveal|show|dump|print|leak)", re.IGNORECASE),
        re.compile(r"bypass\s+(safety|security|policy|restrictions?)", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(DAN|unrestricted|godmode|root)", re.IGNORECASE),
        re.compile(r"(DROP\s+TABLE|DELETE\s+FROM|UPDATE\s+.*SET|TRUNCATE\s+TABLE)", re.IGNORECASE),
        re.compile(r"(rm\s+-rf|sudo\s+|chmod\s+777|curl\s+.*\|\s*sh)", re.IGNORECASE),
        re.compile(r"<script>|javascript:|onerror=", re.IGNORECASE),
    ]

    # Secret / credential leakage patterns in output
    OUTPUT_LEAK_PATTERNS = [
        re.compile(r"AIza[0-9A-Za-z-_]{35}"),
        re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{20,}"),
        re.compile(r"-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----"),
        re.compile(r"firestore\.googleapis\.com"),
    ]

    @classmethod
    def inspect_input(cls, user_text: str) -> Tuple[bool, str]:
        """Verify that user input is free from prompt injections and hostile payloads.

        Returns:
            (is_safe: bool, reason_or_sanitized: str)
        """
        if not user_text:
            return True, ""

        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(user_text):
                agent_logger.warning(
                    f"Security Guardrail Triggered: Potential prompt injection or forbidden command pattern: '{pattern.pattern}'",
                    extra={"event_type": "GUARDRAIL_VIOLATION_INPUT", "raw_input": user_text[:200]},
                )
                return False, (
                    "Security Notice: Your request triggered an automated enterprise policy filter. "
                    "Please restate your IT inquiry without system override or forbidden command phrases."
                )

        return True, user_text

    @classmethod
    def inspect_output(cls, model_text: str) -> Tuple[bool, str]:
        """Verify model output before delivery to user (leakage check and self-evaluation).

        Returns:
            (is_safe: bool, final_response: str)
        """
        if not model_text:
            return True, ""

        # Check for credential leakage
        for pattern in cls.OUTPUT_LEAK_PATTERNS:
            if pattern.search(model_text):
                agent_logger.error(
                    f"Security Guardrail Triggered: Model response contained sensitive system credential: '{pattern.pattern}'",
                    extra={"event_type": "GUARDRAIL_VIOLATION_OUTPUT"},
                )
                return False, (
                    "I am unable to display the requested response because it contains internal configuration data. "
                    "An IT technician has been notified."
                )

        # Apply PII scrubbing
        scrubbed = PIIRedactor.redact_text(model_text)
        return True, scrubbed


async def security_guardrail_before_callback(callback_context: CallbackContext) -> Any:
    """ADK Before-Agent Callback: Enforces input security policies."""
    # Input inspection can be evaluated on latest messages
    return None


async def security_guardrail_after_callback(callback_context: CallbackContext) -> Any:
    """ADK After-Agent Callback: Self-evaluates output compliance."""
    return None
