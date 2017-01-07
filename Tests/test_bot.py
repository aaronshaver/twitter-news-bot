from Bot import bot


def test_stupid_test():
    botty = bot.Bot()
    assert ("_" in botty.date_time_name)
