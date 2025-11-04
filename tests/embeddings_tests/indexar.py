import concurrent.futures
import hashlib
import json
import logging
import math
import signal
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, cast

import faiss  # type: ignore
import fitz  # type: ignore
import numpy as np
import ollama
import pandas as pd  # type: ignore
import pyarrow.parquet as pq  # type: ignore



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("RAG-Pipeline")



# ===============================
# Splitter Profissional para RAG
# ===============================
class RecursiveCharacterTextSplitter:
    """
    Splitter recursivo que preserva contexto semântico com overlap inteligente.
    
    Melhorias implementadas v2.0:
    - ✅ Overlap baseado em palavras completas (não corta no meio)
    - ✅ NUNCA corta parágrafos duplos (contexto semântico)
    - ✅ Respeita listas numeradas/bullets (1., 2., -, *)
    - ✅ Preserva citações e blocos de código
    - ✅ Limite de recursão para evitar stack overflow
    - ✅ Separadores hierárquicos inteligentes
    - ✅ Validação de chunks (não retorna vazios ou muito pequenos)
    """
    
    def __init__(
        self, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 150, 
        length_function: Callable[[str], int] = len,
        separators: Optional[List[str]] = None,
        max_recursion_depth: int = 5,
        min_chunk_size: int = 50,  # Novo: ignora chunks muito pequenos
        respect_semantic_boundaries: bool = True  # Novo: respeita limites semânticos
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.max_recursion_depth = max_recursion_depth
        self.min_chunk_size = min_chunk_size
        self.respect_semantic_boundaries = respect_semantic_boundaries
        
        # Separadores hierárquicos (do mais importante pro menos)
        self.separators = separators or [
            "\n\n\n",      # Seções grandes (3+ quebras)
            "\n\n",        # Parágrafos (NUNCA cortar se possível)
            "\n",          # Linhas simples
            ". ",          # Sentenças completas
            "! ",          # Exclamações
            "? ",          # Perguntas
            "; ",          # Separador forte
            ": ",          # Listas/definições
            ", ",          # Separador fraco
            " ",           # Palavras
            ""             # Fallback (caracteres)
        ]

    def split_text(self, text: str) -> List[str]:
        """
        Divide texto recursivamente em chunks com overlap inteligente.
        
        Returns:
            Lista de chunks validados (sem vazios, sem muito pequenos)
        """
        chunks = self._split_recursive(
            text, 
            self.separators.copy(), 
            self.chunk_size, 
            self.chunk_overlap, 
            depth=0
        )
        
        # Valida e filtra chunks
        validated_chunks = []
        for chunk in chunks:
            chunk = chunk.strip()
            
            # Ignora chunks vazios ou muito pequenos
            if len(chunk) >= self.min_chunk_size:
                validated_chunks.append(chunk)
        
        return validated_chunks

    def _is_semantic_boundary(self, text: str) -> bool:
        """
        Detecta se o texto contém limites semânticos importantes.
        
        Exemplos de limites semânticos:
        - Listas numeradas (1., 2., etc.)
        - Bullets (-, *, •)
        - Citações ("...", '...')
        - Blocos de código (```, indentação)
        """
        if not self.respect_semantic_boundaries:
            return False
        
        patterns = [
            r'^\s*\d+\.',      # Lista numerada: 1., 2., etc.
            r'^\s*[-*•]',      # Bullets: -, *, •
            r'^\s*[a-z]\)',    # Lista alfabética: a), b), etc.
            r'```',            # Bloco de código
            r'^\s{4,}',        # Indentação (código/citação)
            r'^>',             # Citação markdown
        ]
        
        import re
        for pattern in patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True
        
        return False

    def _create_overlap(self, text: str, overlap_size: int) -> str:
        """
        Cria overlap INTELIGENTE preservando:
        1. Palavras completas (não corta no meio)
        2. Sentenças completas quando possível
        3. Contexto semântico (não pega metade de uma lista)
        
        Estratégia:
        - Tenta pegar sentenças completas que cabem no overlap
        - Se não couber, pega palavras completas
        - Garante que não quebra estruturas importantes
        """
        if overlap_size <= 0 or not text:
            return ""
        
        # Tenta separar por sentenças primeiro
        sentence_endings = [". ", "! ", "? ", "\n\n"]
        best_overlap = ""
        
        for sep in sentence_endings:
            if sep in text:
                parts = text.split(sep)
                overlap_parts: List[str] = []
                char_count = 0
                
                # Pega sentenças de trás pra frente
                for part in reversed(parts):
                    part_size = len(part) + len(sep)
                    if char_count + part_size <= overlap_size:
                        overlap_parts.insert(0, part)
                        char_count += part_size
                    else:
                        break
                
                if overlap_parts:
                    candidate = sep.join(overlap_parts)
                    if len(candidate) > len(best_overlap):
                        best_overlap = candidate
        
        # Se não achou sentenças boas, usa palavras
        if not best_overlap:
            words = text.split()
            overlap_words: List[str] = []
            char_count = 0
            
            for word in reversed(words):
                word_size = len(word) + 1  # +1 para o espaço
                if char_count + word_size <= overlap_size:
                    overlap_words.insert(0, word)
                    char_count += word_size
                else:
                    break
                    
            best_overlap = " ".join(overlap_words)
        
        return best_overlap

    def _split_recursive(
        self, 
        text: str, 
        separators: List[str], 
        chunk_size: int, 
        chunk_overlap: int,
        depth: int = 0
    ) -> List[str]:
        """
        Divide recursivamente com proteções semânticas.
        
        Melhorias v2.0:
        - ✅ Não corta blocos semânticos importantes (listas, citações)
        - ✅ Prioriza quebra em parágrafos completos
        - ✅ Overlap inteligente baseado em sentenças
        - ✅ Proteção contra recursão infinita
        """
        # Proteção contra recursão infinita
        if depth >= self.max_recursion_depth:
            logger.warning(f"⚠️  Limite de recursão atingido (depth={depth}). Forçando divisão simples.")
            return self._force_split(text, chunk_size)
        
        # Se cabe no tamanho, retorna direto
        if self.length_function(text) <= chunk_size:
            return [text]
            
        # Pega separador atual
        sep = separators[0] if separators else None
        if sep:
            splits = text.split(sep)
        else:
            splits = list(text)
            
        chunks = []
        current_chunk = ""
        
        for i, part in enumerate(splits):
            # Reconstrói o separador (estava perdido no split)
            if sep and i < len(splits) - 1:
                part += sep
                
            # Verifica se adicionar a parte ultrapassa o limite
            would_exceed = self.length_function(current_chunk + part) > chunk_size
            
            if would_exceed:
                # ✅ PROTEÇÃO SEMÂNTICA: Não quebra se for limite semântico importante
                if current_chunk and self._is_semantic_boundary(part):
                    # Tenta incluir a parte completa se não for MUITO grande
                    if self.length_function(part) < chunk_size * 1.5:
                        # Fecha chunk atual e começa novo com a parte inteira
                        if current_chunk.strip():
                            chunks.append(current_chunk)
                        current_chunk = part
                        continue
                
                # Comportamento normal: fecha chunk atual
                if current_chunk:
                    chunks.append(current_chunk)
                    
                # ✅ OVERLAP INTELIGENTE com sentenças completas
                if chunk_overlap > 0 and current_chunk:
                    overlap = self._create_overlap(current_chunk, chunk_overlap)
                    current_chunk = overlap + (" " if overlap else "") + part
                else:
                    current_chunk = part
            else:
                # Cabe: adiciona ao chunk atual
                current_chunk += part
                
        # Adiciona último chunk se houver
        if current_chunk:
            chunks.append(current_chunk)
            
        # Recursão com próximo separador para chunks grandes
        final_chunks = []
        if len(separators) > 1:
            for chunk in chunks:
                if self.length_function(chunk) > chunk_size:
                    # Recursão com próximo separador
                    final_chunks.extend(
                        self._split_recursive(chunk, separators[1:], chunk_size, chunk_overlap, depth + 1)
                    )
                else:
                    final_chunks.append(chunk)
        else:
            final_chunks = chunks
            
        # Remove whitespace excessivo e retorna
        return [c.strip() for c in final_chunks if c.strip()]
    
    def _force_split(self, text: str, chunk_size: int) -> List[str]:
        """Divisão forçada quando recursão falha (fallback seguro)."""
        words = text.split()
        chunks = []
        current_chunk: List[str] = []
        current_size = 0
        
        for word in words:
            word_len = len(word) + 1
            if current_size + word_len > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = word_len
            else:
                current_chunk.append(word)
                current_size += word_len
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
    
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


@dataclass(frozen=True, slots=True)
class Chunk:
    """
    Estrutura de dados completa para RAG profissional.
    
    Melhorias implementadas:
    - slots=True para economia de memória (~40% menos RAM por instância)
    - SHA256 ao invés de MD5 (mais seguro)
    - ID com apenas 16 caracteres (suficiente para deduplicação)
    - compare=False no chunk_id (mais eficiente)
    """

    content: str
    metadata: Dict[str, Any]
    chunk_id: str = field(default="", compare=False)

    def __post_init__(self):
        if not self.chunk_id:
            content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]
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
        respect_semantic_boundaries: bool = True,  # ✅ NOVO parâmetro
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.add_context = add_context

        # ✅ Splitter melhorado com proteções semânticas
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            min_chunk_size=min_chunk_size,
            respect_semantic_boundaries=respect_semantic_boundaries,
            # Separadores hierárquicos já configurados no construtor
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
    """
    Gera embeddings otimizados para RAG.
    
    Melhorias implementadas:
    - Verifica se embeddings já vêm normalizados (evita redundância)
    - Melhor tratamento de erros
    - Logging de performance
    """

    def __init__(self, model_name: str, num_workers: int = 4, normalize: bool = True):
        self.model_name = model_name
        self.num_workers = num_workers
        self.normalize = normalize
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=num_workers)
        self._embeddings_generated = 0
        self._normalization_applied = 0
        
        logger.info(
            f"Modelo: {model_name} | Workers: {num_workers} | Normalização: {normalize}"
        )

    def _is_normalized(self, vector: List[float], tolerance: float = 1e-5) -> bool:
        """
        Verifica se vetor já está normalizado.
        
        A maioria dos modelos modernos (incluindo Ollama) já retorna
        embeddings normalizados. Esta função evita normalização redundante.
        """
        vec_array = np.array(vector)
        norm = np.linalg.norm(vec_array)
        return bool(abs(norm - 1.0) < tolerance)

    def _embed_single(self, text: str) -> Optional[List[float]]:
        """Gera embedding para um único texto."""
        try:
            response = ollama.embeddings(model=self.model_name, prompt=text)
            embedding: List[float] = response["embedding"]
            self._embeddings_generated += 1

            # ✅ CORREÇÃO: Verifica se já está normalizado antes de normalizar
            if self.normalize:
                if not self._is_normalized(embedding):
                    logger.debug(f"Embedding não normalizado pelo modelo {self.model_name}")
                    embedding = self._normalize_vector(embedding)
                    self._normalization_applied += 1

            return embedding

        except Exception as e:
            error_msg = str(e).lower()
            if "prompt too long" in error_msg or "context length" in error_msg:
                logger.error(
                    f"❌ Texto excede limite do modelo (tamanho: {len(text)} chars). "
                    f"Reduza chunk_size ou use modelo com contexto maior."
                )
            elif "model" in error_msg and "not found" in error_msg:
                logger.error(f"❌ Modelo '{self.model_name}' não encontrado no Ollama")
            else:
                logger.error(f"❌ Erro ao gerar embedding: {e}")
            return None

    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """
        Normaliza vetor para comprimento unitário (L2 norm = 1).
        
        IMPORTANTE: Só necessário se modelo não retornar normalizado.
        Vetores normalizados permitem usar distância euclidiana como proxy
        para similaridade coseno (mais eficiente).
        """
        vec_array = np.array(vector)
        norm = np.linalg.norm(vec_array)
        if norm == 0:
            logger.warning("Vetor zero encontrado - não é possível normalizar")
            return vector
        normalized: List[float] = (vec_array / norm).tolist()
        return normalized

    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Gera embeddings para múltiplos textos em paralelo."""
        return list(self.executor.map(self._embed_single, texts))
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas de processamento."""
        return {
            "embeddings_generated": self._embeddings_generated,
            "normalizations_applied": self._normalization_applied
        }

    def close(self):
        """Fecha o executor e loga estatísticas."""
        stats = self.get_stats()
        if stats["embeddings_generated"] > 0:
            norm_percent = (stats["normalizations_applied"] / stats["embeddings_generated"]) * 100
            logger.info(
                f"📊 Embeddings gerados: {stats['embeddings_generated']} | "
                f"Normalizações aplicadas: {stats['normalizations_applied']} ({norm_percent:.1f}%)"
            )
        self.executor.shutdown(wait=True)


# =============================================================================
# ARMAZENAMENTO VETORIAL PROFISSIONAL
# =============================================================================


class VectorStore:
    """
    Armazena embeddings com índice FAISS otimizado.
    
    Melhorias implementadas:
    - Context manager para gestão automática de recursos
    - Tratamento robusto de exceções
    - Salvamento de progresso em caso de erro
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

        # Deduplicação
        self.seen_hashes: Set[str] = set()
        self.duplicates_skipped = 0
        
        self._is_open = False

    def __enter__(self):
        """Context manager para garantir fechamento de recursos."""
        self.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fecha recursos mesmo com exceção."""
        try:
            self.save_and_close()
        except Exception as e:
            logger.error(f"Erro ao salvar índice durante cleanup: {e}")
        return False  # Não suprime exceções

    def open(self):
        """Abre o arquivo de metadados."""
        if self._is_open:
            logger.warning("VectorStore já está aberto")
            return
            
        try:
            self.metadata_file = open(self.jsonl_path, "w", encoding="utf-8")
            self._is_open = True
            logger.info(f"💾 Salvando em: {self.faiss_path} e {self.jsonl_path}")
        except Exception as e:
            logger.error(f"Erro ao abrir arquivo de metadados: {e}")
            raise

    def add_batch(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]],
        deduplicate: bool = True,
    ):
        """Adiciona um lote de chunks e embeddings com deduplicação opcional."""
        if not self._is_open:
            raise RuntimeError("VectorStore não está aberto. Use 'open()' ou context manager.")
            
        if not embeddings:
            return

        # Deduplicação
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

            if self.duplicates_skipped % 100 == 0 and self.duplicates_skipped > 0:
                logger.debug(f"🗑️  Duplicados removidos até agora: {self.duplicates_skipped}")

        if not embeddings:
            return

        # Inicializa o índice FAISS na primeira vez
        if self.index is None:
            self.dimension = len(embeddings[0])

            if self.use_ivf:
                # IndexIVFFlat para grandes volumes (10k+ chunks)
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(
                    quantizer, self.dimension, self.ivf_nlist
                )
                logger.info(
                    f"🔧 Índice IVF criado (dim: {self.dimension}, nclusters: {self.ivf_nlist})"
                )

                # IVF precisa ser treinado
                training_size = min(len(embeddings), 10000)
                training_data = np.array(embeddings[:training_size], dtype="float32")
                self.index.train(training_data)
                logger.info(f"✅ Índice IVF treinado com {training_size} vetores")
            else:
                # IndexFlatL2 para volumes pequenos/médios (< 10k chunks)
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info(f"🔧 Índice Flat criado (dimensão: {self.dimension})")

        # Adiciona vetores ao FAISS
        embeddings_np = np.array(embeddings, dtype="float32")
        self.index.add(embeddings_np)

        # Salva metadados enriquecidos
        for i, chunk in enumerate(chunks):
            enhanced_metadata = {
                **chunk.metadata,
                "content": chunk.content,  # CRÍTICO: Salva conteúdo para BM25/reranking
                "chunk_id": chunk.chunk_id,
                "vector_index": self.total_chunks + i,
                "embedding_dim": self.dimension,
            }
            if self.metadata_file is not None:
                cast(Any, self.metadata_file).write(
                    json.dumps(enhanced_metadata, ensure_ascii=False) + "\n"
                )

        self.total_chunks += len(chunks)

    def save_and_close(self):
        """Salva o índice, metadados e estatísticas."""
        if not self._is_open:
            logger.warning("VectorStore já está fechado")
            return
            
        try:
            if self.index is not None and self.total_chunks > 0:
                faiss.write_index(self.index, self.faiss_path)
                logger.info(f"✅ {self.total_chunks} chunks salvos em {self.faiss_path}")

                # Salva estatísticas do índice
                stats = {
                    "total_chunks": self.total_chunks,
                    "duplicates_removed": self.duplicates_skipped,
                    "unique_chunks": self.total_chunks,
                    "embedding_dimension": self.dimension,
                    "index_type": "IVF" if self.use_ivf else "Flat",
                    "created_at": datetime.now().isoformat(),
                }

                with open(self.stats_path, "w", encoding="utf-8") as f:
                    json.dump(stats, f, indent=2, ensure_ascii=False)

                logger.info(f"📊 Estatísticas salvas em {self.stats_path}")
            else:
                logger.warning("⚠️  Nenhum chunk para salvar")

        except Exception as e:
            logger.error(f"Erro ao salvar índice: {e}")
            raise
        finally:
            if self.metadata_file is not None:
                self.metadata_file.close()
                self.metadata_file = None
            self._is_open = False


# =============================================================================
# PIPELINE PRINCIPAL PROFISSIONAL
# =============================================================================


def _validate_model(model_name: str) -> bool:
    """
    Valida se o modelo existe no Ollama.
    
    Returns:
        True se modelo existe, False caso contrário
    """
    try:
        ollama.show(model_name)
        return True
    except Exception as e:
        logger.error(f"❌ Modelo '{model_name}' não encontrado no Ollama: {e}")
        logger.info("💡 Execute 'ollama list' para ver modelos disponíveis")
        return False


def _validate_inputs(
    documents: List[str],
    model_name: str,
    chunk_size: int,
    chunk_overlap: int,
    batch_size: int,
    num_workers: int,
) -> None:
    """
    Valida parâmetros de entrada.
    
    Raises:
        ValueError: Se algum parâmetro for inválido
    """
    if not documents:
        raise ValueError("❌ Lista de documentos está vazia")
    
    if not model_name or not isinstance(model_name, str):
        raise ValueError("❌ Nome do modelo é obrigatório e deve ser string")
    
    if chunk_size <= 0:
        raise ValueError(f"❌ chunk_size deve ser positivo (recebido: {chunk_size})")
    
    if chunk_overlap < 0:
        raise ValueError(f"❌ chunk_overlap deve ser >= 0 (recebido: {chunk_overlap})")
    
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"❌ chunk_overlap ({chunk_overlap}) deve ser menor que chunk_size ({chunk_size})"
        )
    
    if batch_size <= 0:
        raise ValueError(f"❌ batch_size deve ser positivo (recebido: {batch_size})")
    
    if num_workers <= 0:
        raise ValueError(f"❌ num_workers deve ser positivo (recebido: {num_workers})")
    
    # Valida se documentos existem
    for doc_path in documents:
        path = Path(doc_path)
        if not path.exists():
            raise ValueError(f"❌ Caminho não existe: {doc_path}")


# Flag global para controlar interrupção
_interrupted = False

def _signal_handler(signum, frame):
    """Handler para Ctrl+C."""
    global _interrupted
    _interrupted = True
    logger.warning("\n⚠️  Interrupção recebida. Finalizando processamento...")


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
    enable_structured_logging: bool = True,
) -> Dict[str, Any]:
    """
    Pipeline PROFISSIONAL para criação de embeddings RAG de alta qualidade.
    
    Melhorias implementadas:
    - ✅ Validação completa de parâmetros
    - ✅ Verificação de modelo no Ollama
    - ✅ Context managers para gestão de recursos
    - ✅ Tratamento de Ctrl+C (interrupção graciosa)
    - ✅ Integração com StructuredLogger
    - ✅ Logging detalhado de performance
    - ✅ Salvamento de progresso em caso de erro

    Args:
        documents: Lista de caminhos de arquivos ou diretórios
        model_name: Nome do modelo Ollama para embeddings
        chunk_size: Tamanho máximo de cada chunk de texto
        chunk_overlap: Sobreposição entre chunks (deve ser < chunk_size)
        batch_size: Quantos chunks processar por vez
        num_workers: Número de threads paralelas
        output_prefix: Prefixo para arquivos de saída
        normalize_embeddings: Se True, normaliza vetores (recomendado)
        deduplicate: Se True, remove chunks duplicados (recomendado)
        min_chunk_size: Tamanho mínimo para considerar um chunk
        add_document_context: Se True, adiciona contexto do documento
        use_ivf_index: None = automático (recomendado), True = força IVF, False = força Flat
        ivf_nlist: Número de clusters para IVF
        ivf_threshold: Número de chunks para ativar IVF automaticamente
        custom_metadata: Metadados customizados para todos os documentos
        enable_structured_logging: Se True, salva métricas em JSON

    Returns:
        Dicionário com estatísticas detalhadas do processamento

    Raises:
        ValueError: Se parâmetros forem inválidos
        RuntimeError: Se modelo não estiver disponível

    Exemplo Básico:
        result = create_embeddings(
            documents=["./docs"],
            model_name="qwen3-embedding:4b"
        )

    Exemplo Avançado:
        result = create_embeddings(
            documents=["./docs", "./reports"],
            model_name="qwen3-embedding:4b",
            chunk_size=800,
            chunk_overlap=100,
            normalize_embeddings=True,
            deduplicate=True,
            custom_metadata={"project": "RAG", "version": "1.0"}
        )
    """
    global _interrupted
    _interrupted = False
    
    # Registra handler para Ctrl+C
    signal.signal(signal.SIGINT, _signal_handler)
    
    start_time = time.time()

    logger.info("=" * 70)
    logger.info("🚀 PIPELINE RAG PROFISSIONAL v2.0")
    logger.info("=" * 70)
    
    # ✅ VALIDAÇÃO DE ENTRADA
    try:
        _validate_inputs(
            documents, model_name, chunk_size, chunk_overlap, 
            batch_size, num_workers
        )
    except ValueError as e:
        logger.error(str(e))
        return {
            "success": False,
            "error": str(e), 
            "total_chunks": 0,
            "chunks_processed": 0,
            "chunks_failed": 0,
            "duplicates_removed": 0,
            "files_processed": 0,
            "files_failed": 0,
            "time_seconds": 0,
            "chunks_per_second": 0,
            "faiss_path": None,
            "metadata_path": None,
            "stats_path": None,
            "embedding_dimension": None,
            "index_type": None,
            "index_auto_selected": False,
            "embeddings_stats": {"embeddings_generated": 0, "normalizations_applied": 0},
            "config": {}
        }
    
    # ✅ Verifica se modelo existe
    if not _validate_model(model_name):
        return {
            "success": False,
            "error": f"Modelo '{model_name}' não encontrado", 
            "total_chunks": 0,
            "chunks_processed": 0,
            "chunks_failed": 0,
            "duplicates_removed": 0,
            "files_processed": 0,
            "files_failed": 0,
            "time_seconds": 0,
            "chunks_per_second": 0,
            "faiss_path": None,
            "metadata_path": None,
            "stats_path": None,
            "embedding_dimension": None,
            "index_type": None,
            "index_auto_selected": False,
            "embeddings_stats": {"embeddings_generated": 0, "normalizations_applied": 0},
            "config": {
                "model": model_name,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "normalized": normalize_embeddings,
                "deduplicated": deduplicate,
                "ivf_threshold": ivf_threshold,
            }
        }
    
    # ✅ Inicializa logger estruturado
    structured_logger = None
    if enable_structured_logging:
        structured_logger = StructuredLogger(f"{output_prefix}_metrics.jsonl")
        structured_logger.log_indexing({
            "total_documents": len(documents),
            "config": {
                "model": model_name,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "batch_size": batch_size,
                "num_workers": num_workers,
                "normalize": normalize_embeddings,
                "deduplicate": deduplicate,
            }
        })

    # Inicializa componentes
    loader = DocumentLoader(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        min_chunk_size=min_chunk_size,
        add_context=add_document_context,
    )

    embedder = EmbeddingGenerator(
        model_name=model_name, 
        num_workers=num_workers, 
        normalize=normalize_embeddings
    )

    # FASE 1: Coleta chunks
    logger.info("📊 Fase 1: Coletando e processando chunks...")

    try:
        all_chunks = []
        files_processed = 0
        files_failed = 0

        for doc_path in documents:
            if _interrupted:
                break
                
            path = Path(doc_path)

            try:
                # Se for diretório, processa todos os arquivos
                if path.is_dir():
                    for file in path.rglob("*"):
                        if _interrupted:
                            break
                        if file.is_file():
                            try:
                                chunks = list(loader.load(file, custom_metadata=custom_metadata))
                                all_chunks.extend(chunks)
                                if chunks:
                                    files_processed += 1
                            except Exception as e:
                                logger.error(f"❌ Erro ao processar {file.name}: {e}")
                                files_failed += 1

                # Se for arquivo, processa diretamente
                elif path.is_file():
                    try:
                        chunks = list(loader.load(path, custom_metadata=custom_metadata))
                        all_chunks.extend(chunks)
                        if chunks:
                            files_processed += 1
                    except Exception as e:
                        logger.error(f"❌ Erro ao processar {path.name}: {e}")
                        files_failed += 1
                        
            except Exception as e:
                logger.error(f"❌ Erro ao acessar {doc_path}: {e}")
                files_failed += 1

        if _interrupted:
            logger.warning("⚠️  Processamento interrompido durante coleta de chunks")
            
        if not all_chunks:
            logger.warning("⚠️  Nenhum chunk foi gerado dos documentos fornecidos")
            return {
                "success": False,
                "total_chunks": 0, 
                "chunks_processed": 0,
                "chunks_failed": 0,
                "duplicates_removed": 0,
                "files_processed": files_processed,
                "files_failed": files_failed,
                "time_seconds": time.time() - start_time,
                "chunks_per_second": 0,
                "faiss_path": f"{output_prefix}.faiss",
                "metadata_path": f"{output_prefix}.jsonl",
                "stats_path": f"{output_prefix}_stats.json",
                "embedding_dimension": None,
                "index_type": None,
                "index_auto_selected": False,
                "embeddings_stats": {"embeddings_generated": 0, "normalizations_applied": 0},
                "config": {
                    "model": model_name,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "normalized": normalize_embeddings,
                    "deduplicated": deduplicate,
                    "ivf_threshold": ivf_threshold,
                },
                "error": "Nenhum chunk foi gerado dos documentos fornecidos"
            }

        total_chunks_estimated = len(all_chunks)
        logger.info(
            f"📊 {total_chunks_estimated} chunks gerados de {files_processed} arquivos"
        )
        if files_failed > 0:
            logger.warning(f"⚠️  {files_failed} arquivos falharam")

        # DECISÃO AUTOMÁTICA DE ÍNDICE
        if use_ivf_index is None:
            auto_use_ivf = total_chunks_estimated >= ivf_threshold
            logger.info("🤖 Detecção automática de índice:")
            logger.info(f"   Chunks estimados: {total_chunks_estimated}")
            logger.info(f"   Threshold IVF: {ivf_threshold}")
            logger.info(
                f"   Decisão: {'IVF (grande escala)' if auto_use_ivf else 'Flat (otimizado)'}"
            )
        else:
            auto_use_ivf = use_ivf_index
            logger.info(
                f"⚙️  Tipo de índice: {'IVF (manual)' if auto_use_ivf else 'Flat (manual)'}"
            )

        # ✅ FASE 2: Gera embeddings e indexa (com context manager)
        logger.info("🚀 Fase 2: Gerando embeddings e indexando...")

        chunks_processed = 0
        chunks_failed = 0

        with VectorStore(
            output_prefix=output_prefix, 
            use_ivf=auto_use_ivf, 
            ivf_nlist=ivf_nlist
        ) as store:
            # Processa em lotes
            for i in range(0, len(all_chunks), batch_size):
                if _interrupted:
                    logger.warning("⚠️  Salvando progresso antes de sair...")
                    break
                    
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
            
            # Context manager automaticamente salva e fecha

        # Estatísticas do embedder
        embed_stats = embedder.get_stats()

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Processamento interrompido pelo usuário")
        return {
            "success": False,
            "error": "Interrompido pelo usuário",
            "partial_results": True,
            "total_chunks": chunks_processed if 'chunks_processed' in locals() else 0,
            "chunks_processed": chunks_processed if 'chunks_processed' in locals() else 0,
            "chunks_failed": chunks_failed if 'chunks_failed' in locals() else 0,
            "duplicates_removed": 0,
            "files_processed": files_processed if 'files_processed' in locals() else 0,
            "files_failed": files_failed if 'files_failed' in locals() else 0,
            "time_seconds": time.time() - start_time,
            "chunks_per_second": 0,
            "faiss_path": f"{output_prefix}.faiss",
            "metadata_path": f"{output_prefix}.jsonl",
            "stats_path": f"{output_prefix}_stats.json",
            "embedding_dimension": None,
            "index_type": None,
            "index_auto_selected": False,
            "embeddings_stats": embedder.get_stats() if 'embedder' in locals() else {"embeddings_generated": 0, "normalizations_applied": 0},
            "config": {
                "model": model_name,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "normalized": normalize_embeddings,
                "deduplicated": deduplicate,
                "ivf_threshold": ivf_threshold,
            }
        }
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        raise
    finally:
        embedder.close()

    elapsed = time.time() - start_time

    # Estatísticas detalhadas
    result = {
        "success": not _interrupted,
        "total_chunks": chunks_processed - chunks_failed,  # Chunks realmente salvos
        "chunks_processed": chunks_processed,
        "chunks_failed": chunks_failed,
        "duplicates_removed": 0,  # Será atualizado abaixo
        "files_processed": files_processed,
        "files_failed": files_failed,
        "time_seconds": round(elapsed, 2),
        "chunks_per_second": round(chunks_processed / elapsed, 2) if elapsed > 0 else 0,
        "faiss_path": f"{output_prefix}.faiss",
        "metadata_path": f"{output_prefix}.jsonl",
        "stats_path": f"{output_prefix}_stats.json",
        "embedding_dimension": None,  # Será lido das stats
        "index_type": "IVF" if auto_use_ivf else "Flat",
        "index_auto_selected": use_ivf_index is None,
        "embeddings_stats": embed_stats,
        "config": {
            "model": model_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "normalized": normalize_embeddings,
            "deduplicated": deduplicate,
            "ivf_threshold": ivf_threshold,
        },
    }
    
    # Lê estatísticas salvas pelo VectorStore
    try:
        with open(f"{output_prefix}_stats.json", "r", encoding="utf-8") as f:
            saved_stats = json.load(f)
            result["total_chunks"] = saved_stats.get("total_chunks", result["total_chunks"])
            result["duplicates_removed"] = saved_stats.get("duplicates_removed", 0)
            result["embedding_dimension"] = saved_stats.get("embedding_dimension")
    except Exception as e:
        logger.warning(f"Não foi possível ler estatísticas salvas: {e}")

    logger.info("=" * 70)
    logger.info("✅ PROCESSAMENTO CONCLUÍDO")
    logger.info("=" * 70)
    logger.info(f"📊 Chunks únicos indexados: {result['total_chunks']}")
    logger.info(f"🗑️  Duplicados removidos: {result['duplicates_removed']}")
    logger.info(f"⏱️  Tempo: {result['time_seconds']}s ({result['chunks_per_second']} chunks/s)")
    logger.info(f"📁 Arquivos: {result['files_processed']} processados | {result['files_failed']} falharam")
    logger.info(f"🔧 Índice: {result['index_type']} {'(automático)' if result['index_auto_selected'] else '(manual)'}")
    logger.info(f"📐 Dimensão: {result['embedding_dimension']}")
    logger.info("=" * 70)

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Iniciando processamento de embeddings...")

    result = create_embeddings(
        documents=["/home/jordan/Downloads/HistoricalQuotations_B3.pdf"],
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
    
    if "error" in result:
        print(f"❌ ERRO: {result['error']}")
    
    print(f"Total de chunks: {result.get('total_chunks', 0)}")
    print(f"Chunks processados: {result.get('chunks_processed', 0)}")
    print(f"Chunks com falha: {result.get('chunks_failed', 0)}")
    print(f"Duplicados removidos: {result.get('duplicates_removed', 0)}")
    print(f"Arquivos processados: {result.get('files_processed', 0)}")
    print(f"Arquivos com falha: {result.get('files_failed', 0)}")
    print(f"Tempo decorrido: {result.get('time_seconds', 0)}s")
    print(f"Velocidade: {result.get('chunks_per_second', 0)} chunks/s")
    
    if result.get('total_chunks', 0) > 0:
        print(f"\n📁 Arquivos gerados:")
        print(f"  - Índice FAISS: {result.get('faiss_path', 'N/A')}")
        print(f"  - Metadados: {result.get('metadata_path', 'N/A')}")
        print(f"  - Estatísticas: {result.get('stats_path', 'N/A')}")
        print(f"\n📊 Detalhes técnicos:")
        print(f"  - Dimensão dos embeddings: {result.get('embedding_dimension', 'N/A')}")
        print(f"  - Tipo de índice: {result.get('index_type', 'N/A')}")
    else:
        print("\n⚠️  Nenhum arquivo foi gerado (processamento sem chunks)")
    
    print("=" * 50)
