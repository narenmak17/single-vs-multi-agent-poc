from datetime import datetime, timedelta


def test_created_task_appears_in_list(client):
    created = client.post("/api/tasks", json={"title": "Write tests"})
    assert created.status_code == 201

    tasks = client.get("/api/tasks").get_json()
    assert [t["title"] for t in tasks] == ["Write tests"]
    assert tasks[0]["id"] == created.get_json()["id"]


def test_patch_done_true_marks_task_done(client):
    task_id = client.post("/api/tasks", json={"title": "Ship it"}).get_json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"done": True})

    assert response.status_code == 200
    assert response.get_json()["done"] is True
    assert client.get("/api/tasks").get_json()[0]["done"] is True


def test_task_due_within_24h_has_reminder(client):
    due_at = (datetime.now() + timedelta(hours=2)).isoformat(timespec="minutes")
    client.post("/api/tasks", json={"title": "Due soon", "due_at": due_at})

    task = client.get("/api/tasks").get_json()[0]

    assert task["reminder"] is True
