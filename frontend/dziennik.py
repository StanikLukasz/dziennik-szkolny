import sys

from flask import Flask, redirect, url_for, render_template, request
from flask_pymongo import PyMongo, pymongo
from bson.objectid import ObjectId
import pprint

sys.path.insert(1, "../backend")
import uzytkownik as uz

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/dziennik-dev"
mongo = PyMongo(app)
db = mongo.db
print = pprint.pprint


@app.route("/")  # jeśli nie jesteś zalogowany -> przekieruj na stronę logowania, w przeciwnym wypadku -> mainPage
def startPage():
    # if loggedIn:
    #    go to mainPage()
    # else:
    return redirect(url_for("loginPage"))


@app.route("/login", methods=["POST", "GET"])  # prosta stronka z loginem
def loginPage():
    if request.method == "POST":
        formLogin = request.form["email"]
        formPassword = request.form["password"]
        try:
            uzytkownik = uz.Uzytkownik(db=db, login=formLogin)
        except FileNotFoundError:
            return "Nie znaleziono uzytkownika!"
        else:
            rola = uzytkownik.properties["rola"]
            user_id = uzytkownik.get_user_id()
            return redirect(url_for("mainPage", rola=rola, user_id=user_id))
    else:
        return render_template("loginPage.html")

@app.route("/main/<rola>/<user_id>")
def mainPage (rola, user_id):
    if rola == "admin":
        return render_template("adminMainPage.html", rola="heje")
    else:
        return "witam pana " + rola

@app.route("/main/tworzUzytkownika", methods=["POST", "GET"])
def tworzUzytkownikaPage():
    if request.method == "POST":
        nowy_uzytkownik = uz.Uzytkownik(properties={"imie": request.form["imie"],
                           "nazwisko": request.form["nazwisko"],
                           "mail": request.form["mail"],
                           "telefon": request.form["telefon"],
                           "adres": request.form["adres"],
                           "rola": request.form["rola"]
                           }, db=db)
        return "Nowy uzytkownik o danych {} został utworzony".format(nowy_uzytkownik.properties)
    else:
        return render_template("tworzUzytkownika.html")

@app.route("/main/ukladajPlan")
def ukladajPlanPage():
    return "czynascie"

@app.route("/main-<name>-<password>")  # rozumiem to jako pierwsza strona, jaką już zalogowany użytkownik zobaczy, czyli tam gdzie będzie lista funkcji i np. tablica
def mainPage2(name, password):
    return render_template("boardPage.html", email=name, password=password)


@app.route("/<wrongPageURL>", methods=["POST", "GET"])  # "pretty self explanatory", zastąpienie wadliwego adresu naszą stronką, aby nie było basic error screen'a
def wrongPage(wrongPageURL):
    if request.method == "GET":
        return render_template("wrongPage.html", url=wrongPageURL)
    else:
        return redirect(url_for("startPage")) # this is for "return home" button


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
