import evadb
import os
from typing import Dict, List, Text, Any
import shutil
import pandas as pd
from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from pathlib import Path
import requests
from rasa_sdk.events import SlotSet
import openai
import json

class ActionEVADB(Action):
    def name(self) -> Text:
        return "evadb_connect"

    def run (self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cursor = evadb.connect().cursor()
        open_ai_key = os.environ.get('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')
        #pd.set_option('display.max_colwidth', None)
        print(Path.cwd())
        print(tracker.get_slot('name'))
        name = tracker.get_slot('name')
        if name == "":
            dispatcher.utter_message("The name of the person you are asking about could not be located")
            return []
        lname = tracker.get_slot('lname')
        if lname == "":
            dispatcher.utter_message("The name of the person you are asking about could not be located")
            return []
        queryFor = tracker.get_slot('info_type')
        if queryFor != 'state' and queryFor != 'zip' and queryFor != 'city' and queryFor != 'address':
            dispatcher.utter_message("You are not looking for a valid piece of data")
            return []
        #sql = """CREATE DATABASE sqlite_data WITH ENGINE = 'sqlite', PARAMETERS = {
        #  "user": "eva",
        #  "password": "password",
        #  "host": "localhost",
        #  "port": "5432",
        #  "database": "evadb"
        #};"""
        #print(cursor.query(sql).df())
        #For the love of god and all things holy do not uncomment the drop table command evadb will wipe everything and force me to rename the table in all subsequent queries because its working like the table is still there and not there at the same time
        #cursor.query("""DROP TABLE IF EXISTS Addresses""")
        cursor.query("""CREATE TABLE IF NOT EXISTS Addresses (count INTEGER UNIQUE, first TEXT(30), last TEXT(30), address TEXT(40), city TEXT(30), state TEXT(2), zip INTEGER)""").df()
        cursor.query("""DELETE FROM Addresses WHERE addresses.count >= 0""").df()
        cursor.query("""LOAD CSV 'addresses.csv' INTO Addresses""").df()
        #print(cursor.query("""SELECT * FROM Addresses""").df())
        #print(cursor.query("""SELECT addresses.state FROM Addresses WHERE addresses.first = 'John'""").df())
        #print(cursor.query(f'SELECT addresses.{queryFor} FROM Addresses WHERE addresses.first = \'{name}\';').df()[0])
        #print(cursor.query(f'SELECT addresses.{queryFor} FROM Addresses WHERE addresses.first = \'{name}\';').df()[0][addresses.{queryFor}])
        print(cursor.query(f'SELECT addresses.{queryFor} FROM Addresses WHERE addresses.first = \'{name}\' AND addresses.last = \'{lname}\';').df().values)
        temp = cursor.query(f'SELECT addresses.{queryFor} FROM Addresses WHERE addresses.first = \'{name}\' AND addresses.last = \'{lname}\';').df().values
        #temp now has correct info
        #Why the hell does drop table error out??? WHere is table data stored????
        #cursor.query("DROP TABLE IF EXISTS TEXT_SUMMARY").df()
        cursor.query("""CREATE TABLE IF NOT EXISTS TEXTSUMM (summary TEXT(1000))""").df()
        #print(cursor.query(text_summarization_query).df())
        chatgpt_udf = """
            SELECT ChatGPT('Is this summary related to Ukraine russia war', summary) 
            FROM TEXTSUMM;
        """
        print(cursor.query(chatgpt_udf).df())
        if temp.size == 0:
            dispatcher.utter_message("The name of the person you are asking about could not be located")
            return []
        if queryFor == "zip":
            msg = f"{name} {lname} resides in a residence with zip code {temp[0][0]}"
            dispatcher.utter_message(text = msg)
            return []
        msg = f"{name} {lname} resides in {temp[0][0]}"
        dispatcher.utter_message(text = msg)
        return []