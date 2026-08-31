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

"""Firestore Database Seeding Script.

Populates enterprise test data across all collections:
1. 'devices': Hardware assets, statuses, and warranty information
2. 'knowledge_base': Verified IT articles for Wi-Fi, VPN, Passwords, etc.
3. 'approval_requests': Human-in-the-loop audit logs and authorization states
4. 'tickets': Active and historical IT service management tickets
5. 'security_incidents': SecOps escalation logs and containment records
"""

import os
from dotenv import load_dotenv
from google.cloud import firestore

load_dotenv()
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
print(f"Connecting to Firestore for project: {project_id or '(default)'}...")

try:
    db = firestore.Client(project=project_id) if project_id else firestore.Client()
except Exception as e:
    print(f"Firestore connection failed: {e}")
    db = None

# ============================================================================
# 1. SEED HARDWARE DEVICES (devices)
# ============================================================================
DEVICES_SEED_DATA = {
    "LAPTOP-002": {
        "model": "ThinkPad T14 Gen 4",
        "status": "Needs Repair",
        "warranty": "Expired",
        "user": "Alice Chen",
        "department": "Engineering",
        "last_inspection": "2026-02-01",
    },
    "LAPTOP-001": {
        "model": "MacBook Pro 16-inch M3",
        "status": "Active",
        "warranty": "Active (AppleCare+ until 2027)",
        "user": "Bob Smith",
        "department": "Design",
        "last_inspection": "2026-01-15",
    },
    "WORKSTATION-101": {
        "model": "Dell Precision 5820 Tower",
        "status": "Active",
        "warranty": "Active ProSupport",
        "user": "Carlos Rodriguez",
        "department": "Data Analytics",
        "last_inspection": "2025-11-20",
    },
    "PHONE-044": {
        "model": "Google Pixel 9 Pro Enterprise",
        "status": "Active",
        "warranty": "Active",
        "user": "Diana Prince",
        "department": "Operations",
        "last_inspection": "2026-03-01",
    },
}

# ============================================================================
# 2. SEED KNOWLEDGE BASE ARTICLES (knowledge_base)
# ============================================================================
KNOWLEDGE_BASE_SEED_DATA = {
    "KB-NET-402": {
        "article_id": "KB-NET-402",
        "title": "Corporate Wi-Fi Onboarding Guide",
        "category": "network",
        "keywords": ["wifi", "wi-fi", "wireless", "network", "connect", "internet", "corp-secure"],
        "solution": (
            "To connect to Corp-Secure Wi-Fi: 1. Select 'Corp-Secure-WPA3' network. "
            "2. Enter your enterprise SSO username and password. "
            "3. Confirm the Enterprise Root Certificate when prompted. "
            "4. For guest access, visit https://guestwifi.corp.internal for temporary tokens."
        ),
    },
    "KB-SEC-101": {
        "article_id": "KB-SEC-101",
        "title": "Self-Service Enterprise Password Reset",
        "category": "security",
        "keywords": ["password", "reset", "forgot", "unlock", "account", "login", "credentials"],
        "solution": (
            "To reset your corporate password: 1. Visit https://auth.corp.internal/selfservice. "
            "2. Authenticate using your secondary 2FA hardware Security Key or Google Authenticator. "
            "3. Enter a new password meeting enterprise complexity requirements (16+ chars, numbers, symbols). "
            "4. Allow 5 minutes for directory replication across all cloud services."
        ),
    },
    "KB-NET-505": {
        "article_id": "KB-NET-505",
        "title": "Global Remote Access VPN Setup",
        "category": "network",
        "keywords": ["vpn", "remote", "globalprotect", "access", "tunnel", "home"],
        "solution": (
            "For Remote Access VPN: 1. Launch the GlobalProtect VPN client on your workstation. "
            "2. Portal Address: 'us-central-vpn.corp.internal'. "
            "3. Tap your physical security key when the WebAuthn prompt appears. "
            "4. If connection fails with Code 403, ensure your device health compliance check has run today."
        ),
    },
    "KB-HW-201": {
        "article_id": "KB-HW-201",
        "title": "Monitor and Docking Station Troubleshooting",
        "category": "hardware",
        "keywords": ["monitor", "display", "screen", "dock", "usb-c", "thunderbolt", "flickering"],
        "solution": (
            "For external monitor or USB-C dock issues: 1. Disconnect and firmly reconnect the Thunderbolt/USB-C cable. "
            "2. Power cycle the docking station by unplugging power for 10 seconds. "
            "3. Update Intel/Apple display firmware via the Enterprise Software Center."
        ),
    },
    "KB-GEN-001": {
        "article_id": "KB-GEN-001",
        "title": "General IT Support and Ticket SLA Guidelines",
        "category": "general",
        "keywords": ["general", "help", "support", "hours", "sla", "ticket"],
        "solution": (
            "For general IT support: Standard business hours are 24/7 for SEV1/Critical incidents, "
            "and 8:00 AM - 6:00 PM local time for standard tickets. "
            "Hardware repairs typically complete within 24-48 business hours with loaner devices available."
        ),
    },
}

# ============================================================================
# 3. SEED APPROVAL REQUESTS (approval_requests)
# ============================================================================
APPROVAL_SEED_DATA = {
    "APPR-SAMPLE-001": {
        "approval_id": "APPR-SAMPLE-001",
        "action_type": "HARDWARE_REPLACEMENT_OVER_BUDGET",
        "target_resource": "LAPTOP-002",
        "status": "APPROVED",
        "approver": "supervisor@corp.internal",
        "justification": "Developer requires high-RAM replacement workstation.",
        "timestamp": "2026-08-30T14:22:00Z",
    }
}


def seed_database():
    """Seed all Firestore collections with enterprise data."""
    if not db:
        print("ERROR: Firestore client not initialized. Cannot seed database.")
        return

    print("--- Seeding 'devices' collection ---")
    for device_id, data in DEVICES_SEED_DATA.items():
        db.collection("devices").document(device_id).set(data)
        print(f"  + Seeded device: {device_id} ({data['model']})")

    print("\n--- Seeding 'knowledge_base' collection ---")
    for article_id, data in KNOWLEDGE_BASE_SEED_DATA.items():
        db.collection("knowledge_base").document(article_id).set(data)
        print(f"  + Seeded KB article: {article_id} - {data['title']}")

    print("\n--- Seeding 'approval_requests' collection ---")
    for appr_id, data in APPROVAL_SEED_DATA.items():
        db.collection("approval_requests").document(appr_id).set(data)
        print(f"  + Seeded approval record: {appr_id}")

    print("\nDatabase seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
