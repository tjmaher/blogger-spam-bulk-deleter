"""
delete_blogger_comments.py
--------------------------
Deletes every comment on a Blogger blog via the Blogger API v3.

PREREQUISITES
-------------
1. Install dependencies:
       pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

2. Create a Google Cloud project and enable the Blogger API v3:
       https://console.cloud.google.com/apis/library/blogger.googleapis.com

3. Create OAuth 2.0 credentials (Desktop app type) and download the JSON file.
   Rename it to:  client_secrets.json
   Place it in the same directory as this script.

4. Set YOUR_BLOG_ID below.
   To find your Blog ID, visit:
       https://www.blogger.com/blog/posts/<your-blog-name>
   or call: GET https://www.googleapis.com/blogger/v3/blogs/byurl?url=https://www.tjmaher.com

RATE LIMIT WARNING
------------------
The default Blogger API quota is 10,000 units/day.
Each DELETE costs 50 units  =>  max ~200 deletions/day on the default quota.
With 11,000 comments you need to either:
  a) Request a quota increase at console.cloud.google.com > IAM & Admin > Quotas, OR
  b) Run the script over multiple days (it picks up where it left off via --dry-run
     first, then live runs once quota resets).

USAGE
-----
Dry run (prints what would be deleted, touches nothing):
    python delete_blogger_comments.py --dry-run

Live run:
    python delete_blogger_comments.py --delay 1.0

Live run, slower pace (2-second delay between deletions, safer for large quotas):
    python delete_blogger_comments.py --delay 2.0

Debug mode (shows detailed HTTP requests and responses):
    python delete_blogger_comments.py --dry-run --debug
"""

import argparse
import time
import sys
import logging

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── CONFIGURE THIS ────────────────────────────────────────────────────────────
YOUR_BLOG_ID        = os.getenv("BLOG_ID")
CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE", "client_secrets.json")
TOKEN_FILE          = "token.json"
# ─────────────────────────────────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/blogger"]

# Global debug flag
DEBUG_MODE = False

def debug_log(message):
    """Print debug messages only when debug mode is enabled."""
    if DEBUG_MODE:
        print(f"🔍 {message}")


def get_credentials():
    """Returns valid OAuth2 credentials, refreshing or prompting as needed."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def list_all_posts(service, blog_id):
    """Generator: yields every post dict for the given blog."""
    page_token = None
    while True:
        try:
            debug_log(f"API CALL: posts().list(blogId={blog_id}, pageToken={page_token}, maxResults=500)")
            resp = (
                service.posts()
                .list(
                    blogId=blog_id,
                    pageToken=page_token,
                    maxResults=500,
                    fields="items(id,title),nextPageToken",
                    status="LIVE",
                )
                .execute()
            )
            debug_log(f"API RESPONSE: Got {len(resp.get('items', []))} posts, nextPageToken={resp.get('nextPageToken')}")
        except HttpError as e:
            http_call = f"GET https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?pageToken={page_token}&maxResults=500&status=LIVE"
            error_msg = f"HTTP {e.resp.status} - {e.resp.reason}"
            debug_log(f"API ERROR: {error_msg}")
            print(f"\n[ERROR] HTTP Call Failed:")
            print(f"Request: {http_call}")
            print(f"Response: {error_msg}")
            if e.resp.status == 429:
                print(f"\n[ERROR] Daily API quota exceeded while listing posts.")
                print(f"The Blogger API has a daily limit of 10,000 units.")
                print(f"Please wait until tomorrow for the quota to reset, or")
                print(f"request a quota increase at: console.cloud.google.com > IAM & Admin > Quotas")
                sys.exit(1)
            else:
                raise
        
        for post in resp.get("items", []):
            yield post
        page_token = resp.get("nextPageToken")
        if not page_token:
            break


def list_all_comments(service, blog_id, post_id):
    """Generator: yields every comment dict for a given post."""
    page_token = None
    while True:
        try:
            debug_log(f"API CALL: comments().list(blogId={blog_id}, postId={post_id}, pageToken={page_token})")
            resp = (
                service.comments()
                .list(
                    blogId=blog_id,
                    postId=post_id,
                    pageToken=page_token,
                    maxResults=500,
                    fields="items(id,author/displayName,published),nextPageToken",
                    status="LIVE",
                )
                .execute()
            )
            debug_log(f"API RESPONSE: Got {len(resp.get('items', []))} comments, nextPageToken={resp.get('nextPageToken')}")
        except HttpError as e:
            http_call = f"GET https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/{post_id}/comments?pageToken={page_token}&maxResults=500&status=LIVE"
            error_msg = f"HTTP {e.resp.status} - {e.resp.reason}"
            debug_log(f"API ERROR: {error_msg}")
            print(f"\n[ERROR] HTTP Call Failed:")
            print(f"Request: {http_call}")
            print(f"Response: {error_msg}")
            if e.resp.status == 429:
                print(f"\n[ERROR] Daily API quota exceeded while listing comments.")
                print(f"The Blogger API has a daily limit of 10,000 units.")
                print(f"Please wait until tomorrow for the quota to reset, or")
                print(f"request a quota increase at: console.cloud.google.com > IAM & Admin > Quotas")
                sys.exit(1)
            else:
                raise
        
        for comment in resp.get("items", []):
            yield comment
        page_token = resp.get("nextPageToken")
        if not page_token:
            break


def delete_comment(service, blog_id, post_id, comment_id, dry_run, delay):
    """Deletes a single comment, or logs the action when in dry-run mode."""
    if dry_run:
        return  # nothing to do
    try:
        debug_log(f"API CALL: comments().delete(blogId={blog_id}, postId={post_id}, commentId={comment_id})")
        service.comments().delete(
            blogId=blog_id,
            postId=post_id,
            commentId=comment_id,
        ).execute()
        debug_log(f"API RESPONSE: Comment {comment_id} deleted successfully")
        time.sleep(delay)
    except HttpError as e:
        http_call = f"DELETE https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/{post_id}/comments/{comment_id}"
        error_msg = f"HTTP {e.resp.status} - {e.resp.reason}"
        debug_log(f"API ERROR: {error_msg}")
        if e.resp.status == 404:
            debug_log("Comment already gone - treating as success")
            # Already gone - treat as success
            pass
        elif e.resp.status in (429, 500, 503):
            # Rate limited or transient server error - back off and retry once
            print(f"    [WARN] {error_msg} - backing off 60 s then retrying...")
            print(f"    Failed Request: {http_call}")
            time.sleep(60)
            debug_log("RETRY: Attempting delete again after backoff")
            try:
                service.comments().delete(
                    blogId=blog_id,
                    postId=post_id,
                    commentId=comment_id,
                ).execute()
                debug_log(f"RETRY SUCCESS: Comment {comment_id} deleted on retry")
            except HttpError as retry_e:
                retry_error_msg = f"HTTP {retry_e.resp.status} - {retry_e.resp.reason}"
                print(f"    [ERROR] Retry failed: {retry_error_msg}")
                print(f"    Failed Request: {http_call}")
                raise retry_e
        else:
            print(f"\n[ERROR] HTTP Call Failed:")
            print(f"Request: {http_call}")
            print(f"Response: {error_msg}")
            raise


def main():
    parser = argparse.ArgumentParser(
        description="Delete all comments from a Blogger blog."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List comments that would be deleted without touching anything.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to sleep between each DELETE request (default: 0.5).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show detailed HTTP requests and responses for debugging.",
    )
    args = parser.parse_args()

    # Enable HTTP debugging if requested
    if args.debug:
        global DEBUG_MODE
        DEBUG_MODE = True
        import httplib2
        httplib2.debuglevel = 1
        logging.basicConfig(level=logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        print("🔍 HTTP debugging enabled - showing all API requests/responses\n")

    if YOUR_BLOG_ID == "PASTE_YOUR_BLOG_ID_HERE":
        print("ERROR: Set YOUR_BLOG_ID in the script before running.")
        sys.exit(1)

    creds = get_credentials()
    service = build("blogger", "v3", credentials=creds)

    mode_label = "DRY RUN" if args.dry_run else "LIVE"
    print(f"\n=== Blogger Comment Deletion [{mode_label}] ===")
    print(f"Blog ID : {YOUR_BLOG_ID}")
    print(f"Delay   : {args.delay}s between deletes\n")

    total_posts = 0
    total_comments = 0
    deleted = 0

    try:
        for post in list_all_posts(service, YOUR_BLOG_ID):
            total_posts += 1
            post_id = post["id"]
            post_title = post.get("title", "(no title)")
            post_comment_count = 0

            for comment in list_all_comments(service, YOUR_BLOG_ID, post_id):
                total_comments += 1
                post_comment_count += 1
                author = comment.get("author", {}).get("displayName", "unknown")
                cid = comment["id"]
                pub = comment.get("published", "")[:10]

                action = "WOULD DELETE" if args.dry_run else "DELETING"
                print(
                    f"  [{action}] Post: {post_title[:50]!r:52} "
                    f"| Comment #{cid} by {author[:20]} ({pub})"
                )

                delete_comment(
                    service,
                    YOUR_BLOG_ID,
                    post_id,
                    cid,
                    dry_run=args.dry_run,
                    delay=args.delay,
                )
                if not args.dry_run:
                    deleted += 1

            if post_comment_count:
                print(
                    f"  -> Post {post_id}: {post_comment_count} comment(s) processed.\n"
                )

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")

    print("\n=== Summary ===")
    print(f"Posts scanned    : {total_posts}")
    print(f"Comments found   : {total_comments}")
    if not args.dry_run:
        print(f"Comments deleted : {deleted}")
    else:
        print("No comments were deleted (dry-run mode).")
    print()


if __name__ == "__main__":
    main()
