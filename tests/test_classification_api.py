# tests/test_classification_api_component.py

import pytest
import uuid
from datetime import datetime, timezone

# Make sure the main FastAPI app instance is importable
# Adjust the import path based on your project structure
# e.g., if your app is created in 'src/openapi_server/main.py'
from openapi_server.main import app
from fastapi.testclient import TestClient

# Import expected data/constants from the implementation if needed for assertions
from openapi_server.implementation.classification_service import (
    MOCK_RESPONSES,
    DEFAULT_RESPONSE_DATA,
    EXPECTED_PDF_HEADER
)

# --- Test Constants ---
SAMPLE_PDF_BODY = EXPECTED_PDF_HEADER + b" some pdf content bytes"
INVALID_BODY_HEADER = b'IAMNOTAPDF'
INVALID_BODY_SHORT = b'%PD'  # Shorter than required header length


# --- Fixtures ---

@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    Create a TestClient instance for the FastAPI app.
    'module' scope means it's created once per test module.
    """
    return TestClient(app)


# --- Helper Function ---

def _generate_uuid_ending_with(ending: str) -> uuid.UUID:
    """Helper to create a UUID with a specific ending."""
    if not (isinstance(ending, str) and len(ending) == 2 and ending.isdigit()):
        raise ValueError("Ending must be a 2-digit string")
    base_uuid_str = "00000000-0000-0000-0000-0000000000"
    test_uuid_str = base_uuid_str + ending
    return uuid.UUID(test_uuid_str)


# --- Test Cases ---

def test_classify_pdf_success_uuid_10(client: TestClient):
    """
    Test POST /classify/{uuid} - Success case with UUID ending '10'.
    """
    test_uuid = _generate_uuid_ending_with("10")
    url = f"/api/v1/classify/{test_uuid}"
    expected_data = MOCK_RESPONSES["10"]

    response = client.post(
        url,
        content=SAMPLE_PDF_BODY,
        headers={"Content-Type": "application/pdf"}  # Crucial header
    )

    assert response.status_code == 200
    response_json = response.json()

    # Assert top-level structure
    assert "class_id" in response_json
    assert response_json["custom_id"] == str(test_uuid)
    assert "result" in response_json

    # Assert result item details
    result = response_json["result"]
    assert result["kind"] == expected_data["kind"]

    # Assert nested QualifiedValues
    assert result["doc_id"]["value"] != ""
    assert result["doc_id"]["score"] == expected_data["doc_id_score"]
    assert result["doc_date_sic"]["value"] != ""
    assert result["doc_date_sic"]["score"] == expected_data["doc_date_sic_score"]
    assert result["doc_subject"]["value"] != ""
    assert result["doc_subject"]["score"] == expected_data["doc_subject_score"]

    # Assert parsed date (comes back as string in JSON)
    assert result["doc_date_parsed"] == expected_data["doc_date_parsed"]
    # Optional: Parse it back to check if it's valid
    parsed_dt = datetime.fromisoformat(
        result["doc_date_parsed"].replace('Z', '+00:00'))  # Handle Z for older python if needed
    assert parsed_dt.tzinfo is not None  # Should be timezone-aware


def test_classify_pdf_success_uuid_20(client: TestClient):
    """
    Test POST /classify/{uuid} - Success case with UUID ending '20'.
    """
    test_uuid = _generate_uuid_ending_with("20")
    url = f"/api/v1/classify/{test_uuid}"
    expected_data = MOCK_RESPONSES["20"]

    response = client.post(
        url,
        content=SAMPLE_PDF_BODY,
        headers={"Content-Type": "application/pdf"}
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["custom_id"] == str(test_uuid)
    assert response_json["result"]["kind"] == expected_data["kind"]
    assert response_json["result"]["doc_id"]["value"] != ""
    # Add more assertions if needed


def test_classify_pdf_success_default_uuid_99(client: TestClient):
    """
    Test POST /classify/{uuid} - Success case with non-matching UUID '99' (default response).
    """
    test_uuid = _generate_uuid_ending_with("99")  # Assuming '99' is not in MOCK_RESPONSES
    url = f"/api/v1/classify/{test_uuid}"
    expected_data = DEFAULT_RESPONSE_DATA

    response = client.post(
        url,
        content=SAMPLE_PDF_BODY,
        headers={"Content-Type": "application/pdf"}
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["custom_id"] == str(test_uuid)
    assert response_json["result"]["kind"] == expected_data["kind"]
    assert response_json["result"]["doc_id"]["value"] != ""
    assert response_json["result"]["doc_id"]["score"] == expected_data["doc_id_score"]
    # Add more assertions for default data

def test_classify_pdf_fail_invalid_uuid_format(client: TestClient):
    """
    Test POST /classify/{uuid} - Failure with invalid UUID format in path.
    """
    url = "/api/v1/classify/this-is-not-a-uuid"
    response = client.post(
        url,
        content=SAMPLE_PDF_BODY,
        headers={"Content-Type": "application/pdf"}
    )
    # FastAPI/Starlette handles invalid path parameter types before your code runs
    assert response.status_code == 422  # Unprocessable Entity

def test_classify_pdf_fail_empty_body(client: TestClient):
    """
    Test POST /classify/{uuid} - Failure with empty request body.
    """
    test_uuid = _generate_uuid_ending_with("10")
    url = f"/api/v1/classify/{test_uuid}"
    response = client.post(
        url,
        content=b'',  # Empty bytes
        headers={"Content-Type": "application/pdf"}
    )
    assert response.status_code == 400  # Bad Request
    response_json = response.json()
    assert "detail" in response_json
    # Check the specific detail message from assertValidBody
    assert response_json["detail"] == "PDF body must be present"


def test_classify_pdf_fail_body_too_short(client: TestClient):
    """
    Test POST /classify/{uuid} - Failure with body shorter than PDF header.
    """
    test_uuid = _generate_uuid_ending_with("10")
    url = f"/api/v1/classify/{test_uuid}"
    response = client.post(
        url,
        content=INVALID_BODY_SHORT,
        headers={"Content-Type": "application/pdf"}
    )
    assert response.status_code == 400  # Bad Request
    response_json = response.json()
    assert "detail" in response_json
    assert response_json["detail"] == "PDF body too short"


def test_classify_pdf_fail_invalid_header(client: TestClient):
    """
    Test POST /classify/{uuid} - Failure with body not starting with PDF header.
    """
    test_uuid = _generate_uuid_ending_with("10")
    url = f"/api/v1/classify/{test_uuid}"
    response = client.post(
        url,
        content=INVALID_BODY_HEADER,
        headers={"Content-Type": "application/pdf"}
    )
    assert response.status_code == 400  # Bad Request
    response_json = response.json()
    assert "detail" in response_json
    assert response_json["detail"] == "Invalid file format: Does not appear to be a PDF."

# --- To Run the Tests ---
# 1. Make sure 'pytest' and 'httpx' are installed:
#    pip install pytest httpx
# 2. Save this code as e.g., `tests/test_classification_api_component.py`.
# 3. Navigate to the directory *above* `tests` and `src` (your project root) in your terminal.
# 4. Run: pytest
