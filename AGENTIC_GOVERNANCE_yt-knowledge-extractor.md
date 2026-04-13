# Fiche de Gouvernance Agentique — yt-knowledge-extractor

> Agent autonome de surveillance et traitement de vidéos YouTube  
> **Version** : 1.0 — Avril 2026  
> **Statut** : V1 — champs `[à compléter]` bloquants avant mise en production

---

## 0. Fiche d'Identité de l'Agent

> Tout agent sans ces 6 points documentés est un agent shadow — même approuvé verbalement.  
> *(La Dette de Contrôle — Checklist Gouvernance Agent par Agent)*

| Point | Valeur |
|---|---|
| **Nom** | yt-knowledge-generator |
| **Version** | 1.0 |
| **Fournisseur IA** | Google Gemini API — Modèle : `[à verrouiller avant mise en prod]` |
| **Responsable interne** | François Bill |
| **Périmètre déclaré** | Détection de nouvelles vidéos sur une liste de chaînes configurées → génération de fiches d'extraction de la connaissance en mode batch via Gemini API → validation de conformité → notification humain → quarantaine des fiches non conformes |
| **Permissions** | Lecture API YouTube officielle. Appel batch Gemini API. Écriture log + quarantaine. Pas de full access. Token à permissions minimales (least-privilege). |
| **Supervision** | François Bill — fréquence : `[à définir]` |
| **Coupe-circuit** | Kill switch ≤ 30 secondes — Autorité : François Bill |
| **Audit** | Log append-only. Rétention : **90 jours**. Reviewer : François Bill |

---

## 1. Contenu d'une Fiche d'Extraction de la Connaissance

Chaque fiche produite par l'agent contient les 8 champs suivants :

| # | Champ | Description |
|---|---|---|
| 1 | **Thèse centrale** | Argument principal développé dans la vidéo |
| 2 | **Chapitrage inféré** | Structure narrative reconstruite par l'agent |
| 3 | **Carte des idées** | Graphe des concepts et de leurs relations |
| 4 | **Concepts clés** | Définitions dans les termes de l'auteur |
| 5 | **Formulations notables verbatim** | Citations exactes significatives |
| 6 | **Questions ouvertes** | Points non résolus ou tensions identifiées |
| 7 | **Sources filtrées** | Références citées dans la vidéo |
| 8 | **Transcript horodaté complet** | Transcription brute avec timestamps |

---

## 2. Points de Contrôle Agentiques

### 2.1 Contrôle des décisions et escalade humaine

| Point de contrôle | Statut | Risque si absent |
|---|---|---|
| Agent ne décide pas, il signale | ✅ Implémenté | Délégation non supervisée |
| Actions irréversibles remontent à l'humain | ✅ Implémenté | Output diffusé sans validation |
| Seuil d'escalade défini (enjeu, volume, anomalie) | ⚠️ À définir | Escalade discrétionnaire = non gouvernée |
| Responsable humain nommé et imputable | ✅ François Bill | Agent shadow de facto |

### 2.2 Contrôle qualité et quarantaine

| Point de contrôle | Statut | Risque si absent |
|---|---|---|
| Scoring de conformité automatique | ✅ Implémenté | Fiches non validées en production |
| Quarantaine pour fiches non conformes | ✅ Implémenté | Propagation de contenus défectueux |
| Behavior monitoring actif (détection dérive) | ❌ Manquant | Dérive silencieuse des outputs non détectée |
| Ré-étalonnage périodique humain (échantillon aléatoire) | ✅ Implémenté | Dérive accumulée non corrigée |
| Test de régression sur jeu « gold standard » | ❌ Manquant | Régression silencieuse après mise à jour |

### 2.3 Traçabilité et audit

| Point de contrôle | Statut | Risque si absent |
|---|---|---|
| Log append-only de chaque action | ✅ Implémenté | Non-rétractabilité absente |
| Durée de rétention définie (90 jours) + reviewer nommé | ✅ François Bill | Log sans gouvernance = artefact inutile |
| Vérification hash du prompt système au démarrage | ✅ Implémenté | Prompt modifié non détecté |
| Version exacte du modèle Gemini loggée à chaque appel | ❌ Manquant | Changement de comportement invisible |

### 2.4 Sécurité des inputs

> ⚠️ **Risque critique** : Les transcripts YouTube sont des inputs externes non fiables.  
> Un transcript peut contenir des instructions malveillantes camouflées dans le contenu vidéo,  
> traitées par Gemini API comme des instructions légitimes (vecteur **EchoLeak** / CVE-2025-32711).  
> Une couche de sanitisation entre l'input externe et l'exécution du prompt est requise.

| Point de contrôle | Statut | Risque si absent |
|---|---|---|
| Sanitisation des inputs externes avant exécution du prompt | ❌ Manquant | Prompt injection indirecte via transcripts |
| Vérification de la provenance (API YouTube officielle uniquement) | ⚠️ À confirmer | Injection via titre/description manipulé |

### 2.5 Arrêt et coupe-circuit

| Point de contrôle | Statut | Risque si absent |
|---|---|---|
| Règles d'arrêt automatique (N échecs consécutifs = suspension) | ✅ Implémenté | Boucle d'échecs non stoppée |
| Kill switch manuel ≤ 30 secondes — Autorité : François Bill | ✅ Nommé | Arrêt d'urgence impossible sans ticket IT |
| Purpose binding (incapacité technique à sortir du périmètre) | ❌ Manquant | Dérive de périmètre non prévenue |

### 2.6 Droits, rétention et conformité

| Point de contrôle | Statut | Risque si absent |
|---|---|---|
| Politique de rétention des transcripts horodatés (90 jours) | ✅ Définie | Risque droit d'auteur + RGPD |
| Token API Gemini à permissions minimales (least-privilege) | ⚠️ À vérifier | Surface d'attaque élargie si compromis |

---

## 3. Tableau de Bord de Contrôle

| Métrique | Seuil d'alerte | Action déclenchée |
|---|---|---|
| Taux de fiches en quarantaine | `[à calibrer]` % sur 7 jours glissants | Notification humain + suspension batch |
| Dérive du score de conformité moyen | `[à calibrer]` points de baisse vs baseline | Ré-étalonnage humain forcé |
| Version modèle Gemini utilisée | Changement non planifié détecté | Arrêt agent + validation manuelle |

---

## 4. Plan d'Action Gouvernance

| Priorité | Action | Responsable | Échéance |
|---|---|---|---|
| **P0** | Verrouiller la version Gemini API dans la config | Développeur | Avant mise en prod |
| **P0** | Implémenter sanitisation des inputs externes (anti-injection) | Développeur | Avant mise en prod |
| **P0** | Documenter le seuil d'escalade humaine | François Bill | Avant mise en prod |
| **P1** | Logger la version Gemini à chaque appel API | Développeur | Sprint suivant |
| **P1** | Créer le jeu « gold standard » pour tests de régression | François Bill | Sprint suivant |
| **P1** | Calibrer les seuils du tableau de bord (section 3) | François Bill | Sprint suivant |
| **P2** | Implémenter behavior monitoring actif (détection dérive) | Développeur | Phase 2 |
| **P2** | Purpose binding technique (contrainte architecturale) | Architecte | Phase 2 |

---

## 5. Références

- **La Dette de Contrôle** — F. Biller, Sopra Steria Next, Février 2026. Checklist Gouvernance Agent par Agent (6 points), Framework PMC, Signal 4 (EchoLeak / prompt injection indirecte).
- **Singapore Model AI Governance Framework for Agentic AI** — IMDA, Janvier 2026. Kill switches obligatoires, purpose binding, behavior monitoring.
- **NIST AI Agent Standards Initiative** — Février 2026. Cadre d'identité et d'autorisation pour agents IA.
- **OWASP Top 10 for LLM Applications** — Prompt injection classée vulnérabilité n°1.
- **EchoLeak (CVE-2025-32711)** — Aim Security / Microsoft, Juin 2025. Première exploitation zero-click d'un LLM en production via prompt injection indirecte.

---

*Document produit avec l'assistance de Claude (Anthropic) dans le cadre de la démarche de gouvernance IA responsable — Sopra Steria Next.*
