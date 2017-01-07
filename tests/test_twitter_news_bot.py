from twitter_news_bot import twitter_news_bot


class TestTwitterNewsBot:
    def test_sample_test(self):
        retweeter = twitter_news_bot.TwitterNewsBot()
        assert (retweeter.wordBlacklist == [])
