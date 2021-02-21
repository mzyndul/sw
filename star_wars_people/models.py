from collections import OrderedDict
from pathlib import Path
from time import time
from typing import Sequence

import petl as etl
from django.conf import settings
from django.db import models

from djangoProject.settings import CSV_PATH
from star_wars_people.sw_api import SWAPI


class SWPeopleCollectionManager(models.Manager):
    @classmethod
    def download_new_collection(cls) -> None:
        # store small dictionary for later on transofrmation
        planets_arr = {}
        for planets in SWAPI.fetch_data(settings.SW_PLANETS_URL):
            planets_arr.update({i['url']: i['name'] for i in planets})

        create = True
        file_name = '{}.csv'.format(time())
        csv_path = Path(CSV_PATH, file_name)

        for people in SWAPI.fetch_data(settings.SW_PEOPLE_URL):
            table = etl.fromdicts(people, header=[
                'name', 'height', 'mass', 'hair_color', 'skin_color', 'eye_color',
                'birth_year', 'gender', 'homeworld', 'edited'
            ]).convert(
                'edited', lambda v: v[0:10]
            ).convert(
                'homeworld', lambda v: planets_arr.get(v, '')
            ).rename('edited', 'date')

            if create:
                etl.tocsv(table, source=csv_path, write_header=True)
                create = False
            else:
                etl.appendcsv(table, source=csv_path)

        c = SWPeopleCollection()
        c.file.name = file_name
        c.save()


class SWPeopleCollection(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    file = models.FileField()
    objects = SWPeopleCollectionManager()

    def get_table(self) -> etl.Table:
        return etl.fromcsv(self.file.path)

    def get_aggregate_data(self, aggregation_keys: Sequence) -> etl.Table:
        agg = OrderedDict()
        agg['count'] = len
        return etl.aggregate(
            self.get_table(),
            key=aggregation_keys if len(aggregation_keys) > 1 else aggregation_keys[0],
            aggregation=agg
        ).convert('count', lambda v: str(v))
