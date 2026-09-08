import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import ExtractedElement


@dataclass
class TextChunk:
    """
    Represents an indexed chunk of text prepared for embedding and vector storage.
    """
    chunk_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0


class BaseChunker(ABC):
    """
    Abstract Base Class for document chunking strategies in SOAR.
    """

    @abstractmethod
    def chunk(self, elements: List[ExtractedElement], document_id: str) -> List[TextChunk]:
        """
        Splits extracted document elements into searchable chunks while preserving metadata.
        """
        pass


class RecursiveCharacterChunker(BaseChunker):
    """
    Splits text recursively using a list of hierarchical separators
    (e.g., paragraphs, newlines, sentences, words) to maintain semantic cohesion.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, elements: List[ExtractedElement], document_id: str) -> List[TextChunk]:
        chunks: List[TextChunk] = []
        global_chunk_idx = 0

        for elem_idx, element in enumerate(elements):
            text = (element.text or "").strip()
            if not text:
                continue

            split_texts = self._split_text(text, self.separators)

            for split_text in split_texts:
                clean_text = split_text.strip()
                if not clean_text:
                    continue

                chunk_id = f"{document_id}_c{global_chunk_idx}"
                # Deepcopy metadata so every chunk has an isolated dict
                chunk_meta = copy.deepcopy(element.metadata)
                chunk_meta["document_id"] = document_id
                chunk_meta["chunk_index"] = global_chunk_idx
                chunk_meta["element_index"] = elem_idx

                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        text=clean_text,
                        metadata=chunk_meta,
                        chunk_index=global_chunk_idx,
                    )
                )
                global_chunk_idx += 1

        return chunks

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively splits text into chunks of at most `chunk_size`."""
        text = text.strip()
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        final_chunks: List[str] = []

        # Find the first valid separator present in text
        separator = separators[-1]
        new_separators = []
        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1 :]
                break

        splits = text.split(separator) if separator else list(text)

        good_splits: List[str] = []
        for s in splits:
            part = s.strip()
            if not part:
                continue

            if len(part) <= self.chunk_size:
                good_splits.append(part)
            else:
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                if new_separators:
                    sub_chunks = self._split_text(part, new_separators)
                    final_chunks.extend(sub_chunks)
                else:
                    # Hard split if no smaller separators exist
                    final_chunks.extend(self._hard_split(part, self.chunk_size, self.chunk_overlap))

        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)

        return final_chunks

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """Merges small text pieces into chunks up to `chunk_size` with `chunk_overlap`."""
        docs: List[str] = []
        current_doc: List[str] = []
        total_len = 0
        join_str = separator if separator else " "

        for piece in splits:
            piece_len = len(piece)
            sep_len = len(join_str) if current_doc else 0
            if total_len + piece_len + sep_len > self.chunk_size:
                if current_doc:
                    doc_text = join_str.join(current_doc).strip()
                    if doc_text:
                        docs.append(doc_text)
                    # Keep overlap pieces from the tail
                    while current_doc and total_len > self.chunk_overlap:
                        current_doc.pop(0)
                        total_len = sum(len(p) for p in current_doc) + (len(join_str) * max(0, len(current_doc) - 1))

            current_doc.append(piece)
            total_len = sum(len(p) for p in current_doc) + (len(join_str) * max(0, len(current_doc) - 1))

        if current_doc:
            doc_text = join_str.join(current_doc).strip()
            if doc_text:
                docs.append(doc_text)

        return docs

    def _hard_split(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Hard character slicing fallback."""
        chunks = []
        step = chunk_size - overlap
        for i in range(0, len(text), step):
            c = text[i : i + chunk_size].strip()
            if c:
                chunks.append(c)
        return chunks
