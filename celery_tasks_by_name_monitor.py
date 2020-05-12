import logging
import threading
import time
import prometheus_client
import requests

CELERY_TASKS_BY_NAME = prometheus_client.Gauge(
    "celery_tasks_by_name", "Count of tasks by name and state", ["name", "state"]
)


class CeleryTasksByNameSetupMonitorThread(threading.Thread):
    def __init__(self, flower_host, *args, **kwargs):
        self.flower_host = flower_host
        self.log = logging.getLogger(f"monitor.{flower_host}")
        self.log.info("Setting up monitor thread")
        self.log.debug(f"Running monitoring thread for {self.flower_host} host.")
        self.setup_metrics()
        super().__init__(*args, **kwargs)

    def setup_metrics(self):
        logging.info("Setting metrics up")
        for metric in CELERY_TASKS_BY_NAME.collect():
            for sample in metric.samples:
                CELERY_TASKS_BY_NAME.labels(**sample[1]).set(0)

    def get_metrics(self):
        while True:
            self.log.debug(f"Getting workers data from {self.flower_host}")
            try:
                req_session = requests.Session()
                req_request = requests.Request("GET", self.endpoint)
                request_prepped = req_request.prepare()
                data = req_session.send(request_prepped, timeout=(3, 15))
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


class CeleryTasksByNameMonitorThread(CeleryTasksByNameSetupMonitorThread):
    @property
    def endpoint(self):
        self.log.debug("URL endpoint: " + self.flower_host)
        return self.flower_host + "/api/tasks"

    def convert_data_to_prometheus(self, data):
        # Here, 'data' is a dictionary type for "print(type(data))".
        # API call for '/api/tasks' returns JSON with task name, each with kv pairs at the second level,
        # from which we extract the task's state.
        # See https://flower.readthedocs.io/en/latest/api.html

        # As some of these tasks may not have purged off since the last API call, we first reset
        # all of the counters to zero.
        for key, value in data.items():
            state = ""
            for k1, v1 in value.items():
                if k1 == "state":
                    state = str(v1)
            CELERY_TASKS_BY_NAME.labels(name=key, state=state).set(0)

        # Ok, now go trough the data capture again and increment the counters.
        for key, value in data.items():
            state = ""
            for k1, v1 in value.items():
                if k1 == "state":
                    state = str(v1)
            CELERY_TASKS_BY_NAME.labels(name=key, state=state).inc()


# Cheers!
