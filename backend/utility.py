from datetime import datetime


def czas_teraz():
    czas = datetime.now()
    czas_2 = datetime.fromtimestamp(0)
    return (czas - czas_2).total_seconds()


def czas_zformatowany(czas_w_sekundach):
    return datetime.fromtimestamp(czas_w_sekundach).strftime("%Y-%m-%d %H:%M")
