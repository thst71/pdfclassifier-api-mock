# coding: utf-8

from fastapi.testclient import TestClient


from openapi_server.models.classification_result import ClassificationResult  # noqa: F401
from openapi_server.models.error import Error  # noqa: F401


def test_classify_pdf(client: TestClient):
    """Test case for classify_pdf

    Classify a PDF uploaded as binary data into type with id-values
    """
    body = '/path/to/file'

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/classify/{uuid}".format(uuid='f47ac10b-58cc-4372-a567-0e02b2c3d479'),
    #    headers=headers,
    #    json=body,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

