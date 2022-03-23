# What am I missing at Data Council Austin?

This demo uses [Materialize](https://materialize.com/docs/) to keep track of and explore what's happening at Data Council Austin 2022 based on Twitter activity. It was mostly an excuse to play around with :sparkles:[Hex](https://hex.tech/):sparkles:! Once the event is over, it can be adjusted to track something else with some tweaks to the [data generator](./data-generator/README.md#twitter-data-generator).

## Docker

The pipeline uses Docker Compose to make it easier to bundle up all the services feeding into Hex:

<p align="center">
<img width="650" alt="demo_overview" src="https://user-images.githubusercontent.com/23521087/159373277-9d16f680-c368-4194-b5fb-83a779e75c76.png">
</p>

#### Authentication :raised_hand:

If you want to spin the demo up, you'll need to register an app in the [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard) to get a hold of the [auth token](https://developer.twitter.com/en/docs/authentication/oauth-2-0/application-only) (`BEARER_TOKEN`). If you already have a Twitter developer account, the process should be pretty smooth!

#### Getting the setup up and running

```bash
# Export the credentials
export BEARER_TOKEN='<your_bearer_token>'

# Start the setup
docker-compose up -d

# Is everything really up and running?
docker-compose ps
```

## Redpanda

```bash
docker-compose exec redpanda rpk topic consume dc_tweets

docker-compose exec redpanda rpk topic consume dc_users

# This topic isn't really used since it gets close to no data
docker-compose exec redpanda rpk topic consume dc_places
```

## Materialize

### Source

```sql
CREATE SOURCE rp_twitter_tweets
FROM KAFKA BROKER 'redpanda:9092' TOPIC 'dc_tweets'
  FORMAT BYTES;

CREATE SOURCE rp_twitter_users
FROM KAFKA BROKER 'redpanda:9092' TOPIC 'dc_users'
  FORMAT BYTES
ENVELOPE UPSERT;

CREATE SOURCE rp_twitter_places
FROM KAFKA BROKER 'redpanda:9092' TOPIC 'dc_places'
  FORMAT BYTES
ENVELOPE UPSERT;
```

### Views and materialized views

```sql
CREATE MATERIALIZED VIEW twitter_tweets AS
SELECT (data->>'id')::bigint AS tweet_id,
	   (data->'referenced_tweets'->0->>'type')::string AS tweet_type,
	   (data->>'text')::string AS tweet_text,
	   (data->'referenced_tweets'->0->>'id')::string AS tweet_id_rr,
	   (data->>'author_id')::bigint AS user_id,
	   (data->'geo'->>'place_id')::string AS place_id,
	   (data->>'created_at')::timestamp AS created_at
FROM (SELECT CONVERT_FROM(data,'utf8')::jsonb AS data FROM rp_twitter_tweets);

CREATE MATERIALIZED VIEW twitter_users AS
SELECT (data->>'id')::bigint AS user_id,
	   (data->>'username')::string AS username,
	   (data->>'name')::string AS user_name,
	   (data->>'location')::string AS location
FROM (SELECT CONVERT_FROM(data,'utf8')::jsonb AS data FROM rp_twitter_users);

CREATE MATERIALIZED VIEW twitter_places AS
SELECT (data->0->>'id')::string AS place_id,
	   (data->0->>'name')::string AS place_name,
	   (data->0->>'full_name')::string AS place_full_name,
	   (data->0->>'full_name')::string AS place_type
FROM (SELECT CONVERT_FROM(data,'utf8')::jsonb AS data FROM rp_twitter_places);


CREATE MATERIALIZED VIEW tweets_hourly AS
SELECT
  date_bin(interval '1 hours', created_at, '2022-03-22') AS time_bucket,
  COUNT(tweet_id) AS total_tweets
FROM twitter_tweets
GROUP BY 1;

CREATE MATERIALIZED VIEW agg_users AS
	SELECT COUNT(twitter_id) AS total_tweets
	FROM twitter_tweets
	GROUP BY twitter_id;


CREATE VIEW twitter_tweets_enriched AS
SELECT tweet_text AS tweet,
	   username,
	   CASE WHEN tweet_type = 'quoted' THEN 'quoted retweet'
	        WHEN tweet_type = 'replied to' THEN 'tweet reply'
	   ELSE 'tweet'
	   END AS tweet_type,
       created_at
FROM twitter_tweets tt
JOIN twitter_users tu ON tt.user_id = tu.user_id;

CREATE MATERIALIZED VIEW agg_tweets AS
SELECT COUNT(tweet) AS total_tweets,
	   username
FROM twitter_tweets_enriched
GROUP BY username;
```

### Tables

```sql
CREATE TABLE users_not_there
(
	username STRING
);
```

## Hex

This was my first time using Hex and I have to say: I'm here for it. I'll follow this demo up with a blogpost walking through the magic underneath the [shared app]().