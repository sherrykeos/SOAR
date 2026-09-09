import hashlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from app.database.repository import DatabaseManager
from app.storage import (
    BaseFileStorage,
    FileNotFoundStorageError,
    FileTooLargeError,
    InvalidFileError,
    InvalidFilenameError,
    LocalFileStorage,
    PathTraversalError,
    StorageError,
    StoredFileMetadata,
)


class TestLocalStorage(unittest.TestCase):
    """
    Test suite for SOAR LocalFileStorage subsystem.
    Validates storage, retrieval, deletion, security containment, and DB integration.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_dir = Path(self.test_dir) / "managed_files"
        self.db_path = Path(self.test_dir) / "test_soar.db"
        self.db_manager = DatabaseManager(db_path=self.db_path)
        self.storage = LocalFileStorage(
            storage_dir=self.storage_dir,
            max_file_size_bytes=1024 * 1024,  # 1 MB limit for test
            allow_empty=True,
            db_manager=self.db_manager,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # 1. Upload & Storage Tests
    # -------------------------------------------------------------
    def test_save_from_path(self):
        # Create a sample source file
        src = Path(self.test_dir) / "source_doc.txt"
        src.write_text("Hello SOAR local storage!", encoding="utf-8")

        meta = self.storage.save(src)
        self.assertIsInstance(meta, StoredFileMetadata)
        self.assertEqual(meta.original_filename, "source_doc.txt")
        self.assertEqual(meta.extension, ".txt")
        self.assertEqual(meta.size_bytes, len(b"Hello SOAR local storage!"))
        self.assertEqual(
            meta.sha256,
            hashlib.sha256(b"Hello SOAR local storage!").hexdigest(),
        )
        self.assertTrue(Path(meta.storage_path).exists())
        self.assertTrue(self.storage.exists(meta.file_id))

    def test_save_from_bytes(self):
        binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00"
        meta = self.storage.save(binary_data, filename="sample_image.png")
        self.assertEqual(meta.original_filename, "sample_image.png")
        self.assertEqual(meta.extension, ".png")
        self.assertEqual(meta.size_bytes, len(binary_data))
        self.assertEqual(meta.mime_type, "image/png")
        self.assertEqual(self.storage.get_bytes(meta.file_id), binary_data)

    def test_save_from_stream(self):
        stream_data = b"Stream payload contents"
        stream = io.BytesIO(stream_data)
        meta = self.storage.save(stream, filename="report.pdf", content_type="application/pdf")
        self.assertEqual(meta.original_filename, "report.pdf")
        self.assertEqual(meta.extension, ".pdf")
        self.assertEqual(meta.mime_type, "application/pdf")
        self.assertEqual(self.storage.get_bytes(meta.file_id), stream_data)

    def test_save_unicode_filename(self):
        unicode_name = "报告_2026_résumé_спецификация.pdf"
        content = b"%PDF-1.4 unicode test"
        meta = self.storage.save(content, filename=unicode_name)
        self.assertEqual(meta.original_filename, unicode_name)
        self.assertEqual(meta.extension, ".pdf")
        self.assertTrue(self.storage.exists(meta.file_id))

    def test_save_duplicate_content(self):
        content = b"Exact same content"
        meta1 = self.storage.save(content, filename="file1.txt")
        meta2 = self.storage.save(content, filename="file2.txt")

        # Must have distinct file_ids and stored paths, but same sha256
        self.assertNotEqual(meta1.file_id, meta2.file_id)
        self.assertNotEqual(meta1.storage_path, meta2.storage_path)
        self.assertEqual(meta1.sha256, meta2.sha256)
        self.assertTrue(self.storage.exists(meta1.file_id))
        self.assertTrue(self.storage.exists(meta2.file_id))

    def test_empty_file_handling(self):
        # By default allow_empty=True
        empty_meta = self.storage.save(b"", filename="empty.txt")
        self.assertEqual(empty_meta.size_bytes, 0)
        self.assertEqual(self.storage.get_bytes(empty_meta.file_id), b"")

        # Disallow empty files
        strict_storage = LocalFileStorage(
            storage_dir=self.storage_dir,
            allow_empty=False,
        )
        with self.assertRaises(InvalidFileError):
            strict_storage.save(b"", filename="strict_empty.txt")

    def test_missing_source_path(self):
        non_existent = Path(self.test_dir) / "does_not_exist.txt"
        with self.assertRaises(FileNotFoundStorageError):
            self.storage.save(non_existent)

    def test_directory_passed_as_file(self):
        sub_dir = Path(self.test_dir) / "some_dir"
        sub_dir.mkdir()
        with self.assertRaises(InvalidFileError):
            self.storage.save(sub_dir)

    def test_max_file_size_exceeded_bytes(self):
        # Configured limit in setUp is 1 MB
        oversized_data = b"X" * (1024 * 1024 + 10)
        with self.assertRaises(FileTooLargeError):
            self.storage.save(oversized_data, filename="too_big.bin")

    def test_max_file_size_exceeded_stream(self):
        oversized_stream = io.BytesIO(b"Y" * (1024 * 1024 + 50))
        with self.assertRaises(FileTooLargeError):
            self.storage.save(oversized_stream, filename="too_big_stream.bin")

    # -------------------------------------------------------------
    # 2. Security & Path Traversal Tests
    # -------------------------------------------------------------
    def test_path_traversal_relative_forward_slash(self):
        # ../../secret.txt
        meta = self.storage.save(b"Confidential", filename="../../secret.txt")
        # Sanitization should strip path traversal and safely store as 'secret.txt' inside storage_dir
        self.assertEqual(meta.original_filename, "secret.txt")
        self.assertFalse((self.storage_dir.parent / "secret.txt").exists())
        self.assertTrue(Path(meta.storage_path).parent.resolve() == self.storage_dir.resolve())

    def test_path_traversal_relative_backslash(self):
        # ..\..\secret_windows.txt
        meta = self.storage.save(b"Confidential", filename="..\\..\\secret_windows.txt")
        self.assertEqual(meta.original_filename, "secret_windows.txt")
        self.assertTrue(Path(meta.storage_path).parent.resolve() == self.storage_dir.resolve())

    def test_path_traversal_absolute_unix_path(self):
        meta = self.storage.save(b"Passwd fake content", filename="/etc/passwd")
        self.assertEqual(meta.original_filename, "passwd")
        self.assertTrue(Path(meta.storage_path).parent.resolve() == self.storage_dir.resolve())

    def test_path_traversal_absolute_windows_path(self):
        meta = self.storage.save(b"cmd fake", filename=r"C:\Windows\System32\cmd.exe")
        self.assertEqual(meta.original_filename, "cmd.exe")
        self.assertTrue(Path(meta.storage_path).parent.resolve() == self.storage_dir.resolve())

    def test_null_byte_in_filename_rejected(self):
        with self.assertRaises(InvalidFilenameError):
            self.storage.save(b"null test", filename="exploit.txt\0.pdf")

    def test_windows_reserved_device_names(self):
        for reserved in ["CON.txt", "prn.docx", "AUX.pdf", "NUL", "COM1.txt", "lpt9.dat"]:
            meta = self.storage.save(b"reserved test", filename=reserved)
            # Must be prefixed or sanitized safely
            self.assertTrue(meta.original_filename.startswith("safe_"))
            self.assertTrue(Path(meta.storage_path).exists())

    def test_arbitrary_path_access_via_file_id(self):
        # Attempt to access outside files using traversal file_id
        with self.assertRaises((PathTraversalError, FileNotFoundStorageError)):
            self.storage.get_path("../../etc/passwd")

        with self.assertRaises((PathTraversalError, FileNotFoundStorageError)):
            self.storage.get_path("..\\..\\Windows\\System32\\calc.exe")

        with self.assertRaises((PathTraversalError, FileNotFoundStorageError)):
            self.storage.get_bytes("../test_soar.db")

        # exists should return False without raising unhandled exception
        self.assertFalse(self.storage.exists("../../outside_file"))

    # -------------------------------------------------------------
    # 3. Download & Retrieval Tests
    # -------------------------------------------------------------
    def test_get_path_valid(self):
        meta = self.storage.save(b"Valid download", filename="valid.txt")
        path = self.storage.get_path(meta.file_id)
        self.assertEqual(path.resolve(), Path(meta.storage_path).resolve())
        self.assertEqual(path.read_text(encoding="utf-8"), "Valid download")

    def test_get_path_nonexistent_id(self):
        with self.assertRaises(FileNotFoundStorageError):
            self.storage.get_path("non_existent_uuid_12345")

    def test_get_bytes_and_stream(self):
        content = b"Binary stream verification \x01\x02\x03\x04"
        meta = self.storage.save(content, filename="stream_test.bin")

        retrieved_bytes = self.storage.get_bytes(meta.file_id)
        self.assertEqual(retrieved_bytes, content)

        with self.storage.get_stream(meta.file_id) as f:
            streamed_content = f.read()
            self.assertEqual(streamed_content, content)

    def test_get_metadata(self):
        meta = self.storage.save(b"Meta check", filename="check.txt")
        fetched = self.storage.get_metadata(meta.file_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.file_id, meta.file_id)
        self.assertEqual(fetched.original_filename, "check.txt")
        self.assertEqual(fetched.size_bytes, len(b"Meta check"))

        none_meta = self.storage.get_metadata("unknown_id")
        self.assertIsNone(none_meta)

    def test_list_files(self):
        self.assertEqual(len(self.storage.list_files()), 0)
        m1 = self.storage.save(b"File 1", filename="f1.txt")
        m2 = self.storage.save(b"File 2", filename="f2.txt")
        m3 = self.storage.save(b"File 3", filename="f3.txt")

        files = self.storage.list_files()
        self.assertEqual(len(files), 3)
        file_ids = {f.file_id for f in files}
        self.assertEqual(file_ids, {m1.file_id, m2.file_id, m3.file_id})

    # -------------------------------------------------------------
    # 4. Deletion Tests
    # -------------------------------------------------------------
    def test_delete_existing_file(self):
        meta = self.storage.save(b"Delete me", filename="to_delete.txt")
        file_path = Path(meta.storage_path)
        self.assertTrue(file_path.exists())
        self.assertTrue(self.storage.exists(meta.file_id))

        # Delete
        result = self.storage.delete(meta.file_id)
        self.assertTrue(result)
        self.assertFalse(file_path.exists())
        self.assertFalse(self.storage.exists(meta.file_id))
        self.assertIsNone(self.storage.get_metadata(meta.file_id))

    def test_delete_nonexistent_file(self):
        result = self.storage.delete("nonexistent_id_9999")
        self.assertFalse(result)

    # -------------------------------------------------------------
    # 5. Database Integration & Standalone Operation
    # -------------------------------------------------------------
    def test_sqlite_sync(self):
        content = b"Database synced file"
        meta = self.storage.save(content, filename="synced.txt")

        # Verify SQLite record directly
        db_row = self.db_manager.get_file(meta.file_id)
        self.assertIsNotNone(db_row)
        self.assertEqual(db_row["original_filename"], "synced.txt")
        self.assertEqual(db_row["content_hash"], meta.sha256)

        # Lookup by hash
        hash_row = self.db_manager.get_file_by_hash(meta.sha256)
        self.assertIsNotNone(hash_row)
        self.assertEqual(hash_row["id"], meta.file_id)

        # Delete through storage and verify removed from SQLite
        self.storage.delete(meta.file_id)
        self.assertIsNone(self.db_manager.get_file(meta.file_id))

    def test_standalone_storage_without_db(self):
        standalone = LocalFileStorage(
            storage_dir=Path(self.test_dir) / "standalone_files",
            db_manager=None,
        )
        meta = standalone.save(b"No DB required", filename="standalone.txt")
        self.assertTrue(standalone.exists(meta.file_id))
        self.assertEqual(standalone.get_bytes(meta.file_id), b"No DB required")
        self.assertEqual(len(standalone.list_files()), 1)
        self.assertTrue(standalone.delete(meta.file_id))
        self.assertFalse(standalone.exists(meta.file_id))


if __name__ == "__main__":
    unittest.main()
