# Dossier de recherche — EviSuff-Finance

**Date de l'audit : 13 juillet 2026**  
**Statut : thème sélectionné, protocole spécifié, noyau d'évaluation implémenté ; annotations humaines et expériences sur modèles réels encore à exécuter.**

## 1. Décision scientifique

Le thème large initial — *evidence sufficiency and calibrated abstention in
long-document financial agents* — est pertinent, mais il n'est pas nouveau en
l'état. Des travaux récents couvrent déjà la suffisance du contexte,
l'abstention, les questions non répondables, les citations, les preuves
contradictoires, les erreurs temporelles, le retrieval financier et
l'évaluation des agents de recherche.

La version défendable consiste à transformer cette idée générale en une
évaluation causale et appariée : pour chaque question financière réelle, on
identifie manuellement un ou plusieurs **ensembles minimaux suffisants de
preuves** (*minimal sufficient evidence sets*, MSES), puis on retire le plus
petit ensemble de passages qui casse toutes les voies de preuve possibles. On
mesure si l'agent passe correctement d'une réponse soutenue à une abstention,
tout en restant stable lorsque l'on retire seulement un passage non pertinent.

### Thème final recommandé

**When Relevant Evidence Is Not Enough: Counterfactual Evidence-Sufficiency
Evaluation for Long-Document Financial Agents**

Nom court du benchmark : **EviSuff-Finance**.

La contribution principale est un **benchmark diagnostique accompagné d'une
étude empirique**. Ce n'est pas un nouvel algorithme RAG. Cette décision est
importante : une simple comparaison BM25/dense/hybride/contextual retrieval
serait incrémentale et ne répondrait pas à la question scientifique centrale.

### Ce que l'article cherchera à établir

Les évaluations actuelles récompensent surtout le contenu de la réponse. Elles
ne montrent pas nécessairement que l'agent utilise causalement les preuves
requises. Un modèle peut retrouver des passages thématiquement proches,
répondre avec ses connaissances paramétriques ou produire une citation qui
semble plausible même lorsqu'aucune chaîne complète de preuve n'est présente.

L'article testera donc la proposition suivante, sans présumer du résultat :

> La pertinence des passages ne suffit pas à garantir une réponse justifiée ;
> la fiabilité doit être mesurée par la sensibilité comportementale de l'agent
> à la présence ou à l'absence des preuves nécessaires.

## 2. Audit de nouveauté

### Méthode de la revue

La revue a privilégié les articles primaires, les dépôts officiels et les
publications officielles de laboratoires. Les familles examinées sont : agents
financiers et QA financier, retrieval dans les filings longs, suffisance du
contexte et abstention, citations et attribution, preuves contradictoires ou
temporellement invalides, deep-research agents et travaux des frontier labs.
L'audit est large et récent, mais aucune recherche bibliographique ne peut
garantir littéralement l'exhaustivité. Une nouvelle recherche par titre,
abstract et citations devra être exécutée juste avant la soumission.

### Chevauchements directs

| Travail primaire | Ce qui existe déjà | Différence maintenue par EviSuff-Finance |
|---|---|---|
| [IPO Finance Agent](https://arxiv.org/abs/2606.23032) | 70 tâches IPO, recherche contextuelle, rubriques, dépôt SpaceX S-1 | Pas de MSES ni de paires où toutes les voies de preuve sont cassées |
| [Fin-RATE](https://arxiv.org/abs/2602.07294) | Tâches SEC, oracle vs RAG, diagnostic des erreurs d'entité et de temps | Ne modifie pas causalement l'answerability d'une même question |
| [Sufficient Context](https://arxiv.org/abs/2411.06037) | Suffisance du contexte et génération sélective | Étiquette surtout des contextes observés ; pas de MSES IPO et intervention appariée |
| [OverSearchQA](https://arxiv.org/abs/2601.05503) | Recherche répondable/non répondable et abstention | Web search, pas de longs filings ni de complétude de chaînes de preuve |
| [LIT-RAGBench](https://arxiv.org/abs/2603.06198) | Intégration, raisonnement, tableaux et abstention | Petit benchmark fictif ; pas de workflow SEC réel ni de paires MSES |
| [ERA](https://arxiv.org/abs/2604.20854) | Abstention fondée sur l'évidence | Ne combine pas IPO, MSES, citations par claim et oracle retrieval/génération |
| [RAGuard](https://arxiv.org/abs/2502.16101), [MAGIC](https://arxiv.org/abs/2507.21544), [ArbGraph](https://arxiv.org/abs/2604.18362) | Preuves trompeuses ou conflictuelles | Le cœur d'EviSuff est la suppression de preuve nécessaire ; les conflits restent une extension |
| [ALCE](https://arxiv.org/abs/2305.14627) | Exactitude et complétude des citations | Ne teste pas le changement de comportement après suppression de la preuve |
| [Cited but Not Verified](https://arxiv.org/abs/2605.06635) | Attribution de sources dans des rapports web | Pas d'interventions contrôlées sur l'answerability dans des filings |
| [FinAgentBench](https://arxiv.org/abs/2508.14052) | Sélection de documents et passages financiers | Retrieval-centric ; pas d'abstention après rupture des ensembles de preuve |
| [LOFin/HiREC](https://arxiv.org/abs/2505.20368) | Retrieval SEC à grande échelle et preuves curées | Ne mesure pas la sensibilité causale à la suffisance |
| [FinSage](https://arxiv.org/abs/2504.14493) | Agent financier et retrieval | Pas de protocole contrefactuel MSES |
| [Look-Ahead-Bench](https://arxiv.org/abs/2601.13770) | Biais temporel dans les LLM financiers point-in-time | Le temps n'est pas l'intervention principale proposée ici |
| [ResearchRubrics](https://arxiv.org/abs/2511.07685), [Mind2Web 2](https://arxiv.org/abs/2506.21506) | Évaluation d'agents de recherche et tâches web longues | Pas d'ensembles minimaux de preuve dans un corpus financier fermé |

Les travaux officiels des frontier labs confirment que le problème intéresse
directement leurs axes d'évaluation : [BrowseComp d'OpenAI](https://openai.com/index/browsecomp/)
évalue la recherche difficile sur le web, le [Contextual Retrieval
d'Anthropic](https://www.anthropic.com/engineering/contextual-retrieval)
travaille la récupération de contexte, et [FACTS Grounding de Google
DeepMind](https://deepmind.google/blog/facts-grounding-a-new-benchmark-for-evaluating-the-factuality-of-large-language-models/)
cible la factualité ancrée dans des sources. EviSuff-Finance se place à leur
intersection, mais avec une intervention contrôlée sur la nécessité de la
preuve.

### Verdict de nouveauté

La nouveauté **ne peut pas** être formulée comme « premier benchmark de
suffisance » ou « première évaluation de l'abstention ». La formulation
provisoire défendable est :

> À notre connaissance après audit au 13 juillet 2026, aucun travail examiné ne
> combine, sur des tâches réelles de filings IPO, des ensembles minimaux
> suffisants de preuves validés par humains, une suppression par *hitting set*
> cassant toutes les voies de preuve, un contrôle de suppression non pertinente,
> des citations au niveau des claims et une décomposition retrieval versus
> utilisation de la preuve.

Il s'agit d'une conclusion provisoire à revérifier, pas d'une déclaration
absolue de priorité.

## 3. Trois sujets évalués

Notes sur 5 ; une note élevée est favorable.

| Sujet | Type | Nouv. | 7–8 sem. | Gold labels | Coût | Reprod. | Hors finance | Frontier labs | Décision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| **A. EviSuff-Finance : interventions MSES appariées** | Benchmark + empirique | 4 | 4 | 4 | 4 | 5 | 4 | 5 | **Principal** |
| **B. The Evidence-Use Gap in IPO Agents** : version réduite sur 30 questions | Étude empirique | 3 | 5 | 4 | 5 | 4 | 3 | 4 | **Secours / MVP** |
| **C. Set-Aware Abstention Gate** : modèle apprenant à détecter la suffisance | Méthode | 3 | 2 | 4 | 2 | 3 | 5 | 5 | Ne pas choisir en primaire |

Le sujet C nécessiterait des données d'entraînement, une vraie innovation de
modélisation, davantage de compute et des comparaisons fortes. En sept semaines,
il augmente fortement le risque sans améliorer la validité des gold labels.
Une méthode pourra être ajoutée plus tard, une fois le benchmark stabilisé.

**Proposition rejetée :** « comparer plusieurs pipelines RAG sur IPO Finance
Agent ». Elle ne fournit ni nouvelle unité d'évaluation, ni intervention
causale, ni gold labels plus solides. Les retrievers restent des baselines et
des facteurs expérimentaux.

## 4. Questions de recherche falsifiables

### RQ1 — Sensibilité contrefactuelle

Un agent répond-il correctement lorsque la preuve est suffisante puis
s'abstient-il lorsque la plus petite intervention casse toutes les MSES ?

- Hypothèse à préenregistrer après le pilote : le taux de persistance non
  soutenue est supérieur à une valeur fixée par analyse de puissance.
- Résultat qui réfute l'hypothèse : la majorité des modèles passent presque
  toujours à l'abstention après suppression nécessaire, avec intervalles de
  confiance étroits.
- Métrique principale : **Paired Behavior Success**.

### RQ2 — Retrieval ou utilisation de la preuve

Quelle part de l'erreur disparaît lorsque l'on donne directement une MSES
gold ?

- Si l'oracle corrige presque toutes les erreurs, le retrieval est le goulot.
- Si des erreurs et réponses non soutenues persistent, le problème se situe
  aussi dans l'intégration de la preuve et la calibration.
- Comparaison principale : meilleur retrieval gelé versus `gold_only`.

### RQ3 — Pertinence ou suffisance

Les modèles réagissent-ils davantage à la suppression d'une preuve nécessaire
qu'à celle d'un distracteur ?

- Une bonne sensibilité exige un changement après `necessary_removal` et une
  stabilité après `irrelevant_removal`.
- Un modèle piloté par la proximité thématique échouera ce contraste.

## 5. Données et construction des gold labels

### Corpus principal

- Cible complète : **60 questions**, minimum défendable **40**.
- Minimum **3 filings S-1/F-1**, préférence **5**.
- Sources : SEC EDGAR, avec accession number, date, URL, hash du fichier et
  version du script d'extraction. L'[API EDGAR officielle](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
  doit être utilisée conformément à sa politique d'accès.
- SpaceX : moins de 40 % du test final afin d'éviter un benchmark mono-émetteur.
- Point de départ : les 70 questions publiques d'IPO Finance Agent, filtrées et
  reformulées seulement quand une réponse vérifiable existe dans le corpus
  autorisé.

Répartition cible : 18 questions quantitatives/multi-tables, 14 de disclosure,
12 comptables/forensic, 8 gouvernance/contrôle et 8 comparatives avec sources
externes gelées.

### Schéma d'annotation

Chaque item contient : question, réponse gold, claims atomiques, identifiants
stables des documents et passages, texte exact des preuves, une ou plusieurs
MSES, distracteurs, label d'answerability, date limite éventuelle, annotateurs
et décision d'adjudication.

Une MSES est suffisante si ses passages permettent de justifier tous les claims
nécessaires, et minimale si le retrait de n'importe lequel de ses éléments la
rend insuffisante. S'il existe plusieurs voies de preuve, elles doivent toutes
être annotées. L'intervention nécessaire retire alors un plus petit *hitting
set* qui intersecte chaque MSES.

Les questions de type « le filing ne divulgue pas X » seront traitées à part :
une absence n'est pas prouvée par un passage unique. Il faut définir une zone de
recherche bornée et un protocole de vérification exhaustif.

### Assurance qualité

- 10 items d'entraînement pour les annotateurs ;
- au moins 25 % en double annotation, idéalement 100 % pour le MVP de 30 items ;
- kappa de Cohen pour l'answerability ;
- précision/rappel/F1 au niveau des unités de preuve pour les spans ou sets ;
- adjudication de chaque désaccord ;
- vérification indépendante de chaque paire `necessary_removal` ;
- gel des données avant toute expérience sur les modèles finaux ;
- aucun même modèle ne doit générer les questions, fabriquer les gold labels,
  répondre et juger ses propres réponses.

### Go/no-go après deux semaines

Continuer si 20 paires sont validées, si le kappa d'answerability atteint 0,80
ou si les désaccords sont résolus par des règles explicites, si au moins 70 %
des items ont des MSES non ambiguës, et si deux personnes confirment que la
suppression nécessaire rend réellement la question non répondable dans le
corpus autorisé. Sinon, réduire aux questions quantitatives et de disclosure
déterministe.

## 6. Conditions expérimentales

Pour chaque question :

1. `full` : contexte complet fourni par le retrieval gelé ;
2. `gold_only` : une MSES sans distracteur ;
3. `necessary_removal` : le *hitting set* minimal est retiré, donc aucune MSES
   complète ne subsiste ;
4. `irrelevant_removal` : un distracteur est retiré, la réponse doit rester
   stable.

Extensions seulement si le cœur est terminé : injection de distracteurs
thématiques, puis contradiction avec métadonnées de date et de crédibilité. Le
test temporel est volontairement reporté pour éviter de diluer la contribution
et de chevaucher Look-Ahead-Bench.

Le prompt exige un JSON structuré : `answerable`, `p_answerable`, `answer`,
claims atomiques, IDs de citations pour chaque claim et informations manquantes
en cas d'abstention. Le nom de la condition n'est jamais montré au modèle.

## 7. Modèles, retrieval et baselines

### Modèles de génération

Matrice principale recommandée à la date de l'audit :

- OpenAI `gpt-5.6-terra` pour l'équilibre capacité/coût ; sous-échantillon avec
  `gpt-5.6-sol` si le budget le permet. Les identifiants, fenêtres de contexte
  et tarifs courants sont documentés sur la [page officielle des modèles
  OpenAI](https://developers.openai.com/api/docs/models).
- Anthropic `claude-sonnet-5` ; sous-échantillon `claude-opus-4-8`. Les IDs et
  versions sont indiqués dans la [documentation officielle
  Anthropic](https://platform.claude.com/docs/en/about-claude/models/overview).
- Google `gemini-2.5-pro` comme version stable et, seulement en analyse
  secondaire, `gemini-3.1-pro-preview` si sa version exacte peut être gelée. La
  [liste officielle Gemini](https://ai.google.dev/gemini-api/docs/models)
  distingue les modèles stables et preview.
- Open-weight : `Qwen/Qwen3-14B` quantifié 4 bits pour la baseline reproductible.
  Un modèle 30B–32B est optionnel sur A100.

Tous les IDs exacts doivent être gelés le jour du premier run. Température 0,
trois répétitions par configuration, même contrat JSON, même limite de sortie,
et journalisation du prompt, de la latence, des tokens, du coût et des erreurs.

### Retrieval

- BM25 ;
- dense `BAAI/bge-m3` ;
- hybride par Reciprocal Rank Fusion ;
- hybride contextualisé avec reranker ;
- oracle gold.

Chunks de 512 et 1 024 tokens, overlap 128 ; `top-k` dans {5, 10, 20} sur le
développement, puis un choix gelé. Les systèmes de retrieval sont évalués
d'abord sans génération. La matrice de génération complète n'utilise ensuite
que le meilleur retrieval gelé et l'oracle, afin d'éviter une explosion du
coût et un article réduit à une comparaison de pipelines.

### Baselines comportementales

- always-answer ;
- abstention par seuil sur score de retrieval ;
- meilleur pipeline IPO Finance Agent reproductible ;
- oracle gold ;
- closed-book pour détecter la connaissance paramétrique ;
- tâche « answer given, locate evidence » pour isoler l'attribution ;
- ordre des passages mélangé pour tester la sensibilité positionnelle.

### Ablations

- sans instruction explicite d'abstention ;
- sans score probabiliste ;
- une citation par réponse versus citations par claim ;
- une seule MSES annotée versus toutes les MSES ;
- retrait naïf d'un passage versus *hitting-set removal* ;
- chunk 512 versus 1 024 ;
- top-k faible versus élevé ;
- avec et sans reranker.

## 8. Métriques et statistiques

### Métriques primaires

**Paired Behavior Success (PBS)** : proportion de paires où le modèle répond
correctement en `full` et s'abstient en `necessary_removal`.

**Unsupported Persistence Rate (UPR)** : proportion de cas
`necessary_removal` où le modèle répond tout de même.

**Counterfactual Abstention Shift (CAS)** :

`P(abstain | necessary removal) - P(abstain | full)`.

### Retrieval, réponse, citations et calibration

- Recall@k et nDCG@k ;
- **Complete Evidence Recall** : au moins une MSES entière est récupérée ;
- précision/rappel des claims ;
- précision des citations : une citation émise soutient-elle réellement le
  claim associé ?
- complétude des citations : tous les claims nécessaires ont-ils une citation
  suffisante ?
- selective accuracy, courbe risque-couverture et AURC ;
- score de Brier pour `p_answerable` ; ECE seulement en secondaire ;
- stabilité après suppression non pertinente ;
- latence, tokens, appels outils et coût.

### Tests statistiques

- bootstrap apparié par question, IC à 95 % ;
- test de McNemar pour les différences comportementales appariées ;
- régression logistique à effets mixtes avec modèle et question/filing comme
  effets ;
- correction de Holm pour les comparaisons secondaires ;
- tailles d'effet et intervalles de confiance, pas seulement des p-values ;
- analyse par catégorie préspécifiée, pas de sous-groupes improvisés.

Pour les réponses ouvertes, les claims sont évalués séparément. Un juge LLM ne
devient acceptable qu'après calibration sur au moins 150 paires claim-citation
étiquetées par humains, avec accord juge-humain publié et audit manuel des
désaccords des modèles principaux.

## 9. Taille de l'expérience, machine et budget

### Expérience complète

Avec 60 questions, 4 conditions, 5 modèles et 3 répétitions : environ **3 600
générations**. Le retrieval est évalué séparément, ce qui évite de multiplier
ce nombre par chaque retriever.

### Machine recommandée

Pour une étude principalement via API : 8–16 cœurs CPU, 32 Go de RAM minimum
(64 Go préférés), 100 Go de SSD, sans GPU obligatoire.

Pour la baseline locale 14B quantifiée et le reranking : RTX 4090 ou A10G 24 Go,
64 Go de RAM et 200 Go de SSD. Pour un 32B : A100 40/80 Go recommandé. Un 70B
n'est pas nécessaire au papier principal.

La machine de ce workspace ne possède actuellement ni GPU détectable, ni stack
`torch/transformers`, ni clés API de modèles. Le noyau d'évaluation fonctionne
ici, mais les runs réels doivent attendre un environnement de calcul et des
identifiants configurés par variables d'environnement. Les secrets ne doivent
jamais être inscrits dans le dépôt.

### Budget

Les tarifs changent. Les pages officielles [OpenAI](https://openai.com/api/pricing/),
[Anthropic](https://platform.claude.com/docs/en/about-claude/models/overview)
et [Gemini](https://ai.google.dev/gemini-api/docs/pricing) doivent être figées
dans le journal d'expérience. Pour 3 600 runs de contexte récupéré, réserver
**500 à 1 500 USD** est prudent, incluant générations, répétitions, juges et
reruns. Le MVP peut viser **150 à 500 USD**. Un pilote de 5 questions doit
mesurer les tokens réels avant d'autoriser la matrice complète.

## 10. Grandes lignes de l'article

1. **Introduction** : la pertinence ne garantit pas la suffisance ; limite des
   rubriques answer-only ; intervention MSES ; contributions.
2. **Related Work** : finance QA/agents, retrieval long-document, suffisance et
   abstention, citations, conflits/temps, deep-research evaluation.
3. **Task Definition** : claims atomiques, MSES, hitting set, quatre conditions,
   métriques appariées.
4. **EviSuff-Finance Dataset** : filings, sélection, annotation, adjudication,
   questions négatives, accord et contamination.
5. **Experimental Setup** : retrievers, modèles/version, prompts, répétitions,
   juges, statistiques, compute et coût.
6. **Results** : comportement apparié ; oracle vs retrieval ; contrôle
   nécessaire vs non pertinent ; citations ; calibration ; coût.
7. **Analysis** : taxonomie d'erreurs, catégories, modèles, sensibilité à
   l'ordre et au top-k, cas vérifiés.
8. **Limitations** : taille, spécialisation finance, subjectivité de la
   minimalité, API drift, connaissance paramétrique.
9. **Conclusion** : conclusion étroite sur le suivi de la preuve nécessaire,
   pas sur la qualité générale de l'analyste financier.

## 11. Ce qui a déjà été implémenté

Le dossier `evisuff-finance` contient :

- schéma JSONL des items, claims, preuves, MSES, dates et métadonnées ;
- validation automatique des ensembles minimaux ;
- calcul du plus petit *hitting set* ;
- génération déterministe des quatre conditions ;
- PBS, UPR, CAS, Brier, abstention, citations, Complete Evidence Recall et
  bootstrap apparié ;
- configuration expérimentale ;
- huit tests unitaires ;
- exemple fictif et smoke test ;
- audit reproductible du dépôt IPO Finance Agent ;
- protocole, audit bibliographique et plan d'article.

## 12. Résultats disponibles aujourd'hui

### Résultats réels : audit du dépôt public

Au commit `091f06913e39738ef464ac3548ad4b533ac47c50`, le dépôt public contient 70
questions SpaceX : 28 quantitatives, 21 disclosure, 8 forensic, 6 comparatives,
4 gouvernance et 3 modeling.

Dans `rubrics_checked_7thpass.json`, les blocs de qualité automatisés du dépôt
ont une moyenne de 0,896 et contiennent 23 recommandations `stop`, 43 `repair`,
4 `enrich`, 149 problèmes listés et aucun champ top-level d'identifiant de
preuve. Ces valeurs sont un audit d'artefacts amont, pas une validation humaine
indépendante ni une estimation du nombre de rubriques incorrectes.

Un artefact public Qwen de 70 réponses contient une URL dans 68 réponses,
avec une médiane d'une URL, mais aucune citation Markdown inline ni identifiant
stable de passage. Cela décrit uniquement le format de cet artefact ; ce n'est
pas une mesure de factualité et cela ne doit pas être généralisé aux autres
modèles. Le constat justifie toutefois l'ajout de provenance au niveau des
claims.

### Résultats synthétiques : validation logicielle seulement

Huit tests unitaires passent. Sur trois items fictifs, un comportement
`evidence_sensitive` obtient PBS=1 et UPR=0, tandis qu'un comportement
`relevance_only` obtient PBS=0 et UPR=1. Cela prouve que le code distingue les
deux comportements attendus. **Ces nombres ne sont pas des résultats
scientifiques et ne doivent pas apparaître comme résultats du papier.**

Il n'existe pas encore de résultats réels de modèles sur EviSuff-Finance,
parce que les MSES réelles n'ont pas encore été annotées et que cet
environnement n'a ni clés API ni GPU. Toute table de performance fournie
maintenant serait fabriquée.

## 13. Sujet principal, secours et version minimale publiable

### Principal

Benchmark de 60 questions, 3–5 filings, quatre conditions, 4–5 modèles, gold
labels humains, retrieval/oracle, citations par claim et statistiques
appariées.

### Secours

Étude empirique de 30 questions sur au moins 3 filings, double annotation
complète, trois modèles frontier plus Qwen3-14B, conditions `full`, `gold_only`,
`necessary_removal` et contrôle non pertinent. Ne pas revendiquer un benchmark
large ; revendiquer un protocole et un résultat empirique soigneusement
délimités.

### Minimum publiable

20–30 questions principalement quantitatives/disclosure, 3 filings, toutes
double-annotées, 4 modèles, 3 répétitions, quatre conditions, PBS/UPR/CAS,
Complete Evidence Recall, précision/complétude des citations et bootstrap
apparié. Cette version peut convenir à un workshop si les effets sont nets et
les labels irréprochables ; elle serait trop faible pour prétendre à une
couverture générale du domaine.

## 14. Calendrier réaliste

Au 13 juillet 2026, la deadline main track NeurIPS 2026 du 6 mai est passée.
Le [calendrier officiel](https://neurips.cc/Conferences/2026/Dates) indique une
date suggérée du **29 août 2026** pour les contributions aux workshops. Le plan
doit donc viser un workshop précis, SSRN et le term paper, pas présenter le
travail comme une nouvelle soumission main track 2026.

- Semaine 1 : fixer le workshop, les filings et 40–60 questions candidates ;
- Semaine 2 : annoter/adjudication des 20 premières paires, décision go/no-go ;
- Semaine 3 : terminer les gold labels et geler les données ;
- Semaine 4 : ingestion, retrieval, prompts, pilote de coût et contrôle qualité ;
- Semaine 5 : matrice principale de modèles ;
- Semaine 6 : audit humain, statistiques, figures et erreurs ;
- Semaine 7 : rédaction NeurIPS, limitations, reproducibility checklist ;
- marge finale : quatre reviews chatbot exigées, corrections, GitHub, SSRN et
  soumission workshop selon son appel exact.

## 15. Contraintes encore inconnues et bloquantes

- workshop exact, deadline et limite de pages ;
- budget API total ;
- accès aux modèles et régions autorisées ;
- disponibilité d'un GPU ;
- nombre et expertise des annotateurs ;
- droit de republier les passages SEC extraits et choix du format de
  redistribution ;
- liste finale des émetteurs/filings ;
- disponibilité de sorties complètes d'IPO Finance Agent pour les baselines ;
- capacité à garder un sous-ensemble test caché ;
- politique du cours après la deadline du 5 mai ;
- auteurs, rôles, ordre des auteurs et validation de Mostapha.

La prochaine action critique n'est pas de rédiger l'introduction : c'est de
faire valider par Mostapha le thème, les trois RQ, les quatre conditions et le
go/no-go, puis d'annoter les 20 premières paires. Sans ce pilote, il n'est pas
possible de savoir si la contribution repose sur des gold labels suffisamment
stables.
