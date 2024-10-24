import asyncio
from dotenv import load_dotenv
from os import getenv
import discord
from discord.ext import commands
from datetime import datetime, time, timedelta
import urllib.request, json
from PIL import Image
import random
from types import NoneType

load_dotenv()

token = getenv('DISCORD_TOKEN')
channel_id = int(getenv('BOT_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents, command_prefix='$')

subreddit_url_list = ['UnethicalLifeProTips',
                      'stupidquestions',
                      'gambling']

wsb_url = 'wallstreetbets'

reddit_run_time = time(9, 0, 0)

url_beginning = 'https://www.reddit.com/r/'
url_end = '/top/.json?t=day'


def get_top_post_reddit(subreddit,
                        use_flair=True,
                        flair='Loss'):
    url = url_beginning + subreddit + url_end

    file_name = None
    with urllib.request.urlopen(url) as url:
        print(f'Generating new post from {subreddit}')
        data = json.load(url)
        for post in data['data']['children']:
            if post['data']['link_flair_text'] == flair or use_flair is False:
                post_content = post['data']['selftext']
                post_title = post['data']['title']
                post_user = post['data']['author']
                post_url = 'https://www.reddit.com' + post['data']['permalink']
                if type(post['data']['media']) is not NoneType:
                    post_media_url = post['data']['media']['fallback_url']
                    file_name = 'img/wsb_video_downloaded.mp4'
                    urllib.request.urlretrieve(post_media_url, filename=file_name)
                else:
                    try:
                        post_media_url = post['data']['url_overridden_by_dest']
                        file_name = 'img/wsb_image_downloaded.png'
                        urllib.request.urlretrieve(post_media_url, filename=file_name)
                    except KeyError:
                        file_name = None
                break

    return {
        'post_content': post_content,
        'post_title': post_title,
        'post_user': post_user,
        'post_url': post_url,
        'post_file': file_name
    }


def create_discord_reddit_message(subreddit_name, post, post_title, post_user, post_url):
    if post == '':
        message = (f'Sub Reddit - r/{subreddit_name}/\n\n'
                   f'User {post_user} made a post titled {post_title}\n'
                   f'Link: {post_url}\n')
    else:
        message = (f'Sub Reddit - r/{subreddit_name}/\n\n'
                   f'User {post_user} made a post titled {post_title}\n'
                   f'Link: {post_url}\n'
                   f'Post:\n {post}')

    return message


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    now = datetime.now()
    if now.time() > reddit_run_time:
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()
        print('Waiting until tomorrow - {}s'.format(seconds))
        await asyncio.sleep(seconds)

    while True:
        now = datetime.now()
        target_time = datetime.combine(now.date(), reddit_run_time)
        seconds_until_target = (target_time - now).total_seconds()
        print('Waiting until target time - {}s'.format(seconds_until_target))
        await asyncio.sleep(seconds_until_target)
        await bot_reddit_post_daily()
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()
        await asyncio.sleep(seconds)


@client.event
async def bot_reddit_post_daily():
    await client.wait_until_ready()
    channel = client.get_channel(channel_id)

    wsb_post_data = get_top_post_reddit(subreddit=wsb_url)

    wsb_message = create_discord_reddit_message(subreddit_name=wsb_url,
                                                post=wsb_post_data['post_content'],
                                                post_title=wsb_post_data['post_title'],
                                                post_user=wsb_post_data['post_user'],
                                                post_url=wsb_post_data['post_url'])

    if wsb_post_data['post_file'] is not None:
        file = [discord.File(wsb_post_data['post_file'])]
        await channel.send(files=file, content=wsb_message)
    else:
        await channel.send(content=wsb_message)

    subreddit_picked_url = random.choice(subreddit_url_list)

    random_post_data = get_top_post_reddit(subreddit=subreddit_picked_url, use_flair=False)

    random_message = create_discord_reddit_message(subreddit_name=subreddit_picked_url,
                                                   post=random_post_data['post_content'],
                                                   post_title=random_post_data['post_title'],
                                                   post_user=random_post_data['post_user'],
                                                   post_url=random_post_data['post_url'])

    if random_post_data['post_file'] is not None:
        file = [discord.File(random_post_data['post_file'])]
        await channel.send(files=file, content=random_message)
    else:
        await channel.send(content=random_message)


@client.event
async def on_message(message):
    print(f'{message.author} - {message.content}')
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('$goodbye'):
        await message.channel.send('Goodbye!')

    if message.content.startswith('$'):
        await message.channel.send(message.content.replace('$', ''))


client.run(token)
