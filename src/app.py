
from flask import Flask, request, jsonify
from typing import Dict, List
import os
import queue
from datetime import datetime
from .models import Event
from .dedup_store import DedupStore
from .consumer import ConsumerThread

def create_app():
    app = Flask(__name__)

    DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
    os.makedirs(DATA_DIR, exist_ok=True)
    DEDUP_PATH = os.path.join(DATA_DIR, "dedup.json")

    dedup = DedupStore(DEDUP_PATH)
    q: "queue.Queue[dict]" = queue.Queue(maxsize=10000)
    events_by_topic: Dict[str, List[dict]] = {}

    class EventSink:
        def append(self, event: dict):
            topic = event["topic"]
            events_by_topic.setdefault(topic, []).append(event)

    sink = EventSink()
    consumer = ConsumerThread(q, dedup, sink)
    consumer.start()

    start_time = datetime.utcnow()

    @app.get("/stats")
    def stats():
        topics = sorted(list(events_by_topic.keys()))
        return jsonify({
            "received": consumer.received,
            "unique_processed": consumer.unique_processed,
            "duplicate_dropped": consumer.duplicate_dropped,
            "topics": topics,
            "uptime_sec": (datetime.utcnow() - start_time).total_seconds()
        })

    @app.get("/events")
    def get_events():
        topic = request.args.get("topic")
        if not topic:
            return jsonify({"error":"query param 'topic' is required"}), 400
        return jsonify(events_by_topic.get(topic, []))

    @app.post("/publish")
    def publish():
        try:
            data = request.get_json(force=True, silent=False)
        except Exception:
            return jsonify({"error":"invalid JSON"}), 400

        batch = data if isinstance(data, list) else [data]

        valid_events = []
        errors = []
        for idx, item in enumerate(batch):
            try:
                evt = Event(**item)
                valid_events.append(evt.model_dump())
            except Exception as e:
                errors.append({"index": idx, "error": str(e)})

        if errors:
            return jsonify({"message":"some events invalid", "errors": errors}), 422

        accepted = 0
        for ev in valid_events:
            try:
                q.put_nowait(ev)
                accepted += 1
            except queue.Full:
                break

        return jsonify({"accepted": accepted, "batch": len(batch)}), 200

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
