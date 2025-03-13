from icecream import ic
from pyairtable import Api
from os import environ
from dotenv import load_dotenv
import praw
from prawcore import NotFound
import pprint
from datetime import datetime
from dateutil.relativedelta import relativedelta

load_dotenv()
client_id = environ.get("client_id")
client_secret = environ.get("client_secret")
airtable_api = environ.get("airtable_token")
table_name = environ.get("table_name")
base_id = environ.get("base_id")



reddit = praw.Reddit(
    client_id = client_id,
    client_secret = client_secret,
    user_agent="python:reddit-airtable-sync:v1.0 (by u/narutominecraft1)"  # Custom User-Agent (change this)
)
api = Api(airtable_api)
table = api.table(table_name=table_name,base_id=base_id)



def get_account_age(user):
    """
    Given a Reddit user object, returns a string describing the user's account age as of the current time.
    
    The string is in the format "X year(s) and Y month(s)" if the user's account is at least a year old, or
    "X month(s)" if it is between 1 and 12 months old, or "X day(s)" if it is less than 1 month old.
    
    If the user object does not have a 'created' attribute, the function returns "N/A".
    """
    try:
        created = datetime.fromtimestamp(user.created)
        now = datetime.now()
        delta = relativedelta(now, created)
        if delta.years > 0:
            return f"{delta.years} year{'s' if delta.years != 1 else ''} and {delta.months} month{'s' if delta.months != 1 else ''}"
        elif delta.months > 0:
            return f"{delta.months} month{'s' if delta.months != 1 else ''}"
        else:
            return f"{delta.days} day{'s' if delta.days != 1 else ''}"
    except AttributeError:
        return "N/A"

def get_reddit_info(username):
    """
    Given a reddit username, returns a dictionary of information about that user.
    
    If the user is found, the dictionary will contain the following keys:
        - username: the username given to this function
        - status: The status of the user. Either "active", "banned", or "suspended"
        - age: the age of the account, in years, months, or days
        - comment_karma: the user's comment karma
        - post_karma: the user's post karma
        - total_karma: the sum of the user's comment and post karma
        - days_since_last_post: the time difference between the current time and the last post the user made,
            formatted as "X day(s) and Y hour(s)"
    
    If the user is not found, the dictionary will only contain the following keys:
        - username: the username given to this function
        - status: "error"
    
    If there is an unexpected error, the dictionary will contain the following keys:
        - username: the username given to this function
        - status: "error"
        - exception: the exception that was raised
    """
    user_info = {"username":username,"status":"error","age":"N/A","comment_karma":0,"post_karma":0,"total_karma":0} # default
    try:
        user = reddit.redditor(username)
        
        status = "active" # default.
        user_info.update(
            {
                "status":status,
                "age":get_account_age(user),
                "comment_karma":user.comment_karma,
                "post_karma":user.link_karma,
                "total_karma":user.total_karma
            }
        )
        # pprint(vars(user))
        posts = (list(user.submissions.new(limit = 1)))
        if posts:
            last_post = posts[0]
            # pprint.pprint(vars(last_post))
            
            time_difference = datetime.now() - datetime.fromtimestamp(last_post.created)
            user_info['days_since_last_post'] = f"{time_difference.days} day{'s' if time_difference.days!=1 else ''} and {time_difference.seconds // 3600} hours"
            user_info['last_post'] = last_post.url
            user_info['last_post_subreddit'] = last_post.subreddit_name_prefixed

        else:
            user_info['days_since_last_post'] = "No posts"
    except NotFound:
        user_info.update({"status":"banned",})
    except Exception as e:
        if hasattr(user,"is_suspended"):
            print(f"{username} has been recorded as suspended.")
            user_info.update({"status":"suspended"})
        else:
            print(f"Unexpected error for {username}: {e}")
            user_info.update({"status":"error"})
            


    
    print(f"Finished User: {username}. ({user_info['status']})")
    return user_info

# getting the list of usernames from airtable
all_users = table.all(fields = ['username'])
usernames = [user['fields']['username'] for user in all_users]


# sending the usernames to the reddit API
users = [get_reddit_info(user) for user in usernames] 

# mapping username from airtable to ID
existing_users = {user["fields"]['username']:user['id'] for user in all_users}

users_for_update = []
for user in users:
    if user['username'] in existing_users: #user already exists
        users_for_update.append({"id":existing_users[user['username']],"fields":user})

    else: #user doesn't exist
        table.create(user)

if users_for_update:
    table.batch_update(records=users_for_update)







