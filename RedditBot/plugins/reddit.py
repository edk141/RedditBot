from RedditBot import bot

import re
import requests

reddit_link = re.compile('http://(?:www\.)?redd(?:\.it/|it\.com/(?:tb|(?:r/[\w\.]+/)?comments)/)(\w+)(/.+/)?(\w{7})?')
headers = {'User-Agent': 'irc.gamesurge.net #redditmc/RedditBot'}


def make_request(url):
    try:
        r = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        return 'Connection error'
    except requests.exceptions.Timeout:
        return 'Request timed out'
    except:
        return 'Unhandled exception ({})'.format(r.status_code)
    return r.json

@bot.command
def reddit(context):
    subreddit = context.args.strip().split(' ')[0]
    query_string = ''
    if subreddit is '':
        return 'Usage: .reddit <subreddit>'
    elif subreddit.lower().endswith(('/new', '/new/')):
        # reddit occasionally returns fuck all if the query string is not added
        query_string = '?sort=new'

    url = 'http://www.reddit.com/r/{}.json{}'.format(subreddit, query_string)
    submission = make_request(url)
    if isinstance(submission, dict):
        try:
            submission = submission['data']['children'][0]['data']
        except:
            return 'Could not fetch json, does that subreddit exist?'
    else:
        return submission

    info = {
        'username': context.line['user'],
        'subreddit': submission['subreddit'],
        'title': submission['title'],
        'up': submission['ups'],
        'down': submission['downs'],
        'shortlink': 'http://redd.it/' + submission['id']
    }
    line = u'{username}: /r/{subreddit} \'{title}\' +{up}/-{down} {shortlink}'.format(**info)
    return line


@bot.command
def karma(context):
    redditor = context.args.strip().split(' ')[0]
    if redditor is '':
        return 'Usage: .karma <redditor>'

    url = 'http://www.reddit.com/user/{}/about.json'.format(redditor)
    redditor = make_request(url)
    if isinstance(redditor, dict):
        try:
            redditor = redditor['data']
        except:
            return 'Could not fetch json, does that user exist?'
    else:
        return redditor

    info = {
        'redditor': redditor['name'],
        'link': redditor['link_karma'],
        'comment': redditor['comment_karma'],
    }
    line = '{redditor} has {link} link and {comment} comment karma'.format(**info)
    return line


@bot.regex(reddit_link)
def announce_reddit(context):
    submission_id = context.line['regex_search'].group(1)
    url = 'http://www.reddit.com/comments/{}.json'.format(submission_id)
    submission = make_request(url)
    if isinstance(submission, list):
        try:
            submission = submission[0]['data']['children'][0]['data']
        except Exception:
            return 'Could not fetch json'
    else:
        return submission

    info = {
        'title': submission['title'],
        'up': submission['ups'],
        'down': submission['downs'],
        'shortlink': 'http://redd.it/' + submission['id']
    }
    line = '\'{title}\' - +{up}/-{down} - {shortlink}'.format(**info)
    if context.line['regex_search'].group(3):
        # Link to comment
        return '[Comment] ' + line
    else:
        # Link to submission
        return line