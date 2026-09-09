import unittest

from app.orchestrator.routing import TaskClassifier, TaskProfile


class TestTaskClassifier(unittest.TestCase):
    """
    Comprehensive test suite for SOAR Task Classifier.
    Ensures deterministic, fast classification of user requests into TaskProfiles.
    """

    def setUp(self):
        self.classifier = TaskClassifier()

    def test_simple_general_question(self):
        profile = self.classifier.classify("What is the capital of France?")
        self.assertEqual(profile.task_type, "general")
        self.assertEqual(profile.complexity, "simple")
        self.assertFalse(profile.requires_rag)
        self.assertFalse(profile.requires_vision)
        self.assertFalse(profile.requires_coding)
        self.assertFalse(profile.requires_tools)
        self.assertEqual(profile.execution_mode, "direct_answer")

    def test_rag_knowledge_question(self):
        profile = self.classifier.classify("What is the pressure limit for Boiler B-4?")
        self.assertEqual(profile.task_type, "question_answering")
        self.assertEqual(profile.complexity, "simple")
        self.assertTrue(profile.requires_rag)
        self.assertFalse(profile.requires_vision)
        self.assertFalse(profile.requires_coding)
        self.assertEqual(profile.execution_mode, "direct_answer")

    def test_rag_sop_question(self):
        profile = self.classifier.classify("What are the safety requirements outlined in our safety manual?")
        self.assertEqual(profile.task_type, "question_answering")
        self.assertTrue(profile.requires_rag)
        self.assertEqual(profile.execution_mode, "direct_answer")

    def test_python_coding_generation(self):
        profile = self.classifier.classify("Write a Python function to add three numbers.")
        self.assertEqual(profile.task_type, "coding")
        self.assertTrue(profile.requires_coding)
        self.assertFalse(profile.requires_tools)
        self.assertEqual(profile.execution_mode, "code")
        self.assertFalse(profile.metadata.get("run_sandbox", False))

    def test_python_coding_with_sandbox_verification(self):
        profile = self.classifier.classify("Write and test a Python function that adds three numbers.")
        self.assertEqual(profile.task_type, "coding")
        self.assertTrue(profile.requires_coding)
        self.assertTrue(profile.requires_tools)
        self.assertEqual(profile.execution_mode, "code")
        self.assertTrue(profile.metadata.get("run_sandbox", False))

    def test_python_bug_fixing(self):
        profile = self.classifier.classify("Fix the bug in this Python script that causes an index error.")
        self.assertEqual(profile.task_type, "coding")
        self.assertTrue(profile.requires_coding)
        self.assertEqual(profile.execution_mode, "code")

    def test_vision_multimodal_request(self):
        profile = self.classifier.classify("What does this image show?")
        self.assertEqual(profile.task_type, "multimodal")
        self.assertTrue(profile.requires_vision)
        self.assertFalse(profile.requires_coding)
        self.assertEqual(profile.execution_mode, "direct_answer")

    def test_vision_image_path_detection(self):
        profile = self.classifier.classify("Analyze the telemetry diagram at inputs/sensor_reading.png")
        self.assertEqual(profile.task_type, "multimodal")
        self.assertTrue(profile.requires_vision)
        self.assertIn("inputs/sensor_reading.png", profile.metadata["file_paths"])

    def test_document_summary_agent_task(self):
        profile = self.classifier.classify("Summarize this inspection report.")
        self.assertEqual(profile.task_type, "document")
        self.assertTrue(profile.requires_tools)
        self.assertEqual(profile.execution_mode, "agent")

    def test_multi_step_document_creation_agent_task(self):
        profile = self.classifier.classify("Read inputs/inspection_report.pdf and create outputs/approval_note.docx")
        self.assertEqual(profile.task_type, "document")
        self.assertTrue(profile.requires_tools)
        self.assertEqual(profile.execution_mode, "agent")
        self.assertIn("inputs/inspection_report.pdf", profile.metadata["file_paths"])
        self.assertIn("outputs/approval_note.docx", profile.metadata["file_paths"])

    def test_complex_rag_and_document_agent_task(self):
        profile = self.classifier.classify(
            "Analyze this inspection report against our safety manual and create an approval note."
        )
        self.assertEqual(profile.task_type, "document")
        self.assertEqual(profile.complexity, "hard")
        self.assertTrue(profile.requires_rag)
        self.assertTrue(profile.requires_tools)
        self.assertEqual(profile.execution_mode, "agent")

    def test_make_docx_creation_agent_task(self):
        profile = self.classifier.classify("make docx of first 20 periodic table element ")
        self.assertEqual(profile.task_type, "document")
        self.assertTrue(profile.requires_tools)
        self.assertEqual(profile.execution_mode, "agent")

    def test_make_pdf_creation_agent_task(self):
        profile = self.classifier.classify("make a pdf with executive summary")
        self.assertEqual(profile.task_type, "document")
        self.assertTrue(profile.requires_tools)
        self.assertEqual(profile.execution_mode, "agent")

    def test_math_calculation(self):
        profile = self.classifier.classify("What is 2 + 2?")
        self.assertEqual(profile.task_type, "calculation")
        self.assertEqual(profile.complexity, "simple")
        self.assertEqual(profile.execution_mode, "direct_answer")

    def test_hard_reasoning(self):
        profile = self.classifier.classify("Explain why a pressure vessel might experience abnormal pressure.")
        self.assertEqual(profile.task_type, "reasoning")
        self.assertEqual(profile.complexity, "hard")
        self.assertEqual(profile.execution_mode, "direct_answer")

    def test_medium_reasoning(self):
        profile = self.classifier.classify("Explain how a counterflow heat exchanger works.")
        self.assertEqual(profile.task_type, "reasoning")
        self.assertEqual(profile.complexity, "medium")
        self.assertEqual(profile.execution_mode, "direct_answer")


if __name__ == "__main__":
    unittest.main()
