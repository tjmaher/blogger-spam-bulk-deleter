# Blogger Comment Deleter

A Python script that deletes all comments from a Blogger blog using the
[Blogger API v3](https://developers.google.com/blogger/docs/3.0/reference).

This script was written with the assistance of **Claude** (claude.ai), Anthropic's AI assistant. Claude provided suggessions for the OAuth flow, debugged the API errors encountered during development, and improved the retry and rate-limit handling based on live error output.

---

## Background

**T.J. Maher** (Thomas F. Maher Jr.) is a Software Development Engineer in Test (SDET) and QA Automation Engineer based in Bridgewater, MA. His core stack has been for the last ten years Java, Ruby, JavaScript, and TypeScript, but not Python. To fix this, T.J. is in the process of writing a very detailed code walkthrough on his blog, [Adventures in Automation](https://www.tjmaher.com).  

T.J is also the author of the Test Automation University course
[Introduction to Capybara](https://testautomationu.applitools.com/capybara-ruby/)
and a contributing author to
[Continuous Testing for DevOps Professionals](https://www.amazon.com/dp/1789953847)
(Packt, 2019).

- **LinkedIn:** [linkedin.com/in/tjmaher1](https://www.linkedin.com/in/tjmaher1)
- **GitHub:** [github.com/tjmaher](https://github.com/tjmaher)
- **BlueSky:** [@tjmaher1](https://bsky.app/profile/tjmaher1.bsky.social)

[Adventures in Automation](https://www.tjmaher.com) is T.J.'s software testing blog, running since 2015, documents his career arc from manual QA through test automation, and currently looking into AI-assisted quality engineering.

Over the past ten years his blog accumulated roughly 11,000 spam comments that needed to be cleared out in bulk. The Blogger web UI has no bulk-delete feature.

This project handles that problem. 

---

## Prerequisites

### 1. Python

Python 3.8 or later. Tested on Python 3.14 on Windows.

### 2. Dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv
```

### 3. Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com) and
   create a new project (or reuse an existing one).
2. Enable the **Blogger API v3**:
   [console.cloud.google.com/apis/library/blogger.googleapis.com](https://console.cloud.google.com/apis/library/blogger.googleapis.com)

### 4. OAuth 2.0 Credentials

1. Navigate to **APIs & Services > Credentials**.
2. Click **+ Create Credentials > OAuth 2.0 Client ID**.
3. Choose **Desktop app** as the application type.
4. Download the generated JSON file and rename it to `client_secrets.json`.
5. Place `client_secrets.json` in the same directory as the script.

### 5. OAuth Consent Screen

Configure the consent screen at **APIs & Services > OAuth consent screen**:

| Field | Value |
|---|---|
| User type | External |
| App name | `Blogger Comment Deleter` |
| User support email | your Gmail address |
| App domain | your blog URL |
| Developer contact email | your Gmail address |
| Scopes | `https://www.googleapis.com/auth/blogger` |
| Test users | your Gmail address |
| Publishing status | Testing (no verification needed) |

Leave the app in **Testing** status. Google verification is only required
when the app will be used by people outside the test users list.

### 6. Your Blog ID

Create an API key at **APIs & Services > Credentials > + Create Credentials > API key**.
Restrict it to the Blogger API v3 only. Then call this URL in your browser:

```
https://www.googleapis.com/blogger/v3/blogs/byurl?url=https://YOUR-BLOG-URL&key=YOUR_API_KEY
```

The `id` field in the returned JSON is your Blog ID. You will store it in
your `.env` file in the next step.

---

## Keeping Secrets Out of GitHub

> **Why this matters:** Credentials committed to a public GitHub repository
> are exposed to anyone on the internet. Automated bots scan GitHub
> continuously for API keys, OAuth secrets, and tokens. A leaked credential
> can be used to make API calls on your behalf, exhaust your quotas, or
> access your account data. GitHub's own documentation warns that
> [once a secret is pushed, it should be considered compromised](https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning),
> even if you delete it immediately, because the git history retains it.

This project uses three files that must never be committed:

| File | Why it is sensitive |
|---|---|
| `client_secrets.json` | Contains your OAuth client ID and client secret, downloaded from Google Cloud Console. Anyone with this file can impersonate your application. |
| `token.json` | Written automatically after first authentication. Contains your OAuth access and refresh tokens, which grant direct access to your Blogger account. |
| `.env` | Contains your Blog ID and file paths. Less sensitive than the above, but keeping all configuration out of source control is the correct habit. |

The industry standard approach for managing this kind of configuration is
the **twelve-factor app** methodology, which states that
[config should be stored in the environment](https://12factor.net/config),
strictly separated from code. The `python-dotenv` library
([pypi.org/project/python-dotenv](https://pypi.org/project/python-dotenv/))
implements this pattern for local development by loading values from a
`.env` file into environment variables at runtime, so the script reads
them without them ever being hardcoded in source.

### Step 1 - Create a `.env` file

In the same folder as the script, create a file named `.env`:

```
BLOG_ID=your_blog_id_here
CLIENT_SECRETS_FILE=client_secrets.json
```

No quotes around the values. No spaces around the `=` sign.

### Step 2 - Create a `.gitignore` file

In the same folder, create a file named `.gitignore`:

```
.env
client_secrets.json
token.json
```

Git reads `.gitignore` before staging files and silently excludes anything
listed there. This is the standard mechanism for keeping secrets out of
repositories. GitHub maintains a
[collection of recommended `.gitignore` templates](https://github.com/github/gitignore)
for common languages and frameworks. The
[Python template](https://github.com/github/gitignore/blob/main/Python.gitignore)
is a useful reference for any Python project.

> **Before your first commit**, run `git status` and confirm that `.env`,
> `client_secrets.json`, and `token.json` do not appear in the list of
> files to be staged. If they do appear, your `.gitignore` is not in the
> right place or has a typo.

### Step 3 - Create a `.env.example` file

This file is safe to commit. It tells anyone who clones the repository
which values they need to supply, without exposing yours:

```
BLOG_ID=your_blog_id_here
CLIENT_SECRETS_FILE=client_secrets.json
```

The `.env.example` convention is widely used across open source projects.
The [python-dotenv documentation](https://saurabh-kumar.com/python-dotenv/#file-format)
recommends this pattern explicitly. It serves as both documentation and a
template that contributors can copy directly to create their own `.env`.

### Step 4 - Update the script

The script reads from the `.env` file using `python-dotenv`. The relevant
block near the top of `delete_blogger_comments.py` looks like this:

```python
from dotenv import load_dotenv

load_dotenv()

YOUR_BLOG_ID        = os.getenv("BLOG_ID", "")
CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE", "client_secrets.json")
TOKEN_FILE          = "token.json"
```

`load_dotenv()` reads the `.env` file and populates `os.environ` with its
values. `os.getenv()` then reads those values by name. The second argument
is a fallback default used if the variable is not set. This is standard
Python - the
[os.getenv documentation](https://docs.python.org/3/library/os.html#os.getenv)
covers the full signature.

---

## First Run - Authentication

The first time the script runs it opens a browser window to Google's login
page. After you log in and grant the Blogger scope, Google redirects back
to the local server the script is running and you will see:

```
The authentication flow has completed. You may close this window.
```

Close that browser tab. The script writes your credentials to `token.json`
and proceeds. Every subsequent run reads `token.json` directly and skips
the browser step unless the token has expired.

---

## Usage

### Dry run (recommended first step)

Prints every comment that would be deleted. Touches nothing.

```bash
python delete_blogger_comments.py --dry-run
```

### Live run

```bash
python delete_blogger_comments.py
```

### Live run with a longer delay between deletions

```bash
python delete_blogger_comments.py --delay 2.0
```

The `--delay` value is the number of seconds to sleep between each `DELETE`
request. The default is `0.5`. A longer delay reduces the chance of hitting
per-minute quota limits during large runs.

---

## Rate Limits

The Blogger API v3 has two quota constraints to be aware of.

**Per-minute limit** applies to all API calls including list operations.
The script handles this automatically: every list call has a 0.5-second
pause after it completes, and both list and delete operations use
exponential backoff (5s, 10s, 20s... up to 120s) with up to 6 retries on
HTTP 429 and 5xx responses.

**Daily quota** is 10,000 units per day by default. Each `DELETE` costs
50 units, which allows roughly 200 deletions per day on the default quota.
At that rate, 11,000 comments would take approximately 55 days.

To avoid this, request a quota increase at:

> console.cloud.google.com > APIs & Services > Blogger API v3 > Quotas

Google typically approves increases for clearly legitimate use cases. With
an approved higher quota and the default 0.5-second delay, a full 11,000-
comment run completes in well under an hour.

---

## Output

```
=== Blogger Comment Deletion [DRY RUN] ===
Blog ID : 3868566217808655382
Delay   : 0.5s between deletes

  [WOULD DELETE] Post: 'Some post title'   | Comment #12345 by SomeUser (2021-03-15)
  [WOULD DELETE] Post: 'Some post title'   | Comment #12346 by AnotherUser (2021-03-16)
  -> Post 2702750598806372610: 2 comment(s) processed.

=== Summary ===
Posts scanned    : 847
Comments found   : 11243
No comments were deleted (dry-run mode).
```

---

## File Layout

```
Blogger comment deleter/
    delete_blogger_comments.py   ✅ commit this
    README.md                    ✅ commit this
    .gitignore                   ✅ commit this
    .env.example                 ✅ commit this
    .env                         🚫 never commit (listed in .gitignore)
    client_secrets.json          🚫 never commit (listed in .gitignore)
    token.json                   🚫 never commit (listed in .gitignore)
```

---

## About Claude

[Claude](https://claude.ai) is an AI assistant made by
[Anthropic](https://www.anthropic.com). It can read and write code, debug
errors, explain APIs, draft documentation, and work iteratively with you
as a development partner. This project is a practical example of that
workflow: a working Python script built from scratch through a back-and-
forth conversation, with each error pasted back into the chat and resolved
in the next reply.

If you want to explore what Claude can do for your own testing and
automation work, the starting point is [claude.ai](https://claude.ai).

---

## Further Reading

### Environment Variables and `.env` Files

- [python-dotenv - Official Docs](https://saurabh-kumar.com/python-dotenv/) - The authoritative reference for `load_dotenv()`, file format rules, variable expansion, and the CLI interface.
- [python-dotenv - GitHub Repository](https://github.com/theskumar/python-dotenv) - Source code, issue tracker, and the most current usage examples including the recommended `.gitignore` guidance.
- [python-dotenv - PyPI](https://pypi.org/project/python-dotenv/) - Install page with version history and dependency information.
- [The Twelve-Factor App: Config](https://12factor.net/config) - The methodology that established storing config in the environment as a best practice. Written by Heroku engineers in 2011 and still the foundational reference on this topic.
- [GitHub Secret Scanning: About Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning) - GitHub's official explanation of why committed secrets must be treated as permanently compromised, even after deletion.
- [GitHub: gitignore templates](https://github.com/github/gitignore) - The official collection of `.gitignore` templates maintained by GitHub. The [Python template](https://github.com/github/gitignore/blob/main/Python.gitignore) covers virtual environments, build artifacts, and local config files.

### Blogger API v3

- [Blogger API v3 - Introduction](https://developers.google.com/blogger) - Overview of what the API can do and links to getting started materials.
- [Blogger API v3 - Getting Started](https://developers.google.com/blogger/docs/3.0/getting_started) - Covers the five core resource types (Blogs, Posts, Comments, Pages, Users), supported operations, and URI structure.
- [Blogger API v3 - Using the API](https://developers.google.com/blogger/docs/3.0/using) - Practical guide to making requests, authenticating, and working with collections.
- [Blogger API v3 - Reference](https://developers.google.com/blogger/docs/3.0/reference/) - Full reference for all resource types and methods.
- [Blogger API v3 - Comments: delete](https://developers.google.com/blogger/docs/3.0/reference/comments/delete) - The specific endpoint this script calls. Documents required parameters (`blogId`, `postId`, `commentId`) and the required OAuth scope.

### Rate Limits and Quotas

- [Google Cloud Console - Quotas](https://console.cloud.google.com/iam-admin/quotas) - The live view of your project's current quota usage and the interface for requesting increases. Requires login. Filter by "Blogger" to find the relevant limits.
- [Google APIs - Handling Errors](https://developers.google.com/blogger/docs/3.0/using#WorkingWithErrors) - The Blogger API's error handling guide, covering `400`, `401`, `403`, and `503` responses and recommended retry behavior.
- [Google APIs - Exponential Backoff](https://developers.google.com/analytics/devguides/reporting/core/v3/errors#backoff) - Google's own recommendation for handling quota errors with exponential backoff. Written for the Analytics API but the pattern is identical to what this script implements.

### Python Standard Library

- [`os.getenv`](https://docs.python.org/3/library/os.html#os.getenv) - Reads an environment variable by name, with an optional default value if the variable is not set.
- [`time.sleep`](https://docs.python.org/3/library/time.html#time.sleep) - Pauses execution for a given number of seconds. Used here to throttle request rate.
- [`argparse`](https://docs.python.org/3/library/argparse.html) - The standard library module used to parse `--dry-run` and `--delay` from the command line.
- [Exception Handling (`try`/`except`)](https://docs.python.org/3/tutorial/errors.html) - Python's official tutorial on catching and handling exceptions, including the pattern used in `api_call_with_retry`.

### Google Auth Libraries for Python

- [google-auth](https://google-auth.readthedocs.io/en/master/) - The base authentication library. Handles token refresh and credential management.
- [google-auth-oauthlib](https://google-auth-oauthlib.readthedocs.io/en/latest/) - Provides `InstalledAppFlow`, which opens the browser for the initial OAuth consent and writes `token.json`.
- [google-api-python-client](https://googleapis.github.io/google-api-python-client/docs/) - The client library that wraps the Blogger REST API into Python method calls like `service.comments().delete()`.
