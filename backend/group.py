def add_group(db, properties):
    return db.grupy.insert_one(properties)


def get_all_groups(db):
    return db.grupy.find()


def get_all_group_names(db):
    groups = db.grupy.find()
    group_names = set()
    for group in groups:
        group_names.add(group["nazwa"])
    return group_names


def add_student(db, group_name, student_id):
    abc = db.grupy.update_one(
        {"nazwa": group_name},
        {"$addToSet": {"uczniowie": student_id}}
    )
    return abc.acknowledged     # metoda zwraca, czy dodanie do klasy się powiodło


def remove_student(db, group_name, student_id):
    db.grupy.update_one(
        {"nazwa": group_name},
        {"$pull": {"uczniowie": student_id}}
    )
