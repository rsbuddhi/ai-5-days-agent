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

"""Unit tests for tool docstrings, descriptive naming, JSON schemas, and guided error handling.

Verifies Rubric Category 1 (Tool & Interface Design - 20 pts).
"""

import pytest
from app.schemas import (
    CreateTicketInput,
    DeviceStatusQueryInput,
    HumanSupervisorApprovalInput,
    SecurityEscalationInput,
)
from app.tools import (
    create_it_support_ticket,
    escalate_critical_security_incident,
    lookup_device_hardware_warranty_status,
    query_it_knowledge_base,
    request_human_supervisor_approval,
)


def test_tool_docstrings_comprehensive():
    """Criterion 1.1: Verify all tools contain clear, comprehensive docstrings with args, returns, and errors."""
    tools = [
        lookup_device_hardware_warranty_status,
        create_it_support_ticket,
        request_human_supervisor_approval,
        escalate_critical_security_incident,
        query_it_knowledge_base,
    ]
    for tool in tools:
        assert tool.__doc__ is not None, f"Tool {tool.__name__} is missing a docstring."
        assert "Args:" in tool.__doc__, f"Tool {tool.__name__} docstring missing 'Args:'."
        assert "Returns:" in tool.__doc__, f"Tool {tool.__name__} docstring missing 'Returns:'."


def test_descriptive_tool_names():
    """Criterion 1.2: Verify tool names are highly descriptive rather than generic."""
    expected_tools = [
        "lookup_device_hardware_warranty_status",
        "create_it_support_ticket",
        "request_human_supervisor_approval",
        "escalate_critical_security_incident",
        "query_it_knowledge_base",
    ]
    tool_names = [
        lookup_device_hardware_warranty_status.__name__,
        create_it_support_ticket.__name__,
        request_human_supervisor_approval.__name__,
        escalate_critical_security_incident.__name__,
        query_it_knowledge_base.__name__,
    ]
    for name in expected_tools:
        assert name in tool_names, f"Expected descriptive tool name '{name}' not found."


def test_explicit_json_schemas():
    """Criterion 1.3: Verify explicit input schemas validate data and reject invalid types."""
    # Valid input
    valid_device = DeviceStatusQueryInput(device_id="LAPTOP-002")
    assert valid_device.device_id == "LAPTOP-002"

    valid_ticket = CreateTicketInput(
        user="Alice",
        issue="Screen is flickering",
        priority="High",
        category="Hardware",
    )
    assert valid_ticket.user == "Alice"

    # Invalid input rejection
    with pytest.raises(Exception):
        DeviceStatusQueryInput(device_id="")  # min_length violation

    with pytest.raises(Exception):
        CreateTicketInput(user="A", issue="short")  # min_length violations


def test_guided_error_handling_unknown_device():
    """Criterion 1.4: Verify tool returns actionable recovery instructions when an error or missing resource occurs."""
    result = lookup_device_hardware_warranty_status(device_id="UNKNOWN-DEV-999")
    assert result["status"] == "error"
    assert result["error_code"] == "DEVICE_NOT_FOUND"
    assert "recovery_instructions" in result
    assert len(result["recovery_instructions"]) > 10


def test_lookup_device_known_seed():
    """Test successful device lookup for seeded device LAPTOP-002."""
    result = lookup_device_hardware_warranty_status(device_id="LAPTOP-002")
    assert result["status"] == "success"
    assert result["device_id"] == "LAPTOP-002"
    assert "ThinkPad" in result["model"]
    assert result["warranty_status"] == "Expired"


def test_create_ticket_success():
    """Test successful ticket creation with generated ID and confirmation message."""
    result = create_it_support_ticket(
        user="Bob Smith",
        issue="Keyboard spacebar is stuck and unresponsive.",
        priority="Medium",
        category="Hardware",
    )
    assert result["status"] == "success"
    assert result["ticket_id"].startswith("TICKET-")
    assert result["user"] == "Bob Smith"
    assert "Successfully created support ticket" in result["message"]
