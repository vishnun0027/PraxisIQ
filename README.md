

1 PostgreSQL 16+
Run locally via Docker:
```
docker run --name journal-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=journal \
  -p 5432:5432 \
  -d postgres:16
  ```