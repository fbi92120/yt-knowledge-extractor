# Méthode de co-construction des spécifications
## Cas d'application : YT Knowledge Extractor

**Auteur** : François Biller
**Date** : 2026-04-05
**Version** : 6.0
**Repo** : https://github.com/fbi92120/yt-knowledge-extractor
**Chaîne de référence** : [Le SamourAI — IA et Stratégie](https://www.youtube.com/@SamouraiDansant)

---

## Présentation

Ce document est né d'un constat simple : la majorité des projets développés
avec un LLM échouent non pas à cause du code, mais à cause de specs inexistantes
ou formulées trop vite. On donne une idée à Claude Code, il produit quelque chose
qui tourne — mais qui ne résout pas le bon problème.

Ce projet — un outil CLI Python qui extrait la connaissance de vidéos YouTube
et génère des fiches structurées en Markdown — a servi de terrain d'expérimentation
pour une méthode de spécification rigoureuse, entièrement co-construite avec un LLM.

Le point de départ était un besoin personnel concret : suivre une chaîne YouTube
à haute densité conceptuelle — en l'occurrence [Le SamourAI](https://www.youtube.com/@SamouraiDansant),
chaîne française de référence sur la stratégie IA — ne pas perdre la connaissance
après chaque vidéo, et pouvoir retrouver dans quelle vidéo un concept a été
développé. Un besoin partagé par beaucoup, rarement adressé sérieusement.

Ce qui a rendu ce projet intéressant sur le plan méthodologique, c'est la façon
dont il a été construit : trois heures de dialogue structuré avec Claude.ai,
avant d'écrire une seule ligne de code. La session a produit un document de
spécifications complet — SPECS.md — directement consommable par Claude Code.
Ce document est le récit de cette méthode.

Il ne documente pas seulement ce qui a été décidé. Il documente *comment* les
décisions ont été prises, *pourquoi* certaines étapes auraient dû être faites
différemment, et ce qui est directement transférable à d'autres projets.

Deux outils ont été utilisés en tandem tout au long du processus : Claude.ai
pour la réflexion, le cadrage et l'arbitrage — Claude Code pour l'implémentation.
Comprendre la différence de rôle entre ces deux outils, et le rôle irremplaçable
de l'humain qui les orchestre, est l'un des apprentissages centraux de ce projet.
C'est pourquoi ces deux dimensions sont présentées en premier, avant même
les étapes de la méthode.

---

## Glossaire

Les termes suivants sont utilisés de façon précise tout au long de ce document.

**Constitution**
Ensemble de règles non négociables définies avant l'implémentation, que ni le
code ni le LLM ne peuvent violer. Ce ne sont pas des contraintes techniques —
ce sont des principes de fidélité au besoin réel. Sans constitution, le LLM
n'est pas faux. Il est indéfini.

**Contrat**
Description formelle de ce qu'un module doit produire — ses entrées, ses sorties,
ses cas d'erreur — telle que définie dans les specs avant d'écrire le code.
Un module respecte son contrat quand son output correspond exactement à ce
qui a été spécifié, indépendamment de son implémentation interne.

**Dette de contrôle**
Écart croissant entre ce qu'une organisation délègue à l'IA générative et ce
qu'elle supervise réellement. La dette de contrôle s'accumule en silence,
souterraine — jusqu'à l'incident qui la révèle brutalement. Chaque usage non
gouverné, chaque décision prise par le LLM sans validation humaine, chaque
spec qui dérive sans être documentée ajoute à cette dette.

**Slug**
Version simplifiée d'un titre, formatée pour être utilisée comme nom de fichier
ou dans une URL. Les accents sont supprimés, les espaces remplacés par des
tirets, les caractères spéciaux éliminés. Seuls les caractères ASCII alphanumériques
et les tirets sont conservés. Exemple : "La chute d'Anthropic (2026)" devient
`la-chute-d-anthropic-2026`. Le slug garantit que les fichiers générés sont
lisibles et portables sur tous les systèmes, quelle que soit la langue du titre.

**Validateur**
Module du code dont le rôle est de vérifier que l'output généré par le LLM
respecte le contrat défini dans les specs. Il ne teste pas le code interne —
il teste le résultat. Il retourne une liste d'avertissements, pas d'exceptions,
pour permettre une sauvegarde partielle avec signalement plutôt qu'un blocage.

**Writer**
Module du code dont le rôle est d'écrire le fichier de sortie sur le système
de fichiers. Il construit le chemin, génère le slug, crée les dossiers si
nécessaire, demande confirmation si le fichier existe déjà, et préfixe les
avertissements du validateur en tête de fichier si nécessaire.

---

## Le rôle irremplaçable de l'humain

### Sans l'humain, l'IA générative ne s'arrête pas — elle dérive

L'IA générative ne s'arrête pas quand le cadre manque. Elle produit — souvent
de façon impressionnante. Mais sans présence humaine pour définir, cadrer
et contrôler, elle dérive.

> Sans la présence humaine pour définir, cadrer et contrôler,
> l'IA générative ne s'arrête pas — elle dérive.
>
> Elle produit, souvent de façon impressionnante, mais hors-cible :
> du code techniquement correct pour le mauvais problème,
> des outputs structurés mais infidèles au besoin réel,
> des specs qui évoluent sans que personne ne mesure
> l'accumulation de dette.
>
> La dérive est silencieuse. Elle ne produit pas d'erreur —
> elle produit de l'apparence. C'est précisément pourquoi
> le contrôle humain n'est pas une option de confort :
> c'est la condition sans laquelle le travail du LLM
> n'a pas de sens.
>
> Sur les tâches de définition, d'arbitrage, de validation
> et du jugement, l'humain n'est pas assisté par l'IA générative.
> Il en est le gouverneur.

### Les trois formes de dérive

**Dérive de cible** : le LLM optimise pour ce qu'il perçoit, pas pour ce qui
est voulu. Sans l'humain pour définir le problème réel, il répond au problème
apparent — et le fait très bien. Le résultat est techniquement correct
pour le mauvais usage.

**Dérive de spec** : sans l'humain pour geler les décisions, les specs
évoluent pendant le codage. Le code patch, s'allonge, devient ingérable.
Le LLM ne résiste pas — il s'adapte à chaque évolution sans signaler
l'accumulation. Ce qui semblait être de la flexibilité est en réalité
une perte de contrôle progressive. C'est la dette de contrôle appliquée
au développement.

**Dérive de qualité** : sans critères définis par l'humain, le LLM produit
des outputs qui *semblent* corrects. Il n'y a pas d'erreur visible — il y a
une apparence de justesse. Le contenu est plausible, la forme est respectée,
le résultat est livrable. Mais la fidélité au besoin réel s'est évaporée
silencieusement à chaque génération. Personne ne détecte la dégradation
parce que personne n'a défini ce que "correct" signifie précisément.
La qualité ne se mesure pas contre un vide — elle se mesure contre une
constitution. Sans elle, le LLM n'est pas faux. Il est indéfini.

### Ce que l'humain fait que l'IA ne fait pas

L'humain excelle là où le LLM ne peut structurellement pas le remplacer :
**le jugement**. Juger c'est peser des éléments hétérogènes, tenir compte
du contexte implicite, assumer une décision dont on est responsable.
Le LLM produit des options plausibles — l'humain tranche.

Sur les tâches suivantes, l'humain n'est pas remplaçable — et ne doit pas
chercher à l'être :

- **Définir le problème réel** : identifier ce qui est réellement cherché,
  derrière ce qui est formulé. Le LLM répond à ce qu'on lui dit, pas à
  ce qu'on veut dire.
- **Exercer son jugement** : évaluer si ce qui a été produit est juste,
  utile, fidèle — pas seulement plausible. C'est la capacité que l'humain
  ne doit jamais déléguer entièrement.
- **Trancher les décisions** : aucune décision de spec n'est prise par
  le LLM seul. L'humain valide, arbitre, assume.
- **Geler les specs** : décider que la phase de définition est terminée
  et que l'implémentation peut commencer. Sans ce geste délibéré,
  la dérive de spec est inévitable.
- **Contrôler la stratégie de test** : vérifier que les tests sont prévus,
  que leur type est approprié, que l'ordre est respecté. L'humain
  n'est pas le testeur — il est le garant de la stratégie de test.
- **Arbitrer les divergences** : quand le LLM produit quelque chose
  d'inattendu, décider si c'est le code qui doit changer ou la spec.
- **Valider l'alignement final** : s'assurer que ce qui a été produit
  correspond au besoin réel. C'est le rôle du maître d'ouvrage.

L'humain qui n'exerce plus son jugement — qui suit ce que le LLM propose
sans évaluer, sans questionner — a atteint son propre seuil de lucidité
structurelle. Il produit encore. Mais il ne gouverne plus.

---

## Architecture de gouvernance : Claude.ai et Claude Code

### Deux outils, deux rôles distincts

Claude.ai et Claude Code ne sont pas interchangeables. Les utiliser comme
s'ils l'étaient produit du code techniquement correct pour le mauvais usage.

| Dimension | Claude.ai | Claude Code |
|---|---|---|
| Posture naturelle | Réfléchir, cadrer, arbitrer | Produire, implémenter, avancer |
| Contexte principal | Le problème réel et les specs | Le code existant |
| Tendance observée | Séquentiel, prudent | Paralléliser, aller vite |
| Risque propre | Trop conceptuel | Diverge des specs sans le signaler |

### La phase d'orchestration — deux niveaux simultanés

L'orchestration opère à deux niveaux dans tout projet développé avec un LLM.

**Niveau technique** : un module central coordonne les autres sans contenir
de logique métier. Il appelle, il transmet, il séquence — il ne décide pas.
La logique métier est dans les modules spécialisés, pas dans le point d'entrée.
C'est une décision architecturale qui prépare les évolutions futures.

**Niveau processus** : l'humain orchestre les outils LLM en tandem. Il décide
quand utiliser Claude.ai pour cadrer, quand basculer vers Claude Code pour
implémenter, quand stopper et remonter aux specs. Cette orchestration
n'est pas automatique — elle est le travail central de pilotage du projet.

Ces deux niveaux s'alimentent mutuellement : une architecture bien orchestrée
au niveau technique rend le pilotage plus simple. Et un pilotage rigoureux
au niveau processus protège l'intégrité de l'architecture technique.

### Ce qui s'est passé concrètement

En cours de projet, Claude Code a été confronté au code existant et a proposé
une architecture cohérente avec ce qu'il voyait — techniquement correcte,
mais pour un problème différent de celui défini en co-construction.

**La règle opérationnelle appliquée** : face à une proposition de Claude Code
qui diverge des specs ou dépasse le cadre du prompt en cours, l'humain
copie cette proposition dans Claude.ai — qui dispose du contexte des specs
et de la constitution — et exerce son jugement depuis ce contexte.
La décision revient ensuite dans Claude Code sous forme d'instruction précise.
On ne corrige pas dans le code. On juge et arbitre dans Claude.ai d'abord,
puis on instruit Claude Code.

### La tension séquentiel / parallèle

Claude Code tend naturellement à paralléliser. Dans ce projet, cette tendance
était risquée : les modules ont des dépendances strictes. On ne peut pas
écrire le validateur sans les tests de contrat. On ne peut pas tester le
writer sans le validateur.

La discipline imposée : un prompt, un module, un test avant de passer
au suivant — dans l'ordre logique des dépendances.

### Le principe de gouvernance

```
Claude.ai   →  co-construction + specs + constitution
     ↓
Claude Code →  implémentation séquentielle dans ce cadre
     ↓
Divergence  →  l'humain exerce son jugement dans Claude.ai
     ↓
Claude.ai   →  arbitrage depuis le contexte des specs
     ↓
Claude Code →  reçoit une instruction précise et reprend
     ↑
Humain      →  orchestre, juge, valide à chaque étape
```

### Transférer cette méthode à Claude Code via CLAUDE.md

Claude Code lit automatiquement les fichiers CLAUDE.md présents dans
l'environnement. Il existe trois niveaux, lus en cascade du plus général
au plus spécifique :

```
~/.claude/CLAUDE.md                          → global, tous les projets
~/Projects/CLAUDE.md                         → tous les projets dans Projects
~/Projects/yt-knowledge-extractor/CLAUDE.md  → ce projet uniquement
```

En inscrivant les principes de cette méthode dans le CLAUDE.md global,
Claude Code les consulte au démarrage de chaque session et s'y conforme
sans qu'on ait besoin de les répéter. C'est la façon de rendre la méthode
opérationnelle au niveau de l'outil — pas seulement documentée dans un fichier
que personne ne lit avant de coder.

**Ce qui va dans le CLAUDE.md global** (applicable à tous les projets) :
les principes de méthode, la règle anti-dérive de spec, la constitution
minimale de tout projet, la stratégie de test en deux temps.

**Ce qui va dans le CLAUDE.md de projet** (spécifique à ce code) :
la constitution du projet, la stack technique, l'URL de référence pour
les tests, les comportements aux limites.

---

## Principe fondateur de la méthode

> Co-construire la pensée avant de produire un livrable.
> Ne jamais générer un artefact sans avoir d'abord clarifié
> le problème réel, la valeur ajoutée spécifique, et ce qui
> distingue ce livrable du bruit ambiant.

---

## Les 9 étapes de la méthode

### Étape 1 — Dissocier les problèmes

**Ce qu'on a fait** : avant de parler solution, on a nommé précisément
les problèmes. La question "extraire la connaissance d'une vidéo YouTube"
cachait deux problèmes distincts avec des architectures différentes :

- **Problème 1 — Rétention** : ne pas avoir de trace structurée après une vidéo dense
- **Problème 2 — Retrouvabilité** : ne plus savoir dans quelle vidéo un concept a été développé

**Ce que ça a produit** : une décision architecturale claire — V1 fiche
par vidéo, V2 recherche cross-vidéos — avec le transcript conservé dès
la V1 pour préparer la V2 sans migration.

**Transférable à** : tout projet où le besoin initial est formulé de façon vague.
Forcer la dissociation en sous-problèmes avant de chercher une solution unique.

---

### Étape 2 — Partir de l'usage réel, pas du livrable imaginé

**Ce qu'on a fait** : au lieu de proposer une structure, on a posé des
questions sur l'usage concret — ce que l'utilisateur cherche réellement,
comment il s'en sert, ce qu'il ne fera probablement jamais.

**Ce que ça a produit** : un output qui répond à des modes de recherche
réels, pas à une structure générique. Une section "personnelle" conçue
pour rester vide — parce que si le LLM la remplit, c'est lui qui retient,
pas l'utilisateur.

**Transférable à** : tout projet où on conçoit un output pour soi-même
ou un utilisateur. Toujours partir de "à quoi ça sert concrètement"
avant de concevoir la forme.

---

### Étape 3 — Tester les hypothèses avant d'écrire les specs

**Ce qu'on a fait** : avant de rédiger une ligne de spec, on a testé
l'hypothèse technique centrale sur du vrai matériel.

**Ce que ça a produit** : confirmation que l'architecture est faisable,
et une référence réelle pour les tests. Si le test avait échoué, les specs
auraient été différentes.

**Transférable à** : tout projet avec une dépendance technique non triviale.
Tester le point d'incertitude le plus risqué avant de spécifier, pas après.

---

### Étape 4 — Prendre les décisions une par une, pas en bloc

**Ce qu'on a fait** : chaque décision a été posée séparément, avec sa
logique expliquée et ses alternatives présentées.

| Décision | Options présentées | Choix et raison |
|---|---|---|
| Structure de l'output | Template proposé | Co-construite depuis les usages réels |
| Granularité | Fine vs grossière | Adaptée selon la densité du contenu |
| Provider LLM | Outil unique | Couche abstraite, outil par défaut |
| Comportement output incomplet | Bloquer / Sauvegarder | Sauvegarder + avertir |
| Contexte insuffisant | Tronquer / Chunker / Bloquer | Bloquer avec message explicite |

**Ce que ça a produit** : des specs sans ambiguïté. Chaque comportement
est le résultat d'une décision consciente, pas d'un défaut implicite.

**Transférable à** : tout projet de spécification. Forcer chaque décision
à être nommée, même les "évidentes".

---

### Étape 5 — Inscrire une constitution avant le code

**Ce qu'on a fait** : avant les specs techniques, on a rédigé un ensemble
de règles non négociables que ni le code ni le LLM ne peuvent violer.

Ces règles ne sont pas des contraintes de code. Ce sont des principes de
fidélité au besoin réel — ce que le LLM ne doit jamais faire, même si
le résultat semble acceptable en surface.

**Ce que ça a produit** : un garde-fou contre la dérive de qualité.
Sans constitution, le LLM est indéfini — pas faux, pas juste, indéfini.

**Transférable à** : tout projet impliquant un LLM dans la chaîne de
traitement. La constitution n'est pas un obstacle —
c'est le seul chemin pour que l'output soit digne de confiance.

---

### Étape 6 — Auditer les décisions avant de produire

**Ce qu'on a fait** : avant de rédiger les specs finales, on a fait un
audit explicite — décisions tranchées versus points encore ouverts.

**Ce que ça a produit** : des specs sans zones grises. Chaque comportement
est documenté, pas interprété par l'implémenteur.

**Transférable à** : tout processus de spécification. L'audit pré-rédaction
est une étape à part entière, pas une vérification optionnelle.

---

### Étape 7 — Distinguer la pensée du livrable

**Ce qu'on a fait** : plusieurs fois dans la session, la tentation de
raccourci est apparue — produire avant que la pensée soit complète.
À chaque fois, le processus a été ramené à la co-construction.

**Ce que ça a produit** : un document de specs transmissible — quelqu'un
qui n'a pas participé peut implémenter sans contexte additionnel.

**La règle** : si une tentation de produire apparaît avant que la pensée
soit complète, c'est un signal que la co-construction n'est pas terminée.

---

### Étape 8 — Définir les tests avant d'implémenter les modules à contrat fixe

#### Principe

Ne pas écrire les tests après le code pour valider ce qui a été fait.
Écrire les tests avant le code pour décrire ce qui doit être fait.
Cette discipline — le TDD, Test Driven Development — s'applique
spécifiquement aux modules dont le contrat est entièrement défini
dans les specs avant d'écrire une ligne de code.

L'humain ne joue pas le rôle de testeur. Il exerce son jugement sur
la stratégie de test : il vérifie que les tests sont prévus, que leur
type est adapté, que l'ordre est respecté.

#### Les deux temps

**Temps 1 — Tests de contrat : avant les modules concernés**

Les modules à contrat précis ont leurs tests écrits avant eux. Le code
est ensuite écrit pour faire passer ces tests — pas l'inverse.

> "Ne modifie pas les tests pour qu'ils s'adaptent au code.
> C'est le code qui s'adapte aux tests."

**Temps 2 — Tests d'intégration : après le pipeline complet**

Le test de bout en bout ne peut pas exister avant tous les autres modules.
Il est écrit en dernier.

#### Pourquoi c'est important avec un LLM implémenteur

Un LLM produit du code qui fonctionne selon sa propre interprétation
des specs. Les tests écrits avant lui donnent une définition non ambiguë
du succès. Sans eux, "ça marche" signifie "ça tourne" — pas "ça respecte
le contrat".

---

### Étape 9 — Angle mort : la sécurité

La sécurité n'a pas été abordée dans cette session. Ce n'est pas un oubli
anodin — c'est un angle mort structurel qui aurait dû être adressé
à deux étapes précises.

**À l'Étape 4** : valider les entrées utilisateur, définir le comportement
si une clé API est absente, avertir l'utilisateur que le contenu est envoyé
à une API externe.

**À l'Étape 5** : inscrire dans la constitution la responsabilité de
l'utilisateur concernant la confidentialité du contenu soumis.

**La règle** : la sécurité s'inscrit dans les décisions (Étape 4) et dans
la constitution (Étape 5). Si elle n'est pas adressée à ces deux moments,
elle ne sera pas adressée.

---

## La fiche comme preuve de concept

La fiche produite sur la vidéo de [Le SamourAI](https://www.youtube.com/@SamouraiDansant)
— *"La chute d'Anthropic : Le scandale qui révèle les failles de toute l'industrie de l'IA"*
— valide que SPECS.md fonctionne : 8 sections présentes, 8 blocs de chapitrage,
4 concepts avec définitions de l'auteur, citations verbatim, "Mes notes" vide,
23 sources filtrées.

Mais la fiche établit aussi des connexions directes avec la méthode —
la vidéo décrit, à l'échelle d'une industrie, exactement les risques
que cette méthode cherche à prévenir à l'échelle d'un projet.

### Les quatre connexions

**Le "seuil de lucidité structurelle" = la dérive de spec**
La vidéo définit ce seuil comme le moment où la vitesse de production dépasse
la capacité d'introspection. C'est exactement la dérive de spec : quand on code
plus vite qu'on ne spécifie, les patches s'accumulent, la dette de contrôle
grandit, et personne ne mesure l'écart.

**La "défection universelle" = l'absence de constitution**
Quand la pression pousse tout le monde à abandonner ses règles de prudence,
personne ne peut les maintenir unilatéralement. La constitution est précisément
le dispositif qui inscrit les règles non négociables avant que la pression
ne s'exerce — pas pendant.

**Le "coût de sortie cognitif" = le risque de dépendance au LLM**
Des organisations incapables de se désengager de leur outil IA parce qu'elles
y ont délégué leur mémoire et leurs processus. Dans la méthode, c'est le risque
de laisser Claude Code prendre les décisions d'architecture. L'humain gouverneur
— qui exerce son jugement — est la réponse directe à ce risque.

**Le "test du pilote" = l'exercice du jugement comme critère de maturité**
La vidéo propose d'évaluer si une organisation peut fonctionner sans son outil IA.
La méthode pose la même question : l'humain exerce-t-il réellement son jugement,
ou suit-il ce que les LLMs proposent ? L'humain qui ne juge plus — qui valide
sans évaluer — a atteint son propre seuil de lucidité structurelle.

---

## Ce qui est systématiquement transférable

### La séquence de questions

```
1.  Quel est le problème réel ? (dissocier si plusieurs)
2.  Quel est l'usage concret ? (partir du besoin, pas du livrable)
3.  Quelle est l'hypothèse technique risquée ? (tester avant de spécifier)
4.  Quelles sont les décisions à prendre ? (les nommer toutes, sécurité incluse)
5.  Quelles sont les règles non négociables ? (constitution)
6.  Y a-t-il des zones grises ? (audit pré-rédaction)
7.  Le livrable est-il transmissible sans contexte ? (test de transmissibilité)
8.  Quels modules ont un contrat fixe ? (tests de contrat avant implémentation)
9.  Quels risques de sécurité n'ont pas été adressés ? (angle mort explicite)
```

### La structure de specs en 5 blocs + constitution

```
Bloc 0 — Constitution              (règles non négociables)
Bloc 1 — Vue d'ensemble            (objectif, périmètre, hors scope, évolutions)
Bloc 2 — Architecture              (stack, structure, flux de traitement)
Bloc 3 — Prompt système            (en anglais, instruction LLM)
Bloc 4 — Comportements aux limites (chaque cas d'erreur et sa réponse)
Bloc 5 — Stratégie de test         (contrat, smoke, checklist humaine)
```

### Les principes centraux

> **Principe de non-raccourci** : si une tentation de produire apparaît
> avant que la pensée soit complète, c'est un signal que la co-construction
> n'est pas terminée.

> **Principe de dérive** : sans présence humaine pour définir, cadrer
> et contrôler, l'IA générative ne s'arrête pas — elle dérive.
> Elle produit de l'apparence, pas du sens.

> **Principe de gouvernance** : Claude.ai cadre et arbitre.
> Claude Code implémente dans ce cadre.
> L'humain orchestre les deux, exerce son jugement à chaque étape,
> et remonte les divergences dans Claude.ai avant de les accepter
> dans le code.

---

## Ce que cette méthode démontre comme expertise

**Usage** : savoir utiliser Claude.ai et Claude Code en tandem —
chacun dans son rôle — avec l'humain comme orchestrateur et gouverneur
qui exerce son jugement.

**Application** : avoir produit des specs transmissibles depuis une
session de dialogue structuré, avec une architecture de gouvernance
LLM documentée et un projet open-source installable.

**Expertise** : pouvoir cadrer cette méthode pour d'autres — en mission
client pour structurer un projet IA, en formation pour illustrer ce que
gouvernance-first signifie concrètement au niveau d'un projet,
en contribution à la communauté [Le SamourAI](https://www.youtube.com/@SamouraiDansant).

---

## Annexe A — Guide technique : tests dans un projet CLI Python + LLM

*Pour les lecteurs qui veulent répliquer la méthode sur un projet technique.*

### Tests de contrat — écrits avant les modules concernés

```python
def test_sections_obligatoires():
    assert "## Section A" in output
    assert "## Section B" in output

def test_section_personnelle_vide():
    section = extraire_section(output, "## Notes")
    assert section.strip() == "*(espace libre)*"

def test_chapitrage_dans_les_limites():
    n = compter_lignes_tableau(output, "## Chapitrage")
    assert 6 <= n <= 12
```

Règle absolue : si un test échoue, on corrige le code — jamais le test.

### Tests d'intégration — écrits après le pipeline complet

```python
def test_smoke():
    result = run_pipeline("URL_DE_REFERENCE")
    assert result.exists()
    assert result.stat().st_size > 0
```

### Séquence d'implémentation avec TDD partiel

```
Prompt 1  — Bootstrap (structure + fichiers vides + docstrings)
Prompt 2  — Module source de données
Prompt 3  — Module métadonnées
Prompt 4  — Couche LLM abstraite
Prompt 5  — Module de génération
Prompt 6  — Tests de contrat     ← avant validateur et writer
Prompt 7  — Validateur           ← implémenté pour passer les tests
Prompt 8  — Writer
Prompt 9  — Point d'entrée CLI
Prompt 10 — Test d'intégration   ← après pipeline complet
Prompt 11 — Documentation
```

### Instruction à donner au LLM implémenteur

```
Écris les tests de contrat avant que les modules concernés existent.
Les tests décrivent le contrat défini dans les specs — pas le code actuel.
Le module sera implémenté ensuite pour faire passer ces tests.
Ne modifie jamais un test pour qu'il s'adapte au code produit.
```

---

## Annexe B — Checklist sécurité minimale : tout projet CLI + LLM

*À parcourir à l'Étape 4 (décisions) et à l'Étape 5 (constitution).*

**Entrées utilisateur**
- [ ] Les entrées sont validées avant tout traitement
- [ ] Un format invalide produit un message d'erreur lisible, pas un crash
- [ ] Les URLs ou chemins sont vérifiés avant d'être passés aux APIs

**Clés et secrets**
- [ ] Les clés API sont dans `.env`, jamais dans le code
- [ ] `.env` est dans `.gitignore` — vérifié avant le premier commit
- [ ] `.env.example` documente les variables sans valeurs réelles
- [ ] Le comportement si une clé est absente est défini dans les specs

**Données envoyées aux APIs externes**
- [ ] La nature des données envoyées au LLM est documentée
- [ ] L'utilisateur est averti si le contenu peut être confidentiel
- [ ] Le provider LLM par défaut tient compte de la confidentialité

**Versioning**
- [ ] `.gitignore` exclut `.env`, fichiers de config, dossiers de sortie
- [ ] Le premier commit ne contient aucune clé ou donnée personnelle
- [ ] Les fichiers d'exemple ne contiennent que des valeurs fictives

---

*Document produit dans le cadre du projet YT Knowledge Extractor*
*Méthode applicable à tout projet de spécification technique impliquant un LLM*
*Communauté de référence : [Le SamourAI — IA et Stratégie](https://www.youtube.com/@SamouraiDansant)*
