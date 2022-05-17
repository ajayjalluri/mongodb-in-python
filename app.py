import pickle

from flask import Flask, render_template, request, url_for,Response
from bs4 import BeautifulSoup
import numpy as np
from flask import jsonify
# initiate flask
app = Flask(__name__)
import re
import string
from nltk.stem import PorterStemmer
import re
import pymongo
import json

from pymongo import MongoClient
# Mongodb database connection


cluster = MongoClient("mongodb+srv://nikhil:nikhil@cluster0.0kyus.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

print(cluster["search_engine"])
print("@@@@@@@@@@@@@@@@@@@@@")
print("")
db = cluster["search_engine"]

print(db["inverted"])
print("@@@@@@@@@@@@@@@@@@@@@")
print("")
collection  = db["inverted"]





def decontracted(phrase):
    # specific
    phrase = re.sub(r"won't", "will not", phrase)
    phrase = re.sub(r"can\'t", "can not", phrase)

    # general
    phrase = re.sub(r"n\'t", " not", phrase)
    phrase = re.sub(r"\'re", " are", phrase)
    phrase = re.sub(r"\'s", " is", phrase)
    phrase = re.sub(r"\'d", " would", phrase)
    phrase = re.sub(r"\'ll", " will", phrase)
    phrase = re.sub(r"\'t", " not", phrase)
    phrase = re.sub(r"\'ve", " have", phrase)
    phrase = re.sub(r"\'m", " am", phrase)
    return phrase

ps = PorterStemmer()
stopwords= set(['br', 'the', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",\
            "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', \
            'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their',\
            'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', \
            'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', \
            'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', \
            'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after',\
            'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',\
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',\
            'most', 'other', 'some', 'such', 'only', 'own', 'same', 'so', 'than', 'too', 'very', \
            's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', \
            've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn',\
            "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn',\
            "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", \
            'won', "won't", 'wouldn', "wouldn't",""])





@app.route('/index',methods = ['POST'])
def index() :
    if request.method == 'POST':

        data = request.get_json()
        print(data["document"]) # one collection

        try:

            if (db.datas.count_documents({})== 0) :

                db.inverted.insert_one({})

                db.tag.insert_one({})
            dbResponse=db.datas.insert_one(data["document"])
            print(dbResponse.inserted_id)
            idd=dbResponse.inserted_id


        except Exception as ex:
            print(ex)
            return jsonify({"message":"failed"})

        inv_index = db.inverted.find()[0]
        tags = db.tag.find()[0]

        #idd = 123 #(ur task)
        d = data["document"]
        text = d["title"] + " " + d["body"]


        sentance = re.sub(r"http\S+", "",text)
        sentance = BeautifulSoup(sentance, 'html').get_text()
        sentance = decontracted(sentance)
        sentance = re.sub("\S*\d\S*", "", sentance).strip()

        tokens = sentance.split()
        tokens = [token.lower() for token in tokens]
        l = []
        for x in tokens:

            l.append(re.sub(r'[^a-z]', '', x))

        sentance = " ".join(l)
        tokens = sentance.split()

        tokens = [token for token in tokens if token not in stopwords]
        tokens = [ps.stem(token) for token in tokens]
        Id = str(idd)

        for x in set(tokens) :

            if x in inv_index.keys():
                    inv_index[x]["IDs"].append({Id:tokens.count(x),"TF":(tokens.count(x)/len(tokens))})
                    inv_index[x]["idf"] = tokens.count(x) + inv_index[x]["idf"]
            else :

                inv_index[x] = {}
                inv_index[x]["IDs"] = []

                inv_index[x]["IDs"].append({Id:tokens.count(x),"TF":(tokens.count(x)/len(tokens))})
                inv_index[x]["idf"] = tokens.count(x)

        for x in set(d["tags"]):

            if x in tags.keys():
                tags[x].append(Id)
            else :

                tags[x] = []
                tags[x].append(Id)


        print(inv_index)
        print(tags)

        try:
            db.inverted.drop()
            dbResponse=db.inverted.insert_one(inv_index)
            db.tag.drop()
            dbResponse=db.tag.insert_one(tags)
        except Exception as ex:
            print(ex)

            return jsonify({"message":"failed"})



    return jsonify({"message":"success"})


@app.route('/search',methods = ['GET'])
def search() :
    if request.method == 'GET':
        n = db.datas.count_documents({})
        query = request.args.get("search")
        print(query)
        tokens = query.split()
        tokens = [token.lower() for token in tokens]
        print(tokens)
        l = []
        for x in tokens:

            l.append(re.sub(r'[^a-z]', '', x))

        sentance = " ".join(l)
        tokens = sentance.split()

        tokens = [token for token in tokens if token not in stopwords]
        tokens = [ps.stem(token) for token in tokens]


        inv_index = db.inverted.find()[0]
        tags = db.tag.find()[0]

        print(tokens)
        S = {}
        for x in set(tokens):
            if x in inv_index.keys():
                print(x)
                print(inv_index[x])
                for y in inv_index[x]["IDs"] :
                    print(y)

                    try :
                        S[list(y.keys())[0]] = S[list(y.keys())[0]] + (y["TF"] * np.log((n/inv_index[x]["idf"])))

                    except:

                        S[list(y.keys())[0]] = y["TF"] * np.log((n/inv_index[x]["idf"]))



        print(S)
        s = sorted(S.items(), key=lambda x: x[1], reverse=True)
        k = [x[0] for x in s]
        if len(k) <= 5 :
            pass
        else :
            k = k[0:5]






        print(k)
        rtags = []
        docs1 = []
        document = list(db.datas.find())
        for x in k :

            for i in document:
                if str(i["_id"])==x:
                    print(dict(i))

                    t = {}
                    t["title"] = i["title"]
                    t["body"] = i["body"]
                    t["tags"] = i["tags"]
                    t["_id"] = str(i["_id"])
                    docs1.append(t)
                    data=i['tags']
                    rtags.extend(list(data))


        tagdict = {}
        for item in rtags:
            if (item in tagdict):
                tagdict[item] += 1
            else:
                tagdict[item] = 1

        s1 = sorted(tagdict.items(), key=lambda x: x[1], reverse=True)
        print(s1)
        t = [x[0] for x in s1]
        print(t)
        if len(t) <= 5 :
            pass
        else :
            t = t[0:5]

        artd = []
        for x in t :
            artd.extend(tags[x])






        rtd = set(artd) - set(k)

        rtd = list(rtd)
        docs2 = []
        for x in rtd :

            for i in document:
                if str(i["_id"])==x:
                    print(dict(i))

                    t = {}
                    t["title"] = i["title"]
                    t["body"] = i["body"]
                    t["tags"] = i["tags"]
                    t["_id"] = str(i["_id"])
                    docs2.append(t)
                    data=i['tags']
                    rtags.extend(list(data))







        return jsonify({"Matched Documents":docs1,"Related Documents":docs2})


@app.route('/document_slug',methods = ['GET'])
def documentslug() :
    if request.method == 'GET':
        document_slug = request.args.get("document_slug")
        print(request.args)
        print(document_slug)
        tokens = str(document_slug).split("-")
        tokens = [token.lower() for token in tokens]
        print(tokens)
        l = []
        for x in tokens:

            l.append(re.sub(r'[^a-z]', '', x))

        sentance = " ".join(l)
        tokens = sentance.split()


        tokens = [token for token in tokens if token not in stopwords]
        print(tokens)
        s = ""
        for x in tokens :
            s = s + x +"-"

        if document_slug[-1] == "-":
            return jsonify({"document_slug":s})
        else:

            return jsonify({"document_slug":s[:-1]})





if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0')
