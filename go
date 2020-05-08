
 docker rmi michel-flower-exporter
 docker rmi docker.granduke.net/michel-flower-exporter
 docker images
 sleep 2
 docker build -f ./Dockerfile -t michel-flower-exporter .
 docker login docker.granduke.net
 docker tag michel-flower-exporter docker.granduke.net/michel-flower-exporter
 docker push docker.granduke.net/michel-flower-exporter

