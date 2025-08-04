#!/usr/bin/env python3
"""
GitHub Repository Lister CLI

A command-line tool to retrieve and display GitHub user repositories.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

import requests


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""

    pass


class RateLimitExceededError(GitHubAPIError):
    """Exception raised when GitHub API rate limit is exceeded."""

    pass


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variable."""
    return os.getenv("GITHUB_TOKEN")


def make_github_api_request(username: str, token: Optional[str] = None) -> List[Dict]:
    """
    Make API request to GitHub to get user repositories.

    Args:
        username: GitHub username
        token: Optional GitHub token for authentication

    Returns:
        List of repository dictionaries

    Raises:
        RateLimitExceededError: When rate limit is exceeded
        GitHubAPIError: For other API errors
    """
    url = f"https://api.github.com/users/{username}/repos"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 403:
            # Check if it's a rate limit issue
            rate_limit_info = response.headers.get("X-RateLimit-Remaining")
            if rate_limit_info == "0":
                raise RateLimitExceededError(
                    "Rate limit exceeded. Please wait before making more requests."
                )
            else:
                raise GitHubAPIError(f"API request failed: {response.status_code}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        raise GitHubAPIError(f"Network error: {e}")


def format_repository_output(repo: Dict, output_format: str) -> str:
    """
    Format repository data based on output format.

    Args:
        repo: Repository dictionary from GitHub API
        output_format: Desired output format

    Returns:
        Formatted string representation of repository
    """
    if output_format == "json":
        return json.dumps(repo, indent=2)

    elif output_format == "detailed":
        return (
            f"Name: {repo.get('name', 'N/A')}\n"
            f"Description: {repo.get('description', 'No description')}\n"
            f"URL: {repo.get('html_url', 'N/A')}\n"
            f"Private: {repo.get('private', False)}\n"
            f"Fork: {repo.get('fork', False)}\n"
            f"Stars: {repo.get('stargazers_count', 0)}\n"
            f"Watchers: {repo.get('watchers_count', 0)}\n"
            f"Size: {repo.get('size', 0)} KB\n"
            f"Visibility: {repo.get('visibility', 'N/A')}\n"
            f"Last Updated: {repo.get('updated_at', 'N/A')}\n"
            f"Topics: {', '.join(repo.get('topics', []))}\n"
            f"{'=' * 50}"
        )

    elif output_format == "compact":
        return (
            f"- {repo.get('name', 'N/A')} | "
            f"{repo.get('description', 'No description')} | "
            f"{repo.get('stargazers_count', 0)} stars"
        )

    else:  # default format
        return (
            f"- {repo.get('name', 'N/A')}: {repo.get('description', 'No description')}"
        )


def main():
    """Main function to handle CLI execution."""
    parser = argparse.ArgumentParser(
        description="List GitHub repositories for a given username",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s octocat
  %(prog)s octocat --format detailed
  %(prog)s octocat --format json
  %(prog)s octocat --format compact
        """,
    )

    parser.add_argument("username", help="GitHub username to list repositories for")

    parser.add_argument(
        "--format",
        choices=["default", "detailed", "json", "compact"],
        default="default",
        help="Output format (default: default)",
    )

    parser.add_argument(
        "--no-token",
        action="store_true",
        help="Skip using GITHUB_TOKEN environment variable",
    )

    args = parser.parse_args()

    # Get GitHub token
    token = None if args.no_token else get_github_token()

    if not token:
        print(
            "Warning: No GitHub token provided. API calls may be rate limited.",
            file=sys.stderr,
        )

    try:
        # Fetch repositories
        repositories = make_github_api_request(args.username, token)

        if not repositories:
            print(f"No repositories found for user '{args.username}'")
            return

        # Display repositories
        print(f"Found {len(repositories)} repositories for user '{args.username}':")

        # Handle different output formats
        if args.format in ["default", "compact"]:
            # For default and compact formats, output without extra newlines
            for repo in repositories:
                print(format_repository_output(repo, args.format))
        else:
            # For detailed and json formats, add spacing between repositories
            print()  # Add initial newline
            for repo in repositories:
                print(format_repository_output(repo, args.format))
                if args.format != "json":
                    print()  # Add spacing between repositories

    except RateLimitExceededError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(
            "Consider setting GITHUB_TOKEN environment variable for higher rate limits.",
            file=sys.stderr,
        )
        sys.exit(1)

    except GitHubAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
