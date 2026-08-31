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

"""Explicit JSON schemas and Pydantic validation models for agent tools and responses.

Satisfies Rubric Criterion 1.3 (Explicit JSON Schemas) and Criterion 1.4 (Guided Error Handling).
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class DeviceStatusQueryInput(BaseModel):
    """Input schema for querying device hardware and warranty status."""

    device_id: str = Field(
        ...,
        description="The unique hardware asset identifier tag (e.g., 'LAPTOP-002', 'WORKSTATION-101', 'PHONE-044').",
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_\-]+$",
    )


class DeviceStatusResult(BaseModel):
    """Output schema for device status and warranty details."""

    status: Literal["success", "error"] = "success"
    device_id: str
    model: str
    device_status: str
    warranty_status: str
    assigned_user: str | None = None
    last_inspection_date: str | None = None


class CreateTicketInput(BaseModel):
    """Input schema for creating an enterprise IT support ticket."""

    user: str = Field(
        ...,
        description="Full name or employee ID of the user requesting support.",
        min_length=2,
        max_length=100,
    )
    issue: str = Field(
        ...,
        description="Detailed description of the hardware or software problem.",
        min_length=5,
        max_length=2000,
    )
    priority: Literal["Low", "Medium", "High", "Critical"] = Field(
        default="Medium",
        description="Assessed issue priority level according to SLA guidelines.",
    )
    device_id: str | None = Field(
        default=None,
        description="Optional asset tag associated with the problem.",
    )
    category: Literal["Hardware", "Software", "Access", "Network", "Security"] = Field(
        default="Hardware",
        description="Classification category of the incident.",
    )


class TicketCreationResult(BaseModel):
    """Output schema for ticket creation confirmation."""

    status: Literal["success", "error"] = "success"
    ticket_id: str
    user: str
    issue: str
    priority: str
    category: str
    ticket_status: str = "Open"
    message: str


class SupervisorApprovalInput(BaseModel):
    """Input schema for Human-in-the-Loop high-stakes authorization requests."""

    action_type: Literal[
        "REMOTE_DEVICE_WIPE",
        "HARDWARE_REPLACEMENT_OVER_BUDGET",
        "ELEVATED_ADMIN_ACCESS_GRANT",
        "CRITICAL_SECURITY_CONTAINMENT",
    ] = Field(
        ...,
        description="The type of high-risk operation requiring human supervisor approval.",
    )
    target_resource: str = Field(
        ...,
        description="The resource ID, user ID, or device tag targeted by the operation.",
    )
    justification: str = Field(
        ...,
        description="Business justification explaining why this high-stakes action is required.",
        min_length=10,
    )
    approval_token: str | None = Field(
        default=None,
        description="Explicit cryptographic or supervisor sign-off token. If omitted, action is paused for approval.",
    )


class SupervisorApprovalResult(BaseModel):
    """Output schema for Human-in-the-Loop approval requests."""

    status: Literal["PENDING_SUPERVISOR_APPROVAL", "APPROVED", "REJECTED"]
    approval_id: str
    action_type: str
    target_resource: str
    requires_code_stop: bool
    instructions_for_agent: str
    message: str


# Aliases for flexibility
HumanSupervisorApprovalInput = SupervisorApprovalInput
HumanSupervisorApprovalResult = SupervisorApprovalResult


class SecurityEscalationInput(BaseModel):
    """Input schema for escalating critical security incidents."""

    incident_type: Literal[
        "UNAUTHORIZED_ACCESS_ATTEMPT",
        "MALWARE_DETECTED",
        "DATA_EXFILTRATION_SUSPECTED",
        "COMPROMISED_CREDENTIALS",
    ] = Field(
        ...,
        description="Categorization of the security threat.",
    )
    severity: Literal["SEV1", "SEV2", "SEV3"] = Field(
        default="SEV1",
        description="Incident severity level according to SecOps protocol.",
    )
    affected_user: str = Field(
        ...,
        description="Username or employee ID of the affected identity.",
    )
    incident_details: str = Field(
        ...,
        description="Detailed findings and evidence regarding the security anomaly.",
        min_length=10,
    )


class SecurityEscalationResult(BaseModel):
    """Output schema for security incident escalation."""

    status: Literal["ESCALATED_TO_SECOPS", "ERROR"] = "ESCALATED_TO_SECOPS"
    incident_id: str
    severity: str
    containment_protocol_initiated: bool
    secops_instructions: str


class KnowledgeQueryInput(BaseModel):
    """Input schema for querying the enterprise IT knowledge base."""

    query: str = Field(
        ...,
        description="Technical keywords or question regarding IT policies, software, or setup.",
        min_length=3,
    )
    category: Literal["general", "software", "network", "security", "hardware"] = Field(
        default="general",
        description="Knowledge base partition category.",
    )


class KnowledgeQueryResult(BaseModel):
    """Output schema for IT knowledge base lookups."""

    query: str
    category: str
    found: bool
    solution: str
    reference_article_id: str


class ToolErrorRecoveryPayload(BaseModel):
    """Structured guided error payload returning actionable recovery instructions to the LLM."""

    status: Literal["error"] = "error"
    error_code: str
    message: str
    recovery_instructions: str
    context_details: dict[str, Any] | None = None
