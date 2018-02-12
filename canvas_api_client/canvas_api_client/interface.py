from abc import (ABCMeta, abstractmethod)
from typing import Iterator

from canvas_api_client.types import (RequestHeaders, RequestParams, Response)


class CanvasAPIClient(metaclass=ABCMeta):
    """
    Base class (interface) for Canvas API Client subclasses.

    This interface is mostly used for mypy type-checking and python unit tests.
    """

    @abstractmethod
    def get_account_courses(self,
                            account_id: str,
                            params: RequestParams = None
                            ) -> Iterator[Response]:
        """
        Returns a generator of courses for a given account.
        """
        pass

    @abstractmethod
    def get_course_users(self,
                         course_id: str,
                         is_sis_course_id: bool = False,
                         params: RequestParams = None) -> Iterator[Response]:
        """
        Returns a generator of course enrollments for a given course.
        """
        pass

    @abstractmethod
    def delete_enrollment(self,
                          course_id: str,
                          enrollment_id: str,
                          is_sis_course_id: bool = False,
                          params: RequestParams = None) -> Response:
        """
        Deletes an enrollment for a given course.
        """
        pass

    @abstractmethod
    def import_sis_data(self,
                        account_id: str,
                        data_file: str,
                        params: RequestParams = None) -> Response:
        """
        Uploads a CSV containing Student Information Services (SIS) changes.
        """
        pass

    @abstractmethod
    def get_sis_import_status(self,
                              account_id: str,
                              sis_import_id: str,
                              params: RequestParams = None) -> Response:
        """
        Get the status of an already created SIS import.
        """
        pass
