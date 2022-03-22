#!/usr/bin/env python

# Copyright 2020 @TwitterDev

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at

#       http://www.apache.org/licenses/LICENSE-2.0

#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# Modifications copyright (C) 2022 @morsapaes

import logging
import requests
import json
import os
from kafka import KafkaProducer

p = KafkaProducer(bootstrap_servers='redpanda:9092')

bearer_token= os.environ['BEARER_TOKEN']

search_url = "https://api.twitter.com/2/tweets/search/recent"

# Filter the stream to include Data Council content, excluding retweets
# (but including tweets, quote tweets and replies)
query_params = {'query': '(@DataCouncilAI OR "Data Council") -is:retweet',
                'expansions': 'author_id,geo.place_id',
                'tweet.fields': 'author_id,created_at,in_reply_to_user_id,geo,attachments,referenced_tweets',
                'place.fields': 'name,place_type',
                'user.fields': 'location',
                'max_results': 100}


def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r


def connect_to_endpoint(url, params):
    response = requests.get(url, auth=bearer_oauth, params=params)
    print(response.status_code)
    logging.info(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

def main():
    json_response = connect_to_endpoint(search_url, query_params)

    for idx, response in enumerate(json_response['data']):
        if response:

            p.send(topic='dc_tweets', key=json.dumps(response['id']).encode('utf8'), value=json.dumps(response, ensure_ascii=False).encode('utf-8'))

    for idx, response in enumerate(json_response['includes']['users']):
        if response:

            p.send(topic='dc_users', key=json.dumps(response['id']).encode('utf8'), value=json.dumps(response, ensure_ascii=False).encode('utf-8'))

    if 'places' in json_response['includes']:
        for idx, response in enumerate(json_response['includes']['places']):
                p.send(topic='dc_places', key=json.dumps(response['id']).encode('utf8'), value=json.dumps(response, ensure_ascii=False).encode('utf-8'))

    p.flush()

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, filename="logfile", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

    main()
