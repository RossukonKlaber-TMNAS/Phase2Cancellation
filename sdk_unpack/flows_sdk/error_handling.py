"""
This module contains classes related to flow error handling. Currently, the error handling
framework includes:

- **Automatic retries of block errors.** Available in R36+. This feature allows configuring an
  error retry policy on the flow or block level. If a block has an error retry policy defined on
  itself or on its parent flow and its execution results in an error a new block with the same
  input parameters will get scheduled by the flow engine after a time interval, calculated based
  on the effective error retry policy of the failed block.

- **On error flows.** Available in R38+. This feature allows users to configure a flow to run in
  case a flow run fails. Each failed flow run will trigger its own on error flow which will receive
  the UUID for the failed flow run as input under the input key "failed_run_uuid". The on error
  flow is invoked only on terminal failure, errors that will be retried by the block error retry
  policy will not trigger it. Currently, can be configured only in a flow level error handling
  section.
"""

from enum import Enum
from typing import Any, Optional, Union

from pydantic import ConfigDict, Extra, validator
from pydantic.dataclasses import dataclass


class RetryMethod(str, Enum):
    """
    Retry methods for handling block errors in flows. Each method has its own formula for
    calculating the time between a failure and the next retry attempt. Check each enum member for
    the specific formula.
    When calculating your error retry policy values keep in mind that what you get as a result
    using the formulas below is the **minimum** time between retry attempts, blocks may take
    additional time to actually run the work.

    Available in v36 and later.
    """

    FIXED = 'FIXED'
    """
    Each retry runs after retry_interval_seconds seconds.
    """
    LINEAR_BACKOFF = 'LINEAR_BACKOFF'
    """
    Next retry is scheduled after retry_interval_seconds * attempt_number seconds.
    """
    EXPONENTIAL_BACKOFF = 'EXPONENTIAL_BACKOFF'
    """
    Next retry is scheduled after retry_interval_seconds * 2 ^ (attempt_number - 1) seconds. This
    means that the first attempt runs after retry_interval_seconds seconds, the second one after
    2 * retry_interval_seconds, then 4 * retry_interval_seconds, etc.
    """
    NO_RETRY = 'NO_RETRY'
    """
    Not retried.
    """


@dataclass(frozen=True)
class ErrorRetryPolicy:
    """
    Base class for all error retry policies.
    """

    method: RetryMethod
    """
    The algorithm that should be applied when calculating the delay between each retry attempt.
    """


@dataclass(frozen=True, config=ConfigDict(extra=Extra.forbid))
class SimpleErrorRetryPolicy(ErrorRetryPolicy):
    """
    Base class for simple error retry policies that are defined by their method, retry count
    and a retry interval in seconds.

    Available in v36 and later.
    """

    retry_count: int
    """
    How many time a failed block should be retried. This means that if retry_count=3 the block can
    run up to 4 times within a single flow run - 1 original run + 3 retries.
    """
    retry_interval_seconds: float
    """
    The base interval to use when calculating the delay between each retry attempt. Will result in
    different delays depending on the selected retry method.
    """

    @validator('method')
    @classmethod
    def not_no_retry(cls, v: RetryMethod) -> RetryMethod:
        """
        :meta private:
        """
        if v == RetryMethod.NO_RETRY:
            raise ValueError(
                f"Method can't be {RetryMethod.NO_RETRY.name} if retry_count "
                'and/or retry_interval_seconds are specified'
            )
        return v

    @validator('retry_count', 'retry_interval_seconds')
    @classmethod
    def greater_or_equal_to_one(cls, v: Union[float, int]) -> Union[float, int]:
        """
        :meta private:
        """
        if v < 1:
            raise ValueError('retry_count must be greater than or equal to 1')
        return v


@dataclass(frozen=True, config=ConfigDict(extra=Extra.forbid))
class NoRetryErrorRetryPolicy(ErrorRetryPolicy):
    """
    No retry, fail on the first unhandled error during execution. This policy can be used to
    prevent retries for specific blocks in flows that define an error retry policy.

    Available in v36 and later.
    """

    method: RetryMethod = RetryMethod.NO_RETRY

    @validator('method')
    @classmethod
    def always_no_retry(cls, v: RetryMethod) -> RetryMethod:
        """
        :meta private:
        """
        if v != RetryMethod.NO_RETRY:
            raise ValueError(
                f'Method has to be {RetryMethod.NO_RETRY.name} for NoRetryErrorRetryPolicy'
            )
        return v


# Has to be a Union, pydantic doesn't work with specifying the parent class ErrorRetryPolicy
ErrorRetryPolicyType = Union[SimpleErrorRetryPolicy, NoRetryErrorRetryPolicy]


@dataclass(frozen=True)
class OnErrorFlow:
    """
    Specifies the details of the flow that should run in case a flow run fails. Note that the
    OnErrorFlow would be called only in case of terminal failure, failures that will be retried
    will not trigger it.

    Check out the example for more details -
    :ref:`pages/examples:Submission-aware OnError flow`

    **Available since v38.**
    """

    identifier: str
    """
    The identifier of the flow that should be called on error.
    """


@dataclass(frozen=True)
class ErrorHandling:
    """
    Container for error handling related concepts for blocks and flows.

    Available in v36 and later.
    """

    block_error_retry_policy: Optional[ErrorRetryPolicyType] = None
    """
    This error retry policy will be applied to all blocks in the flow. Individual blocks can
    override this using the same class.

    .. collapse:: Example

        .. include:: ../../../samples/block_retries_flow/block_retries_flow.py
            :literal:
    """

    on_error_flow: Optional[OnErrorFlow] = None
    """
    Specification for a flow that should run on error. Can be used only for error handling
    attached on the flow level.

    Available since v38.
    """

    @validator('block_error_retry_policy', pre=True)
    @classmethod
    def no_empty_block_error_retry_policy(cls, v: Any) -> Any:
        """
        :meta private:

        Don't allow parsing block_error_retry_policy={} as NO_RETRY.
        """
        if isinstance(v, dict) and 'method' not in v:
            raise ValueError('"method" is required')
        return v


class ErrorHandlingMixin:
    """
    :meta private:

    Mixin that can be used to add an optional error handling section to another class.
    """

    error_handling: Optional[ErrorHandling] = None
