# openapi_server/implementation/classification_service.py
import datetime
import random
import string
import uuid

from fastapi import HTTPException

# Assuming your models are correctly defined and imported
from openapi_server.apis.classification_api_base import BaseClassificationApi
from openapi_server.models.classification_result import ClassificationResult
from openapi_server.models.result_item import ResultItem
from openapi_server.models.qualified_value import QualifiedValue

EXPECTED_PDF_HEADER = b'%PDF-'  # Note the b prefix for bytes

# --- Data for Mock Responses ---
# Map UUID endings (last 2 digits as string) to response data dictionaries
MOCK_RESPONSES = {
    "10": {
        "kind": "INVOICE",
        "doc_id_val": "DOC123", "doc_id_score": 0.99,
        "doc_date_sic_val": "2024-01-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2024-01-01T10:00:00Z",
        "doc_subject_val": "KFZ Reparatur", "doc_subject_score": 0.8
    },
    "11": {
        "kind": "INVOICE",
        "doc_id_val": "DOC124", "doc_id_score": 0.89,
        "doc_date_sic_val": "2025-03-12", "doc_date_sic_score": 0.7,
        "doc_date_parsed": "2025-03-12T00:00:00Z",  # Corrected 'ß'
        "doc_subject_val": "Ihr Einkauf vielen Dank", "doc_subject_score": 0.8
    },
    "12": {
        "kind": "INVOICE",
        "doc_id_val": "DOC125", "doc_id_score": 0.79,
        "doc_date_sic_val": "2025-03-13", "doc_date_sic_score": 0.6,
        "doc_date_parsed": "2025-03-13T00:00:00Z",  # Corrected 'ß'
        "doc_subject_val": "Ihr Einkauf vielen Dank", "doc_subject_score": 0.7
    },
    # Cases 13-19 are identical to 12
    "13": {"kind": "INVOICE",
           "doc_id_val": "DOC126", "doc_id_score": 0.69,
           "doc_date_sic_val": "2025-03-13", "doc_date_sic_score": 0.5,
           "doc_date_parsed": "2025-03-13T00:00:00Z",
           "doc_subject_val": "Ihr Einkauf vielen Dank", "doc_subject_score": 0.6},
    "14": {"kind": "INVOICE", "doc_id_val": "DOC127", "doc_id_score": 0.59, "doc_date_sic_val": "2025-02-12",
           "doc_date_sic_score": 0.5, "doc_date_parsed": "2025-02-12T00:00:00Z",
           "doc_subject_val": "Ihr Einkauf vielen Dank", "doc_subject_score": 0.5},
    "15": {"kind": "INVOICE", "doc_id_val": "DOC128", "doc_id_score": 0.49, "doc_date_sic_val": "2025-01-11",
           "doc_date_sic_score": 0.4, "doc_date_parsed": "2025-01-11T00:00:00Z",
           "doc_subject_val": "Ihr Einkauf vielen Dank", "doc_subject_score": 0.4},
    "17": {"kind": "INVOICE", "doc_id_val": "DOC129", "doc_id_score": 0.39, "doc_date_sic_val": "2024-12-10",
           "doc_date_sic_score": 0.3, "doc_date_parsed": "2024-12-10T00:00:00Z",
           "doc_subject_val": "Ihr Einkauf vielen Dank", "doc_subject_score": 0.3},
    "18": {"kind": "INVOICE", "doc_id_val": "DOC130", "doc_id_score": 0.29, "doc_date_sic_val": "2024-11-11",
           "doc_date_sic_score": 0.2, "doc_date_parsed": "2024-11-11T00:00:00Z",
           "doc_subject_val": "Ihr Einkauf vielen Dank", "doc_subject_score": 0.2},
    "19": {"kind": "INVOICE", "doc_id_val": "DOC131", "doc_id_score": 0.19, "doc_date_sic_val": "2024-10-09",
           "doc_date_sic_score": 0.1, "doc_date_parsed": "2024-10-09T00:00:00Z",
           "doc_subject_val": "Ihr Einkauf vielen Dank", "doc_subject_score": 0.1},
    "20": {
        "kind": "STATEMENT",
        "doc_id_val": "DE92 1234 5678 9123 87", "doc_id_score": 0.99,
        "doc_date_sic_val": "2025-04-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2025-04-01T00:00:00Z",  # Corrected 'ß'
        "doc_subject_val": "Kontoauszug 3-25", "doc_subject_score": 0.7
    },
    "21": {
        "kind": "STATEMENT",
        "doc_id_val": "DE92 1234 5678 9123 87", "doc_id_score": 0.89,
        "doc_date_sic_val": "2025-03-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2025-03-01T00:00:00Z",  # Corrected 'ß'
        "doc_subject_val": "Kontoauszug 2-25", "doc_subject_score": 0.7
    },
    "22": {
        "kind": "STATEMENT",
        "doc_id_val": "DE92 1234 5678 9123 87", "doc_id_score": 0.79,
        "doc_date_sic_val": "2025-02-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2025-02-01T00:00:00Z",  # Corrected 'ß'
        "doc_subject_val": "Kontoauszug 1-25", "doc_subject_score": 0.7
    },
    "23": {
        "kind": "STATEMENT",
        "doc_id_val": "DE92 1234 5678 9123 87", "doc_id_score": 0.69,
        "doc_date_sic_val": "2025-01-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2025-01-01T00:00:00Z",  # Corrected 'ß'
        "doc_subject_val": "Kontoauszug 12-24", "doc_subject_score": 0.7
    },
    "24": {
        "kind": "STATEMENT",
        "doc_id_val": "DE92 1234 5678 9123 87", "doc_id_score": 0.59,
        "doc_date_sic_val": "2024-12-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2024-12-01T00:00:00Z",
        "doc_subject_val": "Kontoauszug 11-24", "doc_subject_score": 0.7
    },
    "25": {
        "kind": "STATEMENT",
        "doc_id_val": "DE92 1234 5678 9123 87", "doc_id_score": 0.49,
        "doc_date_sic_val": "2024-11-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2024-11-01T00:00:00Z",  # Corrected year from 2025
        "doc_subject_val": "Kontoauszug 10-24", "doc_subject_score": 0.7
    },
    "26": {
        "kind": "STATEMENT",
        "doc_id_val": "DE92 1234 5678 9123 87", "doc_id_score": 0.39,
        "doc_date_sic_val": "2024-10-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2024-10-01T00:00:00Z",  # Corrected year from 2025
        "doc_subject_val": "Kontoauszug 09-24", "doc_subject_score": 0.7
    },
    "27": {
        "kind": "STATEMENT",
        "doc_id_val": "DE92 1234 5678 9123 87", "doc_id_score": 0.29,
        "doc_date_sic_val": "2024-09-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2024-09-01T00:00:00Z",  # Corrected year from 2025
        "doc_subject_val": "Kontoauszug 08-24", "doc_subject_score": 0.7
    },
    "28": {
        "kind": "STATEMENT",
        "doc_id_val": "DE92 1234 5678 9123 87", "doc_id_score": 0.19,
        "doc_date_sic_val": "2024-08-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2024-08-01T00:00:00Z",  # Corrected year from 2025
        "doc_subject_val": "Kontoauszug 07-24", "doc_subject_score": 0.7
    },
    "29": {
        "kind": "STATEMENT",
        "doc_id_val": "DE92 1234 5678 9123 87", "doc_id_score": 0.09,
        "doc_date_sic_val": "2024-07-01", "doc_date_sic_score": 0.9,
        "doc_date_parsed": "2024-07-01T00:00:00Z",  # Corrected year from 2025
        "doc_subject_val": "Kontoauszug 06-24", "doc_subject_score": 0.7
    },
    "30": {
        "kind": "LETTER",
        "doc_id_val": "K7-22389", "doc_id_score": 0.99,
        "doc_date_sic_val": "2025-04-21", "doc_date_sic_score": 0.99,
        "doc_date_parsed": "2025-04-21T00:00:00Z",
        "doc_subject_val": "Versicherungsfall 4711", "doc_subject_score": 0.7
    },
    "31": {
        "kind": "LETTER",
        "doc_id_val": "K7-22389", "doc_id_score": 0.89,
        "doc_date_sic_val": "2025-04-01", "doc_date_sic_score": 0.89,
        "doc_date_parsed": "2025-04-01T00:00:00Z",
        "doc_subject_val": "Versicherungsfall 4711", "doc_subject_score": 0.7
    },
    "32": {
        "kind": "LETTER",
        "doc_id_val": "K7-22389", "doc_id_score": 0.79,
        "doc_date_sic_val": "2025-03-11", "doc_date_sic_score": 0.79,
        "doc_date_parsed": "2025-03-11T00:00:00Z",
        "doc_subject_val": "Beitragsanpassung", "doc_subject_score": 0.7
    },
    "33": {
        "kind": "LETTER",
        "doc_id_val": "B-2025-SSA-KGA", "doc_id_score": 0.69,
        "doc_date_sic_val": "2025-01-12", "doc_date_sic_score": 0.69,
        "doc_date_parsed": "2025-01-12T00:00:00Z",
        "doc_subject_val": "Kindergeld Bertram", "doc_subject_score": 0.7
    },
    "34": {
        "kind": "LETTER",
        "doc_id_val": "Klasse 7b", "doc_id_score": 0.59,
        "doc_date_sic_val": "2024-12-22", "doc_date_sic_score": 0.59,
        "doc_date_parsed": "2024-12-22T00:00:00Z",
        "doc_subject_val": "Einladung zum Elternabend", "doc_subject_score": 0.7
    },
    "35": {
        "kind": "LETTER",
        "doc_id_val": "Wandern", "doc_id_score": 0.49,
        "doc_date_sic_val": "2024-11-10", "doc_date_sic_score": 0.49,
        "doc_date_parsed": "2024-11-10T00:00:00Z",
        "doc_subject_val": "Wanderfreunde Bergisch-Gladbach", "doc_subject_score": 0.7
    },
    "36": {
        "kind": "LETTER",
        "doc_id_val": "Lotto-DE", "doc_id_score": 0.39,
        "doc_date_sic_val": "2024-10-01", "doc_date_sic_score": 0.39,
        "doc_date_parsed": "2024-10-01T00:00:00Z",
        "doc_subject_val": "Hxx-123-so-aaaayxy", "doc_subject_score": 0.2
    },
    "37": {
        "kind": "LETTER",
        "doc_id_val": "", "doc_id_score": 0.29,
        "doc_date_sic_val": "2024-09-01", "doc_date_sic_score": 0.29,
        "doc_date_parsed": "2024-09-01T00:00:00Z",
        "doc_subject_val": "", "doc_subject_score": 0.0
    },
    "38": {  # Note: Table had 39 then 38, assuming 38 comes before 39
        "kind": "LETTER",
        "doc_id_val": "", "doc_id_score": 0.19,
        "doc_date_sic_val": "2024-08-01", "doc_date_sic_score": 0.19,
        "doc_date_parsed": "2024-08-01T00:00:00Z",
        "doc_subject_val": "", "doc_subject_score": 0.0
    },
    "39": {
        "kind": "LETTER",
        "doc_id_val": "", "doc_id_score": 0.09,
        "doc_date_sic_val": "2024-07-01", "doc_date_sic_score": 0.09,
        "doc_date_parsed": "2024-07-01T00:00:00Z",
        "doc_subject_val": "", "doc_subject_score": 0.0
    },
}

# --- Default response if UUID ending doesn't match ---
DEFAULT_RESPONSE_DATA = {
    "kind": "UNKNOWN",
    "doc_id_val": "N/A", "doc_id_score": 0.0,
    "doc_date_sic_val": "N/A", "doc_date_sic_score": 0.0,
    "doc_date_parsed": "1970-01-01T00:00:00Z",
    "doc_subject_val": "Default - No Match", "doc_subject_score": 0.0
}


# Define a set of characters to use for random replacement.
# This excludes control characters but includes common text characters.
PRINTABLE_CHARS = string.ascii_letters + string.digits + string.punctuation + ' '

class ClassificationServiceImpl(BaseClassificationApi):
    """
    Concrete implementation of the Classification API logic.
    """

    @staticmethod
    def corrupt_value(original_value, score_str):
        """
        Corrupts a string value character by character based on a score.
        A higher score means a higher probability of the character being correct.

        Args:
            original_value (str): The string to be corrupted.
            score_str (str): The score as a string (e.g., "0.9").

        Returns:
            str: The potentially corrupted string.
        """
        if not original_value:  # Handle empty or None values
            return ""
        try:
            score = float(score_str)
            if not (0.0 <= score <= 1.0):  # Ensure score is a valid probability
                score = 1.0  # Default to no corruption if score is invalid
        except (ValueError, TypeError):
            # If score is not a valid float or None, return original value (no corruption)
            return original_value

        corrupted_char_list = []
        for char_code in original_value:
            if random.random() < score:
                corrupted_char_list.append(char_code)
            else:
                corrupted_char_list.append(random.choice(PRINTABLE_CHARS))
        return "".join(corrupted_char_list)

    def classify_pdf(
            self,
            uuid_param_str: str,
            body: bytes
    ) -> ClassificationResult:
        """
        Actual implementation to classify the PDF.
        Returns a mocked response based on the last two digits of uuid_param.
        """
        print(f"--- Inside ClassificationServiceImpl.classify_pdf ---")
        print(f"Received UUID: {uuid_param_str}")
        print(f"Received body length: {len(body) if body else 0} bytes")

        # Ensure the uuid_param_str is a string
        uuid_param = self.assertValidUuidParam(uuid_param_str)

        # Ensure the body is somewhat a PDF
        self.assertValidBody(body)

        try:
            # --- Determine response based on UUID ---
            uuid_str = str(uuid_param)
            uuid_ending = uuid_str[-2:]  # Get last two characters

            # Get the specific response data, or use default if not found
            response_data = MOCK_RESPONSES.get(uuid_ending, DEFAULT_RESPONSE_DATA)
            print(f"Using response data for UUID ending: '{uuid_ending}'")

            # --- Construct the ResultItem ---
            # Use the specific data from the selected dictionary
            try:
                parsed_date = datetime.datetime.fromisoformat(response_data["doc_date_parsed"])
            except ValueError:
                parsed_date = None

            result_item = ResultItem(
                kind=response_data["kind"],
                doc_id=QualifiedValue(value=ClassificationServiceImpl.corrupt_value(response_data["doc_id_val"], response_data["doc_id_score"]),
                                      score=response_data["doc_id_score"]),
                doc_date_sic=QualifiedValue(value=ClassificationServiceImpl.corrupt_value(response_data["doc_date_sic_val"], response_data["doc_date_sic_score"]),
                                            score=response_data["doc_date_sic_score"]),
                doc_date_parsed=parsed_date,
                doc_subject=QualifiedValue(value=ClassificationServiceImpl.corrupt_value(response_data["doc_subject_val"], response_data["doc_subject_score"]),
                                           score=response_data["doc_subject_score"])
            )

            # --- Construct the final ClassificationResult ---
            response_model = ClassificationResult(
                class_id=str(uuid.uuid4()),  # Generate a new unique ID for this classification result
                custom_id=uuid_str,  # Use the input UUID as the custom ID
                result=result_item  # Assign the constructed ResultItem
            )
            return response_model

        except Exception as e:
            # Log the detailed error for debugging
            print(f"Error during classification processing for UUID {uuid_param}: {e}")
            import traceback
            traceback.print_exc()  # Print the full traceback to the console

            # Return a generic 500 error to the client
            raise HTTPException(status_code=500,
                                detail=f"Internal server error during classification: An unexpected error occurred. {e}")
            # --- END OF YOUR LOGIC ---

    def assertValidBody(self, body:bytes):
        if not body or len(body) == 0:
            raise HTTPException(status_code=400, detail="PDF body must be present")
        if len(body) <= len(EXPECTED_PDF_HEADER):
            raise HTTPException(status_code=400, detail="PDF body too short")
        if not body or not body[0:len(EXPECTED_PDF_HEADER)] == EXPECTED_PDF_HEADER:
            raise HTTPException(status_code=400, detail="Invalid file format: Does not appear to be a PDF.")

    def assertValidUuidParam(self, uuid_param_str: str) -> uuid.UUID:
        try:
            return uuid.UUID(uuid_param_str)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid UUID format")