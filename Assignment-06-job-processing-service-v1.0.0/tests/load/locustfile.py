"""
Load test scenario (SDD Section 21 - Testing Strategy).

*** WRITTEN BUT NOT EXECUTED - no running service in this sandbox to point
Locust at, and no network access to install Locust itself. ***

Run with:
    pip install locust
    locust -f tests/load/locustfile.py --host http://localhost:8000

Simulates clients submitting jobs and polling for status - the two
endpoints this design exists to make fast (submission) and reliable
(status visibility). A real run should watch, at minimum: p95/p99 latency
on POST /v1/jobs (should stay near-flat regardless of load, since it's
supposed to be decoupled from AI operation duration - SDD NFR1), and queue
backlog growth if you're also watching the worker side.
"""

import uuid

from locust import HttpUser, between, task


class JobSubmitterUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Replace with a real token from your auth system before running -
        # this is a placeholder, not a working credential (SDD Section 16,
        # Section 5 Assumptions: auth is reused from the existing platform).
        self.headers = {"Authorization": "Bearer REPLACE_WITH_REAL_TEST_TOKEN"}
        self.submitted_job_ids: list[str] = []

    @task(3)
    def submit_job(self):
        payload = {
            "operation": "rag_query",
            "payload": {"query": f"Load test query {uuid.uuid4()}"},
            "idempotency_key": str(uuid.uuid4()),
        }
        with self.client.post(
            "/v1/jobs", json=payload, headers=self.headers, catch_response=True
        ) as response:
            if response.status_code == 202:
                job_id = response.json().get("job_id")
                if job_id:
                    self.submitted_job_ids.append(job_id)
                    if len(self.submitted_job_ids) > 50:
                        self.submitted_job_ids.pop(0)
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(1)
    def poll_status(self):
        if not self.submitted_job_ids:
            return
        job_id = self.submitted_job_ids[-1]
        with self.client.get(
            f"/v1/jobs/{job_id}", headers=self.headers, catch_response=True, name="/v1/jobs/[job_id]"
        ) as response:
            if response.status_code in (200, 404):
                # 404 is acceptable here if TRUNCATE/retention cleared old
                # test data between runs - not itself a failure signal.
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(1)
    def list_own_jobs(self):
        with self.client.get(
            "/v1/jobs?limit=20", headers=self.headers, catch_response=True, name="/v1/jobs (list)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")
