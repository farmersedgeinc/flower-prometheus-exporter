
 docker rmi flower-exporter
 docker rmi docker.granduke.net/flower-exporter
 docker images
 sleep 2
 docker build -f ./Dockerfile -t flower-exporter .
 docker login docker.granduke.net
 docker tag flower-exporter docker.granduke.net/flower-exporter
 docker push docker.granduke.net/flower-exporter

