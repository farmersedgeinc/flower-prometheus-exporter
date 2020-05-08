import logging
import threading
import time
import prometheus_client
import requests

CELERY_TASKS_BY_TYPE_AND_STATE = prometheus_client.Gauge(
    "celery_tasks_by_type_and_state",
    "Tasks with tasks type and state",
    ["task", "task_type", "state"],
)


class MonitorThread(threading.Thread):
    def __init__(self, flower_host, *args, **kwargs):
        self.flower_host = flower_host
        self.log = logging.getLogger(f"monitor.{flower_host}")
        self.log.info("Setting up monitor thread")
        self.log.debug(f"Running monitoring thread for {self.flower_host} host.")
        self.setup_metrics()
        super().__init__(*args, **kwargs)

    def setup_metrics(self):
        logging.info("Setting metrics up")
        for metric in CELERY_TASKS_BY_TYPE_AND_STATE.collect():
            for sample in metric.samples:
                CELERY_TASKS_BY_TYPE_AND_STATE.labels(**sample[1]).set(0)

    def get_metrics(self):
        while True:
            self.log.debug(f"Getting workers data from {self.flower_host}")
            try:
                data = requests.get(self.endpoint)
            except requests.exceptions.ConnectionError as e:
                self.log.error(f"Error receiving data from {self.flower_host} - {e}")
                return
            if data.status_code != 200:
                self.log.error(
                    f"Error receiving data from {self.flower_host}. "
                    f"Host responded with HTTP {data.status_code}"
                )
                time.sleep(1)
                continue
            self.convert_data_to_prometheus(data.json())
            time.sleep(10)

    @property
    def endpoint(self):
        raise NotImplementedError

    def convert_data_to_prometheus(self, data):
        raise NotImplementedError

    def run(self):
        self.log.info(f"Running monitor thread for {self.flower_host}")
        self.get_metrics()


class TaskMonitorThread(MonitorThread):
    @property
    def endpoint(self):
        return self.flower_host + "/api/tasks"

    def convert_data_to_prometheus(self, data):
        # Here, 'data' is a dictionary type for "print(type(data))".
        # API call for '/api/tasks' returns JSON with task name, each with kv pairs at the second level.
        # We extract the task-type (field 'name') and state of the task (field 'state').
        # See https://flower.readthedocs.io/en/latest/api.html
        for key, value in data.items():
            name = ""
            state = ""
            for k1, v1 in value.items():
                if k1 == "name":
                    name = str(v1)
                if k1 == "state":
                    state = str(v1)
            self.log.debug("TASK: " + key + " TASK TYPE: " + name + " STATE: " + state)
            CELERY_TASKS_BY_TYPE_AND_STATE.labels(task=key, task_type=name, state=state)


# Cheers!
