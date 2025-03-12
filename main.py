from icecream import ic
from pyairtable import Api
from os import environ
from dotenv import load_dotenv
import praw
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




def get_reddit_info(username):
    try:
        user = reddit.redditor(username)
        status = "active" # default.
        if hasattr(user,"is_suspended"):
            ic("suspended alert!")
            status = "suspended"


        user_info = {
            "username":user.name,
            "status":status,
            "total karma":user.total_karma,

        }
        ic(user_info)
        posts = (list(user.submissions.new(limit = 3)))
        for post in posts:
            ic(post.score)
            ic(post.title)


    except Exception as e:
        ic(f"Error fetching data for {username}: {e}")
        user_info = {
            "username":username,
            "status":"error",
            "total karma": 0
        }
    return user_info


user1 = get_reddit_info("narutominecraft1")
user2 = get_reddit_info("Visual_Ad_2500")
users = [user1,user2]
users_for_upsert = [{"fields":user} for user in users] # needs to be formatted differently.
key_fields = ["username","status","total karma"]
table.batch_upsert(records=users_for_upsert,key_fields=key_fields)



# ToDo: Analyse the posts to get the date of the last released one.