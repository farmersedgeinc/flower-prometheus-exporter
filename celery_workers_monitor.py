import logging
import threading
import time
import prometheus_client
import requests

CELERY_WORKERS = prometheus_client.Gauge(
    "celery_workers", "Number of alive workers", ["app"]
)

# See https://github.com/prometheus/client_python


class CeleryWorkersSetupMonitorThread(threading.Thread):
    def __init__(self, flower_host, *args, **kwargs):
        self.flower_host = flower_host
        # self.log = logging.getLogger(f"monitor.{flower_host}")
        self.log = logging.getLogger("monitor")
        self.log.info("Setting up monitor thread: CeleryWorkersMonitorThread")
        self.log.debug(f"Running monitoring thread for {self.flower_host} host.")
        self.setup_metrics()
        super().__init__(*args, **kwargs)

    def setup_metrics(self):
        logging.info("Setting metrics up")
        for metric in CELERY_WORKERS.collect():
            for sample in metric.samples:
                CELERY_WORKERS.labels(**sample[1]).set(0)

    def get_metrics(self):
        while True:
            self.log.debug(f"Getting workers data from {self.flower_host}")
            try:
                req_session = requests.Session()
                req_request = requests.Request("GET", self.endpoint)
                # request_prepped = req_request.prepare()
                request_prepped = req_session.prepare_request(req_request)
                data = req_session.send(request_prepped, timeout=(3, 15))
                self.log.debug(
                    "API request.get status code: "
                    + str(data.status_code)
                    + " Endpoint: "
                    + str(self.endpoint)
                )
            except requests.exceptions.ConnectionError as e:
                # self.log.error(f"Error receiving data from {self.flower_host} - {e}")
                self.log.error(f"Error receiving data - {e}")
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
        self.log.debug(
            f"Running monitor thread CeleryWorkersMonitorThread for {self.flower_host}"
        )
        self.log.info(f"Running monitor thread CeleryWorkersMonitorThread")
        self.get_metrics()


class CeleryWorkersMonitorThread(CeleryWorkersSetupMonitorThread):
    @property
    def endpoint(self):
        self.log.debug("URL endpoint: " + self.flower_host)
        return self.flower_host + "/api/workers"

    def convert_data_to_prometheus(self, data):
        # Here, 'data' is a dictionary type for "print(type(data))".
        # See https://flower.readthedocs.io/en/latest/api.html
        self.log.debug("Convert data to prometheus")
        app = "triss-test"
        CELERY_WORKERS.labels(app).set(0)
        for k, v in data.items():
            self.log.debug("Worker: " + str(k))
            CELERY_WORKERS.labels(app).inc()


# Cheers!
