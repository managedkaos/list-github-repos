# Prompts

Repo was created using the [Managed Kaos Python Container  Template](https://github.com/managedkaos/python-container-template/tree/main).

## 1. Kick Off

I'm developing a cli and docker-based application using Python.

The goal of the application is to take a single parameter, a user's GitHub ID, and then use the ID to call the GitHub API to retrieve a list of the user's repositories along with each repo's metadata.

The call to the API should use the env var GITHUB_TOKEN after the value is read from the environment.  If the var does not exist, attempt to proceed without the token but build in handling failed calls affected by `Rate limit exceeded` warnings/errors.

After retrieving the repos and metadata, command line switches can be used to control the output that is displayed with the default being the repo name and description.

Here's an example of calling the API using curl:

```bash
curl -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <YOUR-TOKEN>" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/users/USERNAME/repos
```

And here is JSON representation of the fields returned that are of interest. (Other fields are returned and should be preserved but only these are needed for the MVP):

```json
[
  {
    "id": 1296269,
    "name": "Hello-World",
    "full_name": "octocat/Hello-World",
    "owner": {
      "login": "octocat",
      "avatar_url": "https://github.com/images/error/octocat_happy.gif",
      "html_url": "https://github.com/octocat",
    },
    "private": false,
    "html_url": "https://github.com/octocat/Hello-World",
    "description": "This your first repo!",
    "fork": false,
    "url": "https://api.github.com/repos/octocat/Hello-World",
    "stargazers_url": "https://api.github.com/repos/octocat/Hello-World/stargazers",
    "subscribers_url": "https://api.github.com/repos/octocat/Hello-World/subscribers",
    "homepage": "https://github.com",
    "stargazers_count": 80,
    "watchers_count": 80,
    "size": 108,
    "is_template": false,
    "topics": [
      "octocat",
      "atom",
      "electron",
      "api"
    ],
    "visibility": "public",
    "pushed_at": "2011-01-26T19:06:43Z",
    "updated_at": "2011-01-26T19:14:43Z"
]
```

Please update the current `main.py` in this repo to fulfill this specification.

## 2. Update the Output

The script is working great!  Thanks.  Let's make these changes:

1. Remove newlines in default and compact output.

Right now the default and compact outputs have extra lines:

Default:

```bash
Found 30 repositories for user 'charmbracelet':

.github: Default community health files

bubbles: TUI components for Bubble Tea 🫧

bubbletea: A powerful little TUI framework 🏗

bubbletea-app-template: A template repository to create Bubble Tea apps.

catwalk: 🐈 A collection of LLM inference providers and models
```

Compact:

```bash
Found 30 repositories for user 'charmbracelet':

.github | Default community health files  | 2 stars

bubbles | TUI components for Bubble Tea 🫧 | 6694 stars

bubbletea | A powerful little TUI framework 🏗 | 33912 stars

bubbletea-app-template | A template repository to create Bubble Tea apps. | 202 stars

catwalk | 🐈 A collection of LLM inference providers and models  | 159 stars
```

Please remove the extra lines and start each line with a `-` for easier identification

## 3. Add Pagination

Right now the script is only reporting 30 repos for users that i know have more than 30 repos in place.  I think this may be do to paging by the API.  Is it possible to update the API call to check for more paging and then make additional calls?  When making paged calls, please send details to STDERR so the user knows what the script is doing while waiting for potentially long output.

## 4. Add Pagination Controls

OK! Pagination is working great.  Let's add switches to control pagination and the amount of data retrieved.

1. `-r, --repos-per-page NUMBER`: where `NUMBER` indicates the number of repos to request per page
1. `-p, --pages NUMBER`: where `NUMBER` indicates the number of pages to retrieve.  Processing should stop after this limit has been reached.
1. `-l, --limit NUMBER`: where `NUMBER` indicates the total number of repos to retrieve and/or list (since more may be retrieved given the pagination settings).
