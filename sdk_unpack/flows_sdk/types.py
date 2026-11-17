"""
This module contains types that can be useful for writing flows but are not part of the flow's
topology.

Available in v35 and later.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pydantic import validator
from pydantic.dataclasses import dataclass as py_dataclass


@dataclass(frozen=True)
class StoreBlobRequest(object):
    """
    Encapsulates the request parameters for storing a blob.
    """

    name: str
    """Name that will be associated with the blob."""
    content: bytes
    """Blob content in bytes."""


@dataclass(frozen=True)
class StoreBlobResponse(object):
    """
    The result of storing a blob. Contains data that can be used to retrieve the blob.
    """

    uuid: str
    """Unique identifier of the created blob."""
    name: str
    """Name associated with the blob."""


@dataclass(frozen=True)
class Blob(object):
    """
    The result of fetching a blob from the object store.
    """

    content: bytes
    """The content of the blob in bytes."""


@dataclass(frozen=True)
class HsTask:
    """
    A task in the flow engine runtime - contains task and flow metadata.

    Available in v35 and later.
    """

    task_id: str
    """Unique identifier of the task withing the system"""
    flow_run_id: str
    """Unique identifier of the flow run withing the system"""
    correlation_id: str
    """A string that gets passed from parent to child flow runs and can be used to
    identify flow runs that belong to the same execution graph"""
    task_name: str
    """The name of the block that runs the task, e.g. PYTHON_CODE"""
    reference_name: str
    """The unique identifier of the task in the flow definition"""


@py_dataclass(frozen=True)
class Measurement:
    """
    The datum or numerical value associated with a metric, described over the respective dimensions.
    AKA Fact in the OLAP world.

    Measurements do not have uniqueness properties. Two measurements with the exact same values will
    not be considered duplicate, but rather different measurements taken at the same time,
    for the same metric, with the same value and dimensions.

    Available in V41 and later.
    """

    name: str
    """Name is the machine identifier for a metric. Names cannot be blank and, alongside namespace,
    represent the identifier of a metric.
    """
    namespace: str
    """Namespace represents the context under which the metric is used. This property avoids
    conflicts between metrics with the same name, used in different contexts. Similar to the name
    field, a namespace cannot be blank.
    """
    time: datetime
    """
    The 'time' field refers to the "occurrence time" where the measurement was taken. In
    event-driven architecture (EDA) this is usually referred to as "event time", and just like in
    EDA, this has no relation to the real time, i.e., the time at which the event/measurement is
    processed by the analytics system. This datetime field must be timezone-aware.
    """
    dimensions: dict[str, str]
    """Dimensions provide the "who, what, where, when, why, and how" context surrounding a
    measurement. They contain the attributes which characterize the measurement, which, at the
    analytical level, can be used to filter and/or group measurements.
    """
    value: float
    """The datum associated with a metric, described over the respective dimensions. AKA Fact in
    the OLAP world."""

    @validator('time')
    @classmethod
    def _forbid_naive_datetime(cls, v: datetime) -> datetime:
        """
        :meta private:
        """
        if v.utcoffset() is None:
            raise ValueError(f'{v} time must be timezone-aware.')
        return v


class HsBlockInstance(ABC):
    """
    Provides an interface for the base block APIs in code blocks.

    Available in v35 and later.
    """

    class LogLevel(Enum):
        DEBUG = auto()
        INFO = auto()
        WARN = auto()
        ERROR = auto()

    @abstractmethod
    def store_blob(self, blob: StoreBlobRequest) -> StoreBlobResponse:
        """
        Stores a blob in the object store. For more information see store_blobs.

        :param blob: The binary object to store.
        :return: A response object that contains the blob's unique identifier.
        :rtype: StoreBlobResponse
        """
        pass

    @abstractmethod
    def store_blobs(self, blobs: Iterable[StoreBlobRequest]) -> List[StoreBlobResponse]:
        """
        Stores a list of blobs in the object store. The blobs will be associated with the
        flow run where this code gets executed. When this flow run is deleted the blobs will be
        deleted as well.

        :param blobs: List of blobs to store.
        :return: A list of response objects that contain the blobs' unique identifiers.
        :rtype: List[StoreBlobResponse]
        """
        pass

    @abstractmethod
    def fetch_blob(self, blob_reference: str) -> Blob:
        """
        Retrieves the contents for the provided blob reference string.

        :param blob_reference: The unique identifier of the blob to be fetched.
        :return: The blob's content. If no blob with the provided reference exists, an exception
          will be raised.
        :rtype: Blob
        """
        pass

    @abstractmethod
    def log(self, msg: str, level: LogLevel = LogLevel.INFO) -> None:
        """
        Logs a message at the given log level both to the standard out/err stream and to the
        flow execution context, making it available in the `Logs` tab of the View Flow Execution UI.
        Prepends meta information that makes the logs easier to trace (e.g. by correlation id)

        :param msg: The message to log.
        :param level: The log level to use. Defaults to INFO.
        """
        pass

    def hs_request(self, method: str, app_endpoint: str, **kwargs: Dict[Any, Any]) -> Any:
        """
        **Available in v40.2 and later.**

        Makes an authenticated HTTP request to the Hyperscience platform.
        This method will automatically take care of prepending the base url and will include
        the appropriate authentication headers with the request.

        Mandatory parameters:

        :param method: HTTP method to use, e.g. 'GET', 'POST', etc.
        :param app_endpoint: relative url, beginning with a forward slash, to an HTTP endpoint
            served by the Hyperscience platform. For reference on the available endpoints, check out
            https://docs.hyperscience.com/.
            Absolute URLs that include a hostname are allowed only if the flow has received them
            as part of the response of a previous API request that the flow has made.
            Do not hardcode the hostname of the Hyperscience instance in your flow definitions as
            they will not work when you run the flows on another instance,
            or if the hostname changes.

        Optional Parameters:

        :param kwargs: Additional keyword arguments to pass to the request call - the requests
            library is used under the hood. E.g. POST requests probably need a body passed via
            the `data` or `json` argument.
            See https://requests.readthedocs.io/en/latest/api/#requests.request.

        :return: A requests.Response object
        """
        pass

    def hs_get(self, app_endpoint: str, **kwargs: Dict[Any, Any]) -> Any:
        """
        **Available in v40.2 and later.**

        Makes an authenticated GET request to the Hyperscience platform.
        See docs for HsBlockInstance.hs_request above.
        """
        pass

    def hs_post(self, app_endpoint: str, **kwargs: Dict[Any, Any]) -> Any:
        """
        **Available in v40.2 and later.**

        Makes an authenticated POST request to the Hyperscience platform.
        See docs for HsBlockInstance.hs_request above.
        """
        pass

    @abstractmethod
    def publish_measurements(self, measurements: list[Measurement]) -> None:
        """
        **Available in v41 and later.**

        Publishes measurements to the Hyperscience analytics system.

        Mandatory parameters:

        :param measurements: The provided measurements are persisted in the system, and are
            eventually available in Hyperscience reports.

        """
        pass


@dataclass(frozen=True)
class CompatibilitySpec:
    """
    **Available in v38 and later.**

    Provides a definition of the compatibility spec used in blocks. The spec allows to change
    the identifier of a block or a flow to the identifier of a block that corresponds to the spec.
    """

    filter_roles: Optional[List[str]] = None
    """
    Takes a list of strings that represent flow or block roles and allows the UI to filter by them
    """
    filter_schema: Optional[Dict[str, Any]] = None
    """
    Represents a JSON schema, that allows for more intricate filtering.
    """
    label: Optional[str] = None
    """
    Represents the UI label in FlowStudio
    """

    @staticmethod
    def compatibility_spec_dict_factory(data: List[Tuple[str, Any]]) -> Dict[str, Any]:
        return {f: v for f, v in data if v is not None}
