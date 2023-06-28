# Run Qdrant

```bash
docker run -p 6333:6333 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant:latest
```

Navigate to `http://localhost:6333/dashboard` to access the service Dashboard.