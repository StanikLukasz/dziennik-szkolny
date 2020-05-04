import sys
sys.path.insert(1, "../backend/")

from flask import Flask, redirect, url_for, render_template, request, session
from flask_pymongo import PyMongo, pymongo
from bson.objectid import ObjectId
from datetime import timedelta
import pprint

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
            return redirect(url_for("mainPage"))
        else:
            return redirect(url_for("dataProblem"))
    else:
        return redirect(url_for("loginPage"))



@app.route("/login", methods=["POST", "GET"])  # prosta stronka z loginem
def loginPage():
    if request.method == "POST":
        formEmail = request.form["email"]
        formPassword = request.form["password"]

        if len(formEmail) < 3 or len(formPassword) < 3:  # zabezpieczenie przed błędnym wprowadzaniem
            return render_template("loginPage.html")

        # sprawdź tutaj czy takie konto figuruje w bazie danych, jeśli nie - zwróć error
        try:
            uzytkownik = uz.Uzytkownik(db=db, login=formEmail)
        except FileNotFoundError:
            return render_template("loginPage.html", wrongPassword=True)
        else:
            rola = uzytkownik.properties["rola"]
            user_id = uzytkownik.get_user_id()
            # return redirect(url_for("mainPage_dev", rola=rola, user_id=user_id)) DEV

        # dane sesji:
        session.permanent = True
        session["email"] = formEmail
        session["password"] = formPassword  # to idzie później w kosz, nie chcemy hasła trzymać w sesji, używamy go jedynie do autentykacji na początku
        session["status"] = "loggedIn"
        session["rola"] = rola
        session["user_id"] = user_id

        return redirect(url_for("mainPage"))
    else:
        if "status" in session:
            if session["status"] == "loggedIn":
                return redirect(url_for("mainPage"))
            else:
                return redirect(url_for("dataProblem"))
        else:
            return render_template("loginPage.html")


@app.route("/main")  # rozumiem to jako pierwsza strona, jaką już zalogowany użytkownik zobaczy, czyli tam gdzie będzie lista funkcji i np. tablica
def mainPage():
    if "status" in session:
        if "email" in session:  # tu jest poprawna sesja
            email = session["email"]
            if "rola" in session:
                rola = session["rola"]
                if rola == "admin":
                    return render_template("adminMainPage.html", rola=rola)
                else:
                    return render_template("boardPage.html", email=email)
            else:
                return render_template("boardPage.html", email=email)
        else:
            return redirect(url_for("loginPage"))
    else:
        return redirect(url_for("loginPage"))


@app.route("/main/tworzUzytkownika", methods=["POST", "GET"])
def tworzUzytkownikaPage():
    if request.method == "POST":
        nowy_uzytkownik = uz.Uzytkownik(properties={"imie": request.form["imie"],
                           "nazwisko": request.form["nazwisko"],
                           "mail": request.form["mail"],
                           "telefon": request.form["telefon"],
                           "adres": request.form["adres"],
                           "rola": request.form["rola"],
                           "login": request.form["mail"]  # TODO generowanie loginu
                           }, db=db)
        return "Nowy uzytkownik o danych {} został utworzony".format(nowy_uzytkownik.properties)
    else:
        return render_template("tworzUzytkownika.html")


@app.route("/main/ukladajPlan")
def ukladajPlanPage():
    return "placeholder"


@app.route("/logout", methods=["POST", "GET"])
def logoutPage():
    if request.method == "GET":
        try:
            session.clear()
            return render_template("logoutPage.html")
        except:
            return render_template(url_for("dataProblem"))
    else:
        return redirect(url_for("loginPage"))


@app.route("/dataProblem", methods=["POST", "GET"])  # kiedy np. braknie gdzieś twojego maila w sesji, bądź czas sesji się skończy
def dataProblem():
    if request.method == "GET":
        session.clear()
        return render_template("dataProblem.html")
    else:
        return redirect(url_for("loginPage"))


@app.route("/<wrongPageURL>", methods=["POST", "GET"])  # "pretty self explanatory", zastąpienie wadliwego adresu naszą stronką, aby nie było basic error screen'a
def wrongPage(wrongPageURL):
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
