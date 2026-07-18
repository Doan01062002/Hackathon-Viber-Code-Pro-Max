import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import logging
import threading
import time

from redis.exceptions import TimeoutError as RedisTimeoutError

from backend.database import get_session_factory
from backend.redis_client import get_redis_client
from backend.services.optimize_service import OptimizeService

logger = logging.getLogger("srrm.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class EventWorker:
    def __init__(self, debounce_seconds: float = 5.0):
        self.debounce_seconds = debounce_seconds
        self.pending_resolves: dict[int, float] = {}  # trip_id -> target_run_timestamp
        self.pending_resolves_lock = threading.Lock()
        self.running = False
        self.threads = []

    def start(self):
        """Khởi chạy Worker trong các background threads."""
        if self.running:
            print("[EventWorker] start() called but already running")
            return

        self.running = True
        print("[EventWorker] Starting background threads...")

        # 1. Thread đọc sự kiện từ Redis Stream
        t_consume = threading.Thread(target=self._consume_loop, name="StreamConsumer", daemon=True)
        # 2. Thread xử lý debounce timers
        t_debounce = threading.Thread(target=self._debounce_loop, name="DebounceProcessor", daemon=True)

        self.threads = [t_consume, t_debounce]
        for t in self.threads:
            t.start()

        print("[EventWorker] Background threads started successfully.")

    def stop(self):
        """Dừng Worker."""
        print("[EventWorker] Stopping worker...")
        self.running = False
        for t in self.threads:
            t.join(timeout=2.0)
        print("[EventWorker] Worker stopped.")

    def run_forever(self):
        """Khởi chạy Worker inline (blocking) - thích hợp cho CLI script."""
        self.running = True
        logger.info("Starting Worker in blocking mode (press Ctrl+C to exit)...")

        # Chạy thread debounce trong background
        t_debounce = threading.Thread(target=self._debounce_loop, name="DebounceProcessor", daemon=True)
        t_debounce.start()

        try:
            self._consume_loop()
        except KeyboardInterrupt:
            logger.info("Worker terminated by user.")
        finally:
            self.running = False
            t_debounce.join(timeout=2.0)

    def _consume_loop(self):
        """Vòng lặp tiêu thụ sự kiện từ Redis Stream."""
        print("[EventWorker] Consume loop entered.")
        redis_conn = get_redis_client()
        stream_name = "srrm:event_stream"

        # Khởi tạo đọc từ thời điểm hiện tại trở đi ($)
        latest_id = "$"

        print(f"[EventWorker] Listening to stream '{stream_name}' from '{latest_id}'")

        while self.running:
            try:
                # Đọc sự kiện (block 1000ms)
                streams = redis_conn.xread({stream_name: latest_id}, count=10, block=1000)
                if not streams:
                    # Thêm sleep nhỏ để tránh quay vòng 100% CPU trong mock environment
                    time.sleep(0.1)
                    continue

                for s_name, messages in streams:
                    for msg_id, data in messages:
                        latest_id = msg_id

                        trip_id_str = data.get("trip_id")
                        event_type = data.get("event_type")

                        if not trip_id_str:
                            continue

                        trip_id = int(trip_id_str)
                        print(f"[EventWorker] Received event '{event_type}' for trip_id {trip_id}")

                        # Cập nhật debounce timer cho trip_id này
                        with self.pending_resolves_lock:
                            self.pending_resolves[trip_id] = time.time() + self.debounce_seconds
                            print(
                                f"[EventWorker] Scheduled resolve for trip_id {trip_id} at current + {self.debounce_seconds}s"
                            )

            except RedisTimeoutError:
                # A blocking stream read may time out when no event arrives.
                # This is an idle poll, not a worker failure.
                continue
            except Exception as e:
                print(f"[EventWorker] Error in consume loop: {str(e)}")
                time.sleep(2.0)

    def _debounce_loop(self):
        """Vòng lặp kiểm tra và kích hoạt re-solve khi hết thời gian debounce."""
        print("[EventWorker] Debounce loop entered.")
        optimize_service = OptimizeService()
        session_factory = get_session_factory()

        while self.running:
            try:
                now = time.time()
                to_run = []

                # 1. Tìm các trip_id đã sẵn sàng giải tối ưu (hết thời gian debounce)
                with self.pending_resolves_lock:
                    if self.pending_resolves:
                        logger.debug("Pending debounce jobs: %s", self.pending_resolves)
                    for trip_id, run_time in list(self.pending_resolves.items()):
                        if now >= run_time:
                            to_run.append(trip_id)
                            del self.pending_resolves[trip_id]

                # 2. Thực thi re-solve từng trip
                for trip_id in to_run:
                    print(f"[EventWorker] Debounce done for trip_id {trip_id}. Starting optimization batch...")

                    db = session_factory()
                    try:
                        # Thực thi tối ưu hóa DLP và swap active version
                        result = optimize_service.run_optimization_batch(trip_id=trip_id, db=db)
                        print(
                            f"[EventWorker] Re-solve success for trip_id {trip_id}. Run version: {result['run_version']}"
                        )
                    except Exception as ex:
                        print(f"[EventWorker] Re-solve failed for trip_id {trip_id}: {str(ex)}")
                    finally:
                        db.close()

                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error in debounce loop: {str(e)}")
                time.sleep(2.0)


if __name__ == "__main__":
    worker = EventWorker()
    worker.run_forever()
