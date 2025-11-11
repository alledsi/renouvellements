from django.shortcuts import render, redirect
import requests
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

API_URL = "http://localhost:8008"

def login_view(request):
    if request.user.is_authenticated:
        return redirect('list_proposals')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f"Bienvenue {user.username} 👋")
        return redirect('list_proposals')
    return render(request, 'auth/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Déconnexion réussie ✅")
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
    url_verif = f"http://localhost:8008/proposals/verifier_utilisateur/{user}"
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

            # Filtre par statut (optionnel)
            statut_filter = request.GET.get("statut", "TOUS")
            if statut_filter != "TOUS":
                data = [d for d in data if d.get("STATUT_PROPOSITION") == statut_filter]    

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


    return render(request, "proposals/list_proposals.html", {
        "propositions": data,
        "stats": stats,
        "statut_filter": statut_filter,
        "region": region
    })

@csrf_exempt
def decide_proposal(request, id_prop):
    """
    Envoie la décision vers FastAPI : /proposals/proposals/{user}/{id}/decision
    """
    if request.method == "POST":
        statut = request.POST.get("statut")
        mt_accorde = request.POST.get("mt_accorde") or None
        d_prem_ech = request.POST.get("d_prem_ech") or None
        commentaire = request.POST.get("commentaire")
        generer_garanties = request.POST.get("generer_garanties", "Y")
        user = request.user.username

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
            response = requests.post(f"{API_URL}/proposals/proposals/{user}/{id_prop}/decision", json=payload)
            response.raise_for_status()
        except Exception as e:
            print("Erreur lors de l’envoi de la décision:", e)

    return redirect("list_proposals")


@csrf_exempt
def generer_prets(request):
    """
    Appelle la procédure pkg_renouvellement_complet.generer_tous_prets_comite
    sur FastAPI
    """
    if request.method == "POST":
        try:
            user = request.user.username
            print("→ Appel de pkg_renouvellement_complet.generer_tous_prets_comite ...")
            r = requests.post(f"{API_URL}/proposals/proposals/{user}/generate_prets")
            r.raise_for_status()
        except Exception as e:
            print("Erreur de génération des prêts:", e)
    return redirect("list_proposals")

def non_autorise_view(request):
    # Si tu veux envoyer un code HTTP 403 tout en rendant un template :
    response = render(request, "non_autorise.html")
    response.status_code = 403
    return response
