# Common Shared Assets

This directory contains shared assets that are used across multiple services:

- `/schemas` - Shared data schemas and type definitions
- `/clients` - API client templates and specifications

## Usage

### TypeScript/Frontend

Import types from the schemas directory:

```typescript
import { Memory } from '../common/schemas/memory'
```

### Python/Backend

Import schemas for validation:

```python
from common.schemas import memory
```

## Maintenance

When updating schemas, ensure both TypeScript and Python versions are synchronized.
