# flower-prometheus-exporter

flower-prometheus-exporter is a little exporter for Celery related metrics based on Flower API in 
order to get picked up by Prometheus. Main idea is to setup alerting based on flower monitoring.

This was **hugely** inspired by work in these two repositories: 

1. [flower-prometheus-exporter](https://github.com/vooydzig/flower-prometheus-exporter)
1. [celery_prometheus-exporter](https://github.com/zerok/celery-prometheus-exporter)

## Metrics:

So far it provides access to the following metrics for use in Grafana:

~~1) CELERY_WORKERS (Gauge) count   (This gives the worker's name, but I am not currently displaying the name in grafana.)
   This is set up as a "Singlestat" in grafana with `sum(celery_workers{job=~"$job"})`~~  Update 2020Jun23, this was only
   being used for a count of the workers, but it pulls almost a gig each time it is called, causing pod crashed due to 
   curl timeouts.  So disabling it due to its high cost/low value.

2) CELERY_TASK_TYPES_BY_STATE ['task_type', 'state'] with count of instances of each task_type
   This is set up as a "Graph" in grafana with `sum(celery_task_types_by_state{job=~"$job", state="RECEIVED"}) by (task_type)`,
   just change the "state" for each kind "FAILURE, PENDING, RECEIVED, RETRY, REVOKED, STARTED, and SUCCESS".

~~3) CELERY_TASK_DURATION_BY_STATE ['name', 'state'] with runtime as the counter
   This is set up as a "Graph" in grafana with `celery_task_duration_seconds_by_state{job=~"$job",state="RECEIVED"}`
   With Label Format: `{{name}}`~~ (High cardinality, poor candidate for metrics.)

## How to use:

1. Git clone
1. Run in terminal: `$ python flower-prometheus-exporter`

```
[2019-02-17 22:45:06,254: INFO/root] - Starting up on 0.0.0.0:8888
[2019-02-17 22:45:06,254: INFO/root] - Setting metrics up
[2019-02-17 22:45:06,254: INFO/monitor.http://127.0.0.1:5555] - Setting up monitor thread
[2019-02-17 22:45:06,255: INFO/monitor.http://127.0.0.1:5555] - Running monitor thread for http://127.0.0.1:5555
```

Alternatively, you can use the bundle Dockerfile to generate a
Docker image.

By default, the HTTPD will listen at `0.0.0.0:8888`. If you want the HTTPD
to listen to another port, use the `--addr` option or the environment variable
`DEFAULT_ADDR`.

By default, this will expect the flower to be available through
`http://127.0.0.1:5555`, although you can change via environment variable
`FLOWER_HOSTS_LIST`. You can pass multiple flower hosts separated by space. 

For better logging use `--verbose` 

For example:
`python flower-prometheus-exporter --flower http://127.0.0.1:5000 http://127.0.0.1:6000 http://127.0.0.1:5555
`

See an example of building the image in the `build` file.

## Reference:

1. [Flower API doc](https://flower.readthedocs.io/en/latest/api.html)

**Cheers!**
