az acr login --name zinfradevv1
docker build -t zinfradevv1.azurecr.io/dashboardscript:latest .
docker push zinfradevv1.azurecr.io/dashboardscript:latest
