import sys

sys.path.insert(1, "../backend/")

from flask import Flask, redirect, url_for, render_template, request, session
from flask_pymongo import PyMongo, pymongo
from bson.objectid import ObjectId
from datetime import timedelta
import pprint
import json
import os

import uzytkownik as uz


print = pprint.pprint

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/dziennik-dev"
app.secret_key = "pFosAGEabuabfaSDAd"
app.permanent_session_lifetime = timedelta(minutes=15)

mongo = PyMongo(app)
db = mongo.db


@app.route("/")  # jeśli nie jesteś zalogowany -> przekieruj na stronę logowania, w przeciwnym wypadku -> mainPage
def startPage():
    if "status" in session:
        if session["status"] == "loggedIn":
            return redirect(url_for("main_page"))
        else:
            return redirect(url_for("data_problem"))
    else:
        return redirect(url_for("login_page"))


@app.route("/login", methods=["POST", "GET"])  # prosta stronka z loginem
def login_page():
    if request.method == "POST":
        form_email = request.form["email"]
        form_password = request.form["password"]

        if len(form_email) < 3 or len(form_password) < 3:  # zabezpieczenie przed błędnym wprowadzaniem
            return render_template("loginPage.html")

        # sprawdź tutaj czy takie konto figuruje w bazie danych, jeśli nie - zwróć error
        try:
            uzytkownik = uz.Uzytkownik(db=db, login=form_email)
        except FileNotFoundError:
            return render_template("loginPage.html", wrongPassword=True)

        else:
            rola = uzytkownik.properties["rola"]
            user_id = uzytkownik.get_user_id()
            #return redirect(url_for("mainPage_dev", rola=rola, user_id=user_id))  # DEV

        # dane sesji:
        session.permanent = True
        session["email"] = form_email
        # session["password"] = form_password  # to idzie później w kosz, nie chcemy hasła trzymać w sesji, używamy go jedynie do autentykacji na początku
        session["status"] = "loggedIn"
        session["rola"] = rola
        session["user_id"] = user_id
        session["imie"] = uzytkownik.properties["imie"]
        session["nazwisko"] = uzytkownik.properties[
            "nazwisko"]  # TODO wymusić na każdym użytkowniku posiadanie imienia i nazwiska w bazie danych
        session["sections"] = []

        # tutaj pobieram dane o liście kategorii, do których dana rola ma dostep

        current_directory = os.path.dirname(__file__)
        temp_path = os.path.join(current_directory, 'static', 'permissions', str(rola) + ".json")

        with open(temp_path) as json_file_1:
            permission_data = json.loads(json_file_1.read())
            for x in permission_data["sections"]:

                inner_file_path = os.path.join(current_directory, x)
                with open(inner_file_path) as json_file_2:

                    temp_data = json.loads(json_file_2.read())
                    session["sections"].append(temp_data)



            #session["sections"] = permission_data["sections"]  # zwracana jest już lista ścieżek do sekcji
            # TODO pobrać dane z wszystkich plików w tych ścieżkach i w template wygenerować odpowiednią listę




        return redirect(url_for("main_page"))

    else:
        if "status" in session:
            if session["status"] == "loggedIn":
                return redirect(url_for("main_page"))
            else:
                return redirect(url_for("data_problem"))
        else:
            return render_template("loginPage.html")


@app.route(
    "/main")  # rozumiem to jako pierwsza strona, jaką już zalogowany użytkownik zobaczy, czyli tam gdzie będzie lista funkcji i np. tablica
def main_page():
    if "status" in session:
        return render_template("boardPage.html", session=session)
        # zakładajmy, że każdy użytkownik: admin, nauczyciel, rodzic, uczeń zaczynają od "tablicy powiadomień"
        # a potem dopiero poprzez menu idą do odpowiednich sekcji

    #    if "email" in session:  # tu jest poprawna sesja
    #        email = session["email"]
    #        if "rola" in session:
    #            rola = session["rola"]
    #            if rola == "admin":
    #                return render_template("adminMainPage.html", rola=rola)
    #            else:
    #                return render_template("boardPage.html", email=email)
    #        else:
    #            return render_template("boardPage.html", email=email)
    #    else:
    #        return redirect(url_for("loginPage"))

    else:
        return redirect(url_for("login_page"))


@app.route("/addUser", methods=["POST", "GET"])
def tworz_uzytkownika_page():
    if "status" in session:
        if session["status"] == "loggedIn":
            temp_sections = session["sections"]
            flag_is_allowed = False
            for temp_section in session["sections"]:
                if temp_section["name"] == "addUsersPage":
                    flag_is_allowed = True
                    break
            if flag_is_allowed:
                if request.method == "POST":
                    nowy_uzytkownik = uz.Uzytkownik(properties={"imie": request.form["imie"],
                                                                "nazwisko": request.form["nazwisko"],
                                                                "mail": request.form["mail"],
                                                                "telefon": request.form["telefon"],
                                                                "adres": request.form["adres"],
                                                                "rola": request.form["rola"],
                                                                "login": request.form["mail"]
                                                                # TODO generowanie loginu     # TODO
                                                                }, db=db)
                    return "Nowy uzytkownik o danych {} został utworzony".format(nowy_uzytkownik.properties)
                else:
                    return render_template("tworzUzytkownika.html")

    return redirect(url_for("data_problem"))




@app.route("/main/ukladajPlan")
def ukladaj_plan_page():
    return "placeholder"


@app.route("/logout", methods=["POST", "GET"])
def logout_page():
    if request.method == "GET":
        try:
            session.clear()
            return render_template("logoutPage.html")
        except:
            return render_template(url_for("data_problem"))
    else:
        return redirect(url_for("login_page"))


@app.route("/dataProblem",
           methods=["POST", "GET"])  # kiedy np. braknie gdzieś twojego maila w sesji, bądź czas sesji się skończy
def data_problem():
    if request.method == "GET":
        session.clear()
        return render_template("dataProblem.html")
    else:
        return redirect(url_for("login_page"))


@app.route("/<wrongPageURL>", methods=["POST",
                                       "GET"])  # "pretty self explanatory", zastąpienie wadliwego adresu naszą stronką, aby nie było basic error screen'a
def wrong_page(wrongPageURL):
    if request.method == "GET":
        return render_template("wrongPage.html", url=wrongPageURL)
    else:
        return redirect(url_for("startPage"))  # this is for "return home" button


if __name__ == "__main__":
    uz1 = uz.Uzytkownik()
    uz1.properties = {"sdfsdf": "sdsdfb", "sdfbsd": "sdifbdsiuf"}

    print("DEBUG: dziennik - główny moduł")
    if db.uzytkownicy.find_one({"login": "admin"}) is None:
        admin_user_0 = {"login": "admin",
                        "haslo": "admin",
                        "imie": "Admin",
                        "nazwisko": "",
                        "mail": "",
                        "telefon": "",
                        "rola": "admin"
                        }
        db.uzytkownicy.insert_one(admin_user_0)
    db.uzytkownicy.create_index([('login', pymongo.ASCENDING)], unique=True)
    db.uzytkownicy.create_index([('mail', pymongo.ASCENDING)], unique=True)
    app.run(debug=True)
