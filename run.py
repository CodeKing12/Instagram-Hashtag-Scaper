import instaloader
from instaloader.nodeiterator import resumable_iteration, FrozenNodeIterator
from instaloader.exceptions import AbortDownloadException
import random
import traceback
import sys
import json
from json import dumps as dump_json
from json import loads as load_json
from datetime import datetime, timedelta

settings = load_json(open("settings.json").read())
username = settings['username']
password = settings['password']
quantity_needed = 165

# Create an instance of Instaloader class
L = instaloader.Instaloader()

print("Logging In...")
# L.login(username, password)
# Refresh cookies by logging in again using the firefox script, then load the session here. It's more likely to work than running the firefox script here
L.load_session_from_file(username)
print("Logged in. Saving Session...")
hashtag_posts = []

# Set a niche for the pages we want to scrape
niche = settings['niche']

def fetchPostsData(session, hashtag):
    print("Fetching posts data...")

    jsonData = session.context.get_json(path="explore/tags/" + hashtag + "/", params={"__a": 1})
    hasNextPage = True
    pageNumber = 1

    while hasNextPage:
        print("Page " + str(pageNumber))
        sections = jsonData['data']['top']['sections']

        for section in sections:
            for post in section['layout_content']['medias']:
                likes = post['media']['like_count']
                print(likes)

                if likes >= 900:
                    username = post['media']['user']['username']
                    # timestamp = datetime.fromtimestamp(post['media']['taken_at']).date()
                    timestamp = datetime.fromtimestamp(post['media']['taken_at']).ctime()
                    code = post['media']['code']
                    comments = post['media']['comment_count']
                    mediaid = post['media']['id']
                    
                    data = {
                        "id": mediaid,
                        "username": username,
                        "shortcode": code,
                        "likes": likes,
                        "comments": comments,
                        "date": timestamp
                    }
                    print(data)
                    hashtag_posts.append(data)                

        hasNextPage = jsonData['data']['top']['more_available']
        if hasNextPage:
            jsonData = session.context.get_json(
                path="explore/tags/" + hashtag + "/",
                params={"__a": 1,
                        "max_id": jsonData['data']['top']['next_max_id']}
            )
        pageNumber += 1

# Get the top posts in the niche by searching for the niche as a hashtag
def getByIterator():
    post_iterator = instaloader.NodeIterator(
        L.context, "9b498c08113f1e09617a1703c22b2f32",
        lambda d: d['data']['hashtag']['edge_hashtag_to_media'],
        lambda n: instaloader.Post(L.context, n),
        {'tag_name': niche},
        f"https://www.instagram.com/explore/tags/{niche}/"
    )

    retrieved_posts = []
    try:
        with resumable_iteration(
            context=L.context,
            iterator=post_iterator,
            load=lambda _, path: FrozenNodeIterator(**json.load(open(path))),
            save=lambda fni, path: json.dump(fni._asdict(), open(path, 'w')),
            format_path=lambda magic: "resume_info_{}.json".format(magic)
        ) as (is_resuming, start_index):
            for post in post_iterator:
                if len(retrieved_posts) < quantity_needed:
                    if post.likes >= 900:
                        retrieved_posts.append({
                            "id": post.mediaid,
                            "shortcode": post.shortcode,
                            "username": post.owner_profile.username,
                            "followers": post.owner_profile.followers,
                            "likes": post.likes,
                            "comments": post.comments,
                            "date": post.date.ctime()
                        })
                        print("--------------------")
                        print(len(retrieved_posts))
                        print(post.mediaid)
                        print("--------------------")
                    else:
                        print(post.likes)
                else:
                    print(f"{len(retrieved_posts)} posts scraped successfully")
                    raise AbortDownloadException

    except AbortDownloadException:
        with open("store-iterated-posts.json", "w") as posts_db:
            posts_db.write("\n\n")
            posts_db.write(dump_json(retrieved_posts))

        check_usernames = []
        filename = f"{username}_{niche}_{quantity_needed}.json"
        for post in retrieved_posts:
            if post["followers"] > 15000:
                check_usernames.append(post["username"])
        with open(f"output/{filename}", "x") as username_file:
            username_file.write(dump_json(check_usernames))
        print(f"\n{len(check_usernames)} usernames collected and saved to {filename}\n")

    except Exception as e:
        with open("store-iterated-posts.json", "a") as posts_db:
            posts_db.write("\n\n")
            posts_db.write(dump_json(retrieved_posts))
        print("Oh no, an error occured:")
        print(traceback.format_exc())


getByIterator()
sys.exit()
# Find a way to extract at least 150 posts with >= 900 likes so that you can filter them.
try:
    top_posts = fetchPostsData(L, niche)
except Exception as e:
    with open("store-posts.json", "w") as posts_db:
        posts_db.write(dump_json(hashtag_posts))
    print("Oh no, an error occured:")
    print(traceback.format_exc())
    # print(e.with_traceback())

# with open("store-posts.json", "w") as posts_db:
#     posts_db.write(dump_json(hashtag_posts))
print("Top posts acquired")
# top_posts = list(top_posts)
# print(len(top_posts))
# print(top_posts)


# Select pages with 15k-500k followers
# pages = []
# for post in top_posts:
#     print("---------------------------")
#     print(post.caption)
#     print("---------------------------")
#     likes = post.likes
#     if likes >= 900 and post.date > (datetime.now() - timedelta(days=30)):
#         engagement_rate = (likes / post.owner_profile.followers) * 100
#         if engagement_rate > 3 and 15000 <= post.owner_profile.followers <= 500000:
#             pages.append({
#                 "owner": post.owner_username,
#                 "followers": post.owner_profile.followers,
#             })
#             open("database.json", "w").write(dump_json(pages))

# Randomly select 100 pages from the list of pages

# Scrape each page and save its data to a file
# for page in random_pages:
#     try:
#         profile = instaloader.Profile.from_username(L.context, page.username)
#         L.download_profile(profile, profile_pic_only=True)
#     except:
#         pass
