import json
import os
import re
import subprocess
from requests_oauthlib import OAuth1Session
from os.path import join, dirname
from dotenv import load_dotenv


class Pytwi(object):
    """ 簡単なTwitterクライアント
    """

    def __init__(self):
      # configure dotenv
        dotenv_path = join(dirname(__file__), '.env')
        load_dotenv(dotenv_path)
        # set token keys
        CK = os.environ.get("CONSUMER_KEY")
        CS = os.environ.get("CONSUMER_SECRET")
        AT = os.environ.get("ACCESS_TOKEN")
        AS = os.environ.get("ACCESS_TOKEN_SECRET")
        self.twitter = OAuth1Session(CK, CS, AT, AS)

    def get_lists_json(self, screen_name: str):
        """ ユーザーのリスト一覧を取得
        """
        params = {'screen_name': screen_name, 'reverse': True}
        endpoint = 'https://api.twitter.com/1.1/lists/list.json'
        res = self.twitter.get(endpoint, params=params)
        if res.status_code == 200:
            lists = json.loads(res.text)
            return lists

    def get_lists(self, screen_name: str, hide_id=False, show_url=False):
        """ ユーザーのリスト一覧を表示
        """
        lists = self.get_lists_json(screen_name)
        for l in lists:
            print(l['name'])
            if not hide_id:
                print(' id:   ' + l['id_str'])
            if show_url:
                print(' url:  ' + l['uri'])

    def get_list_tweets_by_id(self, list_id, count=10, since_id=-1, max_id=-1, include_entities=False):
        """ 指定IDのリストのタイムラインを取得

            Params:
                count int: 取得するツイート数. Max 200.

        """
        params = {"list_id": list_id, 'count': count,
                  'include_entities': include_entities}
        if since_id > 0:
            params['since_id'] = since_id
        if max_id > 0:
            params['max_id'] = max_id
        endpoint = 'https://api.twitter.com/1.1/lists/statuses.json'
        res = self.twitter.get(endpoint, params=params)
        if res.status_code == 200:
            return json.loads(res.text)

    def to_str_status(self, status, include_entities=False):
        """ ツイートを整形 TODO:entitesの処理
        """
        result = ""
        # RTかどうか
        if 'retweeted_status' in status:
            result += status['user']['name'] + \
                ' (@' + status['user']['screen_name'] + ')がリツイート\n'
            result += self.to_str_status(
                status['retweeted_status'], include_entities)

        else:
            l = [status['user']['name'] + ' (@' + status['user']['screen_name'] + ')',
                 status['text'],
                 'RT:' + str(status['retweet_count']) +
                 ' FV:' + str(status['favorite_count']),
                 status['created_at'],
                 status['id_str'],
                 ]
            result += '\n'.join(l)

        return result

    def show_tweet_images(self, status):
        """ツイートに含まれる画像を表示
        """
        if 'entities' in status and 'media' in status['entities']:
            repttr = re.compile(r'.*jpg$', flags=(re.MULTILINE))
            for media in status['entities']['media']:
                uri = media['media_url_https']
                if repttr.match(uri) is not None:
                    print(uri)
                    subprocess.run(
                        "tiv {uri} -0 -w 30".format(uri=uri), shell=True)

    def show_list_tweets(self, list_id: str, count=10, since_id=-1, max_id=-1, include_entities=False):
        """ 指定IDのリストのツイートを表示
        """
        tweets = self.get_list_tweets_by_id(
            list_id, count, since_id, max_id, include_entities)
        for tweet in tweets:
            print(self.to_str_status(tweet))
            if include_entities:
                self.show_tweet_images(tweet)
            print('=' * 20, end='\n\n')
