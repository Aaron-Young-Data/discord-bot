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
import pandas as pd
from PIL import ImageDraw, ImageFont, Image
import praw

load_dotenv()

token = getenv('DISCORD_TOKEN')
bot_channel_id = int(getenv('BOT_CHANNEL_ID'))
wotd_channel_id = int(getenv('WOTD_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents, command_prefix='$')

subreddit_url_list = ['UnethicalLifeProTips',
                      'stupidquestions',
                      'gambling']

wsb_url = 'wallstreetbets'

reddit_run_time = time(9, 0, 0)

def get_top_post_reddit(subreddit,
                        use_flair=True,
                        flair='Loss'):

    reddit = praw.Reddit(
        client_id=getenv('REDDIT_CLIENT'),
        client_secret=getenv('REDDIT_SECRET'),
        user_agent="Discord Bot by /u/cursingbutton01",
        check_for_async=False
    )

    post_files = None
    post_content = None
    post_title = None
    post_user = None
    post_url = None

    for submission in reddit.subreddit(subreddit).top(time_filter='day', limit=25):
        if submission.link_flair_text == flair or use_flair is False:
            post_user = submission.author.name
            post_content = submission.selftext
            post_title = submission.title
            post_url = submission.url
            try:
                image_dict = submission.media_metadata
                image_url_dict = {}
                for image in image_dict.values():
                    biggest_image_url = image['p'][-1]['u']
                    biggest_image_id = image['id']
                    image_url_dict[biggest_image_id] = biggest_image_url

                post_files = []

                for key in image_url_dict.keys():
                    filename = 'img/' + key + '.png'
                    urllib.request.urlretrieve(image_url_dict[key], filename=filename)
                    post_files.append(filename)
                break
            except AttributeError:
                print('No Images!')
        else:
            print('Post not valid!')

    return {
        'post_content': post_content,
        'post_title': post_title,
        'post_user': post_user,
        'post_url': post_url,
        'post_files': post_files
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


def text_position(text,
                  image,
                  font,
                  text_height=2):
    image_draw = ImageDraw.Draw(image)
    text_length = image_draw.textlength(text, font=font)
    x = (image.width - text_length) / 2
    y = image.height / text_height
    return x, y


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
        await bot_reddit_post_daily_wsb()
        await word_of_the_day()
        await bot_reddit_post_daily_random()
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()
        await asyncio.sleep(seconds)


@client.event
async def bot_reddit_post_daily_wsb():
    await client.wait_until_ready()
    channel = client.get_channel(bot_channel_id)

    wsb_post_data = get_top_post_reddit(subreddit=wsb_url)

    wsb_message = create_discord_reddit_message(subreddit_name=wsb_url,
                                                post=wsb_post_data['post_content'],
                                                post_title=wsb_post_data['post_title'],
                                                post_user=wsb_post_data['post_user'],
                                                post_url=wsb_post_data['post_url'])

    if wsb_post_data['post_files'] is not None:
        file_list = []
        for file in wsb_post_data['post_files']:
            file_list.append(discord.File(file))
        await channel.send(files=file_list, content=wsb_message)
    else:
        await channel.send(content=wsb_message)


@client.event
async def bot_reddit_post_daily_random():
    channel = client.get_channel(bot_channel_id)
    subreddit_picked_url = random.choice(subreddit_url_list)

    random_post_data = get_top_post_reddit(subreddit=subreddit_picked_url, use_flair=False)

    random_message = create_discord_reddit_message(subreddit_name=subreddit_picked_url,
                                                   post=random_post_data['post_content'],
                                                   post_title=random_post_data['post_title'],
                                                   post_user=random_post_data['post_user'],
                                                   post_url=random_post_data['post_url'])

    if random_post_data['post_files'] is not None:
        file_list = []
        for file in random_post_data['post_files']:
            file_list.append(discord.File(file))
        await channel.send(files=file_list, content=random_message)
    else:
        await channel.send(content=random_message)


@client.event
async def word_of_the_day():
    await client.wait_until_ready()
    wotd_channel = client.get_channel(wotd_channel_id)

    word_list = pd.read_csv('data/word_list.csv')['WORD'].to_list()
    image = Image.open('data/don_cheadle.jpg')

    font = ImageFont.truetype("arial.ttf", 90)

    img_text1 = 'Don Cheadle'
    img_text2 = 'word of the day'
    wotd = random.choice(word_list).capitalize()

    text_dict = {img_text1: 17,
                 img_text2: 6,
                 wotd: 1.25}

    img_draw = ImageDraw.Draw(image)

    for text in text_dict:
        print(text, text_dict[text])
        x, y = text_position(text=text, image=image, font=font, text_height=text_dict[text])
        print(x, y)
        img_draw.text((x, y), text, fill=(255, 255, 255), font=font)

    image.save('img/don_cheadle_wotd.png')

    await wotd_channel.send(file=discord.File('img/don_cheadle_wotd.png'))



@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f'{message.author} - {message.content}')

    if message.content.startswith('$'):
        command = message.content.replace('$', '')
        if command.lower() == 'hello':
            await message.channel.send('Hello!')
        if command.lower() == 'goodbye':
            await message.channel.send('Goodbye!')
        else:
            await message.channel.send(command)

client.run(token)
