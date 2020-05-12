import logging
import threading
import time
import prometheus_client
import requests

CELERY_TASK_TYPES_BY_STATE = prometheus_client.Gauge(
    "celery_task_types_by_state",
    "The count of each state for each task type",
    ["task_type", "state"],
)

# See https://github.com/prometheus/client_python


class CeleryTaskTypesByStateSetupMonitorThread(threading.Thread):
    def __init__(self, flower_host, *args, **kwargs):
        self.flower_host = flower_host
        self.log = logging.getLogger(f"monitor.{flower_host}")
        self.log.info("Setting up monitor thread")
        self.log.debug(f"Running monitoring thread for {self.flower_host} host.")
        self.setup_metrics()
        super().__init__(*args, **kwargs)

    def setup_metrics(self):
        logging.info("Setting metrics up")
        for metric in CELERY_TASK_TYPES_BY_STATE.collect():
            for sample in metric.samples:
                CELERY_TASK_TYPES_BY_STATE.labels(**sample[1]).set(0)

    def get_metrics(self):
        while True:
            self.log.debug(f"Getting workers data from {self.flower_host}")
            try:
                req_session = requests.Session()
                req_request = requests.Request("GET", self.endpoint)
                request_prepped = req_request.prepare()
                data = req_session.send(request_prepped, timeout=(3, 15))
                self.log.debug(
                    "API request.get status code: "
                    + str(data.status_code)
                    + " Endpoint: "
                    + str(self.endpoint)
                )
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


class CeleryTaskTypesByStateMonitorThread(CeleryTaskTypesByStateSetupMonitorThread):
    @property
    def endpoint(self):
        return self.flower_host + "/api/tasks"

    def convert_data_to_prometheus(self, data):
        # Here, 'data' is a dictionary type for "print(type(data))".
        # See https://flower.readthedocs.io/en/latest/api.html
        self.log.debug("Convert data to prometheus, clear the gauges.")

        # First run, clear all the task_type - state gauges from this API call:
        for key, value in data.items():
            task_type = ""
            state = ""
            for k1, v1 in value.items():
                if k1 == "name":
                    task_type = str(v1)
                if k1 == "state":
                    state = str(v1)
            CELERY_TASK_TYPES_BY_STATE.labels(task_type=task_type, state=state).set(0)

        # Ok, play it again Sam, but this time increment the guages.
        self.log.debug("Convert data to prometheus")
        for key, value in data.items():
            task_type = ""
            state = ""
            for k1, v1 in value.items():
                if k1 == "name":
                    task_type = str(v1)
                if k1 == "state":
                    state = str(v1)
            CELERY_TASK_TYPES_BY_STATE.labels(task_type=task_type, state=state).inc()


# Cheers!
