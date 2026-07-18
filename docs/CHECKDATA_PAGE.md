# Checkdata Page

Added a backend-only database inspection page at:

```text
http://localhost:8000/checkdata
```

The page uses the same `DATABASE_URL`/`database_url` configuration as the backend, so it checks the PostgreSQL database that the running app is already connected to.

## What It Does

- Loads with no database query. Each button calls only the operation you ask for.
- Counts the total number of tables only when `Count tables` is clicked.
- Lists table names only when `Load table list` is clicked.
- Lets you type a table name directly, so you can load rows without listing all tables first.
- Lets you change `limit` and `offset` for table browsing.
- Counts rows for one selected table only when `Count rows` is clicked.
- Uses a cleaner dashboard-style UI with a status pill, empty state, metrics sidebar, and a wider result table.

## API Endpoints

- `GET /checkdata/api/tables`
  - Returns table count and table summaries. `include_counts` defaults to `false` to avoid counting every table on page load or list load.
- `GET /checkdata/api/table-count`
  - Returns only the total number of tables.
- `GET /checkdata/api/tables/{table_name}?limit=20&offset=0`
  - Returns rows from one validated table.
- `GET /checkdata/api/tables/{table_name}/count`
  - Returns the row count for one validated table.

## Safety Notes

The implementation validates table names against SQLAlchemy inspector metadata before querying, and builds queries with SQLAlchemy `Table`/`select()` instead of string-concatenated SQL.
