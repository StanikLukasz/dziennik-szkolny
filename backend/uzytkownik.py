import re

class Uzytkownik:   # trzeba dodać hasła i sprawdzanie haseł (nawet jeśli proste bez hashowania)

    def __init__(self, properties=dict(), db=None, login=None):
        if login is None:
            self.properties = properties
            if properties != {}:
                db.uzytkownicy.insert_one(properties)
        else:
            if re.search("@", login) is None:
                document = db.uzytkownicy.find_one({"login": login}) # loginem jest nazwa użytkownika
            else:
                document = db.uzytkownicy.find_one({"email": login}) # loginem jest adres e-mail
            if document is None:
                raise FileNotFoundError()
            else:
                self.properties = document

    def get_user_id(self):
        return str(self.properties["_id"])

    @staticmethod
    def get_all_users(db):
        return db.uzytkownicy.find()