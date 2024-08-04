# threading

https://docs.python.org/3/library/threading.html

```python
import time

def execute_task():
    duration = 4
    time.sleep(duration)
    raise Exception("hello")
```

```python
import threading
from queue import Queue
from functools import wraps
import traceback
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def with_heartbeat_and_timeout(
    max_duration=5,
    heartbeat_interval=1.0,
    task_check_interval=0.1,
    join_timeout=0.1
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            heartbeat_event = threading.Event()
            task_stop_event = threading.Event()
            task_done_event = threading.Event()
            heartbeat_lock = threading.Condition()
            result_queue = Queue()

            def run_with_queue():
                try:
                    func(*args, **kwargs)
                    if not task_stop_event.is_set():
                        result_queue.put("success")
                except Exception as e:
                    if not task_stop_event.is_set():
                        result_queue.put("exception")
                        logging.info(f"{traceback.format_exc()}")
                finally:
                    task_done_event.set()

            def send_heartbeat_periodically():
                while not heartbeat_event.is_set():
                    with heartbeat_lock:
                        if task_stop_event.is_set() or task_done_event.is_set():
                            break
                        logger.info("alive")
                        heartbeat_lock.wait(timeout=heartbeat_interval)

            task_thread = threading.Thread(target=run_with_queue, daemon=True)
            task_thread.start()

            heartbeat_thread = threading.Thread(target=send_heartbeat_periodically, daemon=True)
            heartbeat_thread.start()

            try:
                start_time = time.monotonic()
                while not task_done_event.is_set():
                    elapsed_time = time.monotonic() - start_time
                    if elapsed_time >= max_duration:
                        task_stop_event.set()
                        result_queue.put("timeout")
                        break
                    task_done_event.wait(timeout=min(task_check_interval, max_duration - elapsed_time))               
            except KeyboardInterrupt:
                result_queue.put("KeyboardInterrupt")
            except Exception as e:
                result_queue.put("exception")
                logging.info(f"{traceback.format_exc()}")
            finally:
                heartbeat_event.set()
                task_stop_event.set()
                with heartbeat_lock:
                    heartbeat_lock.notify_all()

                task_thread.join(timeout=join_timeout)
                heartbeat_thread.join(timeout=join_timeout)

                if result_queue.empty():
                    result_queue.put("unknown error")

                state = result_queue.get()
                logger.info(f"Final State: {state}")

        return wrapper
    return decorator

# Assume execute_task() is defined in a previous cell

# Now we create execute_task_with_timeout by decorating execute_task
# Customize the parameters as needed
execute_task_with_timeout = with_heartbeat_and_timeout(
    max_duration=5,
    heartbeat_interval=1.0,
    task_check_interval=0.1,
    join_timeout=0.1
)(execute_task)

# Invoke execute_task_with_timeout
try:
    execute_task_with_timeout()
except Exception as e:
    logger.error("outer exception")
    logger.error(f"{traceback.format_exc()}")
```

Example execution: run and send KeyboardInterrupt at 2.9 seconds

```
INFO:__main__:alive
INFO:__main__:alive
INFO:__main__:alive
INFO:__main__:Final State: KeyboardInterrupt
```
