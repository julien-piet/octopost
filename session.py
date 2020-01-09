""" Manage http communication """

import requests


class session():

    def __init__(self, data, max_retries=2):
        adapter = requests.adapters.HTTPAdapter(max_retries=max_retries)
        self.data = data
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def __del__(self):
        self.session.close()

    def get(self, url):
        """Wrapper around requests get, to handle errors"""
        try:
            rq = self.session.get(url)
            return rq.text
        except Exception as e:
            self.data.errors.append(e)
            self.data.log.append("Error occurred while loading url {} : {}".format(url, str(e)))
            return None

    def post(self, url, data):
        """Wrapper around requests post, to handle errors"""
        try:
            rq = self.session.post(url, data=data)
            return rq.text
        except Exception as e:
            self.data.errors.append(e)
            self.data.log.append("Error occurred while loading url {} : {}".format(url, str(e)))
            return None
