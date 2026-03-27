from pathlib import Path

from printer.queue_service import PrintQueueService


def test_queue_retries_and_fail(tmp_path):
    queue_file = tmp_path / "queue.json"
    q = PrintQueueService(str(queue_file))
    q.enqueue({"id_interno": "A"}, "^XA\n^XZ", source="single")

    def always_fail(_):
        raise RuntimeError("boom")

    sent, failed = q.process(always_fail, retries=1, retry_delay_sec=0)
    assert sent == 0
    assert failed == 1
