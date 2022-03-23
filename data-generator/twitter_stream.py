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


def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r


def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )

    logging.info(json.dumps(response.json()))

    return response.json()


def delete_rules(r_get):
    if r_get is None or "data" not in r_get:
        return None

    ids = list(map(lambda rule: rule["id"], r_get["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    logging.info(json.dumps(response.json()))


def set_rules(r_delete):
    # Filter the stream to include Data Council content, excluding retweets
    # (but including tweets, quote tweets and replies)
    rules = [
        {"value": "(@DataCouncilAI OR \"Data Council\") -is:retweet", "tag": "Tweets about Data Council Austin 2022"}
    ]
    payload = {"add": rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    logging.info(json.dumps(response.json()))


def get_stream(r_filter):

    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream",
        auth=bearer_oauth,
        stream=True,
        params={'expansions': 'author_id,geo.place_id',
                'tweet.fields': 'author_id,created_at,in_reply_to_user_id,geo,attachments,referenced_tweets',
                'place.fields': 'name,place_type',
                'user.fields': 'location'}
    )

    logging.info(response.status_code)

    if response.status_code != 200:
        raise Exception(
            "Cannot get stream (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)

            p.send(topic='dc_tweets', value=json.dumps(json_response['data'], ensure_ascii=False).encode('utf-8'))

            for usr in json_response['includes']['users']:
                p.send(topic='dc_users', key=json.dumps(usr['id']).encode('utf8'), value=json.dumps(usr, ensure_ascii=False).encode('utf-8'))

            if 'places' in json_response['includes']:

                for pl in json_response['includes']['places']:
                    p.send(topic='dc_places', key=json.dumps(pl['id']).encode('utf8'), value=json.dumps(pl, ensure_ascii=False).encode('utf-8'))

            p.flush()


def main():
    r_get = get_rules()
    r_delete = delete_rules(r_get)
    r_filter = set_rules(r_delete)

    get_stream(r_filter)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, filename="logfile", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

    while True:
        try:
            main()
        except requests.exceptions.ChunkedEncodingError:
            print('restarting')
