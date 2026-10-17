from flask import Flask, jsonify, render_template, request

import capabilities
import models


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False  # keep spec field order in responses
    app.config["DB_PATH"] = db_path or models.DB_PATH
    models.init_db(app.config["DB_PATH"])

    def db():
        return models.connect(app.config["DB_PATH"])

    def error(message: str, status: int):
        return jsonify({"error": message}), status

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/tasks")
    def list_tasks():
        with db() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
        tasks = [models.Task.from_row(r) for r in rows]
        return jsonify(
            [{**t.to_dict(), "reminder": capabilities.due_soon_reminder(t)} for t in tasks]
        )

    @app.post("/api/tasks")
    def create_task():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return error("body must be a JSON object", 400)
        try:
            with db() as conn:
                task = capabilities.create_task(conn, body.get("title"), body.get("due_at"))
        except ValueError as exc:
            return error(str(exc), 400)
        return jsonify(task.to_dict()), 201

    @app.patch("/api/tasks/<int:task_id>")
    def update_task(task_id: int):
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or not isinstance(body.get("done"), bool):
            return error("body must be {\"done\": true|false}", 400)
        with db() as conn:
            task = capabilities.mark_done(conn, task_id, body["done"])
        if task is None:
            return error(f"task {task_id} not found", 404)
        return jsonify(task.to_dict())

    return app


if __name__ == "__main__":
    create_app().run(port=5001)
