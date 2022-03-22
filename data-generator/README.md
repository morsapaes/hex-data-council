# Twitter Data Generator

The `twitter_streaming.py` data generator fetches tweets is real-time using the (very swanky!) [Twitter API v2](https://developer.twitter.com/en/docs/twitter-api/migrate/overview). What's cool about it is that, for some endpoints, it allows you to consume events through an open, streaming API connection, avoiding the need to dabble with API call scheduling.

In this case, the generator is using the [Filtered Stream](https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/introduction) endpoint group to capture new tweets related to Data Council, and the [Kafka-Python](https://kafka-python.readthedocs.io/en/master/) client to push these tweets into Redpanda.

### Building rules

To find out what we're missing at Data Council, we need to feed our Twitter search with rules that filter and limit the consumption to just tweets that either mention `Data Council` or tag the `@DataCouncilAI` account. For this, we're using a [rule](https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule) that looks like:

`@DataCouncilAI OR "Data Council"`

To exclude retweets (but keep quoted retweets and replies), we're additionally adding:

`-is:retweet`

### Bootstrapping

To get things started ahead of time and avoid parsing surprises, we can bootstrap the broker with some historical data using a one-off data dump that looks back 7 days (the maximum allowed by Twitter for `Essential` access developer accounts). This process is enclosed in the `twitter_historical.py` script and uses the [Recent Search](https://developer.twitter.com/en/docs/twitter-api/tweets/search/introduction) endpoint. To bootstrap the broker with historical data, run:

```bash
docker exec -it data-generator bash

./twitter_historical.py
```

### Output (Redpanda)

#### Tweets

Tweet:

```javascript
{
  "topic": "dc_tweets",
  "key": "\"1503739684228370435\"",
  "value": "{\"created_at\": \"2022-03-15T14:27:33.000Z\", \"id\": \"1503739684228370435\", \"author_id\": \"1116804034533498880\", \"text\": \"We’re excited to be attending Data Council Austin next week (March 23-24)! Stop by our booth for a demo and learn how Materialize is the fastest way to build the fastest data products. \\nhttps://t.co/dD2h9dlLFJ\"}",
  "timestamp": 1647946272022,
  "partition": 0,
  "offset": 85
}
```

Quoted retweet:

```javascript
{
  "topic": "dc_tweets",
  "key": "\"1506232195475812359\"",
  "value": "{\"attachments\": {}, \"author_id\": \"955397748580372480\", \"created_at\": \"2022-03-22T11:31:54.000Z\", \"geo\": {\"place_id\": \"3078869807f9dd36\"}, \"id\": \"1506232195475812359\", \"referenced_tweets\": [{\"type\": \"quoted\", \"id\": \"1506232160029757448\"}], \"text\": \"Quoted tweet https://t.co/a1Z4ATPHf1\"}",
  "timestamp": 1647948725070,
  "partition": 0,
  "offset": 89
}
```

Reply:

```javascript
{
  "topic": "dc_tweets",
  "key": "\"1503716872961015814\"",
  "value": "{\"created_at\": \"2022-03-15T12:56:54.000Z\", \"id\": \"1503716872961015814\", \"author_id\": \"248615990\", \"referenced_tweets\": [{\"type\": \"replied_to\", \"id\": \"1503458784836042752\"}], \"text\": \"@spbail @DataCouncilAI @juansequeda cc @petesoder :)\", \"in_reply_to_user_id\": \"1153584362\"}",
  "timestamp": 1647946272023,
  "partition": 0,
  "offset": 86
}
````

#### Users

```javascript
{
  "topic": "dc_users",
  "key": "\"1116804034533498880\"",
  "value": "{\"name\": \"Materialize\", \"username\": \"MaterializeInc\", \"id\": \"1116804034533498880\", \"location\": \"New York, NY\"}",
  "timestamp": 1647946272211,
  "partition": 0,
  "offset": 57
}
```

#### Places

```javascript
{
  "topic": "dc_places",
  "key": "{\"full_name\": \"Austin, TX\", \"id\": \"c3f37afa9efcf94b\", \"name\": \"Austin\", \"place_type\": \"city\"}",
  "value": "[{\"full_name\": \"Austin, TX\", \"id\": \"c3f37afa9efcf94b\", \"name\": \"Austin\", \"place_type\": \"city\"}]",
  "timestamp": 1647948717075,
  "partition": 0,
  "offset": 1
}
```

## Tweaking the code

If you make any changes to the data generator, rebuild the container using:

```bash
docker-compose build --no-cache

docker-compose up --force-recreate -d
```