import sys

sys.path.insert(1, "../backend/")

from flask_cachebuster import CacheBuster
from flask import Flask, redirect, url_for, render_template, request, session
from flask_pymongo import PyMongo, pymongo
from bson.objectid import ObjectId
from datetime import timedelta, datetime
import pprint
import json
import os

import uzytkownik as uz
import group
import utility
import tablica as tab

print = pprint.pprint

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/dziennik-dev"
app.secret_key = "pFosAGEabuabfaSDAd"
app.permanent_session_lifetime = timedelta(minutes=15)

config = { 'extensions': ['.js', '.css', '.csv'], 'hash_size': 5 }
cache_buster = CacheBuster(config=config)
cache_buster.init_app(app)

mongo = PyMongo(app)
db = mongo.db
tablica = tab.Tablica(db=db)

flag_refresh_messages = True;

if flag_refresh_messages:
    db.tablica.remove()     # czyszczenie poprzednich wiadomosci
for rola in ["admin", "dyrektor", "nauczyciel", "rodzic", "uczen"]:
    tablica.wstaw_wiadomosc_roli("Witaj w aplikacji!", rola)


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
        if form_email == "admin":
            session["email"] = "admin@mail.to"
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
                with open(inner_file_path, encoding='utf-8') as json_file_2:

                    temp_data = json.loads(json_file_2.read())
                    session["sections"].append(temp_data)

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
        if session["status"] == "loggedIn":
            temp_email = session["email"]
            temp_rola = session["rola"]
            # temp_klasa = # TODO stworzyć metodę i pobrać nazwę klasy do której należy uczeń
            wiad_osoby = tablica.top5_wiadomosci_osoby(temp_email)
            wiad_roli  = tablica.top5_wiadomosci_roli(temp_rola)
            #wiad_klasy = tablica.top5_wiadomosci_klasy(temp_klasa)

            lista_wiadomosci = []
            for i in wiad_osoby:
                i["formattedDate"] = utility.czas_zformatowany(i["czas"])
                lista_wiadomosci.append(i)

            #for i in wiad_klasy:
            #    i["formattedDate"] = utility.czas_zformatowany(i["czas"])
            #    lista_wiadomosci.append(i)

            for i in wiad_roli:
                i["formattedDate"] = utility.czas_zformatowany(i["czas"])
                lista_wiadomosci.append(i)

            return render_template("boardPage.html", session=session, wiadomosci=lista_wiadomosci)
        else:
            return redirect(url_for("login_page"))
        # zakładajmy, że każdy użytkownik: admin, nauczyciel, rodzic, uczeń zaczynają od "tablicy powiadomień"
        # a potem dopiero poprzez menu idą do odpowiednich sekcji

    else:
        return redirect(url_for("login_page"))


@app.route("/addUsers", methods=["POST", "GET"])
def tworz_uzytkownika_page():
    if "status" in session:
        if session["status"] == "loggedIn":
            temp_sections = session["sections"]
            flag_is_allowed = False
            for temp_section in temp_sections:
                if temp_section["name"] == "addUsersPage":
                    flag_is_allowed = True
                    break
            if flag_is_allowed:
                if request.method == "POST":
                    how_many_new_users = int(request.form["hidden"])
                    how_many_succeed = 0
                    how_many_failed = 0
                    how_many_incomplete = 0
                    how_many_skipped = 0

                    classFlag = False
                    peopleFlag = True

                    for iterator in range(how_many_new_users + 1):
                        temp_imie       = request.form["imie_"      + str(iterator)]
                        temp_nazwisko   = request.form["nazwisko_"  + str(iterator)]
                        temp_email      = request.form["email_"     + str(iterator)]
                        temp_password   = request.form["password_"  + str(iterator)]
                        temp_rola       = request.form["rola_"      + str(iterator)]
                        temp_telefon    = request.form["telefon_"   + str(iterator)]
                        temp_adres      = request.form["adres_"     + str(iterator)]

                        if temp_imie == "" and temp_nazwisko == "" and temp_email == "" and temp_password == "":    # jeśli nie wprowadzono danych
                            how_many_skipped += 1
                            continue

                        if temp_imie == "" or temp_nazwisko == "" or temp_email == "" or temp_password == "":       # jeśli dane są niekompletne
                            how_many_incomplete += 1
                            continue

                        temp_properties = {
                            "imie": temp_imie,
                            "nazwisko": temp_nazwisko,
                            "email": temp_email,
                            "password": temp_password,
                            "rola": temp_rola,
                            "telefon": temp_telefon,
                            "adres": temp_adres,
                            "login": temp_email,            # TODO usunąć LOGIN, nie potrzebujemy go, korzystamy jedynie z adresu email
                        }
                        if request.form["operacja"] == "klasa":
                            temp_properties["klasa"] = request.form["group_name"]

                        try:
                            nowy_uzytkownik = uz.Uzytkownik(properties=temp_properties, db=db)
                            if request.form["operacja"]=="klasa":
                                group_name = request.form["group_name"]
                                student_id = nowy_uzytkownik.get_user_id()
                                if(group.add_student(db=db, group_name=group_name, student_id=student_id)):
                                    classFlag = True
                                    peopleFlag = False
                                    tablica.wstaw_wiadomosc_osobie("Zostales dodany do klasy {}.".format(group_name), temp_email)
                            else:
                                tablica.wstaw_wiadomosc_osobie("Zostales dodany do systemu.", temp_email)

                            how_many_succeed += 1
                        except:
                            how_many_failed += 1



                    popups = []
                    if classFlag:
                        if how_many_succeed > 0:
                            popups.append("Dodano {} użytkowników do tej klasy.".format(how_many_succeed))

                    if peopleFlag:
                        if how_many_succeed > 0:
                            popups.append("Poprawnie dodano {} nowych użytkowników.".format(how_many_succeed))
                    if how_many_incomplete > 0:
                        popups.append("Dane {} użytkowników były niekompletne - nie zostali dodani.".format(how_many_incomplete))
                    if how_many_skipped > 0:
                        popups.append("Pominięto {} pustych wierszy.".format(how_many_skipped))
                    if how_many_failed > 0:
                        popups.append("{} użytkowników już istnieje w systemie.".format(how_many_failed))

                    group_names = group.get_all_group_names(db=db)
                    return render_template("tworzUzytkownika.html", groupNames=group_names,  popups=popups) #"Nowy uzytkownik o danych {} został utworzony".format(nowy_uzytkownik.properties)
                else:
                    group_names = group.get_all_group_names(db=db)
                    return render_template("tworzUzytkownika.html", groupNames=group_names)

    return redirect(url_for("data_problem"))


@app.route("/addClass", methods=["POST", "GET"])
def add_class_page():
    if "status" in session:
        if session["status"] == "loggedIn":
            temp_sections = session["sections"]
            flag_is_allowed = False
            for temp_section in temp_sections:
                if temp_section["name"] == "addClassPage":
                    flag_is_allowed = True
                    break
            if flag_is_allowed:
                if request.method == "POST":
                    operation = request.form["operacja"]
                    if operation == "create":
                        properties = {
                            "nazwa" : request.form["class_name"],
                            "rok-rozpoczecia": request.form["first_year"],
                            "uczniowie": []
                        }
                        group.add_group(db=db, properties=properties)
                        popup = "Poprawnie dodano grupę"
                    elif operation == "add_students":
                        how_many_new_users = int(request.form["hidden"])
                        group_name = request.form["group_name"]
                        for iterator in range(how_many_new_users + 1):
                            # print(request.form["email_" + str(iterator)])
                            student = uz.Uzytkownik(db=db, login=request.form["email_" + str(iterator)])
                            student_id = student.properties["_id"]
                            group.add_student(db=db, group_name=group_name, student_id=student_id)
                            popup = "Poprawnie dodano uczniów do grupy"
                    elif operation == "remove_students":
                        how_many_new_users = int(request.form["hidden"])
                        group_name = request.form["group_name"]
                        for iterator in range(how_many_new_users + 1):
                            # print(request.form["email_" + str(iterator)])
                            student = uz.Uzytkownik(db=db, login=request.form["email_" + str(iterator)])
                            student_id = student.properties["_id"]
                            group.remove_student(db=db, group_name=group_name, student_id=student_id)
                            popup = "Poprawnie usunięto uczniów z grupy"
                    list_of_students = uz.Uzytkownik.get_all_users(db=db)
                    group_names = group.get_all_group_names(db=db)
                    return render_template("addClass.html", listOfStudents=list_of_students, groupNames=group_names, popups=[popup])
                else:
                    list_of_students = uz.Uzytkownik.get_all_users(db=db)
                    group_names = group.get_all_group_names(db=db)
                    return render_template("addClass.html", listOfStudents=list_of_students, groupNames=group_names)

    return redirect(url_for("data_problem"))


@app.route("/editTimetable", methods=["POST", "GET"])
def edit_timetable_page():
    if "status" in session:
        if session["status"] == "loggedIn":
            temp_sections = session["sections"]
            flag_is_allowed = False
            for temp_section in temp_sections:
                if temp_section["name"] == "editTimetablePage":
                    flag_is_allowed = True
                    break
            if flag_is_allowed:
                if request.method == "POST":
                    operation = request.form["operacja"]
                    if operation == "create":
                        properties = {
                            "nazwa" : request.form["class_name"],
                            "rok-rozpoczecia": request.form["first_year"],
                            "uczniowie": []
                        }
                        group.add_group(db=db, properties=properties)
                        popup = "Poprawnie dodano grupę"
                    elif operation == "add_students":
                        how_many_new_users = int(request.form["hidden"])
                        group_name = request.form["group_name"]
                        for iterator in range(how_many_new_users + 1):
                            # print(request.form["email_" + str(iterator)])
                            student = uz.Uzytkownik(db=db, login=request.form["email_" + str(iterator)])
                            student_id = student.properties["_id"]
                            group.add_student(db=db, group_name=group_name, student_id=student_id)
                            popup = "Poprawnie dodano uczniów do grupy"
                    elif operation == "remove_students":
                        how_many_new_users = int(request.form["hidden"])
                        group_name = request.form["group_name"]
                        for iterator in range(how_many_new_users + 1):
                            # print(request.form["email_" + str(iterator)])
                            student = uz.Uzytkownik(db=db, login=request.form["email_" + str(iterator)])
                            student_id = student.properties["_id"]
                            group.remove_student(db=db, group_name=group_name, student_id=student_id)
                            popup = "Poprawnie usunięto uczniów z grupy"
                    list_of_students = uz.Uzytkownik.get_all_users(db=db)
                    group_names = group.get_all_group_names(db=db)
                    return render_template("editTimetable.html", listOfStudents=list_of_students, groupNames=group_names, popups=[popup])
                else:
                    chosen_group_name = request.args.get("group_name")
                    chosen_teacher = request.args.get("teacher")
                    chosen_classroom = request.args.get("classroom")
                    teachers = uz.Uzytkownik.get_all_teachers(db)
                    teacher_names = set()
                    for teacher in teachers:
                        print(teacher)
                        teacher_names.add(teacher["imie"] + " " + teacher["nazwisko"])
                    group_names = group.get_all_group_names(db=db)
                    # dev
                    group_timetable = {"monday": {}, "tuesday": {}, "wednesday": {}, "thursday": {}, "friday": {}}
                    teacher_timetable = {"monday": {}, "tuesday": {}, "wednesday": {}, "thursday": {}, "friday": {}}
                    classroom_timetable = {"monday": {}, "tuesday": {}, "wednesday": {}, "thursday": {}, "friday": {}}
                    return render_template("editTimetable.html",
                                           groupNames=group_names,
                                           teacherNames=teacher_names,
                                           chosenGroupName=chosen_group_name,
                                           chosenTeacher=chosen_teacher,
                                           chosenClassroom=chosen_classroom,
                                           groupTimetable=group_timetable,
                                           teacherTimetable=teacher_timetable,
                                           classroomTimetable=classroom_timetable,
                                           )

    return redirect(url_for("data_problem"))


@app.route("/sendMessage", methods=["POST", "GET"])
def send_message_page():
    if "status" in session:
        if session["status"] == "loggedIn":
            temp_sections = session["sections"]
            flag_is_allowed = False
            for temp_section in temp_sections:
                if temp_section["name"] == "sendMessagePage":
                    flag_is_allowed = True
                    break
            if flag_is_allowed:
                if request.method == "POST":
                    popups = []
                    wiadomosc = request.form["tresc"];

                    if wiadomosc == "":
                        popups.append("Nie możesz wysłać pustej wiadomości.")
                        list_of_students = uz.Uzytkownik.get_all_users(db=db)
                        group_names = group.get_all_group_names(db=db)
                        return render_template("sendMessagePage.html", listOfStudents=list_of_students, groupNames=group_names, popups=popups)

                    if request.form["operacja"] == "klasa":
                        group_name = request.form["group_name"]
                        tablica.wstaw_wiadomosc_klasie(wiadomosc, group_name)
                        tablica.wstaw_wiadomosc_osobie("Wysłałeś wiadomość klasie {}".format(group_name), session["email"])
                        popups.append("Poprawnie wysłano wiadomość klasie {}".format(group_name))
                    else:
                        user_email = request.form["email_name"]
                        tablica.wstaw_wiadomosc_osobie(wiadomosc, user_email)
                        tablica.wstaw_wiadomosc_osobie("Wysłałeś wiadomość osobie {}".format(user_email), session["email"])
                        popups.append("Poprawnie wysłano wiadomość {}".format(user_email))

                    list_of_students = uz.Uzytkownik.get_all_users(db=db)
                    group_names = group.get_all_group_names(db=db)
                    return render_template("sendMessagePage.html", listOfStudents=list_of_students, groupNames=group_names, popups=popups)
                else:
                    list_of_students = uz.Uzytkownik.get_all_users(db=db)
                    group_names = group.get_all_group_names(db=db)
                    return render_template("sendMessagePage.html", listOfStudents=list_of_students, groupNames=group_names)

    return redirect(url_for("data_problem"))





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


@app.route("/dataProblem", methods=["POST", "GET"])  # kiedy np. czas sesji się skończy
def data_problem():
    if request.method == "GET":
        session.clear()
        return render_template("dataProblem.html")
    else:
        return redirect(url_for("login_page"))


@app.route("/<wrongPageURL>", methods=["POST", "GET"])  # "pretty self explanatory"
def wrong_page(wrongPageURL):
    if request.method == "GET":
        return render_template("wrongPage.html", url=wrongPageURL)
    else:
        return redirect(url_for("startPage"))  # this is for "return home" button


if __name__ == "__main__":
    uz1 = uz.Uzytkownik()
    uz1.properties = {"sdfsdf": "sdsdfb", "sdfbsd": "sdifbdsiuf"}

    #db.uzytkownicy.drop()

    print("DEBUG: dziennik - główny moduł")
    if db.uzytkownicy.find_one({"login": "admin"}) is None:
        admin_user_0 = {"login": "admin",
                        "haslo": "admin",
                        "imie": "Administrator",
                        "nazwisko": "",
                        "email": "admin@mail.to",
                        "telefon": "",
                        "rola": "admin"
                        }
        db.uzytkownicy.insert_one(admin_user_0)
        admin_ogloszenie = {
            "email": "admin@mail.to",
            "tresc": "Witaj w naszej aplikacji!",
            "czas": utility.czas_teraz()
        }
        db.tablica.insert_one(admin_ogloszenie)

    db.uzytkownicy.create_index([('login', pymongo.ASCENDING)], unique=True)
    db.uzytkownicy.create_index([('email', pymongo.ASCENDING)], unique=True)
    app.run(debug=True)

    if db.tablica.find_one({"rola": "admin"}) is None:
        for rola in ["admin", "dyrektor", "nauczyciel", "rodzic", "uczen"]:
            tablica.wstaw_wiadomosc_roli("Witaj w aplikacji!", rola)