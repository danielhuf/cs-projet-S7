# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# Do not forget to open an action server by typing the command "rasa run actions"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet, FollowupAction, EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from datetime import date
import sqlite3

datapath = "/Users/titouannguyenhuynh/Desktop/Rasa/projet-s7-groupe-6/models/data/BDD.db"
conn = sqlite3.connect(datapath)
cursor = conn.cursor()

class ActionSignalMail(Action):

    def name(self) -> Text:
        return "action_signal_mail"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mailvalue = next(tracker.get_latest_entity_values("gender"),None)
        name = tracker.slots.get("gender")
        mailvalue = str(mailvalue)
        text = "Votre adresse mail est "+ mailvalue + str(name)
        dispatcher.utter_message(text)

        return []

class ActionSetUserData(Action):

    def name(self) -> Text:
        return "set_user_data"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        userID = tracker.slots.get("social_security_number")
        nom = tracker.slots.get("name")
        date = tracker.slots.get("birth_date")
        sexe = tracker.slots.get("gender")
        chronique = tracker.slots.get("medical_past")

        cursor.execute(f"INSERT INTO User_Stat VALUES ('{userID}','{nom}', '{date}','{sexe}','{chronique}')")
        conn.commit()
        return []

class ActionGetUserData(Action):

    def name(self) -> Text:
        return "get_user_data"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        userID = tracker.slots.get("social_security_number")

        """ Improvement idea : in case the userID doesn't match any of the ones that are in the database, empty the slot with 
        SlotSet(key = "name", value = "Mary"), and ask again maybe starting the first_entry form again would be sufficient 
        because all the other slots are still filled """

        cursor.execute(f'SELECT * FROM User_Stat WHERE UserId = "{userID}"')
        entry = cursor.fetchone()

        SlotSet("name",str(entry[1]))
        SlotSet("birth_date",str(entry[2]))
        SlotSet("gender",str(entry[3]))
        SlotSet("medical_past",str(entry[4]))
        SlotSet("already_registered",True)

        dispatcher.utter_message(text=f"Welcome back {entry[1]}!")

        return [SlotSet("name",str(entry[1])),SlotSet("birth_date",str(entry[2])),SlotSet("gender",str(entry[3])),SlotSet("medical_past",str(entry[4])), SlotSet("already_registered",True)]

    # @staticmethod
    # def required_slots(tracker: Tracker) -> List[Text]:
    #     return ["answer_health_form"]

    # def slot_mappings(self) -> Dict[Text, Any]:
    #     return {
    #         "answer_health_form": self.from_text(bool)
    #     }

    # def submit(
    #     self,
    #     dispatcher: CollectingDispatcher,
    #     tracker: Tracker,
    #     domain: Dict[Text, Any],
    # ) -> List[Dict[Text, Any]]:
    #     intent = tracker.latest_message.get("intent")
    #     print("submit running")
    #     if intent == "affirm":
    #         answer = True
    #     elif intent == "deny":
    #         answer = False
    #     else:
    #         self.utter_yes_or_no(dispatcher, tracker, domain)
    #         return []     
    #     if answer:
    #         dispatcher.utter_template("utter_confirm_health_form")
    #         return [FollowupAction("confirm_health_form")]
    #     else:
    #         dispatcher.utter_template("utter_deny_health_form")
    #         return [FollowupAction("confirm_health_form")]

    # def utter_yes_or_no(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    #     dispatcher.utter_template("utter_yes_or_no")
    #     return []


class ActionSetLatestHealthForm(Action):

    def name(self) -> Text:
        return "set_latest_health_form"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        userID = tracker.slots.get("social_security_number")
        Date = date.today().strftime("%d/%m/%Y")
        localisation = tracker.slots.get("location")
        SleepingTime = tracker.slots.get("start_sleep")
        WakeUpTime = tracker.slots.get("end_sleep")

        cursor.execute(f"INSERT INTO User_Dynam VALUES ('{userID}', '{Date}','{localisation}','{SleepingTime}','{WakeUpTime}')")
        conn.commit()
        return []

class ActionSetHobbyEntry(Action):

    def name(self) -> Text:
        return "set_hobby_entry"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        userID = tracker.slots.get("social_security_number")
        Date = date.today().strftime("%d/%m/%Y")
        hobby = tracker.slots.get("hobby")
        #hobby_opinion = tracker.slots.get("hobby_opinion")

        cursor.execute(f"INSERT INTO Loisirs VALUES ('{userID}', '{Date}','{hobby}',NULL)")
        conn.commit()
        return []

class ActionAskHobbyOpinion(Action):

    def name(self) -> Text:
        return "ask_hobby_opinion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        #Getting the ID of the current user
        userID = tracker.slots.get("social_security_number")

        cursor.execute(f'SELECT * FROM Loisirs WHERE UserID ="{userID}" ')
        entry = cursor.fetchone()
        if entry != None:

            cursor.execute(f'SELECT * FROM Loisirs WHERE Opinion = NULL AND UserID ="{userID}" ')
            emptyopinion = cursor.fetchone()

            if entry != None :
                #It means we still need to fill the opinions on some of the opinions the user gave
                date = str(emptyopinion[1])
                hobby = str(emptyopinion[2])
                dispatcher.utter_message(f"You mentioned {hobby} as a hobby, could you give me your newest opinion on the matter?")
                return [SlotSet("hobby_date",date),SlotSet("hobby",hobby)]
            else :

                #We will ask to renew the opinion on one of the hobbies we talked about
                """ improvement idea : improve this system by selecting the oldest one, maybe using ORDER BY and fetch(-1) instead of fetchone() """
                
                date = str(entry[1])
                hobby = str(entry[2])
                dispatcher.utter_message(f"You mentioned {hobby} as a hobby, could you give me your newest opinion on the matter?")
                return [SlotSet("hobby_date",date),SlotSet("hobby",hobby)]
        else:
            #This means the user never entered a hobby in the first place.
            return [FollowupAction("hobby_form")]


class ActionSetHobbyOpinion(Action):

    def name(self) -> Text:
        return "set_hobby_opinion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        userID = tracker.slots.get("social_security_number")
        hobby_date = tracker.slots.get("hobby_date")
        new_date = date.today().strftime("%d/%m/%Y") #We want to update the date when we declared this new opinion
        hobby = tracker.slots.get("hobby")
        hobby_opinion = str(tracker.latest_message)

        cursor.execute(f"UPDATE Loisirs SET Opinion = '{hobby_opinion}' Date = '{new_date}' WHERE Date = '{hobby_date}' AND UserID ='{userID}' AND Activité = '{hobby}'")

        return []

class ActionCheckLatestHealthForm(Action):

    def name(self) -> Text:
        return "check_latest_health_form"

    def run(self, dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        userID = tracker.slots.get("social_security_number")
        Date = date.today().strftime("%d/%m/%Y")

        cursor.execute(f'SELECT * FROM User_Dynam WHERE UserId = "{userID}" AND ChatDate = "{Date}"')
        entry = cursor.fetchone()
        # If the user hasn't filled the health form today
        if entry:
            return [SlotSet("filled_today", True)]
        dispatcher.utter_message(text="I noticed you haven't filled the health form today. Would you like to fill it now?")
        return [SlotSet("filled_today", False)]

class TestDb(Action):

    def name(self) -> Text:
        return "test_db"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        #cursor.execute(f"INSERT INTO User_Stat VALUES ('1111111111111','John Doe', '05/01/2002','male','I had chronic pneumonia')")
        #conn.commit()
        dispatcher.utter_message(text=str(tracker.slots.get("birth_date")))

        return []

class ValidateAnswerHealthForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_answer_health_form"

    
    def validate_answer_health_form_slot(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate if the user wants to answer the health form."""
        if tracker.get_intent_of_latest_message() == "affirm":
            dispatcher.utter_message(
                text="Great! Let's go! Say 'Ready' to begin."
            )
            return {"answer_health_form_slot": True}
        if tracker.get_intent_of_latest_message() == "deny":
            dispatcher.utter_message(
                text="Ok, I'll remind you later."
            )
            return {"answer_health_form_slot": False}
        return {"answer_health_form_slot": None}

class AskToAnswerHealthForm(Action):
    def name(self) -> Text:
        return "action_ask_answer_health_form_slot"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(
            text="Would you like to answer the health form?",
            buttons=[
                {"title": "yes", "payload": "/affirm"},
                {"title": "no", "payload": "/deny"},
            ],
        )
        return []
