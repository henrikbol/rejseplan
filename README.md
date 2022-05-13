## Prepare for Digital Ocean

```
docker buildx build  --platform linux/amd64 --tag tog . ; docker tag tog registry.digitalocean.com/uggiuggi/tog ; docker push registry.digitalocean.com/uggiuggi/tog
```

### Run command

```
uvicorn app:app --host 0.0.0.0 --port 8080
```

Local build and run:

```
docker-compose up --build app
```