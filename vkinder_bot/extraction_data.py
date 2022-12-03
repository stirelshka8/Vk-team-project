import configparser
import requests
import vk_api
from Database import Session

config = configparser.ConfigParser()
config.read("config_bot.cfg")


def to_accept_token() -> str:
    """Функция возвращает токен пользователя (acces_token),
    через введения логина и пароля (от ВК),
    так же создание нового конфига в формате json"""
    try:
        vk_session = vk_api.VkApi(token=config["TOKEN"]["vk_user_token"])
    except KeyError:
        username = config["TOKEN"]["vk_user"]
        password = config["TOKEN"]["vk_pass"]
        scope = 'users,notify,friends,photos,offline,wall'
        vk_session = vk_api.VkApi(username, password, scope=scope, api_version='5.124')
    try:
        vk_session.auth(token_only=True)
    except vk_api.AuthError as error_msg:
        print(error_msg)
    set_token_vk = str(vk_session.token['access_token'])
    return set_token_vk


class ExtractingUserData:
    def __init__(self):
        self.id_photo = None
        self.id_user = None
        self.main_vkid = None
        self.dict_city_and_country = None
        self.dict_photo_and_like = None
        self.user_id = None
        self.country = None
        self.sex = None
        self.city = None
        self.age_to = None
        self.age_from = None
        self.count = None
        self.paramitres = None
        self.token = config["TOKEN"]["vk_user_token"]

    def user_search(self, count, age_from, age_to, sex, city, country):
        """
        Метод поиска пользователей сайта VK по заданным параметрам, получает на вход параметры:

        count - количество найденых записей (не более 999)
        age_from - от какого возраста искать
        age_to - до какого возраста искать
        sex - пол (2 мужчина, 1 женщина)
        city - идентификаттор города (берется у пользователя который ведет диалог с ботом)
        country - идентификатор страны (берется у пользователя который ведет диалог с ботом)

        Поиск ведется ТОЛЬКО по страницам пользователей у которых установлен смейный статус "В активном поиске"

        """
        self.count = count
        self.age_from = age_from
        self.age_to = age_to
        self.sex = sex
        self.city = city
        self.country = country

        self.paramitres = {'access_token': self.token, 'count': self.count, 'has_photo': 1, 'age_from': self.age_from,
                           'age_to': self.age_to, 'fields': 'photo_200_orig, relation: 6', 'sex': self.sex,
                           'city': self.city, 'country': self.country, 'v': 5.131}
        request_generation = requests.get(url=f'https://api.vk.com/method/users.search', params=self.paramitres)
        return request_generation.json()['response']['items']

    def photo_extraction(self, user_id):
        """
        Метод получения 3 фотографий пофиля которые имеют наибольшие LIKE, получает на вход параметры:

        user_id - id пользователя

        """
        try:
            self.user_id = user_id
            self.dict_photo_and_like = {}
            self.paramitres = {'access_token': self.token, 'owner_id': self.user_id, 'album_id': 'profile',
                               'extended': 1,
                               'photo_sizes': 0, 'v': 5.131}
            request_generation = requests.get(url=f'https://api.vk.com/method/photos.get', params=self.paramitres)
            for reqer in request_generation.json()['response']['items']:
                self.dict_photo_and_like[(reqer['sizes'][-1]['url'])] = reqer['likes']['count']

            return sorted(self.dict_photo_and_like, key=self.dict_photo_and_like.get)[-3:]
        except KeyError:
            return "Страница пользователя закрыта настройками приватности!"

    def extract_city_and_country(self, user_id):

        """
        Метод для получения идентификатора страны и города пользователя, получает на вход параметры:

        user_id - id пользователя

        на выходе будет список формата [идентификатор_страны, идентификатор_города]

        """
        try:
            self.user_id = user_id
            self.dict_city_and_country = []
            self.paramitres = {'access_token': self.token, 'user_ids': self.user_id, 'fields': 'city, country',
                               'v': 5.131}
            request_generation = requests.get(url=f'https://api.vk.com/method/users.get', params=self.paramitres)
            for reqer in request_generation.json()['response']:
                self.dict_city_and_country.append(reqer['country']['id'])
                self.dict_city_and_country.append(reqer['city']['id'])
            return self.dict_city_and_country
        except KeyError:
            return "Страница пользователя закрыта настройками приватности!"

    def profile_info(self, main_vkid):

        """
        Метод возвращающий информацию о текущем профиле

        Метод принмает vk id пользователя использующего бота

        """
        self.main_vkid = main_vkid
        self.paramitres = {'access_token': self.token, 'user_ids': self.main_vkid, 'fields': 'bdate', 'v': 5.131}
        request_generation = requests.get(url=f'https://api.vk.com/method/users.get',
                                          params=self.paramitres)
        return request_generation.json()['response'][0]

    def like(self, id_user, id_photo):
        """
        Метод добавляет указанный объект в список 'Мне нравится' (Like) текущего пользователя, принимает на вход:
        id_user - Идентификатор владельца объекта
        id_photo - Идентификатор объекта

        https://dev.vk.com/method/likes.add
        """

        try:
            self.id_user = id_user
            self.id_photo = id_photo
            self.paramitres = {'access_token': self.token, 'type': 'photo', 'owner_id': self.id_user,
                               'item_id': self.id_photo, 'v': 5.131}
            requests.get(url=f'https://api.vk.com/method/likes.add', params=self.paramitres)
        except KeyError:
            return "Ошибка добавления объекта в список 'Мне нравится' !!!!"

    def dislike(self, id_user, id_photo):
        """
        Метод удаляет указанный объект из списка 'Мне нравится' (Like) текущего пользователя, принимает на вход:
        id_user - Идентификатор владельца объекта
        id_photo - Идентификатор объекта

        https://dev.vk.com/method/likes.delete
        """

        try:
            self.id_user = id_user
            self.id_photo = id_photo
            self.paramitres = {'access_token': self.token, 'type': 'photo', 'owner_id': self.id_user,
                               'item_id': self.id_photo, 'v': 5.131}
            requests.get(url=f'https://api.vk.com/method/likes.delete', params=self.paramitres)
        except KeyError:
            return "Ошибка удаления объекта из списока 'Мне нравится' !!!!"


