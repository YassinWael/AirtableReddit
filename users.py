from pprint import pprint
from icecream import ic
from pyairtable import Api
from os import environ
from dotenv import load_dotenv
import praw
from prawcore import NotFound
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

load_dotenv()
client_id = environ.get("client_id")
client_secret = environ.get("client_secret")


airtable_api = environ.get("client_airtable_token")
table_name = environ.get("client_table_name")
base_id = environ.get("client_base_id")
start_time = time.time()


reddit = praw.Reddit(
    client_id = client_id,
    client_secret = client_secret,
    user_agent="python:reddit-airtable-sync:v1.0 (by u/narutominecraft1)"  # Custom User-Agent (change this)
)
api = Api(airtable_api)
table = api.table(table_name=table_name,base_id=base_id)

accounts_table = api.table(table_name="Accounts",base_id=base_id)

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

def get_reddit_info(username,table_name=""):
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
    user_info = {"Username":username,"Status":"Error","Age":"N/A","Comment_karma":0,"Post_karma":0,"Total_karma":0} # default
    try:
        user = reddit.redditor(username)
        print(user_status.get(username).strip().lower())
        Status = "Farming" if user_status.get(username).strip().lower()=="farming" else "Active"
        ic(Status)
        user_info.update(
            {
                "Status":Status,
                "Age":get_account_age(user),
                "Comment_karma":user.comment_karma,
                "Post_karma":user.link_karma,
                "Total_karma":user.total_karma
            }
        )
        posts = (list(user.submissions.new(limit = 4)))
        non_pinned_posts = [post for post in posts if not post.pinned]
        if posts and table_name=="": # to make sure we're not on the accounts table
            last_post = non_pinned_posts[0] if non_pinned_posts else None
            
         
            
            time_difference = datetime.now() - datetime.fromtimestamp(last_post.created)
            user_info['Days_since_last_post'] = f"{time_difference.days} day{'s' if time_difference.days!=1 else ''} and {time_difference.seconds // 3600} hours"
            user_info['Last_post'] = last_post.url
            user_info['Last_post_subreddit'] = last_post.subreddit_name_prefixed

        else:
            if table_name=="":
                user_info['Days_since_last_post'] = "No posts"
    except NotFound:
        user_info.update({"Status":"Banned"})
    except Exception as e:
        if hasattr(user,"is_suspended"):
            print(f"{username} has been recorded as suspended.")
            user_info.update({"Status":"Suspended"})
        else:
            print(f"Unexpected error for {username}: {e}")
            user_info.update({"Status":"Error"})
            


    
    print(f"Finished User: {username}. ({user_info['Status']})")
    return user_info

# getting the list of usernames from airtable
all_users = table.all(fields = ['Username','Status'])
usernames = [user['fields']['Username'] for user in all_users]
user_status = {user['fields']['Username']:user['fields']['Status'] for user in all_users}


# sending the usernames to the reddit API
users = [get_reddit_info(user) for user in usernames] 

# mapping username from airtable to ID
existing_users = {user["fields"]['Username']:user['id'] for user in all_users}
ic(existing_users)
users_for_update = []
for user in users:
    if user['Username'] in existing_users: #user already exists
        users_for_update.append({"id":existing_users[user['Username']],"fields":user})

    else: #user doesn't exist
        table.create(user)

if users_for_update:
    table.batch_update(records=users_for_update)
users_for_update = []
user_status = {}
print("Finished the Active Accounts table, starting the Accounts one...")




# update the accounts table
all_users = accounts_table.all(fields = ['Username','Status'])
existing_users = {user['fields']['Username']:user['id'] for user in all_users}
user_status = {user['fields']['Username']:user['fields']['Status'] for user in all_users}


usernames = [user['fields']['Username'] for user in all_users]
users = [get_reddit_info(user,table_name="accounts") for user in usernames]

# modify the users for the accounts table
for user in users:

    del user["Age"]
   
    account_status = user.pop("Status")
    
    user = {"Status":account_status,**user}
   
   
    if user['Username'] in existing_users:
        users_for_update.append({"id":existing_users[user['Username']],"fields":user})

if users_for_update:
    accounts_table.batch_update(records=users_for_update)





end_time = time.time()
print(f"It took {round(end_time - start_time,2)} seconds to run this script.")
