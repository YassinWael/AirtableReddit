from icecream import ic
from pyairtable import Api
from os import environ
from dotenv import load_dotenv
import requests
from datetime import datetime
from time import sleep


def determine_status(user_data):

    if user_data.get("is_suspended"):
        status = "suspended"
    elif user_data['subreddit']['user_is_banned']:
        status = "banned"
    else:
        status = "active"
    return status


def get_reddit_info(username):
    
    """
    Makes a request to the Reddit API to get a user's information.

    Parameters
    ----------
   """
    headers = {"User-Agent":"Mozilla/5.0"}
    url = f"https://www.reddit.com/user/{username}/about.json"
    response = requests.get(url,headers)

    if response.status_code == 200:
        user_data = response.json()['data']
        ic(user_data)
        user_info = {
            "karma":user_data['total_karma'],
            "status":determine_status(user_data)
        }

        ic(user_info)
    elif response.status_code == 429:
        ic("Rate limited, trying again.")
        sleep(2)
        get_reddit_info(username)
    else:
        ic(response.status_code)
    return user_info






# load_dotenv()
# airtable_api = environ.get("airtable_token")
# ic(airtable_api)
# api = Api(airtable_api)
# table = api.table(table_name="reddit",base_id="appgEjnGN8uQYjgjq")
# print(table.all())