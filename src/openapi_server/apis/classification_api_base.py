# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from openapi_server.models.classification_result import ClassificationResult

class BaseClassificationApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseClassificationApi.subclasses = BaseClassificationApi.subclasses + (cls,)
    def classify_pdf(
        self,
        uuid: str,
        body: bytearray,
    ) -> ClassificationResult:
        """Upload a PDF as binary and inspect the contents. The data is uploaded in binary form and the result is a structure that returns the type of the document and a key-value list of type-specific identifiers. """
        ...