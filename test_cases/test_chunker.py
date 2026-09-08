import unittest

from app.ingestion.base import ExtractedElement
from app.ingestion.chunker import RecursiveCharacterChunker


class TestChunker(unittest.TestCase):
    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            RecursiveCharacterChunker(chunk_size=0)
        with self.assertRaises(ValueError):
            RecursiveCharacterChunker(chunk_size=100, chunk_overlap=100)
        with self.assertRaises(ValueError):
            RecursiveCharacterChunker(chunk_size=100, chunk_overlap=150)
        with self.assertRaises(ValueError):
            RecursiveCharacterChunker(chunk_size=100, chunk_overlap=-1)

    def test_single_element_below_chunk_size(self):
        chunker = RecursiveCharacterChunker(chunk_size=200, chunk_overlap=20)
        elements = [
            ExtractedElement(
                text="This is a short document text well within the limit.",
                metadata={"page_number": 1, "filename": "doc.pdf"},
            )
        ]

        chunks = chunker.chunk(elements, document_id="doc-123")
        self.assertEqual(len(chunks), 1)
        chunk = chunks[0]
        self.assertEqual(chunk.chunk_id, "doc-123_c0")
        self.assertEqual(chunk.text, "This is a short document text well within the limit.")
        self.assertEqual(chunk.metadata["page_number"], 1)
        self.assertEqual(chunk.metadata["filename"], "doc.pdf")
        self.assertEqual(chunk.metadata["document_id"], "doc-123")
        self.assertEqual(chunk.metadata["chunk_index"], 0)

    def test_paragraph_and_sentence_splitting(self):
        chunker = RecursiveCharacterChunker(chunk_size=60, chunk_overlap=10)
        para1 = "Paragraph one with some introductory text for section A."
        para2 = "Paragraph two contains the detailed findings and conclusions."
        elements = [
            ExtractedElement(text=f"{para1}\n\n{para2}", metadata={"source": "report.docx"})
        ]

        chunks = chunker.chunk(elements, document_id="doc-docx")
        self.assertTrue(len(chunks) >= 2)
        for chunk in chunks:
            self.assertTrue(len(chunk.text) <= 65)  # slight tolerance for word bounds
            self.assertEqual(chunk.metadata["document_id"], "doc-docx")
            self.assertEqual(chunk.metadata["source"], "report.docx")

    def test_multiple_elements_metadata_isolation(self):
        chunker = RecursiveCharacterChunker(chunk_size=100, chunk_overlap=10)
        elements = [
            ExtractedElement(text="Page one content text.", metadata={"page_number": 1}),
            ExtractedElement(text="Page two content text.", metadata={"page_number": 2}),
        ]

        chunks = chunker.chunk(elements, document_id="doc-multi")
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].metadata["page_number"], 1)
        self.assertEqual(chunks[0].metadata["chunk_index"], 0)
        self.assertEqual(chunks[1].metadata["page_number"], 2)
        self.assertEqual(chunks[1].metadata["chunk_index"], 1)

    def test_empty_and_whitespace_elements(self):
        chunker = RecursiveCharacterChunker(chunk_size=100, chunk_overlap=10)
        elements = [
            ExtractedElement(text="", metadata={"page": 1}),
            ExtractedElement(text="   \n\n   ", metadata={"page": 2}),
            ExtractedElement(text="Valid page three text.", metadata={"page": 3}),
        ]

        chunks = chunker.chunk(elements, document_id="doc-empty")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].text, "Valid page three text.")
        self.assertEqual(chunks[0].metadata["page"], 3)


if __name__ == "__main__":
    unittest.main()
