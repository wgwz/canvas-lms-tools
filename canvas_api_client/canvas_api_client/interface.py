from abc import (ABCMeta, abstractmethod)
from typing import Iterator

from canvas_api_client.types import (RequestHeaders,
    RequestParams,
    Response)


class CanvasAPIClient(metaclass=ABCMeta):
    """
    Base class (interface) for Canvas API Client subclasses.

    This interface is mostly used for mypy type-checking and python unit tests.
    """

    @abstractmethod
    def get_account_courses(
            self,
            account_id: str,
            params: RequestParams = None) -> Iterator[Response]:
        """
        Returns a generator of courses for a given account.
        """
        pass

    @abstractmethod
    def get_course_users(
            self,
            sis_course_id: str,
            params: RequestParams = None) -> Iterator[Response]:
        """
        Returns a generator of course enrollments for a given course.
        """
        pass

    @abstractmethod
    def delete_enrollment(
            self,
            course_id: str,
            enrollment_id: str,
            params: RequestParams = None) -> Response:
        """
        Deletes an enrollment for a given course.
        """
        pass
