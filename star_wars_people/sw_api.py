import requests


class SWAPI:
    @classmethod
    def fetch_data(cls, query: str, one_page: bool = False) -> [dict, None]:
        """
        Simple helper class that allows to fetch all pages from provided URL
        :param one_page: allows to return data as dictionary with provided key instead of array
        :param query: url for list
        :return: json data
        """
        next_page = True
        while next_page:
            response = requests.get(query)
            json_data = response.json()
            yield json_data['results']
            if one_page:
                return
            if bool(json_data['next']):
                query = json_data['next']
            else:
                next_page = False
