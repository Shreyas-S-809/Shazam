"""ACRCloud song recognition service.

Sends audio samples to the ACRCloud identify endpoint and parses
the response.  Requires ACR_HOST, ACR_KEY, ACR_SECRET env vars.
"""

import base64
import hashlib
import hmac
import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

_ACR_TIMEOUT = 15  # seconds per attempt
_MAX_RETRIES = 3
_MAX_SAMPLE_BYTES = 1_000_000  # 1 MB cap for the sample sent to ACRCloud


def _get_credentials() -> tuple[str, str, str]:
    """Read ACRCloud credentials from the environment.

    Raises ``RuntimeError`` with a clear message when a required
    variable is missing so the caller gets a useful error instead
    of a raw ``KeyError``.
    """
    host = os.environ.get("ACR_HOST")
    key = os.environ.get("ACR_KEY")
    secret = os.environ.get("ACR_SECRET")
    missing = [n for n, v in [("ACR_HOST", host), ("ACR_KEY", key),
                               ("ACR_SECRET", secret)] if not v]
    if missing:
        raise RuntimeError(
            f"Missing ACRCloud credentials: {', '.join(missing)}. "
            "Set them in backend/.env"
        )
    return host, key, secret  # type: ignore[return-value]


def _build_signature(access_key: str, access_secret: str,
                     timestamp: str) -> str:
    """Create the HMAC-SHA1 signature for ACRCloud."""
    string_to_sign = "\n".join([
        "POST", "/v1/identify", access_key,
        "audio", "1", timestamp,
    ])
    return base64.b64encode(
        hmac.new(
            access_secret.encode("ascii"),
            string_to_sign.encode("ascii"),
            digestmod=hashlib.sha1,
        ).digest()
    ).decode("ascii")


def identify_song(audio_file: str) -> dict | None:
    """Identify a song from a local audio file via ACRCloud.

    Parameters
    ----------
    audio_file : str
        Path to a WAV (or any format ACRCloud accepts).

    Returns
    -------
    dict | None
        ``{"title": ..., "artist": ..., "album": ...}`` on match,
        ``None`` otherwise.
    """
    host, access_key, access_secret = _get_credentials()

    timestamp = str(int(time.time()))
    signature = _build_signature(access_key, access_secret, timestamp)

    with open(audio_file, "rb") as f:
        audio_bytes = f.read()

    # Cap sample size to avoid timeouts on very large files
    if len(audio_bytes) > _MAX_SAMPLE_BYTES:
        audio_bytes = audio_bytes[:_MAX_SAMPLE_BYTES]
        logger.info("Trimmed sample to %d bytes", len(audio_bytes))

    url = f"https://{host}/v1/identify"
    logger.info("ACRCloud request: host=%s, url=%s, sample=%d bytes",
                host, url, len(audio_bytes))

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = requests.post(
                url,
                files={"sample": (os.path.basename(audio_file), audio_bytes)},
                data={
                    "access_key": access_key,
                    "sample_bytes": str(len(audio_bytes)),
                    "timestamp": timestamp,
                    "signature": signature,
                    "data_type": "audio",
                    "signature_version": "1",
                },
                timeout=_ACR_TIMEOUT,
            )
            response.raise_for_status()
            break  # success
        except requests.exceptions.Timeout as exc:
            logger.warning("ACRCloud timeout (attempt %d/%d): %s",
                           attempt, _MAX_RETRIES, exc)
            last_exc = exc
        except requests.RequestException as exc:
            logger.error("ACRCloud request failed (attempt %d/%d): %s",
                         attempt, _MAX_RETRIES, exc)
            last_exc = exc
    else:
        # All retries exhausted
        raise RuntimeError(
            f"ACRCloud did not respond after {_MAX_RETRIES} attempts — "
            "possible network issue or wrong host"
        ) from last_exc

    result = response.json()
    acr_code = result.get("status", {}).get("code")
    acr_msg = result.get("status", {}).get("msg", "")
    logger.info("ACRCloud response: code=%s  msg=%s", acr_code, acr_msg)

    if acr_code != 0:
        # 1001 = No result, 3003 = exceeded limit, etc.
        return None

    try:
        music = result["metadata"]["music"][0]
        return {
            "title": music["title"],
            "artist": music["artists"][0]["name"],
            "album": music.get("album", {}).get("name", "Unknown"),
        }
    except (KeyError, IndexError, TypeError):
        logger.warning("Unexpected ACRCloud response structure: %s",
                       result.get("metadata"))
        return None
