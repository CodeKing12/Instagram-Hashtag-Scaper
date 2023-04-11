import json

with open("store-iterated-posts.json", "r") as iter_posts:
    check = []
    for post in json.loads(iter_posts.read()):
        if post["followers"] > 15000:
            check.append(post)
    print(len(check))