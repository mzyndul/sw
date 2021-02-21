# Intro

Project was tested on python3.8.
It requires 3 libraries to run:

1. Django
1. petl
1. requests

Project relay on external API under: https://swapi.dev.

For simplicity, it uses sqlite database.

# Installation

1. create new virtualenv and install requirements:

```shell
pip install -r requirements.txt
```

2. Run migrations

```shell
python manage.py migrate
```

3. Run server

```shell
python manage.py runserver
```

4. Open browser http://localhost:8000

# Developer Notes

1. SWAPI helper (star_wars_people.sw_api.py:SWAPI) uses generator to load data in parts.
1. Project test coverage is 100% - but probably it could be done better.
1. I assumed that all characters would eventually need all planets, so I downloaded planets in first place. Those are stored in memory, but in case this wuould get huge, it could be replaced with Cache/Redis or Database.
1. Actually this was the first time I used petl. Nice library.
1. First page is not paginated, probably would be good to implement that if we would expect a lot of records.
1. Filtering and "load more" works together.

## Speed Notes / Improvements

1. Running more thread/processes would increas amount of pages that could be downloaded at once ( on Fetch ). Each process would create its own CSV file and at the end when all processes would finish, the last operation would be to merge all files together. This would prevent any "write access" collision.
   1. Adjust page size - on multithread it could be worth to "experiment" with different page size to find which one is most efficient. 
1. For better frontend expirience it would be good to implement SPA or at least partly ajax ( for "load more" for example).
1. Rendering table directly from etl to html probably would be faster.
1. Initially I thought that on second "fetch" I could use "edited" flag to minize number of requests, but that data is available on details so anyway I had to download it again. In other hand if this would be solution for mass data, then fetching data and checking if it exists in some local storage would save "saving time" of this record.
1. Since API is kind limited I was not able to change page_size limit OR filter by "edited" field which would allow minimaze requests.
1. Some django middlewares were removed for speed improvments ( micro optimization )
1. In current shape, store files in ramdisk could speed up read/write operations ( on "collection details" file could be copied to ramdisk and then ETL used, which should be faster as it goes with big memory usage, something that petl tried to avoid.)
1. Implementing queue system like celery would speed up the process.
1. Storing everything in SLQ/NOSQL would speed up operations.
1. Implementing cache on django would speed up page rendering ( template cache, default collection view cache)
1. Using E-tag on request would speed up initial page rendering
1. Assuming SWAPI can be hosted on multiple servers:
   1. use multithread to use all available CPUS ( or more machines if needed)
   1. load data from multiple places (avoiding network limitation for one api provider). For example having 10 API endpoints for the same database but different URL, system could calculate how to split all requsts and split it into available servers.
   1. put data in celery ( or other queue system )
   1. process data on a separate server dedicated for celery tasks processing 