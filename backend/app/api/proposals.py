from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.db import get_conn
from pydantic import BaseModel
import datetime
import decimal

router = APIRouter()

class ProposalOut(BaseModel):
    CODE_REGION: Optional[str]
    ID_PROPOSITION: Optional[int]
    NO_PRET_SCORE: Optional[int]
    MT_PRET_ORIGINAL: Optional[float]
    SOLDE_A_RACHETER: Optional[float]
    REF_COMITE: Optional[str]
    STATUT_PROPOSITION: Optional[str]
    MATRICULE_CLIENT: Optional[str]
    NOM_COMPLET: Optional[str]
    CODE_BUREAU: Optional[str]
    LIBELLE_BUREAU: Optional[str]
    SCORE_TOTAL: Optional[float]
    MT_PROPOSE: Optional[float]
    MT_ACCORDE: Optional[float]
    D_PREM_ECH: Optional[str]
    DATE_DECISION: Optional[str]
    COMMENTAIRE_DECISION: Optional[str]
    GENERER_GARANTIES: Optional[str]
    PRET_GENERE: Optional[str]
    USER_PROPOSITION: Optional[str]
    DATE_PROPOSITION: Optional[str]
    USER_GENERATION: Optional[str]
    DATE_GENERATION: Optional[str]
    JOURS_DECISION_GENERATION: Optional[int]

class ProposalOutAll(BaseModel):
    CODE_REGION: Optional[str]
    ID_PROPOSITION: Optional[int]
    NO_PRET_SCORE: Optional[int]
    MT_PRET_ORIGINAL: Optional[float]
    REF_COMITE: Optional[str]
    STATUT_PROPOSITION: Optional[str]
    MATRICULE_CLIENT: Optional[str]
    NOM_COMPLET: Optional[str]
    CODE_BUREAU: Optional[str]
    LIBELLE_BUREAU: Optional[str]
    SCORE_TOTAL: Optional[float]
    MT_PROPOSE: Optional[float]
    MT_ACCORDE: Optional[float]
    D_PREM_ECH: Optional[str]
    DATE_DECISION: Optional[str]
    COMMENTAIRE_DECISION: Optional[str]
    GENERER_GARANTIES: Optional[str]
    PRET_GENERE: Optional[str]
    USER_PROPOSITION: Optional[str]
    DATE_PROPOSITION: Optional[str]
    USER_GENERATION: Optional[str]
    DATE_GENERATION: Optional[str]
    JOURS_DECISION_GENERATION: Optional[int]
    LIB_REGION: Optional[str]


class DecisionIn(BaseModel):
    statut_decision: str  # APPROUVE/REJETE/REVISE
    mt_accorde: Optional[float]
    d_prem_ech: Optional[datetime.date]
    generer_garanties: Optional[str]  # 'Y'/'N'
    code_type_gar_demande: Optional[str]
    valeur_gar_demandee: Optional[float]
    commentaire_decision: Optional[str]

# Simple auth dependency placeholder (implement JWT / RBAC in prod)
def get_current_user():
    return {"username":"demo.user","roles":["COMITE"]}

@router.get("/verifier_utilisateur/{username}")
def verifier_utilisateur(username: str):
    sql = """
        SELECT CUTI
        FROM EVUTI
        WHERE CODE_SERV = :code_serv
          AND DMMP >= TRUNC(SYSDATE - 90)
    """
    sql2 = """
        SELECT e.CUTI, r.lib_region
        FROM EVUTI e, REGION r
        WHERE e.CODE_REGION = r.CODE_REGION and e.CODE_SERV = :code_serv
          AND e.DMMP >= TRUNC(SYSDATE - 90)
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(sql, {"code_serv": "004"})
        utilisateurs = [row[0] for row in cursor.fetchall()]
        cursor.execute(sql2, {"code_serv": "004"})
        region = {row[0]: row[1] for row in cursor.fetchall()}

        if username in utilisateurs:
            return {"autorise": True, "message": f"Utilisateur {username} autorisé ✅", "region": region[username]}
        else:
            return {"autorise": False, "message": f"Utilisateur {username} non autorisé ❌"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/{user}", response_model=List[ProposalOut])
def list_proposals(user: str):
    conn = get_conn()
    try:
        cur = conn.cursor()
        sql = """
        SELECT 
            CODE_REGION,
            ID_PROPOSITION,
            NO_PRET_SCORE,
            MT_PRET_ORIGINAL,
            REF_COMITE,
            STATUT_PROPOSITION,
            MATRICULE_CLIENT,
            NOM_COMPLET,
            CODE_BUREAU,
            LIBELLE_BUREAU,
            SCORE_TOTAL,
            MT_PROPOSE,
            MT_ACCORDE,
            D_PREM_ECH,
            DATE_DECISION,
            COMMENTAIRE_DECISION,
            GENERER_GARANTIES,
            PRET_GENERE,
            USER_PROPOSITION,
            DATE_PROPOSITION,
            USER_GENERATION,
            DATE_GENERATION,
            JOURS_DECISION_GENERATION,
            SOLDE_A_RACHETER
        FROM V_RENOUVELLEMENT
        WHERE CODE_REGION = (
        SELECT CODE_REGION
        FROM EVUTI
        WHERE CODE_SERV = :code_serv
        AND DMMP >= TRUNC(SYSDATE -90) 
        AND CUTI = :code_util)
        """
        cur.execute(sql, {"code_serv": "004", "code_util": user})
        def safe(val):
            if val is None:
                return None
            if isinstance(val, (datetime.datetime, datetime.date)):
                return val.isoformat()
            if isinstance(val, decimal.Decimal):
                return float(val)
            return val
        rows = cur.fetchall()
        result = [dict(
            CODE_REGION = safe(r[0]),
            ID_PROPOSITION = safe(r[1]),
            NO_PRET_SCORE = safe(r[2]),
            MT_PRET_ORIGINAL = safe(r[3]),
            REF_COMITE = safe(r[4]),
            STATUT_PROPOSITION = safe(r[5]),
            MATRICULE_CLIENT = safe(r[6]),
            NOM_COMPLET = safe(r[7]),
            CODE_BUREAU = safe(r[8]),
            LIBELLE_BUREAU = safe(r[9]),
            SCORE_TOTAL = safe(r[10]),
            MT_PROPOSE = safe(r[11]),
            MT_ACCORDE = safe(r[12]),
            D_PREM_ECH = safe(r[13]),
            DATE_DECISION = safe(r[14]),
            COMMENTAIRE_DECISION = safe(r[15]),
            GENERER_GARANTIES = safe(r[16]),
            PRET_GENERE = safe(r[17]),
            USER_PROPOSITION = safe(r[18]),
            DATE_PROPOSITION = safe(r[19]),
            USER_GENERATION = safe(r[20]),
            DATE_GENERATION = safe(r[21]),
            JOURS_DECISION_GENERATION = safe(r[22]),
            SOLDE_A_RACHETER = safe(r[23])
        ) for r in rows ]
        print("✅ Nombre de lignes :", len(result))
        return result

    except Exception as e:
        import traceback
        print("\n========== ERREUR ORACLE ==========")
        traceback.print_exc()
        print("==================================\n")
        raise HTTPException(status_code=500, detail=f"Erreur Oracle : {e}")
    finally:
        conn.close()

@router.get("/list/all", response_model=List[ProposalOutAll])
def list_proposals_all():
    conn = get_conn()
    try:
        cur = conn.cursor()
        sql = """
        SELECT
            v.CODE_REGION,
            v.ID_PROPOSITION,
            v.NO_PRET_SCORE,
            v.MT_PRET_ORIGINAL,
            v.REF_COMITE,
            v.STATUT_PROPOSITION,
            v.MATRICULE_CLIENT,
            v.NOM_COMPLET,
            v.CODE_BUREAU,
            v.LIBELLE_BUREAU,
            v.SCORE_TOTAL,
            v.MT_PROPOSE,
            v.MT_ACCORDE,
            v.D_PREM_ECH,
            v.DATE_DECISION,
            v.COMMENTAIRE_DECISION,
            v.GENERER_GARANTIES,
            v.PRET_GENERE,
            v.USER_PROPOSITION,
            v.DATE_PROPOSITION,
            v.USER_GENERATION,
            v.DATE_GENERATION,
            v.JOURS_DECISION_GENERATION,
            r.LIB_REGION
        FROM V_RENOUVELLEMENT v
        LEFT JOIN REGION r
        ON TRIM(v.CODE_REGION) = TRIM(r.CODE_REGION)
        """
        cur.execute(sql)
        def safe(val):
            if val is None:
                return None
            if isinstance(val, (datetime.datetime, datetime.date)):
                return val.isoformat()
            if isinstance(val, decimal.Decimal):
                return float(val)
            return val
        rows = cur.fetchall()
        result = [dict(
            CODE_REGION = safe(r[0]),
            ID_PROPOSITION = safe(r[1]),
            NO_PRET_SCORE = safe(r[2]),
            MT_PRET_ORIGINAL = safe(r[3]),
            REF_COMITE = safe(r[4]),
            STATUT_PROPOSITION = safe(r[5]),
            MATRICULE_CLIENT = safe(r[6]),
            NOM_COMPLET = safe(r[7]),
            CODE_BUREAU = safe(r[8]),
            LIBELLE_BUREAU = safe(r[9]),
            SCORE_TOTAL = safe(r[10]),
            MT_PROPOSE = safe(r[11]),
            MT_ACCORDE = safe(r[12]),
            D_PREM_ECH = safe(r[13]),
            DATE_DECISION = safe(r[14]),
            COMMENTAIRE_DECISION = safe(r[15]),
            GENERER_GARANTIES = safe(r[16]),
            PRET_GENERE = safe(r[17]),
            USER_PROPOSITION = safe(r[18]),
            DATE_PROPOSITION = safe(r[19]),
            USER_GENERATION = safe(r[20]),
            DATE_GENERATION = safe(r[21]),
            JOURS_DECISION_GENERATION = safe(r[22]),
            LIB_REGION = safe(r[23])
        ) for r in rows ]
        print("✅ Nombre de lignes :", len(result))
        return result

    except Exception as e:
        import traceback
        print("\n========== ERREUR ORACLE ==========")
        traceback.print_exc()
        print("==================================\n")
        raise HTTPException(status_code=500, detail=f"Erreur Oracle : {e}")
    finally:
        conn.close()

@router.post("/proposals/{user}/{id}/decision")
def set_decision(user: str, id: int, decision: DecisionIn):
    # user: dict = Depends(get_current_user)
    # 1) Basic validation of statut
    allowed = {"APPROUVE","REJETE","REVISE"}
    if decision.statut_decision not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status")

    conn = get_conn()
    try:
        cur = conn.cursor()
        # 2) Lock row for update to avoid concurrent decisions
        cur.execute("""
            SELECT statut_proposition, pret_genere
            FROM PROPOSITION_RENOUVELLEMENT
            WHERE id_proposition = :id
            FOR UPDATE
        """, {"id": id})
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Proposal not found")
        if row[1] == 'O' and decision.statut_decision == 'APPROUVE':
            raise HTTPException(status_code=400, detail="Loan already generated")

        # 3) Check business rules: e.g. mt_accorde <= some limit — implement as needed
        # Example: ensure mt_accorde is not greater than 2 * mt_propose (dummy rule)
        cur.execute("SELECT mt_propose FROM PROPOSITION_RENOUVELLEMENT WHERE id_proposition=:id", {"id": id})
        mt_propose = cur.fetchone()[0]
        if decision.mt_accorde is not None and mt_propose is not None:
            if decision.mt_accorde > mt_propose * 2:
                raise HTTPException(status_code=400, detail="mt_accorde too large")

        # 4) Update decision and audit fields
        # cur.execute("""
        #     UPDATE PROPOSITION_RENOUVELLEMENT
        #     SET statut_proposition = :statut,
        #         mt_accorde = :mt_accorde,
        #         D_prem_ech = :d_prem_ech,
        #         generer_garanties = :gen_gar,
        #         code_type_gar_demande = :type_gar,
        #         valeur_gar_demandee = :val_gar,
        #         commentaire_decision = :commentaire,
        #         user_proposition = :util,
        #         date_decision = SYSDATE
        #     WHERE id_proposition = :id
        # """, {
        #     "statut": decision.statut_decision,
        #     "mt_accorde": decision.mt_accorde,
        #     "d_prem_ech": decision.d_prem_ech,
        #     "gen_gar": decision.generer_garanties,
        #     "type_gar": decision.code_type_gar_demande,
        #     "val_gar": decision.valeur_gar_demandee,
        #     "commentaire": decision.commentaire_decision,
        #     "util": user,
        #     "id": id
        # })
        cur.callproc("pkg_renouvellement.enregistrer_decision", [id, decision.statut_decision, decision.mt_accorde, decision.d_prem_ech, decision.generer_garanties, decision.commentaire_decision, user])
        conn.commit()
        return {"ok": True}
    except HTTPException:
        # Erreurs métier volontaires (400/404) : on les laisse passer telles quelles
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        import traceback
        print("\n========== ERREUR DECISION ORACLE ==========")
        traceback.print_exc()
        print("============================================\n")
        raise HTTPException(status_code=500, detail=f"Erreur Oracle : {e}")
    finally:
        conn.close()

@router.post("/proposals/{user}/generate_prets")
def generate_prets(user: str):
    """
    Appelle la procédure Oracle :
    pkg_renouvellement.generer_tous_prets_comite
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        sql = """
        SELECT CODE_REGION
        FROM EVUTI
        WHERE CODE_SERV = :code_serv
        AND CUTI = :code_util
        AND DMMP >= TRUNC(SYSDATE -90) 
        """
        cur.execute(sql, {"code_serv": "004", "code_util": user})
        row = cur.fetchone()
        p_nb_generes = cur.var(int)
        if row:
            code_region = row[0]
            print(type(code_region))
            print("▶ Appel de pkg_renouvellement.generer_tous_prets_comite ...")
            cur.callproc("pkg_renouvellement.generer_tous_prets_comite", [code_region, user, p_nb_generes])
            conn.commit()
            return {"ok": True, "message": "Tous les prêts approuvés ont été générés avec succés !"}
        else:
            return {"ko": True, "message": "Code région introuvable"}
    except Exception as e:
        conn.rollback()
        print("Erreur Oracle lors de la génération :", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
