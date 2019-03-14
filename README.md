# twitter-news-bot

## Description

This is a Twitter bot that periodically retweets the most retweeted recent tweets for a search term. It has additional
features, such as being able to specify how many tweets you want to fetch and the maximum age for those tweets.

Originally I wrote this bot in early 2017 when Trump had taken office as a way to keep on top of news about Trump. Running the bot, especially with a "max age" time window of an hour and tweeting every hour, made for a timely snapshot of whatever was the most important breaking news or commentary in that hour. In the old days, you could pay someone to pull stories from newspapers and magazines on a topic and present that collection to you. This is the automated version of that.

One interesting side effect of it being automated is that it has no bias in what it presents to you. If there was a positive story about Trump, it would be presented as long as it had enough retweets even though, at the time, as continues to be the case two years later, most coverage is negative (because Trump is a fucking idiot).

One thing this project made me realize is that sentiment analysis and natural language processing is HARD. If you _did_ want to only show, say, only positive tweets about Trump, it turns out to be harder than you'd think. For example, if your query phrase was "I love Trump", many of the tweets would be positive. But you'd also have tweets that has text like "No one ever said 'I love Trump' without being paid off."

## Setup and Usage

1. Install Python 3.x
2. `pip install -r requirements.txt`
3. Copy the sample_configuration.txt file to configuration.txt, and modify it to use your own settings. (Be sure to set retweeting_enabled to True when you're ready to actually retweet -- to avoid abusing Twitter, it's off by default!)
4. `python twitter_news_bot.py` (this may need to be `python3` on some systems)

Tip: if running on, e.g. an EC2 instance, make sure networking/security groups are sufficiently open for the OAuth
call to be made. Opening up 80, 443, and 22 should be sufficient without exposing overly much but you may want to restrict it even further. Next, run the script with `sudo nohup python twitter_news_bot.py &` to keep it running even when you close
your SSH client. You can then `ps aux` (maybe with ` | grep py`) to see the running process, and `sudo kill <pid>` to kill it.

### Twitter Access Tokens

https://developer.twitter.com/en/apps

### Twitter API Tip

Be careful with searching for large numbers of tweets (max_tweets_to_fetch). It seems to start rate limiting at around 1,000 tweets. It's not a big deal, because Tweepy will respect Twitter's rate limiting, but it's still a pain and something to keep in mind.

### Commands to Run the Bot in EC2

* `sudo yum update`
* `sudo yum install python3`
* `sudo yum -y install git`
* `git clone https://github.com/aaronshaver/twitter-news-bot.git`
* `curl -O https://bootstrap.pypa.io/get-pip.py`
* `python3 get-pip.py --user`
* `pip install tweepy --user`
* `nohup python3 twitter_news_bot/twitter_news_bot.py &`
