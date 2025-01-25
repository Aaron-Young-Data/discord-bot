from os import path
from PIL import ImageDraw
import requests
from urllib.parse import urlparse
from typing import Literal

animals = Literal['dog', 'cat', 'bunny', 'rabbit', 'duck']


class Utils:
    def __init__(self, save_loc: str):

        self.dog_url = 'https://dog.ceo/api/breeds/image/random'
        self.cat_url = 'https://cataas.com/cat'
        self.bunny_url = 'https://api.bunnies.io/v2/loop/random/?media=gif'
        self.duck_url = 'https://random-d.uk/api/v1/random?type=jpg'

        self.save_loc = save_loc

    def download_img(self, url: str):
        name = path.basename(urlparse(url).path)

        if name == 'cat':
            name = 'cat.jpg'

        data = requests.get(url).content
        with open(self.save_loc + name, 'wb') as handler:
            handler.write(data)
        return self.save_loc + name

    def get_api_data(self, url: str):
        response = requests.get(url)
        return response.json()

    def get_random_animal(self, animal: animals):
        if animal == 'dog':
            response_data = self.get_api_data(self.dog_url)
            if response_data['status'] == 'success':
                return {'file': self.download_img(response_data['message']),
                        'url': response_data['message']}
            else:
                raise Exception(f"Request for Dog image failed response - {response_data['status']}")
        elif animal == 'cat':
            return {'file': self.download_img(self.cat_url),
                    'url': self.cat_url}
        elif animal in ('bunny', 'rabbit'):
            response_data = self.get_api_data(self.bunny_url)
            return {'file': response_data['media']['gif'],
                    'url': response_data['media']['gif']}
        elif animal == 'duck':
            response_data = self.get_api_data(self.duck_url)
            return {'file': self.download_img(response_data['url']),
                    'url': response_data['url']}
        else:
            raise Exception(f'Animal {animal} is not supported!')

    def text_position(self, text, image, font, text_height=2):
        image_draw = ImageDraw.Draw(image)
        text_length = image_draw.textlength(text, font=font)
        x = (image.width - text_length) / 2
        y = image.height / text_height
        return x, y
