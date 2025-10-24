
import queue
import threading

class ConsumerThread(threading.Thread):
    def __init__(self, q: "queue.Queue[dict]", dedup_store, event_sink):
        super().__init__(daemon=True)
        self.q = q
        self.dedup_store = dedup_store
        self.event_sink = event_sink
        self._stop = threading.Event()

        self.received = 0
        self.unique_processed = 0
        self.duplicate_dropped = 0

    def run(self):
        while not self._stop.is_set():
            try:
                event = self.q.get(timeout=0.2)
            except queue.Empty:
                continue

            self.received += 1
            topic = event["topic"]
            event_id = event["event_id"]

            if self.dedup_store.contains(topic, event_id):
                self.duplicate_dropped += 1
                self.q.task_done()
                continue

            self.dedup_store.add(topic, event_id)
            self.event_sink.append(event)
            self.unique_processed += 1
            self.q.task_done()

    def stop(self):
        self._stop.set()
