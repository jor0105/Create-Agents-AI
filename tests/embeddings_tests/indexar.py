import concurrent.futures
import hashlib
import json
import logging
import math
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, cast

import faiss  # type: ignore
import fitz  # type: ignore
import numpy as np
import ollama
import pandas as pd  # type: ignore
import pyarrow.parquet as pq  # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("RAG-Pipeline")


# =============================================================================
# LOGGING ESTRUTURADO (JSON para análise posterior)
# =============================================================================


class StructuredLogger:
    """
    Logger estruturado que salva métricas em JSON para análise.
    Permite rastrear performance e qualidade do RAG ao longo do tempo.
    """

    def __init__(self, log_file: str = "rag_metrics.jsonl"):
        self.log_file = log_file
        self.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]

    def log_indexing(self, metrics: Dict[str, Any]):
        """Loga métricas de indexação."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": "indexing",
            "metrics": metrics,
        }
        self._write(entry)

    def log_retrieval(
        self,
        query: str,
        num_results: int,
        retrieval_time: float,
        rerank_time: Optional[float] = None,
        scores: Optional[List[float]] = None,
    ):
        """Loga métricas de retrieval."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": "retrieval",
            "query": query,
            "num_results": num_results,
            "retrieval_time_ms": round(retrieval_time * 1000, 2),
            "rerank_time_ms": round(rerank_time * 1000, 2) if rerank_time else None,
            "avg_score": round(sum(scores) / len(scores), 4) if scores else None,
            "max_score": round(max(scores), 4) if scores else None,
            "min_score": round(min(scores), 4) if scores else None,
        }
        self._write(entry)

    def log_generation(
        self, query: str, response: str, generation_time: float, context_size: int
    ):
        """Loga métricas de geração de resposta."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": "generation",
            "query": query,
            "response_length": len(response),
            "generation_time_ms": round(generation_time * 1000, 2),
            "context_chunks": context_size,
            "response_preview": (
                response[:200] + "..." if len(response) > 200 else response
            ),
        }
        self._write(entry)

    def _write(self, entry: Dict[str, Any]):
        """Escreve entrada no arquivo JSONL."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Erro ao salvar log estruturado: {e}")


# =============================================================================
# BM25 RERANKING (Sem modelos extras - apenas TF-IDF)
# =============================================================================


class BM25Reranker:
    """
    Implementação leve de BM25 para reranking sem modelos extras.
    Ideal para ambientes com RAM limitada (8GB).

    BM25 é baseado em TF-IDF e funciona bem para queries específicas.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Controla saturação de frequência de termos (1.2-2.0 típico)
            b: Controla normalização de tamanho do documento (0.75 típico)
        """
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

        # Calcula document frequency (DF) para cada termo
        for doc in documents:
            unique_terms = set(doc.lower().split())
            for term in unique_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

    def _idf(self, term: str) -> float:
        """Calcula IDF (Inverse Document Frequency)."""
        df = self.doc_freqs.get(term, 0)
        if df == 0:
            return 0.0
        return math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

    def _bm25_score(
        self, query_terms: List[str], doc_terms: List[str], doc_length: int
    ) -> float:
        """Calcula score BM25 para um documento."""
        score = 0.0
        doc_term_freqs = Counter(doc_terms)

        for term in query_terms:
            if term not in doc_term_freqs:
                continue

            tf = doc_term_freqs[term]
            idf = self._idf(term)

            # Fórmula BM25
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_length / self.avg_doc_length)
            )
            score += idf * (numerator / denominator)

        return score

    def rerank(
        self, query: str, documents: List[str], top_k: Optional[int] = None
    ) -> List[Tuple[int, float]]:
        """
        Rerank documentos usando BM25.

        Args:
            query: Query do usuário
            documents: Lista de documentos para reranking
            top_k: Número de documentos a retornar (None = todos)

        Returns:
            Lista de tuplas (índice_original, score) ordenadas por score
        """
        query_terms = query.lower().split()
        scores = []

        for idx, doc in enumerate(documents):
            doc_terms = doc.lower().split()
            score = self._bm25_score(query_terms, doc_terms, len(doc_terms))
            scores.append((idx, score))

        # Ordena por score descendente
        scores.sort(key=lambda x: x[1], reverse=True)

        if top_k:
            scores = scores[:top_k]

        return scores


# =============================================================================
# QUERY EXPANSION (Sem modelos extras)
# =============================================================================


class QueryExpander:
    """
    Expande queries com sinônimos e variações comuns.
    Melhora recall sem usar modelos pesados.
    """

    def __init__(self):
        # Dicionário de sinônimos/expansões comuns (pode ser expandido)
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
        """
        Expande query com termos relacionados.

        Args:
            query: Query original
            max_expansions: Máximo de termos expandidos por palavra

        Returns:
            Query expandida
        """
        words = query.lower().split()
        expanded_terms = []

        for word in words:
            expanded_terms.append(word)

            # Adiciona expansões se existirem
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
        """Adiciona expansão customizada ao dicionário."""
        self.expansions[term.lower()] = expansions


# =============================================================================
# MÉTRICAS DE RETRIEVAL (Avaliação sem frameworks pesados)
# =============================================================================


class RetrievalMetrics:
    """
    Calcula métricas de retrieval sem frameworks pesados.
    Ideal para validação rápida de qualidade do RAG.
    """

    @staticmethod
    def precision_at_k(retrieved: List[int], relevant: List[int], k: int) -> float:
        """
        Precision@K: % de documentos relevantes entre os K primeiros.

        Args:
            retrieved: Índices dos documentos recuperados (ordenados)
            relevant: Índices dos documentos realmente relevantes
            k: Número de documentos a considerar

        Returns:
            Precision@K (0.0 a 1.0)
        """
        if k == 0:
            return 0.0

        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)

        hits = sum(1 for doc_id in retrieved_k if doc_id in relevant_set)
        return hits / k

    @staticmethod
    def recall_at_k(retrieved: List[int], relevant: List[int], k: int) -> float:
        """
        Recall@K: % de documentos relevantes encontrados entre os K primeiros.
        """
        if not relevant:
            return 0.0

        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)

        hits = sum(1 for doc_id in retrieved_k if doc_id in relevant_set)
        return hits / len(relevant)

    @staticmethod
    def mrr(retrieved_lists: List[List[int]], relevant_lists: List[List[int]]) -> float:
        """
        Mean Reciprocal Rank: Média da posição do primeiro documento relevante.

        MRR = 1/n * Σ(1/rank_first_relevant)

        Exemplo: Se primeiro doc relevante está em posição 3, contribui 1/3
        """
        reciprocal_ranks = []

        for retrieved, relevant in zip(retrieved_lists, relevant_lists):
            relevant_set = set(relevant)

            for rank, doc_id in enumerate(retrieved, start=1):
                if doc_id in relevant_set:
                    reciprocal_ranks.append(1.0 / rank)
                    break
            else:
                reciprocal_ranks.append(0.0)

        return (
            sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
        )

    @staticmethod
    def ndcg_at_k(retrieved: List[int], relevant: List[int], k: int) -> float:
        """
        Normalized Discounted Cumulative Gain@K.
        Considera a posição dos documentos relevantes.
        """
        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)

        # DCG
        dcg = sum(
            (1.0 if doc_id in relevant_set else 0.0) / math.log2(rank + 1)
            for rank, doc_id in enumerate(retrieved_k, start=1)
        )

        # IDCG (ideal)
        ideal_k = min(k, len(relevant))
        idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_k + 1))

        return dcg / idcg if idcg > 0 else 0.0


# =============================================================================
# ESTRUTURAS DE DADOS PROFISSIONAIS
# =============================================================================


@dataclass(frozen=True)
class Chunk:
    """
    Estrutura de dados completa para RAG profissional.
    Inclui todos os metadados necessários para rastreabilidade e debug.
    """

    content: str
    metadata: Dict[str, Any]
    chunk_id: str = field(default="")  # Hash único do conteúdo

    def __post_init__(self):
        # Gera ID único baseado no conteúdo (para deduplicação)
        if not self.chunk_id:
            content_hash = hashlib.md5(self.content.encode()).hexdigest()
            object.__setattr__(self, "chunk_id", content_hash)


@dataclass
class RAGConfig:
    """Configuração profissional para RAG."""

    model_name: str
    normalize_embeddings: bool = True  # ✅ CRÍTICO para similaridade coseno
    chunk_size: int = 1000
    chunk_overlap: int = 150
    min_chunk_size: int = 50  # ✅ Ignora chunks muito pequenos
    batch_size: int = 512
    num_workers: int = 4
    deduplicate: bool = True  # ✅ Remove chunks duplicados
    add_document_context: bool = True  # ✅ Adiciona contexto do documento
    use_ivf_index: bool = False  # ✅ Índice otimizado para grandes volumes
    ivf_nlist: int = 100  # Número de clusters para IVF
    output_prefix: str = "vector_index"  # Saída


# =============================================================================
# LOADERS PROFISSIONAIS DE DOCUMENTOS
# =============================================================================


class DocumentLoader:
    """Carrega e divide documentos com metadados completos para RAG."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        min_chunk_size: int = 50,
        add_context: bool = True,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.add_context = add_context

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
        )

    def load(
        self, filepath: Path, custom_metadata: Optional[Dict] = None
    ) -> Generator[Chunk, None, None]:
        """
        Carrega arquivo com metadados ricos.

        Args:
            filepath: Caminho do arquivo
            custom_metadata: Metadados customizados (tags, categoria, etc.)
        """
        ext = filepath.suffix.lower()

        loaders = {
            ".pdf": self._load_pdf,
            ".csv": self._load_csv,
            ".parquet": self._load_parquet,
            ".xlsx": self._load_excel,
            ".xls": self._load_excel,
            ".txt": self._load_text,
            ".md": self._load_text,
        }

        loader_func = loaders.get(ext)
        if not loader_func:
            logger.warning(f"Tipo de arquivo não suportado: {ext}")
            return

        try:
            # Metadados base do documento
            base_metadata = {
                "source": filepath.name,
                "file_path": str(filepath.absolute()),
                "file_size": filepath.stat().st_size,
                "created_at": datetime.fromtimestamp(
                    filepath.stat().st_ctime
                ).isoformat(),
                "indexed_at": datetime.now().isoformat(),
            }

            # Adiciona metadados customizados
            if custom_metadata:
                base_metadata.update(custom_metadata)

            yield from loader_func(filepath, base_metadata)

        except Exception as e:
            logger.error(f"Erro ao processar {filepath.name}: {e}")

    def _load_pdf(
        self, filepath: Path, base_metadata: Dict
    ) -> Generator[Chunk, None, None]:
        """Carrega PDF com rastreamento PRECISO de páginas."""
        logger.info(f"Processando PDF: {filepath.name}")
        doc = fitz.open(filepath)

        # Processa página por página mantendo rastreabilidade
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()

            if len(page_text.strip()) < self.min_chunk_size:
                continue

            # Divide a página em chunks
            chunks = self.text_splitter.split_text(page_text)

            for chunk_idx, chunk_text in enumerate(chunks):
                if len(chunk_text.strip()) < self.min_chunk_size:
                    continue

                metadata = {
                    **base_metadata,
                    "type": "pdf",
                    "page_number": page_num + 1,  # Número real da página
                    "total_pages": len(doc),
                    "chunk_index": chunk_idx + 1,
                    "char_count": len(chunk_text),
                }

                # ✅ Adiciona contexto do documento (opcional)
                if self.add_context:
                    metadata["document_title"] = filepath.stem
                    metadata["page_location"] = f"pág. {page_num + 1}/{len(doc)}"

                yield Chunk(content=chunk_text.strip(), metadata=metadata)

        doc.close()

    def _load_text(
        self, filepath: Path, base_metadata: Dict
    ) -> Generator[Chunk, None, None]:
        """Carrega arquivos de texto (.txt, .md)."""
        logger.info(f"Processando texto: {filepath.name}")

        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = self.text_splitter.split_text(text)

        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.strip()) < self.min_chunk_size:
                continue

            metadata = {
                **base_metadata,
                "type": "text",
                "chunk_index": i + 1,
                "total_chunks": len(chunks),
                "char_count": len(chunk_text),
            }

            yield Chunk(content=chunk_text.strip(), metadata=metadata)

    def _load_csv(
        self, filepath: Path, base_metadata: Dict
    ) -> Generator[Chunk, None, None]:
        """Carrega CSV com contexto de colunas."""
        logger.info(f"Processando CSV: {filepath.name}")

        # ✅ Lê headers primeiro para contexto
        df_sample = pd.read_csv(filepath, nrows=0)
        columns_info = ", ".join(df_sample.columns.tolist())

        for df_batch in pd.read_csv(filepath, chunksize=1000):
            for i, row in df_batch.iterrows():
                content = ", ".join(
                    [f"{col}: {val}" for col, val in row.items() if pd.notna(val)]
                )

                if len(content.strip()) < self.min_chunk_size:
                    continue

                metadata = {
                    **base_metadata,
                    "type": "csv",
                    "row_number": int(i) + 1,
                    "columns": columns_info,  # ✅ Contexto das colunas
                    "char_count": len(content),
                }

                yield Chunk(content=content, metadata=metadata)

    def _load_parquet(
        self, filepath: Path, base_metadata: Dict
    ) -> Generator[Chunk, None, None]:
        """Carrega Parquet com contexto de schema."""
        logger.info(f"Processando Parquet: {filepath.name}")
        parquet_file = pq.ParquetFile(filepath)

        # ✅ Captura schema para contexto
        schema_info = ", ".join([field.name for field in parquet_file.schema])
        row_counter = 0

        for batch in parquet_file.iter_batches(batch_size=1000):
            df_batch = batch.to_pandas()
            for i, row in df_batch.iterrows():
                row_counter += 1
                content = ", ".join(
                    [f"{col}: {val}" for col, val in row.items() if pd.notna(val)]
                )

                if len(content.strip()) < self.min_chunk_size:
                    continue

                metadata = {
                    **base_metadata,
                    "type": "parquet",
                    "row_number": row_counter,
                    "schema": schema_info,  # ✅ Contexto do schema
                    "char_count": len(content),
                }

                yield Chunk(content=content, metadata=metadata)

    def _load_excel(
        self, filepath: Path, base_metadata: Dict
    ) -> Generator[Chunk, None, None]:
        """Carrega Excel com informação de planilhas."""
        logger.info(f"Processando Excel: {filepath.name}")

        # ✅ Processa todas as sheets
        excel_file = pd.ExcelFile(filepath)

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            columns_info = ", ".join(df.columns.tolist())

            for i, row in df.iterrows():
                content = ", ".join(
                    [f"{col}: {val}" for col, val in row.items() if pd.notna(val)]
                )

                if len(content.strip()) < self.min_chunk_size:
                    continue

                metadata = {
                    **base_metadata,
                    "type": "excel",
                    "sheet_name": sheet_name,  # ✅ Nome da planilha
                    "row_number": int(i) + 1,
                    "columns": columns_info,
                    "char_count": len(content),
                }

                yield Chunk(content=content, metadata=metadata)


# =============================================================================
# GERADOR DE EMBEDDINGS PROFISSIONAL
# =============================================================================


class EmbeddingGenerator:
    """Gera embeddings otimizados para RAG."""

    def __init__(self, model_name: str, num_workers: int = 4, normalize: bool = True):
        self.model_name = model_name
        self.num_workers = num_workers
        self.normalize = normalize
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=num_workers)
        logger.info(
            f"Modelo: {model_name} | Workers: {num_workers} | Normalização: {normalize}"
        )

    def _embed_single(self, text: str) -> Optional[List[float]]:
        """Gera embedding para um único texto."""
        try:
            response = ollama.embeddings(model=self.model_name, prompt=text)
            embedding = response["embedding"]

            if self.normalize:
                embedding = self._normalize_vector(embedding)

            return embedding

        except Exception as e:
            if "prompt too long" in str(e):
                logger.error(
                    f"Texto muito grande (reduza chunk_size). Tamanho: {len(text)} chars"
                )
            else:
                logger.error(f"Erro ao gerar embedding: {e}")
            return None

    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """
        Normaliza vetor para comprimento unitário.
        ✅ ESSENCIAL para busca por similaridade coseno eficiente.
        """
        vec_array = np.array(vector)
        norm = np.linalg.norm(vec_array)
        if norm == 0:
            return vector
        return (vec_array / norm).tolist()

    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Gera embeddings para múltiplos textos em paralelo."""
        return list(self.executor.map(self._embed_single, texts))

    def close(self):
        self.executor.shutdown(wait=True)


# =============================================================================
# ARMAZENAMENTO VETORIAL PROFISSIONAL
# =============================================================================


class VectorStore:
    """
    Armazena embeddings com índice FAISS otimizado.
    Suporta IndexFlatL2 (pequeno) e IndexIVFFlat (grande escala).
    """

    def __init__(
        self,
        output_prefix: str = "vector_index",
        use_ivf: bool = False,
        ivf_nlist: int = 100,
    ):
        self.output_prefix = output_prefix
        self.faiss_path = f"{output_prefix}.faiss"
        self.jsonl_path = f"{output_prefix}.jsonl"
        self.stats_path = f"{output_prefix}_stats.json"

        self.use_ivf = use_ivf
        self.ivf_nlist = ivf_nlist

        self.index: Optional[faiss.Index] = None
        self.metadata_file: Optional[Any] = None
        self.total_chunks = 0
        self.dimension: Optional[int] = None

        # ✅ Deduplicação
        self.seen_hashes: Set[str] = set()
        self.duplicates_skipped = 0

    def open(self):
        """Abre o arquivo de metadados."""
        self.metadata_file = open(self.jsonl_path, "w", encoding="utf-8")
        logger.info(f"Salvando em: {self.faiss_path} e {self.jsonl_path}")

    def add_batch(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]],
        deduplicate: bool = True,
    ):
        """
        Adiciona um lote de chunks e embeddings com deduplicação opcional.

        Args:
            chunks: Lista de chunks
            embeddings: Lista de embeddings
            deduplicate: Se True, remove chunks duplicados
        """
        if not embeddings:
            return

        # ✅ Deduplicação
        if deduplicate:
            unique_chunks = []
            unique_embeddings = []

            for chunk, emb in zip(chunks, embeddings):
                if chunk.chunk_id not in self.seen_hashes:
                    self.seen_hashes.add(chunk.chunk_id)
                    unique_chunks.append(chunk)
                    unique_embeddings.append(emb)
                else:
                    self.duplicates_skipped += 1

            chunks = unique_chunks
            embeddings = unique_embeddings

            if self.duplicates_skipped > 0:
                logger.debug(f"Duplicados removidos: {self.duplicates_skipped}")

        if not embeddings:
            return

        # Inicializa o índice FAISS na primeira vez
        if self.index is None:
            self.dimension = len(embeddings[0])

            if self.use_ivf:
                # ✅ IndexIVFFlat para grandes volumes (10k+ chunks)
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(
                    quantizer, self.dimension, self.ivf_nlist
                )
                logger.info(
                    f"Índice IVF criado (dim: {self.dimension}, nclusters: {self.ivf_nlist})"
                )

                # IVF precisa ser treinado
                training_data = np.array(
                    embeddings[: min(len(embeddings), 10000)], dtype="float32"
                )
                self.index.train(training_data)
                logger.info("Índice IVF treinado")
            else:
                # ✅ IndexFlatL2 para volumes pequenos/médios (< 10k chunks)
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info(f"Índice Flat criado (dimensão: {self.dimension})")

        # Adiciona vetores ao FAISS
        embeddings_np = np.array(embeddings, dtype="float32")
        self.index.add(embeddings_np)

        # Salva metadados enriquecidos
        for i, chunk in enumerate(chunks):
            # ✅ Adiciona informações extras aos metadados
            enhanced_metadata = {
                **chunk.metadata,
                "content": chunk.content,  # ✅ CRÍTICO: Salva conteúdo para BM25
                "chunk_id": chunk.chunk_id,
                "vector_index": self.total_chunks + i,  # Posição no índice
                "embedding_dim": self.dimension,
            }
            if self.metadata_file is not None:
                cast(Any, self.metadata_file).write(
                    json.dumps(enhanced_metadata, ensure_ascii=False) + "\n"
                )

        self.total_chunks += len(chunks)

    def save_and_close(self):
        """Salva o índice, metadados e estatísticas."""
        if self.index is not None:
            faiss.write_index(self.index, self.faiss_path)
            logger.info(f"✓ {self.total_chunks} chunks salvos em {self.faiss_path}")

            # ✅ Salva estatísticas do índice
            stats = {
                "total_chunks": self.total_chunks,
                "duplicates_removed": self.duplicates_skipped,
                "unique_chunks": self.total_chunks,
                "embedding_dimension": self.dimension,
                "index_type": "IVF" if self.use_ivf else "Flat",
                "created_at": datetime.now().isoformat(),
            }

            with open(self.stats_path, "w") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Estatísticas salvas em {self.stats_path}")

        if self.metadata_file is not None:
            self.metadata_file.close()


# =============================================================================
# PIPELINE PRINCIPAL PROFISSIONAL
# =============================================================================


def create_embeddings(
    documents: List[str],
    model_name: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    batch_size: int = 512,
    num_workers: int = 4,
    output_prefix: str = "vector_index",
    normalize_embeddings: bool = True,
    deduplicate: bool = True,
    min_chunk_size: int = 50,
    add_document_context: bool = True,
    use_ivf_index: Optional[bool] = None,
    ivf_nlist: int = 100,
    ivf_threshold: int = 10000,
    custom_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Pipeline PROFISSIONAL para criação de embeddings RAG de alta qualidade.

    Args:
        documents: Lista de caminhos de arquivos ou diretórios
        model_name: Nome do modelo Ollama para embeddings
        chunk_size: Tamanho máximo de cada chunk de texto
        chunk_overlap: Sobreposição entre chunks
        batch_size: Quantos chunks processar por vez
        num_workers: Número de threads paralelas
        output_prefix: Prefixo para arquivos de saída
        normalize_embeddings: Se True, normaliza vetores (RECOMENDADO)
        deduplicate: Se True, remove chunks duplicados (RECOMENDADO)
        min_chunk_size: Tamanho mínimo para considerar um chunk
        add_document_context: Se True, adiciona contexto do documento
        use_ivf_index: None = automático (recomendado), True = força IVF, False = força Flat
        ivf_nlist: Número de clusters para IVF
        ivf_threshold: Número de chunks para ativar IVF automaticamente (padrão: 10000)
        custom_metadata: Metadados customizados para todos os documentos

    Returns:
        Dicionário com estatísticas detalhadas do processamento

    Exemplo Básico (Detecção Automática):
        result = create_embeddings(
            documents=["./docs"],
            model_name="qwen3-embedding:4b"
        )
        # Sistema escolhe automaticamente Flat ou IVF

    Exemplo Avançado:
        result = create_embeddings(
            documents=["./docs"],
            model_name="qwen3-embedding:4b",
            normalize_embeddings=True,
            deduplicate=True,
            # use_ivf_index deixado como None para detecção automática
            custom_metadata={"project": "RAG", "version": "1.0"}
        )
    """
    start_time = time.time()

    logger.info("=" * 70)
    logger.info("🚀 PIPELINE RAG PROFISSIONAL")
    logger.info("=" * 70)

    # Inicializa componentes com configuração profissional
    loader = DocumentLoader(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        min_chunk_size=min_chunk_size,
        add_context=add_document_context,
    )

    embedder = EmbeddingGenerator(
        model_name=model_name, num_workers=num_workers, normalize=normalize_embeddings
    )

    # ✅ FASE 1: Coleta chunks e conta total (para decisão automática de índice)
    logger.info("📊 Fase 1: Coletando e processando chunks...")

    try:
        # Coleta todos os chunks com metadados enriquecidos
        all_chunks = []
        files_processed = 0

        for doc_path in documents:
            path = Path(doc_path)

            # Se for diretório, processa todos os arquivos
            if path.is_dir():
                for file in path.rglob("*"):
                    if file.is_file():
                        chunks = list(
                            loader.load(file, custom_metadata=custom_metadata)
                        )
                        all_chunks.extend(chunks)
                        if chunks:
                            files_processed += 1

            # Se for arquivo, processa diretamente
            elif path.is_file():
                chunks = list(loader.load(path, custom_metadata=custom_metadata))
                all_chunks.extend(chunks)
                if chunks:
                    files_processed += 1
            else:
                logger.warning(f"Caminho não encontrado: {doc_path}")

        if not all_chunks:
            logger.warning("⚠️  Nenhum chunk foi gerado dos documentos fornecidos")
            return {"total_chunks": 0, "time_seconds": 0, "files_processed": 0}

        total_chunks_estimated = len(all_chunks)
        logger.info(
            f"📊 {total_chunks_estimated} chunks gerados de {files_processed} arquivos"
        )

        # ✅ DECISÃO AUTOMÁTICA DE ÍNDICE
        if use_ivf_index is None:
            # Detecção automática baseada no volume
            auto_use_ivf = total_chunks_estimated >= ivf_threshold
            logger.info("🤖 Detecção automática de índice:")
            logger.info(f"   Chunks estimados: {total_chunks_estimated}")
            logger.info(f"   Threshold IVF: {ivf_threshold}")
            logger.info(
                f"   Decisão: {'IVF (grande escala)' if auto_use_ivf else 'Flat (otimizado)'}"
            )
        else:
            # Usuário forçou um tipo específico
            auto_use_ivf = use_ivf_index
            logger.info(
                f"⚙️  Tipo de índice: {'IVF (forçado pelo usuário)' if auto_use_ivf else 'Flat (forçado pelo usuário)'}"
            )

        # Cria VectorStore com índice apropriado
        store = VectorStore(
            output_prefix=output_prefix, use_ivf=auto_use_ivf, ivf_nlist=ivf_nlist
        )

        store.open()

        # ✅ FASE 2: Gera embeddings e indexa
        logger.info("🚀 Fase 2: Gerando embeddings e indexando...")

        # Processa em lotes
        chunks_processed = 0
        chunks_failed = 0

        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(all_chunks) + batch_size - 1) // batch_size

            logger.info(f"⚙️  Lote {batch_num}/{total_batches} ({len(batch)} chunks)")

            # Gera embeddings
            contents = [chunk.content for chunk in batch]
            embeddings_raw = embedder.embed_batch(contents)

            # Filtra chunks com embeddings válidos
            valid_chunks = []
            valid_embeddings = []

            for chunk, emb in zip(batch, embeddings_raw):
                if emb is not None:
                    valid_chunks.append(chunk)
                    valid_embeddings.append(emb)
                    chunks_processed += 1
                else:
                    chunks_failed += 1

            # Salva no store com deduplicação
            if valid_embeddings:
                store.add_batch(valid_chunks, valid_embeddings, deduplicate=deduplicate)

        store.save_and_close()

    finally:
        embedder.close()

    elapsed = time.time() - start_time

    # ✅ Estatísticas detalhadas
    result = {
        "total_chunks": store.total_chunks,
        "chunks_processed": chunks_processed,
        "chunks_failed": chunks_failed,
        "duplicates_removed": store.duplicates_skipped,
        "files_processed": files_processed,
        "time_seconds": round(elapsed, 2),
        "chunks_per_second": (
            round(store.total_chunks / elapsed, 2) if elapsed > 0 else 0
        ),
        "faiss_path": store.faiss_path,
        "metadata_path": store.jsonl_path,
        "stats_path": store.stats_path,
        "embedding_dimension": store.dimension,
        "index_type": "IVF" if auto_use_ivf else "Flat",
        "index_auto_selected": use_ivf_index is None,  # ✅ Indica se foi automático
        "config": {
            "model": model_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "normalized": normalize_embeddings,
            "deduplicated": deduplicate,
            "ivf_threshold": ivf_threshold,
        },
    }

    logger.info("=" * 70)
    logger.info("✅ PROCESSAMENTO CONCLUÍDO")
    logger.info("=" * 70)
    logger.info(f"📊 Chunks únicos: {result['total_chunks']}")
    logger.info(f"🗑️  Duplicados removidos: {result['duplicates_removed']}")
    logger.info(
        f"⏱️  Tempo: {result['time_seconds']}s ({result['chunks_per_second']} chunks/s)"
    )
    logger.info(f"📁 Arquivos processados: {result['files_processed']}")
    logger.info(
        f"🔧 Índice: {result['index_type']} {'(seleção automática)' if result['index_auto_selected'] else '(manual)'}"
    )
    logger.info("=" * 70)

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Iniciando processamento de embeddings...")

    result = create_embeddings(
        documents=["./dados"],
        model_name="qwen3-embedding:4b",
        chunk_size=1000,
        chunk_overlap=150,
        batch_size=512,
        num_workers=4,
        output_prefix="notebook_index",
    )

    # Resultados disponíveis para análise
    print("\n" + "=" * 50)
    print("RESUMO DO PROCESSAMENTO")
    print("=" * 50)
    print(f"Total de chunks: {result['total_chunks']}")
    print(f"Tempo decorrido: {result['time_seconds']}s")
    print(f"Índice FAISS: {result['faiss_path']}")
    print(f"Metadados: {result['metadata_path']}")
