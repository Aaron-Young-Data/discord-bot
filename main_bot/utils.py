import secrets
from os import path
from PIL import ImageDraw, Image, ImageFont
import requests
from urllib.parse import urlparse
from typing import Literal
from uuid import uuid4

animals = Literal['dog', 'cat', 'bunny', 'rabbit', 'duck']

class APIUtils:
    def __init__(self, save_loc: str):

        self.dog_url = 'https://dog.ceo/api/breeds/image/random'
        self.cat_url = 'https://cataas.com/cat'
        self.bunny_url = 'https://api.bunnies.io/v2/loop/random/?media=gif'
        self.duck_url = 'https://random-d.uk/api/v1/random?type=jpg'

        self.img_utils = ImgUtils(save_loc=save_loc)

    def get_api_data(self, url: str):
        response = requests.get(url)
        return response.json()

    def get_random_animal(self, animal: animals):
        if animal == 'dog':
            response_data = self.get_api_data(self.dog_url)
            if response_data['status'] == 'success':
                return {'file': self.img_utils.download_img(response_data['message']),
                        'url': response_data['message']}
            else:
                raise Exception(f"Request for Dog image failed response - {response_data['status']}")
        elif animal == 'cat':
            return {'file': self.img_utils.download_img(self.cat_url),
                    'url': self.cat_url}
        elif animal in ('bunny', 'rabbit'):
            response_data = self.get_api_data(self.bunny_url)
            return {'file': response_data['media']['gif'],
                    'url': response_data['media']['gif']}
        elif animal == 'duck':
            response_data = self.get_api_data(self.duck_url)
            return {'file': self.img_utils.download_img(response_data['url']),
                    'url': response_data['url']}
        else:
            raise Exception(f'Animal {animal} is not supported!')


class ImgUtils:
    def __init__(self, save_loc: str):
        self.save_loc = save_loc

    def download_img(self, url: str):
        name = path.basename(urlparse(url).path)

        if name == 'cat':
            name = 'cat.jpg'

        data = requests.get(url).content
        with open(self.save_loc + name, 'wb') as handler:
            handler.write(data)
        return self.save_loc + name

    def create_roulette_img(self, number, colour):
        image = Image.new('RGB', (500, 500), colour)
        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype("arial.ttf", 400)

        position = self.text_position(text=str(number),
                                      image=image,
                                      font=font,
                                      text_height=10)

        bbox = draw.textbbox(position,
                             font=font,
                             text=str(number))

        draw.rectangle(bbox,
                       fill=colour)

        draw.text(position,
                  text=str(number),
                  font=font,
                  fill="white")

        image_loc = self.save_loc + str(uuid4()) + '.png'

        image.save(image_loc)

        return image_loc


    @staticmethod
    def text_position(text, image, font, text_height=2):
        image_draw = ImageDraw.Draw(image)
        text_length = image_draw.textlength(text, font=font)
        x = (image.width - text_length) / 2
        y = image.height / text_height
        return x, y


class GamblingUtils:
    def __init__(self):
        roulette_numbers = [i for i in range(0, 37)]

        self.roulette_numbers_dict = {}

        for number in roulette_numbers:
            if number == 0:
                colour = '#016D29'
            elif number % 2 == 0:
                colour = '#000000'
            else:
                colour = '#E0080B'

            self.roulette_numbers_dict[number] = colour

    def pick_random_roulette_number(self):
        selected_number = secrets.choice(list(self.roulette_numbers_dict.keys()))
        return selected_number

    def get_roulette_number_colour(self, number: int) -> str:
        if number not in list(self.roulette_numbers_dict.keys()):
            raise Exception(f"Roulette number {number} is not allowed it has to be between 0 and 36")

        return self.roulette_numbers_dict[number]

