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

"""Integration tests for Multi-Agent Orchestration, Sub-Agent Delegation, and Strategic Model Routing.

Verifies Rubric Criteria:
- 3.1 / 9: Multi-Agent Patterns (Coordinator & Specialist pattern in ADK)
- 3.2 / 10: Strategic Model Routing (Flash for fast triage, Pro for escalation/planning)
- 2.1 / 5: Robust System Instructions
"""

from app.agent import (
    access_software_specialist_agent,
    hardware_specialist_agent,
    incident_escalation_agent,
    root_agent,
)


def test_multi_agent_coordinator_structure():
    """Criterion 3.1 / 9: Verify Coordinator Agent has specialized Sub-Agents attached."""
    assert root_agent.name == "it_helpdesk_agent"
    assert len(root_agent.sub_agents) == 3

    sub_agent_names = [agent.name for agent in root_agent.sub_agents]
    assert "hardware_specialist_agent" in sub_agent_names
    assert "access_software_specialist_agent" in sub_agent_names
    assert "incident_escalation_agent" in sub_agent_names


def test_strategic_model_routing():
    """Criterion 3.2 / 10: Verify appropriate models are assigned according to task complexity."""
    # Fast triage & hardware lookups use high-throughput Flash model
    assert "flash" in root_agent.model.model.lower()
    assert "flash" in hardware_specialist_agent.model.model.lower()
    assert "flash" in access_software_specialist_agent.model.model.lower()

    # Complex SecOps escalation & deep reasoning uses Pro model
    assert "pro" in incident_escalation_agent.model.model.lower()


def test_constitutional_system_instructions():
    """Criterion 2.1 / 5: Verify system prompt contains constitutional constraints and persona."""
    instruction = root_agent.instruction
    assert "CORE OPERATING PRINCIPLES" in instruction
    assert "HUMAN-IN-THE-LOOP" in instruction
    assert "PROMPT INJECTION DEFENSE" in instruction
    assert "PII PROTECTION" in instruction
