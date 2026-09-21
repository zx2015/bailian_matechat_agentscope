# Technical Guide (Sample)

## Bailian Rich Code Application
A Bailian Rich Code Application is a Python project packaged as a `.whl`
and uploaded via `runtime-fc-deploy`. It must expose `GET /health` and a
chat endpoint, conventionally `POST /process`.

## RAG
Retrieval-Augmented Generation combines an embedding-based retrieval step
with an LLM prompt to ground answers in external documents.
