# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.classification_api_base import BaseClassificationApi
import openapi_server.implementation

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    Path,
    Query,
    Response,
    Security,
    status,
)

from openapi_server.models.extra_models import TokenModel  # noqa: F401
from openapi_server.models.classification_result import ClassificationResult
from openapi_server.models.error import Error


router = APIRouter()

ns_pkg = openapi_server.implementation
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/classify/{uuid}",
    responses={
        200: {"model": ClassificationResult, "description": "PDF classification successful"},
        400: {"model": Error, "description": "The uploaded file is either no PDF or could not be accessed properly"},
    },
    tags=["classification"],
    summary="Classify a PDF uploaded as binary data into type with id-values",
    response_model_by_alias=True,
)
async def classify_pdf(
    uuid: str = Path(..., description="The uuid in the path sets the user&#39;s process id for the uploaded pdf."),
    body: bytes = Body(None, description="The PDF as binary data.", media_type="application/pdf"),
) -> ClassificationResult:
    """Upload a PDF as binary and inspect the contents. The data is uploaded in binary form and the result is a structure that returns the type of the document and a key-value list of type-specific identifiers. """
    return BaseClassificationApi.subclasses[0]().classify_pdf(uuid, body)
