"""Locustfile — M39-c3 (S3c): POST /programs/set-feedback."""

from __future__ import annotations

import os

from locust import HttpUser, between, task

TOKEN = os.environ.get("S3C_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


class FeedbackUser(HttpUser):
    wait_time = between(0.05, 0.2)

    @task
    def set_feedback(self) -> None:
        self.client.post(
            "/api/v1/programs/set-feedback",
            json={
                "member_id": int(os.environ.get("S3C_MEMBER", "1")),
                "entries": [
                    {
                        "movement_id": "pushup-l1",
                        "weight": 0,
                        "target_reps": 10,
                        "reps_done": 12,
                        "rir": 3,
                        "soreness": 2,
                    },
                    {
                        "movement_id": "plank",
                        "weight": 0,
                        "target_reps": 3,
                        "reps_done": 3,
                        "rir": 1,
                        "soreness": 8,
                    },
                ],
            },
            headers=HEADERS,
            name="/programs/set-feedback",
        )
