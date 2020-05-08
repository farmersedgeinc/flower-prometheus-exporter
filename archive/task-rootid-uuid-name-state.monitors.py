import logging
import threading
import time
### import json
import prometheus_client
import requests

WORKER_TASKS = prometheus_client.Gauge(
    'celery_worker_tasks',
    'Tasks and state of tasks per worker per flower instance',
    ['task', 'state']
)

class MonitorThread(threading.Thread):

    def __init__(self, flower_host, *args, **kwargs):
        self.flower_host = flower_host
        self.log = logging.getLogger(f'monitor.{flower_host}')
        self.log.info('Setting up monitor thread')
        self.log.debug(f"Running monitoring thread for {self.flower_host} host.")
        self.setup_metrics()
        super().__init__(*args, **kwargs)

    def setup_metrics(self):
        logging.info("Setting metrics up")
        for metric in WORKER_TASKS.collect():
            for sample in metric.samples:
                WORKER_TASKS.labels(**sample[1]).set(0)

    def get_metrics(self):
        while True:
            self.log.debug(f"Getting workers data from {self.flower_host}")
            try:
                data = requests.get(self.endpoint)
                # print('Michel1: ' + data.text)
                # This only gets the response code: print('Michel1: ' + str(data))
            except requests.exceptions.ConnectionError as e:
                self.log.error(f'Error receiving data from {self.flower_host} - {e}')
                return
            if data.status_code != 200:
                self.log.error(f'Error receiving data from {self.flower_host}. '
                               f'Host responded with HTTP {data.status_code}')
                time.sleep(1)
                continue
            self.convert_data_to_prometheus(data.json())
            time.sleep(1)

    @property
    def endpoint(self):
        raise NotImplementedError

    def convert_data_to_prometheus(self, data):
        raise NotImplementedError

    def run(self):
        self.log.info(f'Running monitor thread for {self.flower_host}')
        self.get_metrics()

class QueueMonitorThread(MonitorThread):
    @property
    def endpoint(self):
        # Michel return self.flower_host + '/api/queues/length'  ## {"active_queues": []}
        # return self.flower_host + '/api/workers'  ## lots
        # return self.flower_host + '/api/tasks'    ## lots
        # return self.flower_host + '/api/task/types'  ## short list
        # return self.flower_host + '/api/queues'   ## "Error, page not found" HTML dump.
        # return self.flower_host + '/api/bogus'    ## "Error, page not found" HTML dump.
        # https://prometheus.io/docs/instrumenting/exposition_formats/
        # https://prometheus.io/docs/practices/naming/
        # return self.flower_host + '/api/workers'
        return self.flower_host + '/api/tasks'

    def convert_data_to_prometheus(self, data):
        print(type(data))
        for key, value in data.items():
            print('TOP: ' + key)
            rooti_id = ''
            uuid = ''
            name = ''
            state = ''
            for k1, v1 in value.items():
                if k1 == 'root_id':
                    root_id = str(v1)
                if k1 == 'uuid':
                    uuid = str(v1)
                if k1 == 'name':
                    name = str(v1)
                if k1 == 'state':
                    state = str(v1)
            # if name == 'None':
            #     print("Bogus")
            #     continue
            print('TOP: ' + key + ' ROOT_ID: ' + root_id + ' UUDI: ' + uuid + ' NAME: ' + name + ' STATE: ' + state)
                
        #for k, v in data.items();
        #    print(k + v)

        #for q_info in data.get('registered', []):
        #    WORKER_TASKS.labels(flower=self.flower_host, task=q_info)
        #    print(str(q_info))
        # Michel
        # for q_info in data.get('active_queues', []):
        #     WORKER_TASKS.labels(flower=self.flower_host, queue=q_info['name']).set(q_info['messages'])
        # for worker_task in data.get([]):
             # WORKER_TASKS.labels(flower=self.flower_host, queue=q_info['name']).set(q_info['messages'])
             # self.log.debug(str(worker_task))
             # print(str(q_info))
             # YES: WORKER_TASKS.labels(flower=self.flower_host)
             # GOAL: WORKER_TASKS.labels(flower=self.flower_host, task=worker_task['name'], worker=worker_task['client'], state=worker_task['state'])
             # WORKER_TASKS.labels(flower=self.flower_host, task=worker_task['uuid'])
             # Populate this: ['flower', 'task', 'worker', 'state']
