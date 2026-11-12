# Dockerized Task Tracker (FastAPI + Postgres + Redis + Nginx)

```
client -> nginx:8080 -> api:8000 -> postgres (data, volume)
                              \-> redis (10s cache of GET /tasks)
```

## Run it
```bash
cp .env.example .env          # edit the password
docker compose up -d --build --wait
./tests/smoke.sh              # end-to-end check
```

## Try it
```bash
curl -X POST localhost:8080/tasks -H 'Content-Type: application/json' -d '{"title":"ship it"}'
curl localhost:8080/tasks      # "source":"db"
curl localhost:8080/tasks      # "source":"cache"
curl -X PATCH localhost:8080/tasks/1/done
curl -X DELETE localhost:8080/tasks/1
```
Interactive API docs: http://localhost:8080/docs

## Useful commands
```bash
docker compose ps                    # health status
docker compose logs -f api           # follow logs
docker compose exec db psql -U taskuser -d tasks -c 'select * from tasks;'
docker compose exec redis redis-cli keys '*'
docker compose restart api
docker compose down                  # stop (data kept)
docker compose down -v               # stop + delete DB volume
docker image ls taskapp-api          # check final image size
```

## Experiments (this is where the learning is)
1. `docker compose down` then `up` again: tasks persist (named volume).
2. `docker compose stop redis`, then call /health: it fails, and the healthcheck marks `api` unhealthy.
3. Try `curl localhost:5432` or `localhost:8000`: not reachable, since only nginx publishes a port.
4. Change `main.py`, run `docker compose up -d --build api`: layer caching keeps rebuilds fast.
5. Scale the API: `docker compose up -d --scale api=3` (nginx resolves `api` via Docker DNS).
6. Push to GitHub: the Actions workflow builds, smoke-tests, and publishes to GHCR.

## Concepts covered
multi-stage builds, non-root user, HEALTHCHECK, .dockerignore, Compose networks,
named volumes, `depends_on: service_healthy`, env-based config, reverse proxy, CI/CD.
