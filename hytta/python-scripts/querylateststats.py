"""Query and print the latest IoT SODA document."""

import argparse
import json

import requests

from const import (
    CONST_SODA_PASSWORD,
    CONST_SODA_QUERY_BODY,
    CONST_SODA_QUERY_URL,
    CONST_SODA_USERNAME,
)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Query the latest IoT SODA document."
    )
    return parser.parse_args()


def query_latest_stats():
    """Return the latest SODA document query response."""
    response = requests.post(
        CONST_SODA_QUERY_URL,
        auth=(CONST_SODA_USERNAME, CONST_SODA_PASSWORD),
        data=CONST_SODA_QUERY_BODY,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main():
    """Print the SODA query response as formatted JSON."""
    parse_args()
    response = query_latest_stats()
    print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
