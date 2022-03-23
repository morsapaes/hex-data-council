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
  "key": "\"1506278626270097410\"",
  "value": "{\"id\": \"1506278626270097410\", \"text\": \"the only profitable vendor at data council this week is going to be a churro cart guy that rebrands as a modern data snack\", \"author_id\": \"24949412\", \"created_at\": \"2022-03-22T14:36:24.000Z\"}",
  "timestamp": 1648000826874,
  "partition": 0,
  "offset": 53
}
```

Quoted retweet:

```javascript
{
  "topic": "dc_tweets",
  "key": "\"1506043533873999876\"",
  "value": "{\"referenced_tweets\": [{\"type\": \"quoted\", \"id\": \"1504083364608946177\"}], \"id\": \"1506043533873999876\", \"attachments\": {\"media_keys\": [\"3_1506043529050558467\"]}, \"text\": \"Looking forward to speaking @DataCouncilAI this week on @MarquezProject and @OpenLineage. Oh, and don’t forget to grab some swag! https://t.co/7sc9MGThuv https://t.co/rTgwSBUkdi\", \"author_id\": \"1035054002767945728\", \"created_at\": \"2022-03-21T23:02:14.000Z\"}",
  "timestamp": 1648000826876,
  "partition": 0,
  "offset": 68
}
```

Reply:

```javascript
{
  "topic": "dc_tweets",
  "key": "\"1506304497391321093\"",
  "value": "{\"referenced_tweets\": [{\"type\": \"replied_to\", \"id\": \"1506303524350558208\"}], \"id\": \"1506304497391321093\", \"text\": \"@j_houg Did Snowflake include the drop in usage caused by everyone being at @DataCouncilAI  as a risk factor in their quarterly forecast?\", \"author_id\": \"14578294\", \"in_reply_to_user_id\": \"376618837\", \"created_at\": \"2022-03-22T16:19:12.000Z\"}",
  "timestamp": 1648000826873,
  "partition": 0,
  "offset": 45
}
````

#### Users

```javascript
{
  "topic": "dc_users",
  "key": "\"14578294\"",
  "value": "{\"id\": \"14578294\", \"name\": \"Josh Wills\", \"location\": \"San Francisco, CA\", \"username\": \"josh_wills\"}",
  "timestamp": 1648000827070,
  "partition": 0,
  "offset": 23
}
```

#### Places

```javascript
{
  "topic": "dc_places",
  "key": "\"101f6c4cf696e007\"",
  "value": "{\"full_name\": \"San Francisco International Airport (SFO)\", \"id\": \"101f6c4cf696e007\", \"name\": \"San Francisco International Airport (SFO)\", \"place_type\": \"poi\"}",
  "timestamp": 1648000827259,
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