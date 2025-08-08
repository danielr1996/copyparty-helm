# copyparty-helm
Temporary repo for copyparty until the helm chart is merged to upstream. See https://github.com/9001/copyparty/issues/475 for the progress.


# TODO
- auto scaling / HA ?
- ci/cd pipeline
- ingress,lb
- pvc
- service monitor
- postgres/mysql operator
- extraObjects
- use latest / proper versioning and syncing between helm appVersion and docker tag (add helper script to automatically get the version from chart yaml or override in values)
- health checks
- option to use existing configmap or pvc