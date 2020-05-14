# TRISS FLOWER Grafana Dashboard:

1) CELERY_WORKERS (Gauge) [app] with count   (This gives the worker's name, but I am not currently displaying the name in grafana.)
   This is set up as a "Singlestat" in grafana with `sum(celery_workers{job=~"$job"})`

2) CELERY_TASK_TYPES_BY_STATE ['task_type', 'state'] with count of instances of each task_type
   This is set up as a "Graph" in grafana with `sum(celery_task_types_by_state{job=~"$job", state="RECEIVED"}) by (task_type)`,
   just change the "state" for each kind "FAILURE, PENDING, RECEIVED, RETRY, REVOKED, STARTED, and SUCCESS".

3) CELERY_TASK_DURATION_BY_STATE ['name', 'state'] with runtime as the counter
   This is set up as a "Graph" in grafana with `celery_task_duration_seconds_by_state{job=~"$job",state="RECEIVED"}`
   With Label Format: `{{name}}`

## Cruft

```
topk(15, celery_task_duration_seconds_by_state{job="michel-flower-exporter", state="SUCCESS"})

topk(15, sum(celery_task_duration_seconds_by_state{job=~"$job", state="RECEIVED"}) by (name))

topk(15, sum(rate(celery_task_duration_seconds_by_state{job=~"$job", state="SUCCESS"}[$TIME_FRAME])) by (name))

WORKS in PROM: topk(7, sum(celery_task_duration_seconds_by_state{job="michel-flower-exporter", state="SUCCESS"}) by (name))

WORKS IN PROM:  topk(7, celery_task_duration_seconds_by_state) 

This will take each "NAME" as a seperate thing to get the top X, so then entire list "topk(7, celery_task_duration_seconds_by_state) by (name)"

shorter list when by state: topk(7, celery_task_duration_seconds_by_state) by (state)

sort_desc(celery_task_duration_seconds_by_state{job=~"$job",state="SUCCESS"})  and lengend-format {{name}}

https://prometheus.io/docs/prometheus/latest/querying/functions/
```

## References:

1. [Histograms](https://prometheus.io/docs/practices/histograms/), you would use buckets for say, runtimes incurred by various task types, as an example.
1. [Histogram example](https://prometheus.io/docs/practices/histograms/#apdex-score)
1. [How do histograms work?](https://www.robustperception.io/how-does-a-prometheus-histogram-work)
1. [Prometheus Types](https://github.com/prometheus/client_python)
1. [Requests Module Advanced Docs](https://requests.readthedocs.io/en/master/user/advanced/)

## Restarts:

Have determined that a "timeout" event on the does NOT coincide with a restart (for which the termination reason in the pod description is "Completed").
Did capture this transient error once (seems to be from the "requests" python module:

```
Exception in thread Thread-2:
Traceback (most recent call last):
  File "/usr/local/lib/python3.6/site-packages/urllib3/response.py", line 362, in _error_catcher
    yield
  File "/usr/local/lib/python3.6/site-packages/urllib3/response.py", line 444, in read
    data = self._fp.read(amt)
  File "/usr/local/lib/python3.6/http/client.py", line 459, in read
    n = self.readinto(b)
  File "/usr/local/lib/python3.6/http/client.py", line 503, in readinto
    n = self.fp.readinto(b)
  File "/usr/local/lib/python3.6/socket.py", line 586, in readinto
    return self._sock.recv_into(b)
ConnectionResetError: [Errno 104] Connection reset by peer

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.6/site-packages/requests/models.py", line 750, in generate
    for chunk in self.raw.stream(chunk_size, decode_content=True):
  File "/usr/local/lib/python3.6/site-packages/urllib3/response.py", line 496, in stream
    data = self.read(amt=amt, decode_content=decode_content)
  File "/usr/local/lib/python3.6/site-packages/urllib3/response.py", line 461, in read
    raise IncompleteRead(self._fp_bytes_read, self.length_remaining)
  File "/usr/local/lib/python3.6/contextlib.py", line 99, in __exit__
    self.gen.throw(type, value, traceback)
  File "/usr/local/lib/python3.6/site-packages/urllib3/response.py", line 380, in _error_catcher
    raise ProtocolError('Connection broken: %r' % e, e)
urllib3.exceptions.ProtocolError: ("Connection broken: ConnectionResetError(104, 'Connection reset by peer')", ConnectionResetError(104, 'Connection reset by peer'))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.6/threading.py", line 916, in _bootstrap_inner
    self.run()
  File "/app/celery_task_types_by_state_monitor.py", line 67, in run
    self.get_metrics()
  File "/app/celery_task_types_by_state_monitor.py", line 38, in get_metrics
    data = req_session.send(request_prepped, timeout=(3, 15))
  File "/usr/local/lib/python3.6/site-packages/requests/sessions.py", line 686, in send
    r.content
  File "/usr/local/lib/python3.6/site-packages/requests/models.py", line 828, in content
    self._content = b''.join(self.iter_content(CONTENT_CHUNK_SIZE)) or b''
  File "/usr/local/lib/python3.6/site-packages/requests/models.py", line 753, in generate
    raise ChunkedEncodingError(e)
requests.exceptions.ChunkedEncodingError: ("Connection broken: ConnectionResetError(104, 'Connection reset by peer')", ConnectionResetError(104, 'Connection reset by peer'))
```

In other cases, looks like a timeout:

```
  File "/usr/local/lib/python3.6/site-packages/requests/adapters.py", line 529, in send
    raise ReadTimeout(e, request=request)
requests.exceptions.ReadTimeout: HTTPConnectionPool(host='triss-flower', port=5555): Read timed out. (read timeout=15)
```

1. Note, `Thread-x` will match the order the treads are set up in the mainline, starting from "1".
1. Note, when this event happens at the apex of a CPU sawtooth climb.

**Cheers!**
