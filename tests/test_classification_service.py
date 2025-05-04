# tests/test_classification_service.py  (or your preferred test directory structure)

import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Assuming your project structure allows this import path
# Adjust if necessary (e.g., if using src layout, you might need path adjustments or installation)
from openapi_server.implementation.classification_service import (
    ClassificationServiceImpl,
    MOCK_RESPONSES,
    DEFAULT_RESPONSE_DATA,
    EXPECTED_PDF_HEADER
)
from openapi_server.models.classification_result import ClassificationResult
from openapi_server.models.result_item import ResultItem
from openapi_server.models.qualified_value import QualifiedValue
from fastapi import HTTPException

# --- Test Constants ---
FIXED_UUID_FOR_CLASS_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
SAMPLE_PDF_BODY = EXPECTED_PDF_HEADER[:] + b"some pdf content"
INVALID_BODY_SHORT = b'%PDF'  # Shorter than header
INVALID_BODY_HEADER = b'IAMNOTAPDF'


class TestClassificationServiceImpl(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        self.service = ClassificationServiceImpl()

    def _generate_uuid_ending_with(self, ending: str) -> uuid.UUID:
        """Helper to create a UUID with a specific ending."""
        if not (isinstance(ending, str) and len(ending) == 2 and ending.isdigit()):
            raise ValueError("Ending must be a 2-digit string")
        # Create a base UUID and replace the last two hex digits
        base_uuid_str = "00000000-0000-0000-0000-0000000000"
        # Convert ending digits to hex representation if needed, or just use them if they fit
        # For simplicity, we'll just use the digits directly if they are 00-99
        test_uuid_str = base_uuid_str + ending
        return uuid.UUID(test_uuid_str)

    @patch('uuid.uuid4', return_value=FIXED_UUID_FOR_CLASS_ID)
    def test_classify_pdf_matching_uuid_10(self, mock_uuid4):
        """Test successful classification with UUID ending in '10'."""
        test_uuid = self._generate_uuid_ending_with("10")
        expected_data = MOCK_RESPONSES["10"]

        result = self.service.classify_pdf(uuid_param_str=str(test_uuid), body=SAMPLE_PDF_BODY)

        # --- Assertions ---
        self.assertIsInstance(result, ClassificationResult)
        self.assertEqual(result.custom_id, str(test_uuid))
        self.assertEqual(result.class_id, str(FIXED_UUID_FOR_CLASS_ID))  # Check mocked value

        # Assert ResultItem
        self.assertIsInstance(result.result, ResultItem)
        res_item = result.result
        self.assertEqual(res_item.kind, expected_data["kind"])

        # Assert QualifiedValues
        self.assertIsInstance(res_item.doc_id, QualifiedValue)
        self.assertEqual(res_item.doc_id.value, expected_data["doc_id_val"])
        self.assertEqual(res_item.doc_id.score, expected_data["doc_id_score"])

        self.assertIsInstance(res_item.doc_date_sic, QualifiedValue)
        self.assertEqual(res_item.doc_date_sic.value, expected_data["doc_date_sic_val"])
        self.assertEqual(res_item.doc_date_sic.score, expected_data["doc_date_sic_score"])

        self.assertIsInstance(res_item.doc_subject, QualifiedValue)
        self.assertEqual(res_item.doc_subject.value, expected_data["doc_subject_val"])
        self.assertEqual(res_item.doc_subject.score, expected_data["doc_subject_score"])

        # Assert Parsed Date (check type and value)
        self.assertIsInstance(res_item.doc_date_parsed, datetime)
        # Compare parsed datetime object with expected value
        expected_dt = datetime.fromisoformat(expected_data["doc_date_parsed"])
        self.assertEqual(res_item.doc_date_parsed, expected_dt)
        # Explicitly check timezone if important (fromisoformat handles 'Z')
        self.assertEqual(res_item.doc_date_parsed.tzinfo, timezone.utc)

        mock_uuid4.assert_called_once()  # Ensure uuid.uuid4 was called

    @patch('uuid.uuid4', return_value=FIXED_UUID_FOR_CLASS_ID)
    def test_classify_pdf_matching_uuid_20(self, mock_uuid4):
        """Test successful classification with UUID ending in '20'."""
        test_uuid = self._generate_uuid_ending_with("20")
        expected_data = MOCK_RESPONSES["20"]

        result = self.service.classify_pdf(uuid_param_str=str(test_uuid), body=SAMPLE_PDF_BODY)

        self.assertIsInstance(result, ClassificationResult)
        self.assertEqual(result.custom_id, str(test_uuid))
        self.assertEqual(result.class_id, str(FIXED_UUID_FOR_CLASS_ID))
        self.assertEqual(result.result.kind, expected_data["kind"])
        self.assertEqual(result.result.doc_id.value, expected_data["doc_id_val"])
        # ... add more assertions for other fields if needed ...
        expected_dt = datetime.fromisoformat(expected_data["doc_date_parsed"])
        self.assertEqual(result.result.doc_date_parsed, expected_dt)

    @patch('uuid.uuid4', return_value=FIXED_UUID_FOR_CLASS_ID)
    def test_classify_pdf_non_matching_uuid_99(self, mock_uuid4):
        """Test classification uses default data for non-matching UUID ending '99'."""
        test_uuid = self._generate_uuid_ending_with("99")  # Assuming '99' is not in MOCK_RESPONSES
        expected_data = DEFAULT_RESPONSE_DATA

        result = self.service.classify_pdf(uuid_param_str=str(test_uuid), body=SAMPLE_PDF_BODY)

        self.assertIsInstance(result, ClassificationResult)
        self.assertEqual(result.custom_id, str(test_uuid))
        self.assertEqual(result.class_id, str(FIXED_UUID_FOR_CLASS_ID))
        self.assertEqual(result.result.kind, expected_data["kind"])
        self.assertEqual(result.result.doc_id.value, expected_data["doc_id_val"])
        self.assertEqual(result.result.doc_id.score, expected_data["doc_id_score"])
        # ... assert other default fields ...
        expected_dt = datetime.fromisoformat(expected_data["doc_date_parsed"])
        self.assertEqual(result.result.doc_date_parsed, expected_dt)

    def test_classify_pdf_body_none(self):
        """Test HTTPException 400 when body is None."""
        test_uuid = self._generate_uuid_ending_with("10")
        with self.assertRaises(HTTPException) as cm:
            self.service.classify_pdf(uuid_param_str=str(test_uuid), body=None)
        self.assertEqual(cm.exception.status_code, 400)
        self.assertEqual(cm.exception.detail, "PDF body must be present")

    def test_classify_pdf_body_empty(self):
        """Test HTTPException 400 when body is empty."""
        test_uuid = self._generate_uuid_ending_with("10")
        with self.assertRaises(HTTPException) as cm:
            self.service.classify_pdf(uuid_param_str=str(test_uuid), body=b'')
        self.assertEqual(cm.exception.status_code, 400)
        # Check against the *actual* first error raised, which is now length check
        self.assertEqual(cm.exception.detail, "PDF body must be present")

    def test_classify_pdf_body_too_short(self):
        """Test HTTPException 400 when body is shorter than header."""
        test_uuid = self._generate_uuid_ending_with("10")
        with self.assertRaises(HTTPException) as cm:
            self.service.classify_pdf(uuid_param_str=str(test_uuid), body=INVALID_BODY_SHORT)
        self.assertEqual(cm.exception.status_code, 400)
        self.assertEqual(cm.exception.detail, "PDF body too short")

    def test_classify_pdf_body_invalid_header(self):
        """Test HTTPException 400 when body doesn't start with PDF header."""
        test_uuid = self._generate_uuid_ending_with("10")
        with self.assertRaises(HTTPException) as cm:
            self.service.classify_pdf(uuid_param_str=str(test_uuid), body=INVALID_BODY_HEADER)
        self.assertEqual(cm.exception.status_code, 400)
        self.assertEqual(cm.exception.detail, "Invalid file format: Does not appear to be a PDF.")

    @patch('datetime.datetime', wraps=datetime)  # Use wraps to keep original datetime behavior unless mocked
    @patch('uuid.uuid4', return_value=FIXED_UUID_FOR_CLASS_ID)
    def test_classify_pdf_internal_error_parsing_date(self, mock_uuid4, mock_datetime_cls):
        """Test HTTPException 500 if date parsing fails internally."""
        test_uuid = self._generate_uuid_ending_with("10")
        error_message = "Mocked ISO format error"

        # Mock the fromisoformat method specifically to raise an error
        mock_datetime_cls.fromisoformat.side_effect = ValueError(error_message)

        with self.assertRaises(HTTPException) as cm:
            self.service.classify_pdf(uuid_param_str=str(test_uuid), body=SAMPLE_PDF_BODY)

        self.assertEqual(cm.exception.status_code, 500)
        self.assertIn("Internal server error during classification", cm.exception.detail)
        self.assertIn(error_message, cm.exception.detail)  # Check if original error is included

        mock_datetime_cls.fromisoformat.assert_called_once()  # Ensure our mock was hit

# --- To Run the Tests ---
# 1. Make sure 'unittest' and 'mock' (if Python < 3.3) are available.
# 2. Save this code as e.g., `tests/test_classification_service.py`.
# 3. Navigate to the directory *above* `tests` and `openapi_server` in your terminal.
# 4. Run: python -m unittest tests.test_classification_service.py
#    Or use a test runner like pytest: pip install pytest; pytest
