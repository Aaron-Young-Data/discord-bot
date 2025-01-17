import asyncio
from dotenv import load_dotenv
from os import getenv, path
import discord
from datetime import datetime, time, timedelta
import random
import pandas as pd
from PIL import ImageDraw, ImageFont, Image
import requests
from urllib.parse import urlparse

load_dotenv()

token = getenv('DISCORD_TOKEN')
bot_channel_id = int(getenv('BOT_CHANNEL_ID'))
wotd_channel_id = int(getenv('WOTD_CHANNEL_ID'))

save_loc = getenv('SAVE_LOC')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents, command_prefix='/')

dog_api_url = 'https://dog.ceo/api/breeds/image/random'

reddit_run_time = time(9, 0, 0)


def text_position(text,
                  image,
                  font,
                  text_height=2):
    image_draw = ImageDraw.Draw(image)
    text_length = image_draw.textlength(text, font=font)
    x = (image.width - text_length) / 2
    y = image.height / text_height
    return x, y


def get_dog_picture():
    response = requests.get(dog_api_url)

    response_data = response.json()

    if response_data['status'] == 'success':
        print(response_data['message'])

        image_url = response_data['message']
        img_name = path.basename(urlparse(image_url).path)

        img_data = requests.get(image_url).content

        with open(save_loc + img_name, 'wb') as handler:
            handler.write(img_data)

        breed = image_url.split('/')[4].replace('-', ' ')

        breed = ' '.join(breed.split()[::-1])

    else:
        raise Exception('API call not successful')

    return {'file': save_loc + img_name,
            'breed': breed}


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
        #await word_of_the_day()
        await daily_send_dog_img()
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()
        await asyncio.sleep(seconds)


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
async def daily_send_dog_img():
    bot_channel = client.get_channel(bot_channel_id)

    dog_pic = get_dog_picture()
    await bot_channel.send(f"It is a {dog_pic['breed']} :dog:",
                           file=discord.File(dog_pic['file']))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f'{message.author} - {message.content}')

    if message.content.startswith('/'):
        command = message.content.replace('/', '')
        if command.lower() == 'hello':
            await message.channel.send('Hello!')
        elif command.lower() == 'goodbye':
            await message.channel.send('Goodbye!')
        elif command.lower() == 'dog':
            dog_pic = get_dog_picture()
            await message.channel.send(f"New dog for {message.author}! It is a {dog_pic['breed']} :dog:",
                                       file=discord.File(dog_pic['file']))
        else:
            await message.channel.send(command)


client.run(token)
