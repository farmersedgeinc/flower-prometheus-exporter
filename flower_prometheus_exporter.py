import argparse
import logging
import os
import signal
import sys

import prometheus_client

from celery_task_duration_seconds_by_state_monitor import (
    CeleryTaskDurationSecondsByStateMonitorThread,
)
from celery_task_types_by_state_monitor import CeleryTaskTypesByStateMonitorThread
from celery_workers_monitor import CeleryWorkersMonitorThread

LOG_FORMAT = "[%(asctime)s: %(levelname)s/%(name)s] - %(message)s"

DEFAULT_ADDR = os.environ.get("DEFAULT_ADDR", "0.0.0.0:8888")
FLOWER_HOSTS_LIST = os.environ.get("FLOWER_HOSTS_LIST", "http://127.0.0.1:5555").split()


def main():
    opts = parse_arguments()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logging.info(f"Starting up on {opts.addr}")
    threads = setup_monitoring_threads(opts)
    start_httpd(opts.addr)
    for t in threads:
        t.join()


def setup_monitoring_threads(opts):
    threads = []
    logging.debug(f"Running {len(opts.flower_addr)} monitoring threads.")
    for flower_addr in opts.flower_addr:
        ctdbs = CeleryTaskDurationSecondsByStateMonitorThread(flower_addr)
        ctdbs.daemon = True
        ctdbs.start()
        threads.append(ctdbs)
        #
        cttbs = CeleryTaskTypesByStateMonitorThread(flower_addr)
        cttbs.daemon = True
        cttbs.start()
        threads.append(cttbs)
        #
        cw = CeleryWorkersMonitorThread(flower_addr)
        cw.daemon = True
        cw.start()
        threads.append(cw)
    return threads


def start_httpd(addr):
    host, port = addr.split(":")
    prometheus_client.start_http_server(int(port), host)


def shutdown(signum, frame):  # pragma: no cover
    logging.info("Shutting down")
    sys.exit(0)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--flower",
        dest="flower_addr",
        default=FLOWER_HOSTS_LIST,
        nargs="+",
        help="List of urls to the Flower monitor. Defaults to {}".format(
            FLOWER_HOSTS_LIST
        ),
    )
    parser.add_argument(
        "--addr",
        dest="addr",
        default=DEFAULT_ADDR,
        help="Address the HTTPD should listen on. Defaults to {}".format(DEFAULT_ADDR),
    )
    parser.add_argument(
        "--verbose", action="store_true", default=False, help="Enable verbose logging"
    )
    opts = parser.parse_args()
    if opts.verbose:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    return opts


if __name__ == "__main__":  # pragma: no cover
    main()
