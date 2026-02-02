"""
Load Test Scenarios

Locust test scenarios for decision and workflow endpoints.

Source: Phase 2 Design & Execution Plan - Section 4.4
"""

import random
import uuid
from typing import Dict, Any

from locust import HttpUser, task, between

from .config import LoadTestConfig


class DecisionTestScenario(HttpUser):
    """
    Decision creation and retrieval load test

    Simulates users creating decisions and retrieving them.
    Tests:
    - POST /api/v1/decisions (decision creation)
    - GET /api/v1/decisions/{id} (decision retrieval)

    Measures:
    - Throughput (decisions/sec)
    - Latency (p50, p95, p99)
    - Cache hit rates (rule cache, idempotency cache)
    - Error rates
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Initialize test data"""
        self.config = LoadTestConfig()
        self.tenant_id = self.config.tenant_id
        self.decision_type = self.config.decision_type
        self.created_decisions = []

    @task(70)
    def create_decision(self):
        """
        Create a new decision (70% of requests)

        Tests:
        - Rule cache hits (after first request)
        - Idempotency checks
        - Decision creation throughput
        """
        decision_id = str(uuid.uuid4())
        idempotency_key = f"load_test_{random.randint(1, 1000)}"

        payload = {
            "tenant_id": self.tenant_id,
            "decision_id": decision_id,
            "decision_type": self.decision_type,
            "context": {
                "customer_id": f"CUST{random.randint(1000, 9999)}",
                "credit_score": random.randint(300, 850),
                "requested_amount": random.randint(1000, 50000),
                "annual_income": random.randint(20000, 200000)
            },
            "idempotency_key": idempotency_key
        }

        with self.client.post(
            "/api/v1/decisions",
            json=payload,
            catch_response=True,
            name="POST /api/v1/decisions"
        ) as response:
            if response.status_code == 201:
                response.success()
                self.created_decisions.append(decision_id)
            elif response.status_code == 409:
                # Idempotency hit (expected, not an error)
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(20)
    def get_decision(self):
        """
        Retrieve existing decision (20% of requests)

        Tests:
        - Decision retrieval latency
        - Database connection pool efficiency
        """
        if not self.created_decisions:
            # No decisions created yet, skip
            return

        decision_id = random.choice(self.created_decisions)

        with self.client.get(
            f"/api/v1/decisions/{decision_id}",
            catch_response=True,
            name="GET /api/v1/decisions/{id}"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Decision not found")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(10)
    def list_decisions(self):
        """
        List decisions for tenant (10% of requests)

        Tests:
        - Database query performance
        - Connection pool utilization
        """
        with self.client.get(
            f"/api/v1/decisions?tenant_id={self.tenant_id}",
            catch_response=True,
            name="GET /api/v1/decisions"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class WorkflowTestScenario(HttpUser):
    """
    Workflow approval load test

    Simulates users creating workflows and processing approvals.
    Tests:
    - POST /api/v1/workflows (workflow creation)
    - POST /api/v1/workflows/{id}/approve (approval)

    Measures:
    - Workflow throughput
    - Approval latency
    - Error rates
    """

    wait_time = between(1, 3)

    def on_start(self):
        """Initialize test data"""
        self.config = LoadTestConfig()
        self.tenant_id = self.config.tenant_id
        self.pending_workflows = []

    @task(60)
    def create_workflow(self):
        """
        Create a new workflow (60% of requests)

        Tests:
        - Workflow creation throughput
        - Rule evaluation performance
        """
        workflow_id = str(uuid.uuid4())
        decision_id = str(uuid.uuid4())

        payload = {
            "tenant_id": self.tenant_id,
            "workflow_id": workflow_id,
            "decision_id": decision_id,
            "workflow_type": "credit_approval",
            "context": {
                "customer_id": f"CUST{random.randint(1000, 9999)}",
                "requested_amount": random.randint(10000, 100000)
            }
        }

        with self.client.post(
            "/api/v1/workflows",
            json=payload,
            catch_response=True,
            name="POST /api/v1/workflows"
        ) as response:
            if response.status_code == 201:
                response.success()
                self.pending_workflows.append(workflow_id)
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(40)
    def approve_workflow(self):
        """
        Approve pending workflow (40% of requests)

        Tests:
        - Approval processing latency
        - State transition logic
        """
        if not self.pending_workflows:
            # No workflows pending, skip
            return

        workflow_id = random.choice(self.pending_workflows)

        payload = {
            "approved": random.choice([True, False]),
            "approver_id": f"USER{random.randint(1, 10)}",
            "comments": "Load test approval"
        }

        with self.client.post(
            f"/api/v1/workflows/{workflow_id}/approve",
            json=payload,
            catch_response=True,
            name="POST /api/v1/workflows/{id}/approve"
        ) as response:
            if response.status_code == 200:
                response.success()
                # Remove from pending list
                if workflow_id in self.pending_workflows:
                    self.pending_workflows.remove(workflow_id)
            elif response.status_code == 404:
                response.failure("Workflow not found")
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class MixedWorkloadScenario(HttpUser):
    """
    Mixed workload (70% decisions, 30% workflows)

    Simulates realistic production workload with both decisions and workflows.

    Tests:
    - Combined throughput
    - Resource contention
    - Connection pool efficiency under mixed load
    """

    wait_time = between(1, 3)

    def on_start(self):
        """Initialize test data"""
        self.config = LoadTestConfig()
        self.tenant_id = self.config.tenant_id
        self.decision_type = self.config.decision_type
        self.created_decisions = []
        self.pending_workflows = []

    @task(50)
    def create_decision(self):
        """Create decision (50% weight)"""
        decision_id = str(uuid.uuid4())
        idempotency_key = f"load_test_{random.randint(1, 1000)}"

        payload = {
            "tenant_id": self.tenant_id,
            "decision_id": decision_id,
            "decision_type": self.decision_type,
            "context": {
                "customer_id": f"CUST{random.randint(1000, 9999)}",
                "credit_score": random.randint(300, 850),
                "requested_amount": random.randint(1000, 50000)
            },
            "idempotency_key": idempotency_key
        }

        with self.client.post(
            "/api/v1/decisions",
            json=payload,
            catch_response=True,
            name="POST /api/v1/decisions"
        ) as response:
            if response.status_code in [201, 409]:
                response.success()
                if response.status_code == 201:
                    self.created_decisions.append(decision_id)

    @task(20)
    def get_decision(self):
        """Retrieve decision (20% weight)"""
        if not self.created_decisions:
            return

        decision_id = random.choice(self.created_decisions)

        with self.client.get(
            f"/api/v1/decisions/{decision_id}",
            catch_response=True,
            name="GET /api/v1/decisions/{id}"
        ) as response:
            if response.status_code == 200:
                response.success()

    @task(20)
    def create_workflow(self):
        """Create workflow (20% weight)"""
        workflow_id = str(uuid.uuid4())
        decision_id = str(uuid.uuid4())

        payload = {
            "tenant_id": self.tenant_id,
            "workflow_id": workflow_id,
            "decision_id": decision_id,
            "workflow_type": "credit_approval",
            "context": {
                "customer_id": f"CUST{random.randint(1000, 9999)}",
                "requested_amount": random.randint(10000, 100000)
            }
        }

        with self.client.post(
            "/api/v1/workflows",
            json=payload,
            catch_response=True,
            name="POST /api/v1/workflows"
        ) as response:
            if response.status_code == 201:
                response.success()
                self.pending_workflows.append(workflow_id)

    @task(10)
    def approve_workflow(self):
        """Approve workflow (10% weight)"""
        if not self.pending_workflows:
            return

        workflow_id = random.choice(self.pending_workflows)

        payload = {
            "approved": random.choice([True, False]),
            "approver_id": f"USER{random.randint(1, 10)}",
            "comments": "Load test approval"
        }

        with self.client.post(
            f"/api/v1/workflows/{workflow_id}/approve",
            json=payload,
            catch_response=True,
            name="POST /api/v1/workflows/{id}/approve"
        ) as response:
            if response.status_code == 200:
                response.success()
                if workflow_id in self.pending_workflows:
                    self.pending_workflows.remove(workflow_id)
