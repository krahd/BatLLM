"""Module responsible for communication with the LLM.

This module encapsulates the logic for sending HTTP requests to the
language model endpoint configured in the application's settings. It
provides a simple interface for the rest of the code base to invoke
the model without having to work directly with Kivy's UrlRequest.

The OllamaConnector class is designed to be a lightweight utility. It
does not maintain any internal state beyond what is required to
execute a request. Instead, all relevant data (such as the target
URL, the request payload and callback functions) is passed in at
execution time. This separation makes it easier to test the game
logic without relying on network calls, and keeps all networking
concerns localized to this file.
"""

import json
from typing import Callable, Any

from kivy.network.urlrequest import UrlRequest


class OllamaConnector:
    """Handles HTTP communication with an LLM endpoint.

    The primary method `send_request` accepts a full URL, a JSON-serialisable
    payload, and three callback functions for success, failure and
    error cases. It constructs a POST request with JSON body and
    returns the UrlRequest object, which Kivy will manage asynchronously.
    """

    def __init__(self) -> None:
        # By default, always send JSON requests
        self.headers = {"Content-Type": "application/json"}

    def send_request(
        self,
        url: str,
        data: dict[str, Any],
        on_success: Callable[[UrlRequest, dict[str, Any]], None],
        on_failure: Callable[[UrlRequest, Any], None],
        on_error: Callable[[UrlRequest, Any], None],
    ) -> UrlRequest:
        """Send a POST request to the given URL with the supplied data.

        Args:
            url: The fully qualified endpoint URL including protocol, host, port and path.
            data: A JSON-serialisable dictionary to send in the request body.
            on_success: Callback executed on HTTP 2xx responses. Receives the
                UrlRequest instance and the decoded JSON response.
            on_failure: Callback executed on HTTP error responses (4xx/5xx). Receives
                the UrlRequest instance and an error message.
            on_error: Callback executed on transport-level errors (network down, etc.).
                Receives the UrlRequest instance and an exception instance.

        Returns:
            UrlRequest: The request object, which can be inspected or cancelled.
        """

        # Serialize the payload to JSON. We do this here so that callers
        # can work purely with Python dictionaries and do not need to
        # think about encoding.
        body = json.dumps(data)

        # Issue the asynchronous request. Kivy's UrlRequest will manage the
        # connection on a background thread and schedule callbacks on the
        # main thread upon completion.
        return UrlRequest(
            url,
            req_headers=self.headers,
            req_body=body,
            on_success=on_success,
            on_failure=on_failure,
            on_error=on_error,
            method="POST",
        )