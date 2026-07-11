![logo](media/djangbook2.png)

Consultare _ipotesi di traccia.pdf_ per info dettagliate sulle funzionalità dell'applicazione.

## Istruzioni per l'avvio
Per clonare il repository:
```git clone https://github.com/154549/tecnologie_web```

È richiesto Python e Pipenv.
```
pip install pipenv
```

Installa l'ambiente (il file Pipenv triggera l'installazione di Django e Pillow).
```
pipenv install
```

Avvia l'ambiente virtuale.
```
pipenv shell
```

Effettua le migrazioni (necessarie per le tabelle) e avvia il server.
```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Seeding
Al primo avvio l'app crea da sola alcuni dati di esempio (vedi `DjangBook/initcmds.py`).
Questi account sono già pronti, tutti con password `password123`:

- `mario`, `andrea`, `giovanna`, `maria`, `marco` sono gli utenti pre caricati


## Superuser
username: `enrik`
password: `password123`

`enrik` è anche un utente normale.

`/admin/` contiene anche le funzionalità di moderazione.

## Altri dettagli
- La cartella `media` contiene le immagini di profilo di default degli utenti precaricati.
- La cartella `media/samples` contiene alcune immagini liberamente usabili per testare le funzionalità dell'applicazione.
- La cartella template contiene solo `base.html`, il quale viene esteso da qualsiasi altro file .html in modo da mantenere lo stesso stile in tutta l'applicazione.

