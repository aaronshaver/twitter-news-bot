# twitter-news-bot

This is a Twitter bot that periodically retweets the most retweeted recent tweets for a search term. It has additional
features, such as being able to specify how many tweets you want to fetch and the maximum age for those tweets.

## Setup

1. Install Python 3.x
2. `pip install -r requirements.txt`
3. Copy the sample_configuration.txt file to configuration.txt, and modify it to use your own settings. (Be sure to set retweeting_enabled to True when you're ready to actually retweet -- to avoid abusing Twitter, it's off by default!)
4. `python twitter_news_bot/twitter_news_bot.py`

Tip: if running on, e.g. an EC2 instance, make sure networking/security groups are sufficiently open for the OAuth
call to be made, and then run the script with 'sudo nohup python Bot/bot.py &' to keep it running even when you close
your SSH client. You can then 'ps aux' to see the running process, and 'sudo kill <pid>' to kill it.

### Twitter access tokens

https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html

### Tips

Be careful with searching for large numbers of tweets (max_tweets_to_fetch), like 5000. You'll get rate limited. Tweepy will respect Twitter's rate limiting, but it's still a pain to deal with.