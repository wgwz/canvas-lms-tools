import argparse
import logging
import configparser
from requests.auth import HTTPBasicAuth
import requests
from xml.etree import ElementTree

class Bowker_Api_Client():
    """
    The following fields are used to pass credientals 
    to bowker from the requests library
    """

    def __init__(self, bowker_ini, isbn):
        self.config = configparser.ConfigParser()
        self.config.read(bowker_ini)
        self.username = self.config.get('Bowker_Credientals','Username')
        self.password = self.config.get('Bowker_Credientals','Password')
        self.bowkerUrl = self.config.get('Bowker_Credientals','bowkerUrl')
        self.bowkerSearchFields = self.config.get('Bowker_Credientals','bowkerSearchFields')
        self.isbn = isbn
        self.query = self.config.get('Bowker_Credientals','query')

    """
    The method below connects to Bowker and then returns xml, 
    only to be converted to a dict for easier parsing.   
    """
    def connect_to_bowker_and_get_info(self):
        xml_response = requests.get(
            self.bowkerUrl+self.isbn+self.query+self.bowkerSearchFields,
            auth=HTTPBasicAuth(self.username, self.password))
        #below is the xml repsonse being converted to a dict
        tree = ElementTree.fromstring(xml_response.content)
        book_info_dict = {}
        for element in tree.iter('*'):
            book_info_dict[element.tag]=element.text
        return book_info_dict
        