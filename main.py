from icecream import ic
from pyairtable import Api
from os import environ
from dotenv import load_dotenv
import praw
import pprint
from datetime import datetime
load_dotenv()
client_id = environ.get("client_id")
client_secret = environ.get("client_secret")
airtable_api = environ.get("airtable_token")


reddit = praw.Reddit(
    client_id = client_id,
    client_secret = client_secret,
    user_agent="test by u/narutominecraft1"  # Custom User-Agent (change this)
)
api = Api(airtable_api)
table = api.table(table_name="reddit",base_id="appgEjnGN8uQYjgjq")


def get_account_age(user):
    try:
        age_created = datetime.fromtimestamp(user.created)
        time_now = datetime.now()
        account_age = time_now - age_created
        if account_age.days > 30:
            months_since_creation = account_age.days // 30
            if months_since_creation>12:
                years_since_creation = months_since_creation // 12
                remainder_months = round(months_since_creation % 12)
                ic(years_since_creation,remainder_months)

                if years_since_creation!=1:
                    account_age = f"{years_since_creation} years and {remainder_months} months."
                else:
                    account_age = f"{years_since_creation} year and {remainder_months} months."
            else:
                account_age = f"{months_since_creation} months" if months_since_creation!=1 else f"{months_since_creation} month"
        else:
            account_age = f"{account_age.days} days" if account_age.days!=1 else f"{account_age.days} day"


        
    except Exception as e:
        account_age = ""
    return account_age



def get_reddit_info(username):
    try:
        try:
            user = reddit.redditor(username)
            
            
        except Exception as e: #banned or deleted
            user_info = {
            "username":username,
            "status":"banned",
            "age":get_account_age(user),
            "comment_karma":0,
            "post_karma":0,
            "total_karma": 0
        }

        status = "active" # default.
        


     
        posts = (list(user.submissions.new(limit = 3)))
        for post in posts:
            time_created = datetime.fromtimestamp(post.created)
            time_now = datetime.now()
            time_difference = time_now - time_created
            hours_since_last_post = round(time_difference.seconds / 3600) #excluding days.

            if time_difference.days!=1 or time_difference==0:
                days_since_last_post = f"{time_difference.days} days and {hours_since_last_post} hours."
            else:
                days_since_last_post = f"{time_difference.days} day and {hours_since_last_post} hours."

            
        user_info = {
            "username":user.name,
            "status":status,
            "age":get_account_age(user),
            "comment_karma":user.comment_karma,
            "post_karma":user.link_karma,
            "total_karma":user.total_karma,
            "days_since_last_post":days_since_last_post

        }

        pprint.pprint(vars(user))
    
    except Exception as e:
        print(f"Error fetching data for {username}: {e}")

        user_info = {
            "username":username,
            "status":"error",
            "age":get_account_age(user),
            "comment_karma":0,
            "post_karma":0,
            "total_karma": 0
        }
        if "403" in str(e):
            user_info = {
            "username":username,
            "status":"suspended",
            "age":get_account_age(user),
            "comment_karma":0,
            "post_karma":0,
            "total_karma": 0
        }
    print(f"Finished User: {username}.")
    return user_info


all_users = table.all()

users_for_update = []
user1 = get_reddit_info("narutominecraft1")
user2 = get_reddit_info("Visual_Ad_2500")
user3 = get_reddit_info("Pepower97")
user4 = get_reddit_info("myvirginityisstrong")
users = [user1,user2,user3,user4] 



for i,user in enumerate(users):
    try:
        new_user = {
            "id":all_users[i]["id"],
            "fields": user
        }
        users_for_update.append(new_user)
    except IndexError: # user isn't in the table.
        table.create(user)



table.batch_update(records=users_for_update)



# ToDo: Analyse the posts to get the date of the last released one.
