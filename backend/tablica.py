import re
import utility


class Tablica:

    def __init__(self, db=None):
        self.db = db

    def wstaw_wiadomosc_roli(self, wiadomosc, rola, temp_time=0):
        if temp_time == 0:
            temp_time = utility.czas_teraz()
        ogloszenie = {
            "rola": rola,
            "tresc": wiadomosc,
            "czas": temp_time
        }
        try:
            self.db.tablica.insert_one(ogloszenie)
        except:
            print("Nie powiodło się dodawanie ogloszenia dla roli {}".format(rola))

    def wstaw_wiadomosc_klasie(self, wiadomosc, klasa, temp_time=0):
        if temp_time == 0:
            temp_time = utility.czas_teraz()
        ogloszenie = {
            "klasa": klasa,
            "tresc": wiadomosc,
            "czas": temp_time
        }
        try:
            self.db.tablica.insert_one(ogloszenie)
        except:
            print("Nie powiodło się dodawanie ogloszenia dla klasy {}".format(klasa))

    def wstaw_wiadomosc_osobie(self, wiadomosc, email, temp_time=0):
        if temp_time == 0:
            temp_time = utility.czas_teraz()
        ogloszenie = {
            "email": email,
            "tresc": wiadomosc,
            "czas": temp_time
        }
        try:
            self.db.tablica.insert_one(ogloszenie)
        except:
            print("Nie powiodło się dodawanie ogloszenia dla użytkownika {}".format(email))

    def wszystkie_wiadomosci_roli(self, rola):
        return self.db.tablica.find({"rola": rola})

    def wszystkie_wiadomosci_klasy(self, klasa):
        return self.db.tablica.find({"klasa": klasa})

    def wszystkie_wiadomosci_osoby(self, email):
        return self.db.tablica.find({"email": email})

    def top5_wiadomosci_roli(self, rola):
        return self.db.tablica.find({"rola": rola}).sort("czas", -1).limit(5)

    def top5_wiadomosci_klasy(self, klasa):
        return self.db.tablica.find({"klasa": klasa}).sort("czas", -1).limit(5)

    def top5_wiadomosci_osoby(self, email):
        return self.db.tablica.find({"email": email}).sort("czas", -1).limit(5)
