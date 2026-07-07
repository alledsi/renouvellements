from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings

# Create your views here.

# URL du backend FastAPI (définie dans settings.py via la variable d'env FASTAPI_URL)
API_URL = settings.API_URL

def login_view(request):
    if request.user.is_authenticated:
        return redirect('list_proposals')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('list_proposals')
    return render(request, 'auth/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # ne pas déconnecter l'utilisateur
        messages.success(request, "Mot de passe modifié avec succès 🔒")
        return redirect('logout')
    return render(request, 'auth/change_password.html', {'form': form})

@login_required
def list_proposals(request):
    user = request.user.username
    url_verif = f"{API_URL}/proposals/verifier_utilisateur/{user}"
    try:
        response = requests.get(url_verif, timeout=5)
        data = response.json()

        if data.get("autorise"):
            region = data.get("region")
            # ✅ autorisé → afficher la page
            try:
                response = requests.get(f"{API_URL}/proposals/{user}/")
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                data = []
                print("Erreur API FastAPI :", e)

            # Catégorie d'onglet (le filtrage se fait côté client)
            for d in data:
                st = d.get("STATUT_PROPOSITION")
                if st == "APPROUVE":
                    d["CAT"] = "GENERE" if d.get("PRET_GENERE") == "Y" else "APPROUVE"
                else:
                    d["CAT"] = st or "EN_ATTENTE"

                # Date 1ère échéance -> jj/mm/aaaa (sans l'heure)
                dpe = d.get("D_PREM_ECH")
                if dpe:
                    try:
                        d["D_PREM_ECH_FMT"] = datetime.datetime.fromisoformat(dpe).strftime("%d/%m/%Y")
                    except Exception:
                        d["D_PREM_ECH_FMT"] = dpe
                else:
                    d["D_PREM_ECH_FMT"] = "-"

            # Tri : les propositions "En attente" en premier
            priorite = {"EN_ATTENTE": 0, "REVISE": 1, "APPROUVE": 2, "GENERE": 3, "REJETE": 4}
            data = sorted(data, key=lambda d: priorite.get(d.get("CAT"), 99))

        else:
            # ❌ non autorisé → redirection
            return redirect("/non_autorise/")
    except Exception as e:
        print("Erreur de vérification FastAPI:", e)
        return redirect("/logout/")
        
    

    # Statistiques globales
    stats = {
        "total": len(data),
        "en_attente": sum(1 for d in data if d.get("STATUT_PROPOSITION") == "EN_ATTENTE"),
        "approuve": sum(1 for d in data if d.get("STATUT_PROPOSITION") == "APPROUVE" and d.get("PRET_GENERE") == 'N'),
        "genere": sum(1 for d in data if d.get("STATUT_PROPOSITION") == "APPROUVE" and d.get("PRET_GENERE") == 'Y'),
        "rejete": sum(1 for d in data if d.get("STATUT_PROPOSITION") == "REJETE"),
        "revise": sum(1 for d in data if d.get("STATUT_PROPOSITION") == "REVISE"),
        "mt_total": sum(float(d.get("MT_PROPOSE") or 0) for d in data),
        "mt_accorde": sum(float(d.get("MT_ACCORDE") or 0) for d in data),
        "mt_approuve": sum(float(d.get("MT_ACCORDE") or 0) for d in data if d.get("STATUT_PROPOSITION") == "APPROUVE" and d.get("PRET_GENERE") == 'N'),
        "mt_genere": sum(float(d.get("MT_ACCORDE") or 0) for d in data if d.get("STATUT_PROPOSITION") == "APPROUVE" and d.get("PRET_GENERE") == 'Y'),
        "mt_en_attente": sum(float(d.get("MT_PROPOSE") or 0) for d in data if d.get("STATUT_PROPOSITION") == "EN_ATTENTE"),
        "mt_rejete": sum(float(d.get("MT_PROPOSE") or 0) for d in data if d.get("STATUT_PROPOSITION") == "REJETE"),
        "mt_revise": sum(float(d.get("MT_PROPOSE") or 0) for d in data if d.get("STATUT_PROPOSITION") == "REVISE")
    }

    # ===== Rapport d'analyse : KPI globaux + répartition par bureau =====
    from collections import defaultdict
    agg = defaultdict(lambda: {
        "nb": 0, "propose": 0.0, "accorde": 0.0,
        "score_sum": 0.0, "score_n": 0,
        "en_attente": 0, "approuve": 0, "genere": 0, "rejete": 0, "revise": 0,
    })
    for d in data:
        b = d.get("LIBELLE_BUREAU") or "—"
        st = d.get("STATUT_PROPOSITION")
        gen = d.get("PRET_GENERE")
        a = agg[b]
        a["nb"] += 1
        a["propose"] += float(d.get("MT_PROPOSE") or 0)
        a["accorde"] += float(d.get("MT_ACCORDE") or 0)
        sc = d.get("SCORE_TOTAL")
        if sc is not None:
            a["score_sum"] += float(sc)
            a["score_n"] += 1
        if st == "EN_ATTENTE":
            a["en_attente"] += 1
        elif st == "APPROUVE" and gen == "Y":
            a["genere"] += 1
        elif st == "APPROUVE":
            a["approuve"] += 1
        elif st == "REJETE":
            a["rejete"] += 1
        elif st == "REVISE":
            a["revise"] += 1

    rapport_bureaux = []
    for b, a in sorted(agg.items(), key=lambda kv: kv[1]["nb"], reverse=True):
        rapport_bureaux.append({
            "bureau": b,
            "nb": a["nb"],
            "propose": a["propose"],
            "accorde": a["accorde"],
            "score_moy": (a["score_sum"] / a["score_n"]) if a["score_n"] else 0,
            "taux": (a["accorde"] / a["propose"] * 100) if a["propose"] else 0,
            "en_attente": a["en_attente"],
            "approuve": a["approuve"],
            "genere": a["genere"],
            "rejete": a["rejete"],
            "revise": a["revise"],
        })

    scores = [float(d["SCORE_TOTAL"]) for d in data if d.get("SCORE_TOTAL") is not None]
    decidees = sum(1 for d in data if d.get("STATUT_PROPOSITION") in ("APPROUVE", "REJETE", "REVISE"))
    n = stats["total"]
    total_capital = sum(float(d.get("MT_PRET_ORIGINAL") or 0) for d in data)
    total_encours = sum(float(d.get("SOLDE_A_RACHETER") or 0) for d in data)
    nb_accorde = sum(1 for d in data if d.get("MT_ACCORDE"))
    rapport = {
        "nb_bureaux": len(rapport_bureaux),
        "score_moyen": (sum(scores) / len(scores)) if scores else 0,
        "taux_accord": (stats["mt_accorde"] / stats["mt_total"] * 100) if stats["mt_total"] else 0,
        "taux_traitement": (decidees / n * 100) if n else 0,
        # Totaux
        "total_capital": total_capital,
        "total_encours": total_encours,
        # Moyennes par dossier
        "capital_moyen": (total_capital / n) if n else 0,
        "montant_moyen_propose": (stats["mt_total"] / n) if n else 0,
        "montant_moyen_accorde": (stats["mt_accorde"] / nb_accorde) if nb_accorde else 0,
    }


    return render(request, "proposals/list_proposals.html", {
        "propositions": data,
        "stats": stats,
        "region": region,
        "rapport": rapport,
        "rapport_bureaux": rapport_bureaux,
    })

@csrf_exempt
def decide_proposal(request, id_prop):
    """
    Envoie la décision vers FastAPI : /proposals/proposals/{user}/{id}/decision
    Répond en JSON (succès OU échec) pour affichage d'un message côté client.
    """
    if request.method != "POST":
        return redirect("list_proposals")

    statut = request.POST.get("statut")
    mt_accorde = request.POST.get("mt_accorde") or None
    d_prem_ech = request.POST.get("d_prem_ech") or None
    commentaire = request.POST.get("commentaire")
    generer_garanties = request.POST.get("generer_garanties", "Y")
    user = request.user.username

    libelles = {
        "APPROUVE": "Proposition approuvée",
        "REVISE": "Proposition révisée",
        "REJETE": "Proposition rejetée",
    }

    payload = {
        "statut_decision": statut,
        "mt_accorde": float(mt_accorde) if mt_accorde else None,
        "d_prem_ech": d_prem_ech,
        "generer_garanties": generer_garanties,
        "code_type_gar_demande": None,
        "valeur_gar_demandee": None,
        "commentaire_decision": commentaire
    }

    try:
        print(f"→ Envoi vers {API_URL}/proposals/proposals/{user}/{id_prop}/decision")
        response = requests.post(
            f"{API_URL}/proposals/proposals/{user}/{id_prop}/decision",
            json=payload, timeout=15
        )
        if response.ok:
            msg = libelles.get(statut, "Décision enregistrée") + " avec succès."
            return JsonResponse({"ok": True, "message": msg})
        # Erreur renvoyée par l'API : on récupère le détail précis
        try:
            detail = response.json().get("detail", "Erreur inconnue")
        except Exception:
            detail = response.text or "Erreur inconnue"
        return JsonResponse(
            {"ok": False, "message": str(detail)},
            status=response.status_code
        )
    except Exception as e:
        print("Erreur lors de l’envoi de la décision:", e)
        return JsonResponse(
            {"ok": False, "message": f"Impossible de contacter l'API : {e}"},
            status=502
        )


@csrf_exempt
def generer_prets(request):
    """
    Appelle pkg_renouvellement.generer_tous_prets_comite via FastAPI.
    Répond en JSON (succès OU échec) pour affichage d'un message côté client.
    """
    if request.method != "POST":
        return redirect("list_proposals")

    user = request.user.username
    try:
        print("→ Appel de pkg_renouvellement.generer_tous_prets_comite ...")
        r = requests.post(
            f"{API_URL}/proposals/proposals/{user}/generate_prets", timeout=120
        )
        if r.ok:
            data = r.json()
            return JsonResponse(
                {"ok": True, "message": data.get("message", "Prêts générés avec succès.")}
            )
        try:
            detail = r.json().get("detail", "Erreur inconnue")
        except Exception:
            detail = r.text or "Erreur inconnue"
        return JsonResponse(
            {"ok": False, "message": f"Échec de la génération : {detail}"},
            status=r.status_code
        )
    except Exception as e:
        print("Erreur de génération des prêts:", e)
        return JsonResponse(
            {"ok": False, "message": f"Impossible de contacter l'API : {e}"},
            status=502
        )

def non_autorise_view(request):
    # Si tu veux envoyer un code HTTP 403 tout en rendant un template :
    response = render(request, "non_autorise.html")
    response.status_code = 403
    return response
