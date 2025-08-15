# copyparty-helm
Temporary repo for copyparty until the helm chart is merged to upstream. See https://github.com/9001/copyparty/issues/475 for the progress.



# Building / Using
See values.yaml for all possible values or values.example.yaml for the values you need to adapt most likely
```shell 
helm upgrade --install --create-namespace -n copyparty --wait -f values.yaml copyparty .
helm upgrade --install --create-namespace -n copyparty --wait -f values.yaml copyparty ghcr.io/danielr1996/copyparty:0.1.0
helm package -u -d dist .
helm push dist/copyparty-x.x.x.tgz oci://ghcr.io/danielr1996
```


# TODO
- auto scaling / HA --> not sure if currently possible because of file based db?
- ci/cd pipeline
- service monitor
- extraObjects
- use latest / proper versioning and syncing between helm appVersion and docker tag (add helper script to automatically get the version from chart yaml or override in values)
- health checks
