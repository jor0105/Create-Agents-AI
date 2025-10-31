import json
import math
import sys
import time
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import faiss  # type: ignore
import numpy as np
import ollama

# =============================================================================
# BM25 RERANKER (Cópia do indexar.py para standalone)
# =============================================================================


class BM25Reranker:
    """Implementação leve de BM25 para reranking."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.corpus_size: int = 0

    def fit(self, documents: List[str]):
        """Indexa documentos para BM25."""
        self.corpus_size = len(documents)
        self.doc_lengths = [len(doc.split()) for doc in documents]
        self.avg_doc_length = (
            sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
        )

        for doc in documents:
            unique_terms = set(doc.lower().split())
            for term in unique_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

    def _idf(self, term: str) -> float:
        """Calcula IDF."""
        df = self.doc_freqs.get(term, 0)
        if df == 0:
            return 0.0
        return math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

    def _bm25_score(
        self, query_terms: List[str], doc_terms: List[str], doc_length: int
    ) -> float:
        """Calcula score BM25."""
        score = 0.0
        doc_term_freqs = Counter(doc_terms)

        for term in query_terms:
            if term not in doc_term_freqs:
                continue

            tf = doc_term_freqs[term]
            idf = self._idf(term)

            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_length / self.avg_doc_length)
            )
            score += idf * (numerator / denominator)

        return score

    def rerank(
        self, query: str, documents: List[str], top_k: Optional[int] = None
    ) -> List[Tuple[int, float]]:
        """Rerank documentos usando BM25."""
        query_terms = query.lower().split()
        scores = []

        for idx, doc in enumerate(documents):
            doc_terms = doc.lower().split()
            score = self._bm25_score(query_terms, doc_terms, len(doc_terms))
            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        if top_k:
            scores = scores[:top_k]

        return scores


# =============================================================================
# QUERY EXPANDER
# =============================================================================


class QueryExpander:
    """Expande queries com sinônimos."""

    def __init__(self):
        self.expansions = {
            # Termos financeiros
            "opção": ["opções", "call", "put", "derivativo"],
            "ação": ["ações", "papel", "ativo", "stock"],
            "índice": ["índices", "benchmark", "referência"],
            # Termos técnicos
            "preço": ["valor", "cotação", "valoração"],
            "volume": ["quantidade", "negociado", "liquidez"],
            "retorno": ["rentabilidade", "ganho", "rendimento"],
            # Termos temporais
            "diário": ["dia", "daily", "intraday"],
            "mensal": ["mês", "monthly"],
            "anual": ["ano", "yearly", "anualized"],
        }

    def expand(self, query: str, max_expansions: int = 2) -> str:
        """Expande query com termos relacionados."""
        words = query.lower().split()
        expanded_terms = []

        for word in words:
            expanded_terms.append(word)

            if word in self.expansions:
                expansions = self.expansions[word][:max_expansions]
                expanded_terms.extend(expansions)

        # Remove duplicatas mantendo ordem
        seen = set()
        unique_terms = []
        for term in expanded_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        return " ".join(unique_terms)

    def add_custom_expansion(self, term: str, expansions: List[str]):
        """Adiciona expansão customizada."""
        self.expansions[term.lower()] = expansions


# =============================================================================
# STRUCTURED LOGGER
# =============================================================================


class StructuredLogger:
    """Logger estruturado em JSON."""

    def __init__(self, log_file: str = "rag_metrics.jsonl"):
        self.log_file = log_file
        import hashlib

        self.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]

    def log_retrieval(
        self,
        query: str,
        original_query: str,
        num_results: int,
        retrieval_time: float,
        rerank_time: Optional[float] = None,
        vector_scores: Optional[List[float]] = None,
        bm25_scores: Optional[List[float]] = None,
    ):
        """Loga métricas de retrieval."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": "retrieval",
            "original_query": original_query,
            "expanded_query": query,
            "num_results": num_results,
            "retrieval_time_ms": round(retrieval_time * 1000, 2),
            "rerank_time_ms": round(rerank_time * 1000, 2) if rerank_time else None,
            "vector_avg_score": (
                round(sum(vector_scores) / len(vector_scores), 4)
                if vector_scores
                else None
            ),
            "bm25_avg_score": (
                round(sum(bm25_scores) / len(bm25_scores), 4) if bm25_scores else None
            ),
        }
        self._write(entry)

    def log_generation(
        self, query: str, response: str, generation_time: float, context_size: int
    ):
        """Loga métricas de geração."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": "generation",
            "query": query,
            "response_length": len(response),
            "generation_time_ms": round(generation_time * 1000, 2),
            "context_chunks": context_size,
        }
        self._write(entry)

    def _write(self, entry: Dict[str, Any]):
        """Escreve entrada no arquivo JSONL."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️  Erro ao salvar log: {e}")


# =============================================================================
# SISTEMA RAG AVANÇADO
# =============================================================================


class AdvancedRAG:
    """Sistema RAG com reranking e query expansion."""

    def __init__(
        self,
        index_path: str,
        metadata_path: str,
        embedding_model: str,
        llm_model: str,
        use_reranking: bool = True,
        use_query_expansion: bool = True,
        enable_logging: bool = True,
    ):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.use_reranking = use_reranking
        self.use_query_expansion = use_query_expansion

        # Componentes
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict[str, Any]] = []
        self.chunks: List[str] = []
        self.bm25: Optional[BM25Reranker] = None
        self.expander = QueryExpander() if use_query_expansion else None
        self.logger = StructuredLogger() if enable_logging else None

        # Carrega recursos
        self._load_resources()

        # Inicializa BM25 se reranking ativado
        if self.use_reranking and self.chunks:
            print("🔧 Inicializando BM25 reranker...")
            self.bm25 = BM25Reranker()
            self.bm25.fit(self.chunks)
            print(f"✅ BM25 pronto ({len(self.chunks)} documentos indexados)")

    def _load_resources(self):
        """Carrega índice FAISS e metadados."""
        try:
            print(f"📂 Carregando índice: {self.index_path}")
            self.index = faiss.read_index(self.index_path)

            print(f"📂 Carregando metadados: {self.metadata_path}")
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                for line in f:
                    meta = json.loads(line)
                    self.metadata.append(meta)
                    # Extrai conteúdo se existir no metadata
                    if "content" in meta:
                        self.chunks.append(meta["content"])

            print(f"✅ {len(self.metadata)} chunks carregados")

        except FileNotFoundError:
            print("❌ ERRO: Arquivos de índice não encontrados!")
            print("   Certifique-se de que existem:")
            print(f"   - {self.index_path}")
            print(f"   - {self.metadata_path}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erro ao carregar recursos: {e}")
            sys.exit(1)

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Gera embedding para texto."""
        try:
            response = ollama.embeddings(
                model=self.embedding_model, prompt=text, keep_alive=0
            )
            return np.array(response["embedding"]).astype("float32").reshape(1, -1)
        except Exception as e:
            print(f"❌ Erro ao gerar embedding: {e}")
            sys.exit(1)

    def retrieve(
        self, query: str, k: int = 10, rerank_to: Optional[int] = None
    ) -> Tuple[List[str], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Recupera documentos relevantes com reranking opcional.

        Args:
            query: Query do usuário
            k: Número de documentos a recuperar (fase 1)
            rerank_to: Número final de documentos após reranking (None = k)

        Returns:
            Tupla (chunks, metadados, métricas)
        """
        start_time = time.time()
        original_query = query

        # 1️⃣ Query Expansion (opcional)
        if self.use_query_expansion and self.expander:
            expanded_query = self.expander.expand(query)
            if expanded_query != query:
                print(f"🔍 Query expandida: '{query}' → '{expanded_query}'")
                query = expanded_query

        # 2️⃣ Busca vetorial no FAISS
        print(f"🔎 Buscando {k} documentos no índice vetorial...")
        embedding = self._generate_embedding(query)

        if self.index is None:
            print("❌ Índice não carregado!")
            return [], [], {}

        distances, indices = self.index.search(embedding, k)
        retrieval_time = time.time() - start_time

        # Extrai chunks e metadados
        retrieved_chunks = []
        retrieved_metadata = []

        for idx in indices[0]:
            if idx < len(self.metadata):
                meta = self.metadata[idx]
                retrieved_metadata.append(meta)

                # Tenta extrair conteúdo do metadata
                if "content" in meta:
                    retrieved_chunks.append(meta["content"])
                elif idx < len(self.chunks):
                    retrieved_chunks.append(self.chunks[idx])

        vector_scores = distances[0].tolist()

        # 3️⃣ BM25 Reranking (opcional)
        rerank_time = None
        bm25_scores = None

        if self.use_reranking and self.bm25 and retrieved_chunks:
            print("🔄 Aplicando BM25 reranking...")
            rerank_start = time.time()

            # Rerank
            reranked_results = self.bm25.rerank(
                query, retrieved_chunks, top_k=rerank_to or k
            )

            # Reordena chunks e metadados
            reranked_chunks = []
            reranked_metadata = []
            bm25_scores = []

            for original_idx, bm25_score in reranked_results:
                reranked_chunks.append(retrieved_chunks[original_idx])
                reranked_metadata.append(retrieved_metadata[original_idx])
                bm25_scores.append(bm25_score)

            retrieved_chunks = reranked_chunks
            retrieved_metadata = reranked_metadata
            rerank_time = time.time() - rerank_start

            print(f"✅ Reranking concluído ({len(retrieved_chunks)} documentos)")

        # 4️⃣ Log métricas
        if self.logger:
            self.logger.log_retrieval(
                query=query,
                original_query=original_query,
                num_results=len(retrieved_chunks),
                retrieval_time=retrieval_time,
                rerank_time=rerank_time,
                vector_scores=vector_scores,
                bm25_scores=bm25_scores,
            )

        metrics = {
            "retrieval_time": retrieval_time,
            "rerank_time": rerank_time,
            "total_time": time.time() - start_time,
            "num_results": len(retrieved_chunks),
            "query_expanded": query != original_query,
        }

        return retrieved_chunks, retrieved_metadata, metrics

    def generate_response(
        self, query: str, context_chunks: List[str], metadata: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        """Gera resposta usando LLM com contexto."""
        start_time = time.time()

        # Monta contexto com metadados
        context_parts = []
        for i, (chunk, meta) in enumerate(zip(context_chunks, metadata), 1):
            source = meta.get("source", "desconhecido")
            page = meta.get("page_number", "?")
            context_parts.append(f"[Documento {i} - {source}, pág. {page}]\n{chunk}")

        context = "\n\n---\n\n".join(context_parts)

        prompt = f"""Use APENAS as informações do CONTEXTO abaixo para responder à PERGUNTA.
Não use conhecimento prévio. Se a resposta não estiver no contexto, diga "Não sei".

CONTEXTO:
{context}

PERGUNTA:
{query}

RESPOSTA:
"""

        print(f"💭 Gerando resposta com {self.llm_model}...")

        try:
            response = ollama.generate(
                model=self.llm_model, prompt=prompt, stream=False, keep_alive=0
            )

            answer = response["response"]
            generation_time = time.time() - start_time

            # Log
            if self.logger:
                self.logger.log_generation(
                    query=query,
                    response=answer,
                    generation_time=generation_time,
                    context_size=len(context_chunks),
                )

            metrics = {
                "generation_time": generation_time,
                "response_length": len(answer),
                "context_chunks": len(context_chunks),
            }

            return answer, metrics

        except Exception as e:
            print(f"❌ Erro ao gerar resposta: {e}")
            return "Erro ao gerar resposta.", {}

    def query(self, question: str, k: int = 10, rerank_to: int = 4) -> Dict[str, Any]:
        """
        Pipeline completo: retrieval + reranking + generation.

        Args:
            question: Pergunta do usuário
            k: Documentos a recuperar inicialmente
            rerank_to: Documentos finais após reranking

        Returns:
            Dicionário com resposta e métricas detalhadas
        """
        print("\n" + "=" * 70)
        print("🚀 SISTEMA RAG AVANÇADO")
        print("=" * 70)
        print(f"📝 Pergunta: {question}")
        print(
            f"⚙️  Reranking: {'✅ Ativado' if self.use_reranking else '❌ Desativado'}"
        )
        print(
            f"⚙️  Query Expansion: {'✅ Ativado' if self.use_query_expansion else '❌ Desativado'}"
        )
        print("=" * 70 + "\n")

        total_start = time.time()

        # Retrieval
        chunks, metadata, retrieval_metrics = self.retrieve(
            question, k=k, rerank_to=rerank_to
        )

        if not chunks:
            return {
                "question": question,
                "answer": "Nenhum documento encontrado.",
                "sources": [],
                "metrics": retrieval_metrics,
            }

        # Generation
        answer, generation_metrics = self.generate_response(question, chunks, metadata)

        total_time = time.time() - total_start

        # Prepara fontes
        sources = []
        for meta in metadata:
            sources.append(
                {
                    "source": meta.get("source", "desconhecido"),
                    "page": meta.get("page_number", "?"),
                    "type": meta.get("type", "unknown"),
                }
            )

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "metrics": {
                **retrieval_metrics,
                **generation_metrics,
                "total_time": total_time,
            },
        }


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Configuração
    INDEX_PREFIX = "vector_index"  # Ajuste para seu prefixo
    EMBEDDING_MODEL = "qwen3-embedding:4b"
    LLM_MODEL = "granite4:latest"

    # Inicializa sistema RAG
    rag = AdvancedRAG(
        index_path=f"{INDEX_PREFIX}.faiss",
        metadata_path=f"{INDEX_PREFIX}.jsonl",
        embedding_model=EMBEDDING_MODEL,
        llm_model=LLM_MODEL,
        use_reranking=True,  # ✅ Ativa BM25 reranking
        use_query_expansion=True,  # ✅ Ativa query expansion
        enable_logging=True,  # ✅ Ativa logging estruturado
    )

    # Exemplo de pergunta
    PERGUNTA = "Qual é o conceito de opções financeiras?"

    # Executa query
    result = rag.query(
        question=PERGUNTA,
        k=10,  # Recupera 10 documentos inicialmente
        rerank_to=4,  # Rerank para os 4 melhores
    )

    # Exibe resultados
    print("\n" + "=" * 70)
    print("📊 RESULTADO")
    print("=" * 70)
    print(f"\n❓ PERGUNTA:\n{result['question']}\n")
    print(f"💡 RESPOSTA:\n{result['answer']}\n")
    print("📚 FONTES:")
    for i, source in enumerate(result["sources"], 1):
        print(f"   {i}. {source['source']} (pág. {source['page']}) - {source['type']}")

    print("\n📈 MÉTRICAS:")
    metrics = result["metrics"]
    print(f"   ⏱️  Tempo total: {metrics['total_time']:.2f}s")
    print(f"   🔍 Retrieval: {metrics['retrieval_time']:.2f}s")
    if metrics.get("rerank_time"):
        print(f"   🔄 Reranking: {metrics['rerank_time']:.2f}s")
    print(f"   💭 Geração: {metrics['generation_time']:.2f}s")
    print(f"   📊 Documentos usados: {metrics['context_chunks']}")
    print(f"   📝 Tamanho resposta: {metrics['response_length']} caracteres")

    print("\n" + "=" * 70)
    print("✅ Métricas salvas em: rag_metrics.jsonl")
    print("=" * 70)
