import asyncio
from dotenv import load_dotenv
from os import getenv, path
import discord
from datetime import datetime, time, timedelta
import random
import pandas as pd
from PIL import ImageDraw, ImageFont, Image
from typing import Literal, get_args
from utils import ImgUtils, APIUtils, animals, GamblingUtils

load_dotenv()

token = getenv('DISCORD_TOKEN')
bot_channel_id = int(getenv('BOT_CHANNEL_ID'))
wotd_channel_id = int(getenv('WOTD_CHANNEL_ID'))
gambling_channel_id = int(getenv('GAMBLING_CHANNEL_ID'))
save_loc = getenv('SAVE_LOC')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents, command_prefix='/')

reddit_run_time = time(9, 0, 0)

gambling_utils = GamblingUtils()
api_utils = APIUtils(save_loc=save_loc)
img_utils = ImgUtils(save_loc=save_loc)

win_gif = "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExc2xoZTB3a2h5MHp6MGE4NDlzaXJ2ZnhjdHd4cmYwb2MzOWFtNXIwdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l2SpXDaRDHBhLc0s8/giphy.gif"
lose_gif = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExc3B5eXN2MmZ1ejNldnZmNTRrMnVyano5aDg0cnVhcDA1bjYwZmM0MSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l2SpO2558KNLdARcQ/giphy.gif"

@client.event
async def on_ready():
    gambling_channel = client.get_channel(gambling_channel_id)
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
        await word_of_the_day()
        await daily_send_dog_img()
        roulette_num = gambling_utils.pick_random_roulette_number()
        img_loc = img_utils.create_roulette_img(number=roulette_num,
                                                colour=gambling_utils.get_roulette_number_colour(roulette_num))
        await gambling_channel.send("Today's roulette number:", file=discord.File(img_loc))
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
        x, y = img_utils.text_position(text=text, image=image, font=font, text_height=text_dict[text])
        print(x, y)
        img_draw.text((x, y), text, fill=(255, 255, 255), font=font)

    image.save('img/don_cheadle_wotd.png')

    await wotd_channel.send(file=discord.File('img/don_cheadle_wotd.png'))


@client.event
async def daily_send_dog_img():
    bot_channel = client.get_channel(bot_channel_id)

    dog_pic = api_utils.get_random_animal(animal='dog')

    breed = dog_pic['url'].split('/')[4].replace('-', ' ')

    breed = ' '.join(breed.split()[::-1])

    await bot_channel.send(f"New daily Dog! It is a {breed} :dog:",
                           file=discord.File(dog_pic['file']))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f'{message.author} - {message.content}')

    if message.content.startswith('/'):
        command = message.content.replace('/', '')
        command_prefix = command.split(' ')[0]
        if command_prefix.lower() == 'roulette':
            if message.channel.id == gambling_channel_id:
                user_num = command.split(' ')[-1]
                passed = False
                try:
                    int(user_num)
                    if int(user_num) not in [i for i in range(0, 37)]:
                        await message.channel.send('Please enter number between 0 and 36')
                    else:
                        passed = True
                except ValueError:
                    await message.channel.send(f'{user_num} was not recognised as a number')

                if passed:
                    roulette_num = gambling_utils.pick_random_roulette_number()
                    img_loc = img_utils.create_roulette_img(number=roulette_num,
                                                            colour=gambling_utils.get_roulette_number_colour(roulette_num))

                    if roulette_num == int(user_num):
                        await message.channel.send(f"The number is:",
                                                   file=discord.File(img_loc))
                        await message.channel.send(f"You Win!")
                        await message.channel.send(win_gif)
                    else:
                        await message.channel.send(f"The number is:",
                                                   file=discord.File(img_loc))
                        await message.channel.send(f"You Lose!")
                        await message.channel.send(lose_gif)
        elif command_prefix.lower() == 'animal':
            animal = command.split(' ')[1]
            if animal.lower() in get_args(animals):
                data = api_utils.get_random_animal(animal.lower())
                img = data['file']
                url = data['url']
                if animal.lower() == 'dog':
                    breed = url.split('/')[4].replace('-', ' ')
                    breed = ' '.join(breed.split()[::-1]).capitalize()
                    await message.channel.send(f"New dog for {message.author.mention}! It is a {breed} :dog:",
                                               file=discord.File(img))
                else:
                    if animal.lower() in ('bunny', 'rabbit'):
                        animal = 'rabbit'
                        await message.channel.send(f"New {animal} for {message.author.mention}! :{animal}:")
                        await message.channel.send(f"{img}")
                    else:
                        await message.channel.send(f"New {animal} for {message.author.mention}! :{animal}:",
                                                   file=discord.File(img))

            else:
                await message.channel.send('I cant find that animal yet!')
        else:
            await message.channel.send(f'Command {command} not recognised!')

client.run(token)
