# Blogger Spam Bulk Deleter

**The Problem:** My blog, [Adventures in Automation](https://www.tjmaher.com), collected over 11,000 spam comments over the past ten years, and unfortunately bare-bones Blogger.com does not have a bulk delete function. Through the Blogger UI, you can only delete a hundred at a time.

**The Solution:** Pair-programming with Claude.ai, we whipped up a quick Python script to get around this using the [Blogger API v3](https://developers.google.com/blogger/docs/3.0/reference), Google OAuth libraries, and some Google API Clients. The errors that appeared after running the code, I fed back to Claude, who then fixed the issues, and added some setup documentation I was able to muddle through.

So, now I have a Python project that works somehow, one I don't really understand. Since becoming an automation developer, I have worked on-the-job with Java, Ruby, JavaScript, and TypeScript, but not yet with Python.

Python, I haven't touched since grad school, which is a shame, since that seems to be a big gap on the old resume when it comes to the AI QA positions I've just started looking into.

---

## About the Author

Greetings! I'm **T.J. Maher** (Thomas F. Maher Jr.), a Software Development Engineer in Test (SDET) and QA Automation Engineer based in Boston. To better understand Python, I've been writing a detailed code walkthrough on my blog about this project Claude and I have cobbled together as part of my Python learning journey.

**Find me on:**
- **LinkedIn:** [linkedin.com/in/tjmaher1](https://www.linkedin.com/in/tjmaher1)
- **GitHub:** [github.com/tjmaher](https://github.com/tjmaher)
- **BlueSky:** [@tjmaher1](https://bsky.app/profile/tjmaher1.bsky.social)

[Adventures in Automation](https://www.tjmaher.com) documents my career arc from manual QA through test automation, and I'm currently looking into AI-assisted quality engineering. 

---

## Getting Started

This project expects Python 3.8 or later. It was tested on Python 3.14 on Windows.

**About Python:**
- **Official Website**: [python.org](https://www.python.org/)
- **Windows Installer**: [python.org/downloads/windows](https://www.python.org/downloads/windows/)
- **Documentation**: [docs.python.org/3](https://docs.python.org/3/)
- **Tutorial**: [docs.python.org/3/tutorial](https://docs.python.org/3/tutorial/index.html)

### Install Dependencies

Install the required packages using Python's Package Installer (pip), which fetches packages from the Python Package Index (PyPI):

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv
```

**What these packages do:**
- **google-api-python-client**: The official Google client library for Python that provides access to Google's REST APIs, including the Blogger API v3
- **google-auth-httplib2**: Adapter that connects Google's authentication library to httplib2, the HTTP client used by the API client
- **google-auth-oauthlib**: Handles the OAuth 2.0 authorization flow - opens a browser window for the first-time login, manages tokens automatically afterwards
- **python-dotenv**: Loads environment variables from a `.env` file to keep sensitive values out of your source code

As Claude noted: "google-api-python-client makes the API calls, google-auth-oauthlib + google-auth-httplib2 handle authenticating as your Google account, and python-dotenv keeps your OAuth credentials out of the script itself".

### Google Cloud Setup

Set up a free Google Cloud project to get API access:

1. Go to the [Google Cloud Console](https://console.cloud.google.com) and create a new project (or reuse an existing one)
2. Enable the **Blogger API v3**: [console.cloud.google.com/apis/library/blogger.googleapis.com](https://console.cloud.google.com/apis/library/blogger.googleapis.com)

### OAuth 2.0 Credentials (The Keys to Your Kingdom)

1. Navigate to **APIs & Services > Credentials**.
2. Click **+ Create Credentials > OAuth 2.0 Client ID**.
3. Choose **Desktop app** as the application type.
4. Download the generated JSON file and rename it to `client_secrets.json`
5. Place `client_secrets.json` in the same directory as the script

**Example of what the JSON structure looks like:**
```json
{
  "installed": {
    "client_id": "1234.apps.googleusercontent.com",
    "project_id": "maps-api-project-1234",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "ABC123",
    "redirect_uris": ["http://localhost"]
  }
}
```

The `client_id` and `client_secret` values will be unique to your project. Don't share this file or commit it to version control - treat it like a password that identifies your specific application to Google's servers.

### OAuth Consent Screen (Telling Google What You're Up To)

Configure the consent screen that users see when logging in. Go to **APIs & Services > OAuth consent screen**:

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

Leave the app in **Testing** status. Google verification is only required when the app will be used by people outside the test users list. Since you're the only one running this script, Testing status works indefinitely.

### Finding Your Blog ID (One More Quick Step)

Create an API key at **APIs & Services > Credentials > + Create Credentials > API key**. Restrict it to the Blogger API v3 only for security. Then call this URL in your browser (replacing the placeholders with your actual values):

```
https://www.googleapis.com/blogger/v3/blogs/byurl?url=https://YOUR-BLOG-URL&key=YOUR_API_KEY
```

The `id` field in the returned JSON is your Blog ID. You'll store this in your `.env` file in the next step.

---

## How To Keep Secrets Out of GitHub

> **Why this matters:** Credentials committed to a public GitHub repository are exposed to anyone on the internet. Automated bots scan GitHub continuously for API keys, OAuth secrets, and tokens. A leaked credential can be used to make API calls on your behalf, exhaust your quotas, or access your account data. GitHub's own documentation warns that once a secret is pushed, it should be considered compromised, even if you delete it immediately, because the git history retains it.

- GitHub Docs / Code Security / Secret Scanning: (https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning)

Secrets, Tokens, and Environment variables must never be committed to GitHub.

| File | Why it is sensitive |
|---|---|
| `client_secrets.json` | Contains your OAuth client ID and client secret, downloaded from Google Cloud Console. Anyone with this file can impersonate your application. |
| `token.json` | Written automatically after first authentication. Contains your OAuth access and refresh tokens, which grant direct access to your Blogger account. |
| `.env` | Contains your Blog ID and file paths. Less sensitive than the above, but keeping all configuration out of source control is the correct habit. |

The industry standard approach for managing this kind of configuration, according to Claude, is the **twelve-factor app** methodology, which states that [config should be stored in the environment](https://12factor.net/config), strictly separated from code.

**Sidenote:** Originally created by Heroku (2011), it's been adopted by cloud platforms (AWS, Google Cloud, Azure), major tech companies (Netflix, Spotify, Uber), and enterprise software providers (Salesforce, GitHub). It focuses on deployment and configuration practices rather than language-specific syntax.

The `python-dotenv` library ([pypi.org/project/python-dotenv](https://pypi.org/project/python-dotenv/)) implements this pattern for local development by loading values from a `.env` file into environment variables at runtime, so the script reads them without them ever being hardcoded in source.

### Step 1 - Create a `.env` file

In the same folder as the script, create a file named `.env`:

```
BLOG_ID=your_blog_id_here
CLIENT_SECRETS_FILE=client_secrets.json
```


### Step 2 - Create a `.gitignore` file (Your Safety Net)

In the same folder, create a file named `.gitignore`:

```
.env
client_secrets.json
token.json
```

Git reads `.gitignore` before staging files and silently excludes anything listed there. This is the standard mechanism for keeping secrets out of repositories. GitHub maintains a [collection of recommended `.gitignore` templates](https://github.com/github/gitignore) for common languages and frameworks. The [Python template](https://github.com/github/gitignore/blob/main/Python.gitignore) is a useful starting point for any Python project and represents community consensus on what Python files should never be committed (virtual environments, `__pycache__` directories, `.pyc` files, etc.).

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

## First Run - The Authentication Dance

The first time the script runs, it opens a browser window to Google's login page. After you log in and grant the Blogger scope, Google redirects back to the local server the script is running and you'll see:

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

## Rate Limits and What to Expect

The Blogger API v3 has two quota constraints to be aware of.

**Per-minute limits** apply to all API calls including list operations. The script handles this automatically: every list call has a 0.5-second pause after it completes, and both list and delete operations use exponential backoff (5s, 10s, 20s… up to 120s) with up to 6 retries on HTTP 429 and 5xx responses. This follows Google's official recommendation for [exponential backoff algorithms](https://developers.google.com/workspace/drive/api/guides/limits#exponential), which state that when you receive HTTP 403 or 429 responses, you should retry using exponentially increasing wait times.

**Daily quotas** vary by project and can be viewed in your [Google Cloud Console → APIs & Services → Blogger API v3 → Quotas](https://console.cloud.google.com/iam-admin/quotas). The default limits are typically sufficient for small-scale personal use, but large-scale comment deletion may require requesting quota increases through the console. Google's [quota documentation](https://developers.google.com/workspace/drive/api/guides/limits#increase) confirms that "not all projects have the same quotas" and that quota values can be increased based on resource usage patterns.

**Performance expectations**: The actual deletion speed depends on your quota allocation, the 0.5-second default delay between operations, and API response times. For large comment volumes, expect the process to take multiple sessions across several days unless you have increased quotas.


---

## Error Handling and Debugging

The script provides detailed error information when API calls fail, showing both the HTTP request that was attempted and the response received from Google's servers. This helps you understand exactly what's happening under the hood.

### Debug Mode

Enable detailed HTTP debugging with the `--debug` flag:

```bash
python delete_blogger_comments.py --dry-run --debug
```

This shows all HTTP requests and responses, including headers and timing information.

### HTTP Call Failure Reporting

When an API call fails, the script displays:
- **Request**: The exact HTTP method and URL that was attempted
- **Response**: The HTTP status code and error message returned by the server

#### Example Error Output

```
[ERROR] HTTP Call Failed:
Request: DELETE https://www.googleapis.com/blogger/v3/blogs/12345/posts/67890/comments/11111  
Response: HTTP 403 - Forbidden
```

#### Common Error Scenarios

| Status Code | Meaning | Action |
|---|---|---|
| `403 Forbidden` | Insufficient permissions or OAuth scope issues | Check OAuth consent screen configuration and ensure blogger scope is granted |
| `404 Not Found` | Comment already deleted or doesn't exist | Script treats this as success and continues |
| `429 Too Many Requests` | Rate limit exceeded | Script automatically retries after backoff period |
| `500/503 Server Error` | Temporary Google server issues | Script retries once after 60-second delay |

#### Retry Logic

For rate limits (`429`) and server errors (`500`/`503`), the script:
1. Shows the failed request details
2. Waits 60 seconds
3. Attempts the same request once more
4. If the retry also fails, shows both the original and retry error details

Example retry output:
```
[WARN] HTTP 429 - Too Many Requests - backing off 60 s then retrying...
Failed Request: DELETE https://www.googleapis.com/blogger/v3/blogs/12345/posts/67890/comments/11111

[ERROR] Retry failed: HTTP 429 - Too Many Requests
Failed Request: DELETE https://www.googleapis.com/blogger/v3/blogs/12345/posts/67890/comments/11111
```

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

Claude says: "[Claude](https://claude.ai) is an AI assistant made by [Anthropic](https://www.anthropic.com). It can read and write code, debug errors, explain APIs, draft documentation, and work iteratively with you as a development partner. 

"This project is a practical example of that workflow: a working Python script built from scratch through a back-and-forth conversation, with each error pasted back into the chat and resolved in the next reply. When I hit roadblocks or got cryptic error messages, I'd copy-paste them to Claude, who would then suggest fixes - often improving the code's robustness in the process".

Remember, although Claude speaks with the Voice of Authority, Claude is not an authority.
- Looking for technical information? Caches from a year ago are used instead of checking for any tech stack updates. 
- Need AI to recheck a web page after editing it with AI's suggestions? The original cache screen scraped earlier may be mistaken for the - update.
- Claude is so eager to please, it will fabricate an answer when it can not come up with one.

Review its answers. Be skeptical. Use critical thinking. Ask it to cite its sources.



**Essential practices when using Claude, According to Claude:**
- **Verify specific technical claims** against official documentation
- **Ask for sources** when Claude provides detailed specifications  
- **Stay skeptical** when something sounds too precise or authoritative
- **Check official APIs** rather than trusting Claude's technical details
- **Document corrections** so Claude can learn from its mistakes

"If you want to explore what Claude can do for your own testing and automation work, the starting point is [claude.ai](https://claude.ai). Just remember to always verify technical claims and check official documentation - even AI assistants can make mistakes!"

**Related reading:**
- [How I've Detected Claude's Fabrications and How I've Handled Them](https://www.tjmaher.com/2026/03/how-ive-detected-claudes-fabrications.html) - My experience catching and correcting AI fabrications during this project

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

---

## Wrapping Up

Claude says, "Whether you're dealing with your own spam comment problem or just curious about Python API development, I hope this project gives you some useful insights. For me, it was a great way to get my hands dirty with Python again and see how modern development workflows can incorporate AI assistance.

"The combination of Google's well-documented APIs, Python's excellent HTTP libraries, and careful defensive programming creates a tool that's both powerful and safe to use - exactly what you want when dealing with bulk operations on your precious blog content".

Happy testing!

-T.J. Maher  
Software Engineer in Test  
[BlueSky](https://bsky.app/profile/tjmaher1.bsky.social) | [LinkedIn](https://www.linkedin.com/in/tjmaher1) | [GitHub](https://github.com/tjmaher) | [Blog](https://www.tjmaher.com)
