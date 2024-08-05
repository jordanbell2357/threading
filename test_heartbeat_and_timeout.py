import logging
import time
from heartbeat_and_timeout import with_heartbeat_and_timeout
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_task(x):
    time.sleep(x)

# Now we create execute_task_with_timeout by decorating execute_task
# Customize the parameters as needed
execute_task_with_timeout = with_heartbeat_and_timeout(
    max_duration=7,
    heartbeat_interval=1.0,
    task_check_interval=0.1,
    join_timeout=0.1
)(execute_task)

# Invoke execute_task_with_timeout
try:
    execute_task_with_timeout(x=1)
except Exception as e:
    logger.error("outer exception")
    logger.error(f"{traceback.format_exc()}")
