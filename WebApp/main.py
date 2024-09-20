import flask
import regex as re

import asyncio
import aiohttp

import bs4

import tf_keras
import tensorflow as tf

OPINION_DB = "./user_entry_db/opinion.csv"

app = flask.Flask(__name__)

async def process(title, text):
    flask.session["focus_title"] = title
    flask.session["focus_text"] = text

    final_content = ["[TITLE]" + title + "[TEXT]" + text]
    if len(text.split()) < 24:
        # Not enough words to make a conclusion
        return flask.render_template("failed.html", message="We don't support dynamically generated web pages, enter the title and content manually")
    model = tf_keras.models.load_model("../NLP/model/model_v1.2.keras")
    result = model.predict([final_content])[0][0]
    score = round((1-result) * 100)
    if score > 70:
        return flask.render_template("check_hq.html", title=title, score=score, content=final_content[0])
    elif score > 30:
        return flask.render_template("check_mq.html", title=title, score=score, content=final_content[0])
    else:
        return flask.render_template("check_lq.html", title=title, score=score, content=final_content[0])

@app.route("/")
async def index():
    return flask.render_template("index.html")

@app.route("/check", methods = ["GET", "POST"])
async def check():
    if flask.request.method == "GET":
        return flask.redirect("/", code=302)
    url = flask.request.form.get("url")
    if url:
        if re.fullmatch(r"http[s]?:\/\/[A-Za-z][A-Za-z0-9\.]*\/[A-Za-z0-9\/#\-_\.?=&:]*", url):
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    rawHTML = await resp.content.read()
            soup = bs4.BeautifulSoup(rawHTML, "html.parser")
            
            title = soup.find("title").string
            if not title:
                title = soup.find(class_="display-title").string
            if not title:
                title = soup.find(class_="title").string
            if not title:
                title = soup.find("h1").string
            if not title:
                title = url
                title.replace("https://", "")
                title.replace("http://,", "")
            title = title.strip()
            article = soup.find("article") # MOST PROPERLY FORMATTED SITES
            if not article:
                article = soup
            
            [x.decompose() for x in article.find_all("header")]
            [x.decompose() for x in article.find_all("nav")]
            [x.decompose() for x in article.find_all("footer")]
            [x.decompose() for x in article.find_all("button")]
            [x.decompose() for x in article.find_all("style")]
            [x.decompose() for x in article.find_all("script")]
            [x.decompose() for x in article.find_all("link")]
            [x.decompose() for x in article.find_all("svg")]
            [x.decompose() for x in article.find_all("img")]
            [x.decompose() for x in article.find_all("aside")]
            [x.decompose() for x in article.find_all("form")]
            [x.decompose() for x in article.find_all("li")]
            [x.decompose() for x in article.find_all("tag")]
            [x.decompose() for x in article.find_all(class_="social")]
            [x.decompose() for x in article.find_all(class_="article-meta")]
            [x.decompose() for x in article.find_all(class_="tag")]
            [x.decompose() for x in article.find_all(id="ad")]
            [x.decompose() for x in article.find_all(id="tag")]
            [x.decompose() for x in article.find_all(id="top-wrapper")]
            [x.decompose() for x in article.find_all(id="bottom-wrapper")]
            [x.decompose() for x in article.find_all(attrs={"data-testid" : "prism-ad-wrapper"})]
            
            texts = article.findAll(text=True)
                
            readable_texts = [x.get_text() for x in texts if x.parent.name in ["p", "a"]]
            return await process(title, " ".join(readable_texts))
        else:
            return "INVALID URL"
    else:
        title = flask.request.form.get("title")
        content = flask.request.form.get("content")
        if title and content:
            content.replace("\n", "")
            print(content)
            return await process(title, content)
        else:
            return flask.redirect("/", code=302)

@app.route("/opinion", methods = ["GET", "POST"])
async def opinion():
    if flask.request.method == "GET":
        return flask.redirect("/", code=302)
    title = flask.session.get("focus_title")
    text = flask.session.get("focus_text")
    score = flask.request.form.get("opinion_score")
    explaination = flask.request.form.get("opinion_explaination")
    if score == None or explaination == None:
        score = 50
        explaination = ""
    else:
        score = int(score)
    entry = f"\n{title},\"{text}\",{score / 100},\"{explaination}\""
    with open(OPINION_DB, "a") as f:
        f.write(entry)
        f.close()
    return flask.render_template("successful.html")


if __name__=="__main__":
    import os
    app.secret_key = os.urandom(12)
    app.run(debug=True)