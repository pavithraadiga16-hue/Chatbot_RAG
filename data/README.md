# Development sample data

`knowledge_base/` contains fictional Northstar Institute policy text for local RAG development only. These are not real or approved institutional policies. Replace them with reviewed institutional documents before using the assistant for real policy guidance.

`students/` contains synthetic sample records for development and is intentionally excluded from the RAG ingestion process. Do not add real student records to the RAG corpus. The current RAG index is built only from `.txt` files directly inside `knowledge_base/`.
