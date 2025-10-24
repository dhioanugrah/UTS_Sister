
import shutil, tempfile, time
from src.app import create_app

def fresh_app(tmp):
    import os
    os.environ["DATA_DIR"] = tmp
    app = create_app()
    app.testing = True
    return app

def test_publish_and_dedup_single():
    tmp = tempfile.mkdtemp()
    app = fresh_app(tmp)
    c = app.test_client()

    evt = {"topic":"orders","event_id":"evt-1","timestamp":"2025-10-23T15:00:00Z","source":"test","payload":{"x":1}}
    assert c.post("/publish", json=evt).status_code == 200
    assert c.post("/publish", json=evt).status_code == 200
    assert c.post("/publish", json=evt).status_code == 200
    time.sleep(0.2)
    s = c.get("/stats").get_json()
    assert s["unique_processed"] == 1 and s["duplicate_dropped"] >= 2
    evs = c.get("/events?topic=orders").get_json()
    assert len(evs) == 1
    shutil.rmtree(tmp, ignore_errors=True)

def test_batch_publish_with_dupes():
    tmp = tempfile.mkdtemp()
    app = fresh_app(tmp); c = app.test_client()
    batch = [
        {"topic":"orders","event_id":"evt-10","timestamp":"2025-10-23T15:00:00Z","source":"test","payload":{"n":1}},
        {"topic":"orders","event_id":"evt-11","timestamp":"2025-10-23T15:00:00Z","source":"test","payload":{"n":2}},
        {"topic":"orders","event_id":"evt-10","timestamp":"2025-10-23T15:00:00Z","source":"test","payload":{"n":"dupe"}},
    ]
    assert c.post("/publish", json=batch).status_code == 200
    time.sleep(0.2)
    s = c.get("/stats").get_json()
    assert s["unique_processed"] == 2 and s["duplicate_dropped"] >= 1
    shutil.rmtree(tmp, ignore_errors=True)

def test_schema_validation():
    tmp = tempfile.mkdtemp()
    app = fresh_app(tmp); c = app.test_client()
    bad = {"topic":"","event_id":"","timestamp":"bad-ts","source":"","payload":{}}
    r = c.post("/publish", json=bad)
    assert r.status_code == 422 and "errors" in r.get_json()
    shutil.rmtree(tmp, ignore_errors=True)

def test_persistence_across_restart():
    tmp = tempfile.mkdtemp()
    app1 = fresh_app(tmp); c1 = app1.test_client()
    evt = {"topic":"orders","event_id":"evt-99","timestamp":"2025-10-23T15:00:00Z","source":"test","payload":{}}
    c1.post("/publish", json=evt); time.sleep(0.3)

    app2 = fresh_app(tmp); c2 = app2.test_client()
    c2.post("/publish", json=evt); time.sleep(0.3)
    s2 = c2.get("/stats").get_json()
    assert s2["unique_processed"] == 1 and s2["duplicate_dropped"] >= 1
    shutil.rmtree(tmp, ignore_errors=True)

def test_stats_and_events_consistency():
    tmp = tempfile.mkdtemp()
    app = fresh_app(tmp); c = app.test_client()
    for i in range(5):
        evt = {"topic":"metrics","event_id":f"e-{i}","timestamp":"2025-10-23T15:00:00Z","source":"test","payload":{"i":i}}
        c.post("/publish", json=evt)
    time.sleep(0.3)
    evs = c.get("/events?topic=metrics").get_json()
    s = c.get("/stats").get_json()
    assert len(evs) == 5 and s["unique_processed"] >= 5
    shutil.rmtree(tmp, ignore_errors=True)
