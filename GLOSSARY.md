# Domain Glossary

This glossary captures the domain terminology for simple-rag.

## RAG

- **RAG (Retrieval-Augmented Generation):** A technique that combines information retrieval with large language model generation. The system retrieves relevant documents from a vector store and augments the LLM's prompt with them before generating a response.

## Vector Store

- **Vector Store:** A database optimized for storing and querying high-dimensional vectors (embeddings). In simple-rag, this is the persistent store for document embeddings.

## Embedding

- **Embedding:** A dense vector representation of text produced by an embedding model. Documents are embedded and stored in the vector store; queries are embedded and matched against stored vectors.

## Chunk

- **Chunk:** A segment of a document split during ingestion. Chunks are the unit stored in the vector store and retrieved during a query.

## Index

- **Index:** The structured organization of document chunks in the vector store, typically with metadata (source file, chunk index, etc.).

## Query

- **Query:** A user's question or prompt that triggers retrieval from the vector store. The query is embedded and matched against stored vectors to find relevant chunks.

## Prompt

- **Prompt:** The text sent to the LLM, consisting of system instructions plus retrieved context plus the user's question.

## Retrieval

- **Retrieval:** The process of finding relevant document chunks for a given query, typically via similarity search (cosine similarity, etc.).

## LLM

- **LLM (Large Language Model):** The language model used for generation. In simple-rag, this is configured via the `llm` setting.

## Embedding Model

- **Embedding Model:** The model used to produce vector embeddings for documents and queries.

## Context Window

- **Context Window:** The maximum number of tokens the LLM can process in a single prompt. Retrieved chunks are trimmed to fit within this window.

## Similarity Threshold

- **Similarity Threshold:** The minimum similarity score for a retrieved chunk to be included in the prompt. Chunks below this threshold are discarded.

## Max Chunks

- **Max Chunks:** The maximum number of chunks to retrieve for a single query.

## Document Ingestion

- **Document Ingestion:** The process of loading documents, splitting them into chunks, embedding them, and storing them in the vector store.

## Persistence

- **Persistence:** The mechanism by which the vector store state is saved to disk and restored on restart.

## Configuration

- **Configuration:** The settings that control simple-rag behavior, stored in a config file (e.g., `config.json` or `.env`).
