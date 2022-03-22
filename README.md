# What am I missing at Data Council Austin?

This demo uses [Materialize](https://materialize.com/docs/) to keep track of and explore what's happening at Data Council Austin 2022 based on Twitter activity. It was mostly an excuse to play around with :sparkles:[Hex](https://hex.tech/):sparkles:. Once the event is over, it can be adjusted to track something else with some tweaks to the [data generator](./data-generator/README.md#twitter-data-generator))!

## Docker

We'll use Docker Compose to make it easier to bundle up all the services in the pipeline feeding Hex:

<p align="center">
<img width="650" alt="demo_overview" src="https://user-images.githubusercontent.com/23521087/159373277-9d16f680-c368-4194-b5fb-83a779e75c76.png">
</p>

#### Authentication :raised_hand:

Before getting started, you need to register an app in the [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard) to get a hold of the [auth token](https://developer.twitter.com/en/docs/authentication/oauth-2-0/application-only) (`BEARER_TOKEN`). If you already have a Twitter developer account, the process should be pretty smooth!

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

docker-compose exec redpanda rpk topic consume dc_places
```

## Materialize

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

```sql
CREATE MATERIALIZED VIEW twitter_tweets AS
SELECT data['author_id'] AS author_id
FROM (SELECT CONVERT_FROM(data,'utf8')::jsonb AS data FROM rp_twitter_tweets);

CREATE MATERIALIZED VIEW twitter_users AS
SELECT data['username'] AS username
FROM (SELECT CONVERT_FROM(data,'utf8')::jsonb AS data FROM rp_twitter_users);

CREATE MATERIALIZED VIEW twitter_places AS
SELECT data['places'] AS place
FROM (SELECT CONVERT_FROM(data,'utf8')::jsonb AS data FROM rp_twitter_places);
```

## Hex
