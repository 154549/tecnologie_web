from users.models import Profilo, Interesse, DjangoPost, Djangroup, PostGruppo
from django.contrib.auth.models import User
from datetime import date


def init_db():

    try:
        if Profilo.objects.all().count() > 0:
            return
    except Exception:
        return

    lista_interessi = [
        "programmazione", "calcio", "musica", "fotografia",
        "cucina", "viaggi", "cinema", "gaming",
        "ciclismo", "lettura", "tecnologia", "arte"
    ]

    interessi_db = {}
    for nome in lista_interessi:
        i_db = Interesse()
        i_db.nome = nome
        i_db.save()
        interessi_db[nome] = i_db

    lista_utenti = [
        ("mario","mario@djangbook.it","password123","Mario","Rossi",
         "appassionato di tecnologia dal 95",False,["programmazione","calcio","tecnologia"],"profile_pics/dbpfp/Mario Rossi.jpg",date(1995,3,12)),
        ("andrea","andrea@djangbook.it","password123","Andrea","Verdi",
         "amante della musica dal 98",False,["musica","viaggi","fotografia"],"profile_pics/dbpfp/Andrea Verdi.jpg",date(1998,7,25)),
        ("giovanna","giovanna@djangbook.it","password123","Giovanna","Violi",
         "aspirante fotografa dal 97",False,["fotografia","cucina","arte"],"profile_pics/dbpfp/Giovanna Violi.jpg",date(1997,11,8)),
        ("maria","maria@djangbook.it","password123","Maria","Bianchi",
         "in fissa con i videogiochi dalla nascita",True,["programmazione","gaming","cinema"],"profile_pics/dbpfp/Maria Bianchi.jpg",date(2001,1,30)),
        ("marco","marco@djangbook.it","password123","Marco","Azzurri",
         "corro in bicicletta da quando sono nato",False,["ciclismo","lettura","cucina"],"profile_pics/dbpfp/Marco Azzurri.jpg",date(1993,5,17)),
    ]

    utenti_db = {}
    for username, email, pwd, nome, cognome, bio, privato, interessi, foto, nascita in lista_utenti:
        u = User()
        u.username = username
        u.email = email
        u.first_name = nome
        u.last_name = cognome
        u.set_password(pwd)
        u.save()

        p = Profilo()
        p.user = u
        p.bio = bio
        p.data_nascita = nascita
        p.is_privato = privato
        p.immagine_profilo = foto
        p.save()

        for int_nome in interessi:
            p.interessi.add(interessi_db[int_nome])

        utenti_db[username] = p

    utenti_db["mario"].amici.add(utenti_db["andrea"].user)
    utenti_db["andrea"].amici.add(utenti_db["mario"].user)

    utenti_db["mario"].amici.add(utenti_db["giovanna"].user)
    utenti_db["giovanna"].amici.add(utenti_db["mario"].user)

    utenti_db["andrea"].amici.add(utenti_db["maria"].user)
    utenti_db["maria"].amici.add(utenti_db["andrea"].user)

    su = User.objects.filter(username="enrik").first()
    if su is None:
        su = User.objects.create_superuser(username="enrik", email="enrik@djangbook.it", password="password123")
    su.first_name = "Enrik"
    su.last_name = "Lapi"
    su.is_staff = True
    su.is_superuser = True
    su.save()

    p_su = Profilo()
    p_su.user = su
    p_su.bio = "ho scritto DjangBook dalla mia camera da letto"
    p_su.data_nascita = date(2001, 3, 4)
    p_su.immagine_profilo = "founder.jpg"
    p_su.save()

    for username in utenti_db:
        utenti_db[username].amici.add(su)
        p_su.amici.add(utenti_db[username].user)

    post1 = DjangoPost()
    post1.autore = utenti_db["mario"].user
    post1.testo = "questo è il primissimo django!"
    post1.save()

    post2 = DjangoPost()
    post2.autore = utenti_db["andrea"].user
    post2.testo = "ciao a tutti!"
    post2.save()

    g1 = Djangroup()
    g1.nome = "Noi Programmatori Django"
    g1.descrizione = "un gruppo per tutti gli amanti di django!"
    g1.creatore = utenti_db["mario"].user
    g1.save()
    g1.admin.add(utenti_db["mario"].user)
    g1.membri.add(utenti_db["mario"].user)
    g1.membri.add(utenti_db["maria"].user)
    g1.interessi.add(interessi_db["programmazione"])
    g1.interessi.add(interessi_db["tecnologia"])

    g2 = Djangroup()
    g2.nome = "Noi Amanti della Fotografia"
    g2.descrizione = "un gruppo dove postare le nostre foto migliori!"
    g2.creatore = utenti_db["giovanna"].user
    g2.save()
    g2.admin.add(utenti_db["giovanna"].user)
    g2.membri.add(utenti_db["giovanna"].user)
    g2.membri.add(utenti_db["andrea"].user)
    g2.interessi.add(interessi_db["fotografia"])
    g2.interessi.add(interessi_db["arte"])

    pg1 = PostGruppo()
    pg1.autore = utenti_db["mario"].user
    pg1.gruppo = g1
    pg1.testo = "vi do il benvenuto in questo gruppo!"
    pg1.save()

    print("Ho inizializzato il DB")

