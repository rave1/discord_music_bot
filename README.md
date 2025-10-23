# build

```shell
docker build . -t music-bot
```

# run

```shell
docker run --env-file .env -it music-bot /bin/sh
```

remember to keep ur var in file 

if u want u can use ruff for linting

```shell
uv run ruff check
```
