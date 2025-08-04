"""
Unit tests for GitHub Repository Lister CLI
"""

import json
import unittest
from unittest.mock import Mock, patch

import requests

from main import (
    GitHubAPIError,
    RateLimitExceededError,
    format_repository_output,
    get_github_token,
    make_github_api_request,
)


class TestGitHubRepositoryLister(unittest.TestCase):
    def test_get_github_token_with_token(self):
        """Test getting GitHub token when environment variable is set."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"}):
            token = get_github_token()
            self.assertEqual(token, "test_token")

    def test_get_github_token_without_token(self):
        """Test getting GitHub token when environment variable is not set."""
        with patch.dict("os.environ", {}, clear=True):
            token = get_github_token()
            self.assertIsNone(token)

    @patch("requests.get")
    def test_make_github_api_request_success(self, mock_get):
        """Test successful GitHub API request."""
        mock_response = Mock()
        mock_response.json.return_value = [{"name": "test-repo"}]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = make_github_api_request("testuser", "test_token")

        self.assertEqual(result, [{"name": "test-repo"}])
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_make_github_api_request_rate_limit(self, mock_get):
        """Test GitHub API request with rate limit exceeded."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "0"}
        mock_get.return_value = mock_response

        with self.assertRaises(RateLimitExceededError):
            make_github_api_request("testuser", "test_token")

    @patch("requests.get")
    def test_make_github_api_request_other_error(self, mock_get):
        """Test GitHub API request with other error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {"X-RateLimit-Remaining": "100"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Client Error"
        )
        mock_get.return_value = mock_response

        with self.assertRaises(GitHubAPIError):
            make_github_api_request("testuser", "test_token")

    def test_format_repository_output_default(self):
        """Test default output format."""
        repo = {"name": "test-repo", "description": "Test repository"}
        result = format_repository_output(repo, "default")
        self.assertEqual(result, "test-repo: Test repository")

    def test_format_repository_output_detailed(self):
        """Test detailed output format."""
        repo = {
            "name": "test-repo",
            "description": "Test repository",
            "html_url": "https://github.com/user/test-repo",
            "private": False,
            "fork": False,
            "stargazers_count": 10,
            "watchers_count": 5,
            "size": 100,
            "visibility": "public",
            "updated_at": "2023-01-01T00:00:00Z",
            "topics": ["python", "cli"],
        }
        result = format_repository_output(repo, "detailed")
        self.assertIn("Name: test-repo", result)
        self.assertIn("Description: Test repository", result)
        self.assertIn("Stars: 10", result)

    def test_format_repository_output_json(self):
        """Test JSON output format."""
        repo = {"name": "test-repo", "description": "Test repository"}
        result = format_repository_output(repo, "json")
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, repo)

    def test_format_repository_output_compact(self):
        """Test compact output format."""
        repo = {
            "name": "test-repo",
            "description": "Test repository",
            "stargazers_count": 10,
        }
        result = format_repository_output(repo, "compact")
        self.assertEqual(result, "test-repo | Test repository | 10 stars")


if __name__ == "__main__":
    unittest.main()
