from icecream import ic
from pyairtable import Api
from os import environ
from dotenv import load_dotenv
import praw
from prawcore import NotFound
import pprint
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

load_dotenv()

client_id = environ.get("client_id")
client_secret = environ.get("client_secret")
airtable_api = environ.get("airtable_token")
table_name = environ.get("table_name")
posts_table_name = environ.get("posts_table_name")
base_id = environ.get("base_id")
start_time = time.time()

reddit = praw.Reddit(
    client_id = client_id,
    client_secret = client_secret,
    user_agent="python:reddit-airtable-sync:v1.0 (by u/narutominecraft1)"  # Custom User-Agent (change this)
)
api = Api(airtable_api)
users_table = api.table(table_name=table_name,base_id=base_id)
posts_table = api.table(table_name=posts_table_name,base_id=base_id)

def get_posts_by_user(username):
    try:
        user = reddit.redditor(username)
        posts = user.submissions.new(limit = 3)
        return list(posts)
    except Exception as e:
        print(f"Error when processing the user {username}: {e}")
        return []


# get the usernames from the airtable to scrape the posts.
all_users = users_table.all(fields="username",formula="status='active'")
usernames = [user['fields']['username'] for user in all_users]
existing_users = {user['fields']['username'].lower():user['id'] for user in all_users}
ic(existing_users)


# get all posts using the users
posts = []
all_posts = [get_posts_by_user(username) for username in usernames] # list of lists
for user_posts in all_posts:
    for post in user_posts:
        posts.append(post)


## load each post into airtable.

posts_to_upload = []
for post in posts:
    if post.author.name.lower() in [user.lower() for user in existing_users]:
        account_record_id = existing_users[post.author.name.lower()]
    else:
        print(f"Warning: No record found for {post.author.name}, skipping...")
        continue
    post_data = {
        "Account": [account_record_id],  # Must be a list of record IDs
        "Subreddit": post.subreddit_name_prefixed,
        "Status": "",
        "Upvotes": post.ups,
        "Title": post.title,
        "post_link": post.url,
        "Media": post.media.get("fallback_url") if post.media else "",
        "Content": post.selftext
    }
    posts_to_upload.append(post_data)


posts_table.batch_create(posts_to_upload)


end_time = time.time()
print(f"This script took {end_time - start_time:.2f} seconds to execute.")


# ToDo: Fix the .lower() thing when matching usernames and id
# ToDo: Fix the Media never loading

 
