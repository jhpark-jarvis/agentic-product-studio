# D1 Schema

This directory contains the baseline schema intended for Cloudflare D1 migration.

## Files

- `schema.sql`: normalized D1-compatible schema and index definitions
- `export_sqlite_to_d1.py`: exports SQLite rows into D1-friendly `INSERT` SQL

## Notes

- This schema is based on the current operational SQLite database structure in `instance/app.db`.
- Use this as the starting point for future `wrangler d1 execute` migrations.
- Seed or sample data should be managed separately from this baseline schema.
- Generated export files such as `data.sql` should usually stay out of git.
