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


def make_github_api_request(
    username: str,
    token: Optional[str] = None,
    repos_per_page: int = 100,
    max_pages: Optional[int] = None,
    max_repos: Optional[int] = None,
) -> List[Dict]:
    """
    Make API request to GitHub to get user repositories with pagination support.

    Args:
        username: GitHub username
        token: Optional GitHub token for authentication
        repos_per_page: Number of repositories to request per page (1-100)
        max_pages: Maximum number of pages to retrieve (None for no limit)
        max_repos: Maximum total number of repositories to retrieve (None for no limit)

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

    all_repositories = []
    page = 1
    per_page = min(repos_per_page, 100)  # GitHub API maximum is 100

    try:
        while True:
            # Check if we've reached the page limit
            if max_pages is not None and page > max_pages:
                print(f"Reached page limit ({max_pages})", file=sys.stderr)
                break

            # Check if we've reached the repository limit
            if max_repos is not None and len(all_repositories) >= max_repos:
                print(f"Reached repository limit ({max_repos})", file=sys.stderr)
                break

            # Add pagination parameters
            params = {"page": page, "per_page": per_page}

            print(f"Fetching page {page}...", file=sys.stderr)

            response = requests.get(url, headers=headers, params=params, timeout=30)

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

            repositories = response.json()

            # If no repositories returned, we've reached the end
            if not repositories:
                break

            # Add repositories up to the limit
            remaining_slots = (
                max_repos - len(all_repositories)
                if max_repos is not None
                else len(repositories)
            )
            repositories_to_add = repositories[:remaining_slots]

            all_repositories.extend(repositories_to_add)
            print(
                f"Retrieved {len(repositories_to_add)} repositories from page {page}",
                file=sys.stderr,
            )

            # If we got fewer than per_page repositories, this is the last page
            if len(repositories) < per_page:
                break

            # If we've reached the repository limit, stop
            if max_repos is not None and len(all_repositories) >= max_repos:
                break

            page += 1

        print(f"Total repositories fetched: {len(all_repositories)}", file=sys.stderr)
        return all_repositories

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
  %(prog)s octocat --limit 10
  %(prog)s octocat --pages 2 --repos-per-page 50
        """,
    )

    parser.add_argument("username", help="GitHub username to list repositories for")

    parser.add_argument(
        "-f",
        "--format",
        choices=["default", "detailed", "json", "compact"],
        default="default",
        help="Output format (default: default)",
    )

    parser.add_argument(
        "-n",
        "--no-token",
        action="store_true",
        help="Skip using GITHUB_TOKEN environment variable",
    )

    # Pagination control arguments
    parser.add_argument(
        "-r",
        "--repos-per-page",
        type=int,
        default=100,
        help="Number of repositories to request per page (default: 100, max: 100)",
    )

    parser.add_argument(
        "-p",
        "--pages",
        type=int,
        help="Maximum number of pages to retrieve (default: no limit)",
    )

    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        help="Maximum total number of repositories to retrieve (default: no limit)",
    )

    args = parser.parse_args()

    # Validate repos-per-page argument
    if args.repos_per_page < 1 or args.repos_per_page > 100:
        parser.error("--repos-per-page must be between 1 and 100")

    # Validate pages argument
    if args.pages is not None and args.pages < 1:
        parser.error("--pages must be greater than 0")

    # Validate limit argument
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be greater than 0")

    # Get GitHub token
    token = None if args.no_token else get_github_token()

    if not token:
        print(
            "Warning: No GitHub token provided. API calls may be rate limited.",
            file=sys.stderr,
        )

    try:
        # Fetch repositories with pagination controls
        repositories = make_github_api_request(
            args.username,
            token,
            repos_per_page=args.repos_per_page,
            max_pages=args.pages,
            max_repos=args.limit,
        )

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
