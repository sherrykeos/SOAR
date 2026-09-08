import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.database.repository import DatabaseManager
from app.embeddings.base import BaseEmbeddingModel
from app.vector_store.base import BaseVectorStore
from app.vision.base import BaseVisionProcessor, MockVisionProcessor

from .base import BaseExtractor, DocumentIngestionResult
from .chunker import BaseChunker, RecursiveCharacterChunker
from .docx import DOCXExtractor
from .image import ImageExtractor
from .pdf import PDFExtractor
from .pptx import PPTXExtractor

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Multimodal Knowledge Ingestion Pipeline for SOAR.
    Coordinates file-type extraction, scanned-document detection, chunking,
    embedding generation, Chroma vector store persistence, and SQLite metadata indexing.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        vector_store: BaseVectorStore,
        embedding_model: BaseEmbeddingModel,
        chunker: Optional[BaseChunker] = None,
        vision_processor: Optional[BaseVisionProcessor] = None,
        extractors: Optional[List[BaseExtractor]] = None,
    ):
        self.db_manager = db_manager
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.chunker = chunker or RecursiveCharacterChunker(chunk_size=500, chunk_overlap=50)
        self.vision_processor = vision_processor or MockVisionProcessor()

        self._extractors: Dict[str, BaseExtractor] = {}

        if extractors:
            for ext in extractors:
                self.register_extractor(ext)
        else:
            # Default extractor registry
            self.register_extractor(PDFExtractor())
            self.register_extractor(DOCXExtractor())
            self.register_extractor(PPTXExtractor())
            self.register_extractor(ImageExtractor(vision_processor=self.vision_processor))

    def register_extractor(self, extractor: BaseExtractor) -> None:
        """Registers a file-type extractor for all its supported extensions."""
        for ext in extractor.supported_extensions:
            self._extractors[ext.lower()] = extractor

    @property
    def supported_extensions(self) -> List[str]:
        """Returns sorted list of all supported file extensions."""
        return sorted(list(self._extractors.keys()))

    def ingest_file(
        self,
        file_path: str | Path,
        force_reingest: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingests a single document or image file into SOAR's local knowledge base.
        """
        path = Path(file_path).resolve()
        if not path.exists():
            return {
                "status": "error",
                "filename": path.name,
                "source_path": str(path),
                "error": f"File not found at '{file_path}'",
            }

        if path.is_dir():
            return {
                "status": "error",
                "filename": path.name,
                "source_path": str(path),
                "error": f"Path '{file_path}' is a directory, not a file",
            }

        file_bytes = path.read_bytes()
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        filename = path.name
        ext = path.suffix.lower()

        # 1. Duplicate detection
        existing_doc = self.db_manager.get_document_by_hash(content_hash)
        if existing_doc and not force_reingest:
            logger.info(f"Duplicate document detected for '{filename}' (ID: {existing_doc['id']}). Skipping re-indexing.")
            return {
                "status": "duplicate",
                "document_id": existing_doc["id"],
                "filename": filename,
                "source_path": str(path),
                "file_type": existing_doc["file_type"],
                "file_size": existing_doc["file_size"],
                "content_hash": content_hash,
                "chunks_indexed": 0,
                "message": f"Document '{filename}' with matching hash already ingested. Skipping re-indexing.",
            }

        # 2. Select matching extractor
        extractor = self._extractors.get(ext)
        if not extractor:
            return {
                "status": "error",
                "filename": filename,
                "source_path": str(path),
                "error": f"Unsupported file type '{ext}'. Supported formats: {self.supported_extensions}",
            }

        # 3. Extract content and metadata
        extraction_result: DocumentIngestionResult = extractor.extract(path)
        if extraction_result.status == "error":
            return {
                "status": "error",
                "document_id": extraction_result.document_id,
                "filename": filename,
                "source_path": str(path),
                "error": extraction_result.error,
            }

        # 4. Register in SQLite metadata database
        # If force_reingest on an existing doc, reuse existing ID or delete old record
        doc_id = existing_doc["id"] if (existing_doc and force_reingest) else extraction_result.document_id
        if existing_doc and force_reingest:
            self.db_manager.delete_document(existing_doc["id"])

        self.db_manager.insert_document(
            doc_id=doc_id,
            filename=filename,
            source_path=str(path),
            file_type=extraction_result.file_type,
            file_size=extraction_result.file_size,
            content_hash=content_hash,
        )

        # 5. Chunk extracted elements
        chunks = self.chunker.chunk(extraction_result.elements, document_id=doc_id)

        # 6. Index into Chroma Vector Store
        chunks_indexed = 0
        if chunks:
            chunk_texts = [c.text for c in chunks]
            chunk_metas = [c.metadata for c in chunks]
            chunk_ids = [c.chunk_id for c in chunks]

            self.vector_store.add_documents(
                documents=chunk_texts,
                metadatas=chunk_metas,
                ids=chunk_ids,
            )
            chunks_indexed = len(chunks)

        # 7. Audit log event
        event_name = "SCANNED_DOCUMENT_FLAGGED" if extraction_result.is_scanned else "DOCUMENT_INGESTED"
        self.db_manager.log_audit_event(
            event=event_name,
            component="IngestionPipeline",
            details={
                "document_id": doc_id,
                "filename": filename,
                "file_type": extraction_result.file_type,
                "file_size": extraction_result.file_size,
                "content_hash": content_hash,
                "chunks_indexed": chunks_indexed,
                "is_scanned": extraction_result.is_scanned,
                "needs_ocr": extraction_result.needs_ocr,
            },
        )

        return {
            "status": extraction_result.status,
            "document_id": doc_id,
            "filename": filename,
            "source_path": str(path),
            "file_type": extraction_result.file_type,
            "file_size": extraction_result.file_size,
            "content_hash": content_hash,
            "chunks_indexed": chunks_indexed,
            "is_scanned": extraction_result.is_scanned,
            "needs_ocr": extraction_result.needs_ocr,
        }

    def ingest_directory(
        self,
        directory_path: str | Path,
        recursive: bool = True,
        force_reingest: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Ingests all supported document and image files from a directory.
        """
        dir_path = Path(directory_path).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {directory_path}")

        pattern = "**/*" if recursive else "*"
        results: List[Dict[str, Any]] = []

        for item in sorted(dir_path.glob(pattern)):
            if item.is_file() and item.suffix.lower() in self._extractors:
                res = self.ingest_file(item, force_reingest=force_reingest)
                results.append(res)

        return results
