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
    return user_info


naruto = get_reddit_info("myvirginityisstrong")

table.create(naruto)
# ToDo: Analyse the posts to get the date of the last released one.