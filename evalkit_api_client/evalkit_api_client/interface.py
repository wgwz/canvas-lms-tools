from abc import ABCMeta, abstractmethod
from requests import Response
from typing import Iterator

from evalkit_api_client.types import RequestParams


class EvalKitAPIClient(metaclass=ABCMeta):
    """
    Base class (interface) for Evalkit API Client subclasses.

    This interface is mostly used for mypy type-checking and python unit tests.
    """
    @abstractmethod
    def get_projects(self,
                    params: RequestParams = None
                    ) -> Response:
        """
        Returns a generator of projects for a given account.
        """

    @abstractmethod
    def get_non_responders(self,
                          project_id: str,
                          params: RequestParams = None
                          ) -> Response:
        """
        Returns a generator of non-responders for a given project.
        """
