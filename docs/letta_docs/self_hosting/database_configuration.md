---
title: Database configuration | letta-sdk
description: Configure PostgreSQL as the backend database for self-hosted Letta deployments.
---

## Connecting your own Postgres instance

You can set `LETTA_PG_URI` to connect your own Postgres instance to Letta. Your database must have the `pgvector` vector extension installed.

You can enable this extension by running the following SQL command:

```
CREATE EXTENSION IF NOT EXISTS vector;
```
