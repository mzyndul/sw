import os
import time
from pathlib import Path
from unittest.mock import patch

import petl as etl
from django.core.files import File
from django.test import TestCase
from django.urls import reverse

from djangoProject.settings import MEDIA_ROOT
from star_wars_people.models import SWPeopleCollection
from star_wars_people.sw_api import SWAPI

SAMPLE_API_RESULT = [{
    "name": "Luke Skywalker",
    "height": "172",
    "mass": "77",
    "hair_color": "blond",
    "skin_color": "fair",
    "eye_color": "blue",
    "birth_year": "19BBY",
    "gender": "male",
    "homeworld": "http://swapi.dev/api/planets/1/",
    "films": ["http://swapi.dev/api/films/1/", "http://swapi.dev/api/films/2/", "http://swapi.dev/api/films/3/",
              "http://swapi.dev/api/films/6/"],
    "species": [],
    "vehicles": ["http://swapi.dev/api/vehicles/14/", "http://swapi.dev/api/vehicles/30/"],
    "starships": ["http://swapi.dev/api/starships/12/", "http://swapi.dev/api/starships/22/"],
    "created": "2014-12-09T13:50:51.644000Z",
    "edited": "2014-12-20T21:17:56.891000Z",
    "url": "http://swapi.dev/api/people/1/"
    },
    {
    "name": "C-3PO",
    "height": "167",
    "mass": "75",
    "hair_color": "n/a",
    "skin_color": "gold",
    "eye_color": "yellow",
    "birth_year": "112BBY",
    "gender": "n/a",
    "homeworld": "http://swapi.dev/api/planets/1/",
    "films": [
        "http://swapi.dev/api/films/1/",
        "http://swapi.dev/api/films/2/",
        "http://swapi.dev/api/films/3/",
        "http://swapi.dev/api/films/4/",
        "http://swapi.dev/api/films/5/",
        "http://swapi.dev/api/films/6/"
    ],
    "species": [
        "http://swapi.dev/api/species/2/"
    ],
    "vehicles": [],
    "starships": [],
    "created": "2014-12-10T15:10:51.357000Z",
    "edited": "2014-12-20T21:17:50.309000Z",
    "url": "http://swapi.dev/api/people/2/"
}]

SAMPLE_PLANET_RESULT = [{
    "name": "Tatooine",
    "rotation_period": "23",
    "orbital_period": "304",
    "diameter": "10465",
    "climate": "arid",
    "gravity": "1 standard",
    "terrain": "desert",
    "surface_water": "1",
    "population": "200000",
    "residents": ["http://swapi.dev/api/people/1/", "http://swapi.dev/api/people/2/",
                  "http://swapi.dev/api/people/4/", "http://swapi.dev/api/people/6/",
                  "http://swapi.dev/api/people/7/", "http://swapi.dev/api/people/8/",
                  "http://swapi.dev/api/people/9/", "http://swapi.dev/api/people/11/",
                  "http://swapi.dev/api/people/43/", "http://swapi.dev/api/people/62/"],
    "films": ["http://swapi.dev/api/films/1/", "http://swapi.dev/api/films/3/",
              "http://swapi.dev/api/films/4/", "http://swapi.dev/api/films/5/",
              "http://swapi.dev/api/films/6/"],
    "created": "2014-12-09T13:50:49.641000Z",
    "edited": "2014-12-20T20:58:18.411000Z",
    "url": "http://swapi.dev/api/planets/1/"
}]


class TestHomePageView(TestCase):
    def test_get_homepage(self):
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)

    @patch('star_wars_people.models.SWPeopleCollection.objects.download_new_collection')
    def test_post_homepage(self, fd):
        fd.return_value = SAMPLE_API_RESULT
        response = self.client.post(reverse('homepage'))
        self.assertRedirects(response, reverse('homepage'))


class TestCollectionDetailsView(TestCase):

    def setUp(self) -> None:
        self.test_filename = "test_{}.csv".format(time.time())
        with open(Path(MEDIA_ROOT, 'test.csv')) as f:
            self.collection = SWPeopleCollection.objects.create(file=File(f, name=self.test_filename))

    def test_get(self):
        response = self.client.get(reverse('collection_details', args=(self.collection.id,)))
        self.assertEqual(response.status_code, 200)

    def test_aggregation(self):
        response = self.client.get(reverse('collection_details', args=(self.collection.id,)), {'homeworld': 'on'})
        self.assertEqual(response.status_code, 200)

    def tearDown(self) -> None:
        os.remove(Path(MEDIA_ROOT, self.test_filename))


class ResponseMock:
    @classmethod
    def json(cls):
        return {'results': [{'a': 'b'}], 'next': None}


class ResponseMock2Pages:
    data = [
        {'results': [{'c': 'd'}], 'next': None},
        {'results': [{'a': 'b'}], 'next': 'nexturl'}
    ]

    def json(self):
        return self.data.pop()


class TestSWAPI(TestCase):

    @patch('star_wars_people.sw_api.requests.get')
    def test_fetch_data_one_request(self, rg):
        rg.return_value = ResponseMock()
        self.assertEqual(list(SWAPI.fetch_data('someurl')), [[{'a': 'b'}]])

    @patch('star_wars_people.sw_api.requests.get')
    def test_fetch_data_two_request(self, rg):
        rg.return_value = ResponseMock2Pages()
        self.assertEqual(list(SWAPI.fetch_data('someurl')), [[{'a': 'b'}], [{'c': 'd'}]])

    @patch('star_wars_people.sw_api.requests.get')
    def test_one_page_parameter(self, rg):
        rg.return_value = ResponseMock()
        self.assertEqual(list(SWAPI.fetch_data('someurl', one_page=True)), [[{'a': 'b'}]])


class TestModels(TestCase):

    @patch('star_wars_people.models.SWAPI.fetch_data')
    def test_dowload_new_collection(self, swapi):
        swapi.side_effect = [[SAMPLE_PLANET_RESULT], [SAMPLE_API_RESULT, SAMPLE_API_RESULT]]
        SWPeopleCollection.objects.download_new_collection()
        self.assertEqual(SWPeopleCollection.objects.count(), 1)
        sw = SWPeopleCollection.objects.get()
        table = etl.fromcsv(Path(MEDIA_ROOT, sw.file.name))
        self.assertEqual(table.len(), 5)
        os.remove(Path(MEDIA_ROOT, sw.file.name))
