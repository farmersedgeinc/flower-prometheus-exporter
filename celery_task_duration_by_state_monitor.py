import logging
import threading
import time
import prometheus_client
import requests

CELERY_TASK_DURATION_BY_STATE = prometheus_client.Gauge(
    "celery_task_duration_by_state",
    "Runtime for each task and state",
    ["name", "state", "runtime"],
)


class CeleryTaskDurationbyStateSetupMonitorThread(threading.Thread):
    def __init__(self, flower_host, *args, **kwargs):
        self.flower_host = flower_host
        self.log = logging.getLogger(f"monitor.{flower_host}")
        self.log.info("Setting up monitor thread")
        self.log.debug(f"Running monitoring thread for {self.flower_host} host.")
        self.setup_metrics()
        super().__init__(*args, **kwargs)

    def setup_metrics(self):
        logging.info("Setting metrics up")
        for metric in CELERY_TASK_DURATION_BY_STATE.collect():
            for sample in metric.samples:
                CELERY_TASK_DURATION_BY_STATE.labels(**sample[1]).set_to_current_time()

    def get_metrics(self):
        while True:
            self.log.debug(f"Getting data from {self.flower_host}")
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


class CeleryTaskDurationByStateMonitorThread(
    CeleryTaskDurationbyStateSetupMonitorThread
):
    @property
    def endpoint(self):
        self.log.debug("URL endpoint: " + self.flower_host)
        return self.flower_host + "/api/tasks"

    def convert_data_to_prometheus(self, data):
        # Here, 'data' is a dictionary type for "print(type(data))".
        # API call for '/api/tasks' returns JSON with task name, each with kv pairs at the second level,
        # from which we extract the task's state.
        # See https://flower.readthedocs.io/en/latest/api.html

        for key, value in data.items():
            state = ""
            runtime = ""
            for k1, v1 in value.items():
                if k1 == "runtime":
                    runtime = str(v1)
                if k1 == "state":
                    state = str(v1)
            CELERY_TASK_DURATION_BY_STATE.labels(
                name=key, state=state, runtime=runtime
            ).set_to_current_time()


# Cheers!
