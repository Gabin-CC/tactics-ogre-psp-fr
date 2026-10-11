# Guide de traduction — Tactics Ogre: Let Us Cling Together (PSP) → français

## Contexte
RPG tactique médiéval-fantastique, ton grave, politique, souvent archaïsant (l'anglais utilise « ere », « mislike », « thee » ponctuellement).
Le héros s'appelle Denam par défaut mais son nom est une variable `{hero}` ; sa sœur Catiua, son ami d'enfance Vyce.

## Règles techniques (IMPÉRATIVES)
1. **Balises** : tout ce qui est entre accolades `{...}` doit être conservé à l'identique (même orthographe, mêmes espaces, même nombre).
   Exemples : `{np}` (nouvelle bulle, toujours en tout début), `{pp}` (saut de page), `{hero}` (nom du héros), `{order}` (nom de l'ordre),
   `{FF 83 0101fff1f0}` (variable : nom d'unité/objet), `{FF 84 01ff01}` (variable : nombre), `{icon 4}` (icône de bouton),
   `{select 1}` (début d'un menu de choix), `{pal 3}`/`{palreset}` (couleur), `{FF 9A 04}` etc.
   Tu peux déplacer une balise de variable dans la phrase si la syntaxe française l'exige, mais jamais la supprimer ni la dupliquer.
   `{np}`, `{select N}` et les balises `{FF ..}` en tête de texte restent en tête.
2. **Sauts de ligne** `\n` : conserve la même structure. Dans les dialogues (`kind: emes`), le jeu fait le retour à la ligne automatiquement ; les `\n` sont des retours voulus par l'auteur : garde-les au même endroit logique. Une bulle doit rester COURTE : vise au plus ~15 % de caractères de plus que l'anglais par bulle/page. Si une page devient vraiment trop longue, coupe-la en deux avec `{pp}` plutôt que d'allonger.
   Pour les textes de menus/descriptions (`kind: xlc`) avec des `\n` : les lignes ont une largeur limitée ; chaque ligne française doit avoir au plus le nombre de caractères de la ligne anglaise la plus longue du même texte. Recoupe librement les lignes, sans ajouter plus d'une ligne au total.
3. **Libellés courts** (noms d'objets, de classes, de sorts, boutons, en-têtes de menu) : la place est très limitée. Reste aussi court que l'anglais (idéalement ≤ longueur anglaise + 3 caractères). Abrège si nécessaire (ex. « Épée long. » plutôt que rien de lisible).
4. **Libellés entièrement en MAJUSCULES** : écris-les en majuscules SANS accents (la petite police n'a pas d'accents) : « NOM », « OBJETS », « ATTENTION ».
5. Caractères autorisés : lettres latines avec accents français (é è ê ë à â î ï ô ö ù û ü ç œ æ, majuscules accentuées aussi), ponctuation usuelle, « » … — –. Pas d'emoji, pas d'autres alphabets.
6. Ponctuation française : espace avant `? ! : ;` et à l'intérieur des guillemets « », apostrophe droite `'`. Points de suspension : `...` (trois points) comme dans la source.
7. Ne traduis pas : les chaînes techniques (ex. `000_01`, `PROCESS_TYPE_003`, `debugMap`), les noms de personnes. Si une entrée ne doit pas être traduite, renvoie-la telle quelle.

## Style
- Registre soutenu, médiéval. Pas d'anglicismes ni de tournures modernes familières (sauf personnages vulgaires : brigands, mercenaires, Vyce quand il s'emporte).
- **Tu / vous** : Denam, Catiua et Vyce se tutoient entre eux. Les nobles, chevaliers, officiers et inconnus se vouvoient. Un supérieur peut tutoyer un subordonné ; un subordonné vouvoie son supérieur. Les ennemis qui se méprisent peuvent se tutoyer. Reste cohérent au sein d'une même scène.
- Catiua appelle Denam « petit frère » dans certains contextes anglais (« little brother ») ; Denam l'appelle « ma sœur » / « Sœur » (« Sister »).
- Les citations/incantations (sorts) : ton poétique, archaïsant.

## Noms propres et termes (à respecter)
- Personnages : garder les noms anglais (Denam, Catiua, Vyce, Lanselot, Ronwey, Balbatos, Brantyn, Dorgalua, Warren, Canopus, Gildas, Mirdyn…).
- Peuples / factions : **Walister** (invariable : « les Walister », « un Walister », « la résistance walister »), **Galgastan** (invariable : « les Galgastan », « l'armée galgastan », « Galgastani » → « Galgastan »), **Bakram** (invariable), « Bakram-Valerian Kingdom » → « royaume de Bakram-Valeria ».
- Lieux : garder les noms (Valeria, Golyat, Almorica, Heim, Coritanae, Brigantys…). « Isle(s) » → « île(s) ». « Valerian Isles » → « îles de Valeria ».
- Lodis → Lodis ; « Lodissian » → « lodissien » ; « Holy Lodissian Empire » → « Saint-Empire lodissien ». Xenobia → Xenobia ; « Xenobian » → « xenobien ».
- « Dark Knights » → « Chevaliers Noirs » ; « Dark Knights Loslorien » → « Chevaliers Noirs de Loslorien ». « Order » (ordre de chevalerie) → « Ordre ». « Holy Knights » → « Chevaliers Saints ».
- « the Resistance » → « la Résistance ». « Duke » → « duc ». « Regent » → « régent ». « Hierophant » → « hiérophante ». « Sir » → « messire » (ou « sire » pour un roi). « Lord » → « seigneur ».
- « goth » (monnaie) → « goth ». « Warren Report » → « Rapport de Warren ». « Chariot Tarot » → « Tarot du Chariot ». « World Tarot » → « Tarot du Monde ».
- « Philaha » (dieu) → Philaha. « Xytegenia » → Xytegenia. « the Wheel » (du destin) → « la Roue ».
- Statistiques : HP → PV, MP → PM, TP → PT, EXP → EXP, LV/Lv → Nv, STR → FOR, VIT → VIT, DEX → DEX, AGI → AGI, AVD → ESQ, INT → INT, MND → ESP, RES → RES, RT → TR (temps de récupération), Move → Dépl.
- Le glossaire `glossary.json` (s'il est fourni) fait foi pour les noms d'objets, de classes, de compétences et de sorts.
