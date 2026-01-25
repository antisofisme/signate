# CHAT-L1-ARCH-004: RAG Pipeline Architecture

**Status**: Active
**Created**: 2026-01-25
**Complies With**: CHAT-LAW-001, CHAT-LAW-002

---

## Context

Implementasi RAG (Retrieval-Augmented Generation) untuk meng-inject knowledge base ke dalam chat responses.

---

## Decision

### RAG Pipeline Overview

```
Query → Process → Retrieve → Rerank → Assemble → Generate
```

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG Pipeline                             │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────┤
│  Query   │  Embed   │ Retrieve │ Rerank   │ Assemble │ Generate│
│ Process  │  Query   │ Docs     │ (opt)    │ Context  │ Response│
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬────┘
     │          │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼          ▼
┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│QueryProc│ │Embedder│ │Vector  │ │Reranker│ │Context │ │  LLM   │
│         │ │        │ │Store   │ │        │ │Builder │ │        │
└─────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

---

## Stage 1: Query Processing

### Purpose
- Expand or rewrite query for better retrieval
- Extract intent and entities

### Implementation

```python
class QueryProcessor:
    async def process(self, query: str, context: str = None) -> ProcessedQuery:
        # 1. Basic cleaning
        cleaned = self._clean_query(query)

        # 2. Intent detection (optional)
        intent = await self._detect_intent(cleaned)

        # 3. Query expansion (for ambiguous queries)
        if intent.needs_expansion:
            expanded = await self._expand_query(cleaned, context)
        else:
            expanded = [cleaned]

        return ProcessedQuery(
            original=query,
            cleaned=cleaned,
            expanded=expanded,
            intent=intent,
        )

    async def _expand_query(self, query: str, context: str) -> List[str]:
        """Use LLM to generate alternative queries"""
        prompt = f"""
        Original query: {query}
        Context: {context}

        Generate 2-3 alternative phrasings that might help find relevant documents.
        Output as JSON array of strings.
        """
        result = await self.llm.generate([Message(role="user", content=prompt)])
        return json.loads(result)
```

---

## Stage 2: Embedding

### Purpose
- Convert query to vector for similarity search

### Implementation

```python
class EmbeddingService:
    def __init__(self, provider: EmbeddingProvider, cache: Cache):
        self.provider = provider
        self.cache = cache

    async def embed(self, text: str) -> List[float]:
        # Check cache first
        cache_key = f"emb:{hash(text)}"
        cached = await self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        # Generate embedding
        embedding = await self.provider.embed(text)

        # Cache for 24 hours
        await self.cache.set(cache_key, json.dumps(embedding), ttl=86400)

        return embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Check cache for each
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            cache_key = f"emb:{hash(text)}"
            cached = await self.cache.get(cache_key)
            if cached:
                results[i] = json.loads(cached)
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Batch embed uncached
        if uncached_texts:
            embeddings = await self.provider.embed_batch(uncached_texts)
            for i, (idx, text, emb) in enumerate(zip(uncached_indices, uncached_texts, embeddings)):
                results[idx] = emb
                cache_key = f"emb:{hash(text)}"
                await self.cache.set(cache_key, json.dumps(emb), ttl=86400)

        return results
```

---

## Stage 3: Retrieval

### Hybrid Search Strategy

```python
class HybridRAGStrategy(RAGStrategy):
    """
    Combines dense (vector) and sparse (BM25) search with RRF fusion.
    Shown to improve accuracy by 15-30% over dense-only.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        bm25_index: BM25Index,
        alpha: float = 0.5,  # Weight for dense vs sparse
    ):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.alpha = alpha

    async def retrieve(
        self,
        query: str,
        context: RetrievalContext
    ) -> RetrievalResult:
        # 1. Dense search (vector similarity)
        query_embedding = await context.embedder.embed(query)
        dense_results = await self.vector_store.search(
            query_vector=query_embedding,
            top_k=context.top_k * 2,  # Over-retrieve for fusion
            filters={"tenant_id": context.tenant_id}
        )

        # 2. Sparse search (BM25)
        sparse_results = await self.bm25_index.search(
            query=query,
            tenant_id=context.tenant_id,
            top_k=context.top_k * 2
        )

        # 3. Reciprocal Rank Fusion (RRF)
        fused = self._rrf_fusion(dense_results, sparse_results, k=60)

        # 4. Return top_k
        return RetrievalResult(
            documents=fused[:context.top_k],
            strategy="hybrid",
            dense_count=len(dense_results),
            sparse_count=len(sparse_results),
        )

    def _rrf_fusion(
        self,
        dense: List[SearchResult],
        sparse: List[SearchResult],
        k: int = 60
    ) -> List[SearchResult]:
        """Reciprocal Rank Fusion"""
        scores = {}

        # Score from dense results
        for rank, result in enumerate(dense):
            doc_id = result.id
            scores[doc_id] = scores.get(doc_id, 0) + self.alpha / (k + rank + 1)

        # Score from sparse results
        for rank, result in enumerate(sparse):
            doc_id = result.id
            scores[doc_id] = scores.get(doc_id, 0) + (1 - self.alpha) / (k + rank + 1)

        # Sort by fused score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # Get full results
        all_results = {r.id: r for r in dense + sparse}
        return [all_results[doc_id] for doc_id in sorted_ids if doc_id in all_results]
```

### Alternative Strategies

```python
class VanillaRAGStrategy(RAGStrategy):
    """Simple dense-only retrieval"""

    async def retrieve(self, query: str, context: RetrievalContext) -> RetrievalResult:
        query_embedding = await context.embedder.embed(query)
        results = await self.vector_store.search(
            query_vector=query_embedding,
            top_k=context.top_k,
            filters={"tenant_id": context.tenant_id}
        )
        return RetrievalResult(documents=results, strategy="vanilla")


class CorrectiveRAGStrategy(RAGStrategy):
    """
    Self-correcting RAG: Evaluates retrieval quality and retries if poor.
    """

    async def retrieve(self, query: str, context: RetrievalContext) -> RetrievalResult:
        # Initial retrieval
        results = await self.hybrid.retrieve(query, context)

        # Evaluate relevance
        relevance_score = await self._evaluate_relevance(query, results.documents)

        if relevance_score < 0.5:
            # Try query rewriting
            rewritten_query = await self._rewrite_query(query, results.documents)
            results = await self.hybrid.retrieve(rewritten_query, context)

            # Check again
            relevance_score = await self._evaluate_relevance(rewritten_query, results.documents)

            if relevance_score < 0.5:
                # Fallback to web search or no context
                results = RetrievalResult(documents=[], strategy="corrective-failed")

        return results
```

---

## Stage 4: Reranking (Optional)

### Purpose
- Re-score documents using cross-encoder for higher accuracy
- Typically improves accuracy by 10-20%

### Implementation

```python
class CohereReranker(Reranker):
    """Uses Cohere Rerank API"""

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[RankedDocument]:
        response = await self.client.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=documents,
            top_n=top_k,
        )
        return [
            RankedDocument(
                index=r.index,
                score=r.relevance_score,
                document=documents[r.index]
            )
            for r in response.results
        ]


class CrossEncoderReranker(Reranker):
    """Local cross-encoder reranking"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name)

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[RankedDocument]:
        # Create query-document pairs
        pairs = [(query, doc) for doc in documents]

        # Score pairs
        scores = self.model.predict(pairs)

        # Sort by score
        ranked = sorted(
            enumerate(zip(documents, scores)),
            key=lambda x: x[1][1],
            reverse=True
        )

        return [
            RankedDocument(index=idx, score=score, document=doc)
            for idx, (doc, score) in ranked[:top_k]
        ]


class NoReranker(Reranker):
    """Pass-through, no reranking"""

    async def rerank(self, query: str, documents: List[str], top_k: int) -> List[RankedDocument]:
        return [
            RankedDocument(index=i, score=1.0 - (i * 0.1), document=doc)
            for i, doc in enumerate(documents[:top_k])
        ]
```

---

## Stage 5: Context Assembly

### Purpose
- Build final context string for LLM
- Respect token budget

### Implementation

```python
class ContextAssembler:
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    async def assemble(
        self,
        tenant_config: TenantConfig,
        memory_context: MemoryContext,
        retrieved_docs: List[Document],
        current_query: str
    ) -> AssembledContext:
        # Token budget allocation
        budget = TokenBudget(
            total=self.max_tokens,
            system_prompt=1000,
            retrieved_docs=2500,
            user_facts=500,
            conversation=3000,
            current_query=1000,
        )

        # 1. System prompt (always included)
        system = self._build_system_prompt(tenant_config, budget.system_prompt)

        # 2. Retrieved documents
        docs_text = self._format_documents(retrieved_docs, budget.retrieved_docs)

        # 3. User facts (semantic memory)
        facts_text = self._format_facts(memory_context.user_facts, budget.user_facts)

        # 4. Conversation history
        conv_text = self._format_conversation(
            memory_context.working_messages,
            budget.conversation
        )

        # 5. Build messages
        messages = [
            Message(role="system", content=system),
        ]

        if docs_text:
            messages.append(Message(
                role="system",
                content=f"## Relevant Information\n{docs_text}"
            ))

        if facts_text:
            messages.append(Message(
                role="system",
                content=f"## About This User\n{facts_text}"
            ))

        # Add conversation history
        for msg in memory_context.working_messages:
            messages.append(Message(role=msg.role, content=msg.content))

        # Add current query
        messages.append(Message(role="user", content=current_query))

        return AssembledContext(
            messages=messages,
            token_count=self._count_tokens(messages),
            retrieved_doc_ids=[d.id for d in retrieved_docs],
        )

    def _format_documents(self, docs: List[Document], max_tokens: int) -> str:
        """Format documents with token limit"""
        result = []
        current_tokens = 0

        for doc in docs:
            doc_text = f"[{doc.metadata.get('title', 'Document')}]\n{doc.content}\n"
            doc_tokens = estimate_tokens(doc_text)

            if current_tokens + doc_tokens > max_tokens:
                break

            result.append(doc_text)
            current_tokens += doc_tokens

        return "\n".join(result)
```

---

## Stage 6: Generation

### Purpose
- Call LLM with assembled context
- Stream response

### Implementation

```python
class ResponseGenerator:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def generate(
        self,
        context: AssembledContext,
        stream: bool = True
    ) -> AsyncIterator[str]:
        if stream:
            async for chunk in self.llm.stream(
                messages=context.messages,
                temperature=0.7,
                max_tokens=1000
            ):
                yield chunk
        else:
            result = await self.llm.generate(
                messages=context.messages,
                temperature=0.7,
                max_tokens=1000
            )
            yield result.content
```

---

## RAG Orchestrator

```python
class RAGOrchestrator:
    def __init__(
        self,
        query_processor: QueryProcessor,
        embedding_service: EmbeddingService,
        rag_strategy: RAGStrategy,
        reranker: Reranker,
        context_assembler: ContextAssembler,
        generator: ResponseGenerator,
    ):
        self.query_processor = query_processor
        self.embedding_service = embedding_service
        self.rag_strategy = rag_strategy
        self.reranker = reranker
        self.context_assembler = context_assembler
        self.generator = generator

    async def process(
        self,
        query: str,
        tenant_config: TenantConfig,
        memory_context: MemoryContext,
    ) -> AsyncIterator[str]:
        # 1. Process query
        processed = await self.query_processor.process(query)

        # 2. Retrieve documents
        retrieval_context = RetrievalContext(
            tenant_id=tenant_config.tenant_id,
            embedder=self.embedding_service,
            top_k=10,
        )
        retrieved = await self.rag_strategy.retrieve(processed.cleaned, retrieval_context)

        # 3. Rerank (if enabled)
        if len(retrieved.documents) > 0:
            doc_texts = [d.content for d in retrieved.documents]
            reranked = await self.reranker.rerank(query, doc_texts, top_k=5)
            final_docs = [retrieved.documents[r.index] for r in reranked]
        else:
            final_docs = []

        # 4. Assemble context
        context = await self.context_assembler.assemble(
            tenant_config=tenant_config,
            memory_context=memory_context,
            retrieved_docs=final_docs,
            current_query=query,
        )

        # 5. Generate response
        async for chunk in self.generator.generate(context):
            yield chunk
```

---

## Consequences

### Positive
- Hybrid search improves accuracy significantly
- Modular pipeline allows easy experimentation
- Reranking optional (for cost/latency tradeoff)
- Streaming for better UX

### Negative
- More components to manage
- Latency increases with each stage
- Cost increases with reranking API

---

## Configuration

```python
RAG_CONFIG = {
    "strategy": "hybrid",  # vanilla | hybrid | corrective
    "retrieval": {
        "top_k": 10,
        "dense_weight": 0.5,
        "score_threshold": 0.5,
    },
    "reranking": {
        "enabled": True,
        "provider": "cohere",  # cohere | cross-encoder | none
        "top_k": 5,
    },
    "context": {
        "max_tokens": 8000,
        "doc_max_tokens": 2500,
    },
}
```
