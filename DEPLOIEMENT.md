# Procédure de déploiement — ACEP Renouvellements

Serveur : `192.168.0.122`
Services systemd : `fastapi.service` (backend) et `django.service` (frontend)

---

## 1. Sur le PC de développement (pousser les modifications)

```bash
git add <fichiers modifiés>          # ou : git add -A
git commit -m "Description des changements"
git push
```

Avant de pousser, vérifier qu'il ne reste **aucun conflit** :

```bash
git status                            # aucun fichier "both modified"
git grep -n "<<<<<<<"                 # ne doit rien retourner
```

---

## 2. Sur le serveur (récupérer et appliquer)

```bash
cd ~/acep-renouvellements
git pull
```

Puis redémarrer **uniquement** ce qui a changé :

- Modifications du **frontend** (dossier `frontend/`, templates, vues Django) :
  ```bash
  sudo systemctl restart django.service
  ```

- Modifications du **backend** (dossier `backend/`, FastAPI) :
  ```bash
  sudo systemctl restart fastapi.service
  ```

- Les deux si les deux ont changé.

Vérifier que le service est bien reparti :

```bash
sudo systemctl status django.service
sudo systemctl status fastapi.service
```

En cas d'erreur, consulter les logs :

```bash
journalctl -u django.service -n 50 --no-pager
journalctl -u fastapi.service -n 50 --no-pager
```

---

## 3. Configuration (URL du backend)

L'URL du backend FastAPI n'est plus codée en dur : elle est lue depuis la variable
d'environnement `FASTAPI_URL` (voir `frontend/.env.example`).

- En local : rien à faire, la valeur par défaut est `http://localhost:8008`.
- Sur le serveur (backend sur la même machine) : la valeur par défaut suffit.
  Si un jour le backend est sur une autre machine, créer `frontend/.env` :
  ```
  FASTAPI_URL=http://192.168.0.122:8008
  ```
  Le fichier `.env` est ignoré par git : il n'est jamais écrasé par `git pull`.

---

## En cas de conflit lors d'un `git pull --rebase`

1. **Ne PAS faire `git add .` tout de suite.**
2. Voir les fichiers en conflit : `git status`
3. Ouvrir chaque fichier, chercher les marqueurs `<<<<<<<`, `=======`, `>>>>>>>`
   et garder la bonne version (supprimer les marqueurs).
4. Marquer résolu : `git add <fichier>`
5. Continuer : `git rebase --continue`
6. Vérifier qu'il ne reste aucun marqueur : `git grep -n "<<<<<<<"`

---

## Sauvegarde de la base (avant toute manipulation risquée)

La base `frontend/db.sqlite3` contient les comptes utilisateurs Django.
Toujours la sauvegarder avant une opération git inhabituelle :

```bash
cp frontend/db.sqlite3 ~/db.sqlite3.backup
```
