# GitHub Repository Lister CLI

A command-line tool to retrieve and display GitHub user repositories using the GitHub API.

## Features

- Fetch repositories for any GitHub username
- **Automatic pagination** - retrieves all repositories
- Multiple output formats (default, detailed, JSON, compact)
- Rate limit handling with and without authentication
- Docker container support
- Comprehensive error handling
- **Progress reporting** - shows pagination progress to stderr

## Installation

### Local Development

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Set up development environment:

   ```bash
   make development-requirements
   make pre-commit-install
   ```

### Docker

Build and run the Docker container:

```bash
# Build the image
docker build -t github-repo-lister .

# Run with a username
docker run github-repo-lister octocat
```

## Usage

### Basic Usage

```bash
# List repositories for a user (default format)
python main.py octocat

# List repositories with detailed output
python main.py octocat --format detailed

# Output as JSON
python main.py octocat --format json

# Compact output format
python main.py octocat --format compact
```

### Authentication

For higher rate limits, set the `GITHUB_TOKEN` environment variable:

```bash
export GITHUB_TOKEN=your_github_token_here
python main.py octocat
```

Or use with Docker:

```bash
docker run -e GITHUB_TOKEN=your_github_token_here github-repo-lister octocat
```

### Skip Token Usage

To force running without a token (useful for testing):

```bash
python main.py octocat --no-token
```

## Output Formats

### Default Format

```
- repo-name: Repository description
```

### Detailed Format

```
Name: repo-name
Description: Repository description
URL: https://github.com/user/repo-name
Private: False
Fork: False
Stars: 10
Watchers: 5
Size: 100 KB
Visibility: public
Last Updated: 2023-01-01T00:00:00Z
Topics: python, cli
==================================================
```

### JSON Format

Complete repository data in JSON format (same as GitHub API response).

### Compact Format

```
- repo-name | Repository description | 10 stars
```

## Progress Reporting

The application shows pagination progress to stderr:

```
Fetching page 1...
Retrieved 100 repositories from page 1
Fetching page 2...
Retrieved 50 repositories from page 2
Total repositories fetched: 150
```

This allows you to see the progress while the application fetches all repositories, especially useful for users with many repositories.

## Error Handling

The application handles various error scenarios:

- **Rate Limit Exceeded**: When GitHub API rate limit is reached
- **Network Errors**: Connection issues or timeouts
- **API Errors**: Invalid usernames or other API issues
- **Missing Token**: Graceful degradation when no token is provided

## Development

### Running Tests

```bash
python -m pytest test_main.py
```

### Code Quality

The project includes pre-commit hooks for code quality:

```bash
# Install pre-commit hooks
make pre-commit-install

# Run pre-commit on all files
make pre-commit-run

# Format code
make fmt

# Run linting
make lint
```

## API Reference

The application uses the GitHub REST API v3:

- **Endpoint**: `https://api.github.com/users/{username}/repos`
- **Authentication**: Bearer token (optional)
- **Pagination**: Automatically handles all pages (100 repos per page)
- **Rate Limits**:
  - 60 requests/hour (unauthenticated)
  - 5000 requests/hour (authenticated)

## License

This project is licensed under the MIT License.
