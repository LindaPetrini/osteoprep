#!/usr/bin/env python3
"""
Seed Italian MCQ questions for topic quizzes.
CSV format for future bulk import:
  topic_slug,question_it,choice_a,choice_b,choice_c,choice_d,correct_index
  correct_index: 0=A, 1=B, 2=C, 3=D
"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "osteoprep.db")

QUESTIONS = [
    # topic_slug, question_it, [choice_a, choice_b, choice_c, choice_d], correct_index

    # --- BIOLOGY: cellula-eucariotica ---
    ("cellula-eucariotica",
     "Quale delle seguenti strutture è presente nella cellula eucariotica ma NON in quella procariotica?",
     ["Ribosomi", "Membrana plasmatica", "Nucleo delimitato da membrana", "DNA"], 2),

    ("cellula-eucariotica",
     "Il reticolo endoplasmatico rugoso (RER) è coinvolto principalmente in:",
     ["Produzione di lipidi", "Sintesi e trasporto di proteine", "Digestione cellulare", "Produzione di ATP"], 1),

    ("cellula-eucariotica",
     "Quale organello è responsabile della digestione intracellulare tramite enzimi idrolitici?",
     ["Mitocondrio", "Vacuolo", "Lisosoma", "Perossisoma"], 2),

    ("cellula-eucariotica",
     "Il citoscheletro cellulare è composto principalmente da:",
     ["Fosfolipidi e colesterolo", "Microtubuli, microfilamenti e filamenti intermedi", "DNA e RNA", "Glicoproteine di membrana"], 1),

    ("cellula-eucariotica",
     "L'apparato di Golgi svolge la funzione di:",
     ["Sintesi proteica", "Modificazione, smistamento e secrezione di proteine", "Produzione di energia", "Replicazione del DNA"], 1),

    ("cellula-eucariotica",
     "Quale organello contiene la propria molecola circolare di DNA e si riproduce per fissione binaria?",
     ["Lisosoma", "Vacuolo", "Nucleo", "Mitocondrio"], 3),

    # --- BIOLOGY: membrana-cellulare ---
    ("membrana-cellulare",
     "Qual è il principale componente strutturale della membrana plasmatica?",
     ["Glicogeno", "Fosfolipidi", "Proteine integrali", "Colesterolo"], 1),

    ("membrana-cellulare",
     "Quale funzione svolge il colesterolo nella membrana plasmatica a temperature fisiologiche?",
     ["Aumenta la permeabilità al glucosio", "Stabilizza la fluidità della membrana", "Fornisce energia alla cellula", "Trasporta ioni sodio"], 1),

    ("membrana-cellulare",
     "Cosa si intende per 'permeabilità selettiva' della membrana plasmatica?",
     ["La membrana lascia passare solo l'acqua", "La membrana è impermeabile a tutte le molecole", "La membrana regola il passaggio di molecole in base a dimensione e polarità", "La membrana permette il passaggio solo di ioni"], 2),

    ("membrana-cellulare",
     "Come avviene il trasporto attivo attraverso la membrana plasmatica?",
     ["Per gradiente di concentrazione senza consumo energetico", "Tramite proteine di trasporto con consumo di ATP contro gradiente", "Per osmosi diretta", "Mediante fusione di vescicole"], 1),

    ("membrana-cellulare",
     "L'endocitosi è il processo con cui la cellula:",
     ["Espelle materiale verso l'esterno", "Ingloba materiale dall'esterno tramite invaginazione della membrana", "Sintetizza proteine di membrana", "Modifica i lipidi della membrana"], 1),

    # --- BIOLOGY: nucleo-cellulare ---
    ("nucleo-cellulare",
     "Qual è la funzione principale dell'involucro nucleare?",
     ["Sintetizzare proteine", "Separare il DNA dal citoplasma e regolare gli scambi", "Produrre ATP", "Immagazzinare calcio"], 1),

    ("nucleo-cellulare",
     "Dove avviene la sintesi dell'RNA ribosomale (rRNA)?",
     ["Nel citoplasma", "Nel reticolo endoplasmatico", "Nel nucleolo", "Nei mitocondri"], 2),

    ("nucleo-cellulare",
     "I pori nucleari servono principalmente a:",
     ["Permettere il passaggio selettivo di molecole tra nucleo e citoplasma", "Replicare il DNA", "Sintetizzare lipidi", "Produrre RNA ribosomale"], 0),

    ("nucleo-cellulare",
     "Il DNA nucleare negli eucarioti è avvolto attorno a proteine dette:",
     ["Actina", "Tubulina", "Istoni", "Laminine"], 2),

    ("nucleo-cellulare",
     "La cromatina in forma condensata (eterocromatina) è associata a:",
     ["Geni altamente espressi", "Geni trascritti attivamente", "Geni non espressi o poco espressi", "Centromeri attivi"], 2),

    # --- BIOLOGY: mitosi-meiosi ---
    ("mitosi-meiosi",
     "In quale fase della mitosi i cromatidi fratelli si separano e migrano ai poli opposti della cellula?",
     ["Profase", "Metafase", "Anafase", "Telofase"], 2),

    ("mitosi-meiosi",
     "La meiosi produce cellule figlie con numero di cromosomi:",
     ["Uguale alla cellula madre (diploide)", "Doppio rispetto alla cellula madre", "Dimezzato rispetto alla cellula madre (aploide)", "Triplo rispetto alla cellula madre"], 2),

    ("mitosi-meiosi",
     "Il crossing-over avviene nella:",
     ["Anafase I della meiosi", "Profase I della meiosi", "Metafase II della meiosi", "Telofase della mitosi"], 1),

    ("mitosi-meiosi",
     "Quante cellule figlie produce la mitosi da una cellula diploide (2n)?",
     ["1 cellula diploide (2n)", "2 cellule diploidi (2n)", "4 cellule aploidi (n)", "2 cellule aploidi (n)"], 1),

    ("mitosi-meiosi",
     "Quale struttura proteica allinea i cromosomi al centro della cellula durante la metafase?",
     ["Centrosoma", "Fuso mitotico (fibre del fuso)", "Centriolo", "Cinetocoro"], 1),

    ("mitosi-meiosi",
     "Nella meiosi II, cosa si separano?",
     ["Cromosomi omologhi", "Cromatidi fratelli", "Bivalenti", "Tetrade"], 1),

    ("mitosi-meiosi",
     "Qual è il risultato finale della meiosi in un organismo con 2n=46?",
     ["2 cellule con 46 cromosomi", "4 cellule con 46 cromosomi", "4 cellule con 23 cromosomi", "2 cellule con 23 cromosomi"], 2),

    # --- BIOLOGY: dna-rna-proteine ---
    ("dna-rna-proteine",
     "Quale base azotata è presente nell'RNA ma non nel DNA?",
     ["Adenina", "Uracile", "Guanina", "Citosina"], 1),

    ("dna-rna-proteine",
     "La trascrizione del DNA produce:",
     ["Una molecola di DNA figlia", "Una molecola di RNA messaggero", "Una proteina direttamente", "Un ribosoma"], 1),

    ("dna-rna-proteine",
     "Il codone di stop UAA indica al ribosoma di:",
     ["Iniziare la traduzione", "Aggiungere un aminoacido specifico", "Terminare la sintesi proteica", "Spostare l'mRNA"], 2),

    ("dna-rna-proteine",
     "Nella replicazione del DNA, l'enzima che sintetizza il nuovo filamento è:",
     ["RNA polimerasi", "DNA polimerasi", "Ligasi", "Elicasi"], 1),

    ("dna-rna-proteine",
     "Quante basi formano un codone nell'mRNA?",
     ["1", "2", "3", "4"], 2),

    ("dna-rna-proteine",
     "Il tRNA ha il ruolo di:",
     ["Trascrivere il DNA in RNA", "Portare gli aminoacidi al ribosoma durante la traduzione", "Replicare il DNA", "Processare l'mRNA nel nucleo"], 1),

    # --- BIOLOGY: respirazione-cellulare ---
    ("respirazione-cellulare",
     "Dove avviene la glicolisi nella cellula?",
     ["Matrice mitocondriale", "Membrana mitocondriale interna", "Citoplasma (citosol)", "Reticolo endoplasmatico"], 2),

    ("respirazione-cellulare",
     "Quante molecole di ATP vengono prodotte complessivamente dalla respirazione aerobica di una molecola di glucosio?",
     ["2 ATP", "8 ATP", "~36-38 ATP", "~100 ATP"], 2),

    ("respirazione-cellulare",
     "Il ciclo di Krebs (ciclo dell'acido citrico) avviene nella:",
     ["Membrana mitocondriale interna", "Citoplasma", "Matrice mitocondriale", "Membrana mitocondriale esterna"], 2),

    ("respirazione-cellulare",
     "Quale molecola viene completamente ossidata nel ciclo di Krebs?",
     ["Glucosio", "Acetil-CoA", "NADH", "Piruvato"], 1),

    ("respirazione-cellulare",
     "La catena di trasporto degli elettroni è localizzata nella:",
     ["Matrice mitocondriale", "Membrana mitocondriale interna", "Membrana mitocondriale esterna", "Citoplasma"], 1),

    ("respirazione-cellulare",
     "Nella fermentazione lattica, il piruvato viene ridotto a:",
     ["Etanolo", "CO2", "Acido lattico", "Acetil-CoA"], 2),

    ("respirazione-cellulare",
     "L'accettore finale di elettroni nella respirazione aerobica è:",
     ["NAD+", "FAD", "CO2", "Ossigeno molecolare (O2)"], 3),

    # --- BIOLOGY: fotosintesi ---
    ("fotosintesi",
     "Le reazioni luminose della fotosintesi avvengono nei:",
     ["Stroma del cloroplasto", "Tilacoidi (membrane tilacoidali)", "Citoplasma", "Mitocondri"], 1),

    ("fotosintesi",
     "Il ciclo di Calvin (fase oscura) utilizza come prodotti delle reazioni luminose:",
     ["CO2 e H2O", "O2 e glucosio", "ATP e NADPH", "ADP e NADP+"], 2),

    ("fotosintesi",
     "La clorofilla assorbe preferenzialmente luce di colori:",
     ["Verde e giallo", "Rosso e blu-violetto", "Arancio e bianco", "Solo luce ultravioletta"], 1),

    ("fotosintesi",
     "La fotolisi dell'acqua durante le reazioni luminose libera:",
     ["CO2", "O2 (ossigeno molecolare)", "Glucosio", "NADPH"], 1),

    ("fotosintesi",
     "La prima molecola stabile prodotta nel ciclo di Calvin è:",
     ["Glucosio", "RuBP", "3-fosfoglicerato (3-PGA)", "NADPH"], 2),

    ("fotosintesi",
     "La fotosintesi può essere riassunta dalla formula generale:",
     ["6CO2 + 6H2O → C6H12O6 + 6O2", "C6H12O6 + 6O2 → 6CO2 + 6H2O", "6CO2 + 6O2 → C6H12O6 + 6H2O", "6H2O + 6O2 → C6H12O6 + 6CO2"], 0),

    # --- BIOLOGY: genetica-mendeliana ---
    ("genetica-mendeliana",
     "In un incrocio Tt × Tt, quale è il rapporto fenotipico atteso nella generazione F2?",
     ["1:1 alti:bassi", "3:1 dominante:recessivo", "1:2:1", "Tutti dominanti"], 1),

    ("genetica-mendeliana",
     "Un individuo eterozigote per un carattere presenta:",
     ["Due alleli identici", "Due alleli diversi (uno dominante e uno recessivo)", "Solo alleli recessivi", "Nessun allele per quel carattere"], 1),

    ("genetica-mendeliana",
     "Il principio di segregazione di Mendel afferma che:",
     ["I caratteri si mescolano nelle generazioni successive", "I due alleli di un gene si separano durante la formazione dei gameti", "I geni su cromosomi diversi si ereditano insieme", "I caratteri dominanti eliminano quelli recessivi"], 1),

    ("genetica-mendeliana",
     "Se entrambi i genitori sono portatori sani (Aa), qual è la probabilità che un figlio sia malato (aa)?",
     ["25%", "50%", "75%", "100%"], 0),

    ("genetica-mendeliana",
     "Un individuo con genotipo AA è definito:",
     ["Eterozigote dominante", "Eterozigote recessivo", "Omozigote dominante", "Emizigote"], 2),

    ("genetica-mendeliana",
     "La seconda legge di Mendel (legge dell'assortimento indipendente) si applica a geni che:",
     ["Sono sullo stesso cromosoma vicini", "Si trovano su cromosomi omologhi diversi o lontani sullo stesso", "Hanno espressione pleiotropica", "Mostrano codominanza"], 1),

    # --- BIOLOGY: evoluzione-selezione ---
    ("evoluzione-selezione",
     "Quale meccanismo proposto da Darwin e Wallace è alla base dell'evoluzione biologica?",
     ["Eredità dei caratteri acquisiti (Lamarck)", "Selezione naturale", "Deriva genetica", "Mutazione dirigita"], 1),

    ("evoluzione-selezione",
     "L'equilibrio di Hardy-Weinberg descrive una popolazione in cui:",
     ["Le frequenze alleliche cambiano ogni generazione", "Le frequenze alleliche rimangono costanti in assenza di forze evolutive", "La selezione naturale è molto intensa", "Si verifica sempre ibridazione"], 1),

    ("evoluzione-selezione",
     "Il concetto di 'fitness biologica' si riferisce alla capacità di un organismo di:",
     ["Sopravvivere alle malattie", "Riprodursi e trasmettere i propri alleli alla generazione successiva", "Crescere rapidamente", "Resistere alle variazioni climatiche"], 1),

    ("evoluzione-selezione",
     "La speciazione alloptrica si verifica quando:",
     ["Due popolazioni si evolvono nello stesso territorio", "Una barriera geografica isola due popolazioni che divergono nel tempo", "La selezione sessuale favorisce un morfotipo", "Si verifica poliploidia"], 1),

    ("evoluzione-selezione",
     "Quale dei seguenti è un esempio di struttura omologa che supporta l'evoluzione comune?",
     ["Ala del pipistrello e ala della farfalla (analogia)", "Ala del pipistrello e braccio umano", "Occhio del polpo e occhio dei vertebrati", "Pinna del delfino e pinna dello squalo"], 1),

    ("evoluzione-selezione",
     "La deriva genetica ha effetti più pronunciati in:",
     ["Popolazioni molto numerose", "Popolazioni molto piccole (collo di bottiglia)", "Ambienti stabili", "Specie con alto tasso riproduttivo"], 1),

    # --- BIOLOGY: sistema-nervoso ---
    ("sistema-nervoso",
     "La parte del neurone che trasmette l'impulso nervoso verso il corpo cellulare è:",
     ["Assone", "Guaina mielinica", "Dendrite", "Bottone sinaptico"], 2),

    ("sistema-nervoso",
     "La guaina mielinica attorno all'assone svolge la funzione di:",
     ["Nutrire il neurone", "Produrre neurotrasmettitori", "Accelerare la conduzione dell'impulso nervoso (conduzione saltatoria)", "Connettere neuroni diversi"], 2),

    ("sistema-nervoso",
     "La sinapsi chimica trasmette il segnale nervoso tramite:",
     ["Contatto diretto tra neuroni", "Corrente elettrica diretta", "Rilascio di neurotrasmettitori nella fessura sinaptica", "Onde di pressione"], 2),

    ("sistema-nervoso",
     "Il sistema nervoso centrale (SNC) è composto da:",
     ["Nervi cranici e spinali", "Encefalo e midollo spinale", "Sistema simpatico e parasimpatico", "Neuroni motori e sensoriali"], 1),

    ("sistema-nervoso",
     "Un arco riflesso include, nell'ordine corretto:",
     ["Effettore → neurone motore → interneurone → neurone sensoriale → recettore", "Recettore → neurone sensoriale → (interneurone) → neurone motore → effettore", "Encefalo → midollo spinale → muscolo", "Muscolo → nervo → recettore"], 1),

    ("sistema-nervoso",
     "Il potenziale d'azione nel neurone è generato principalmente dall'afflusso di:",
     ["Ioni potassio (K+) verso l'interno", "Ioni sodio (Na+) verso l'interno", "Ioni cloro (Cl-) verso l'esterno", "Ioni calcio (Ca2+) verso l'esterno"], 1),

    # --- BIOLOGY: mitocondri ---
    ("mitocondri",
     "Qual è il prodotto finale principale della catena di trasporto degli elettroni mitocondriale?",
     ["NADH", "CO2", "ATP", "Glucosio"], 2),

    ("mitocondri",
     "La membrana mitocondriale interna è caratterizzata da numerose ripiegature chiamate:",
     ["Cisterne", "Cristae", "Villi", "Lamelle"], 1),

    ("mitocondri",
     "Quale molecola entra nel ciclo di Krebs come substrato iniziale?",
     ["Glucosio", "Piruvato", "Acetil-CoA", "FADH2"], 2),

    ("mitocondri",
     "L'ATP sintasi mitocondriale produce ATP utilizzando:",
     ["Direttamente la luce solare", "Il gradiente protonico (H+) attraverso la membrana interna", "L'ossidazione diretta del glucosio", "L'idrolisi del NADH"], 1),

    ("mitocondri",
     "Quale gas è consumato dai mitocondri durante la respirazione aerobica?",
     ["CO2", "N2", "H2", "O2"], 3),

    # --- BIOLOGY: tessuti-animali ---
    ("tessuti-animali",
     "Quali sono i quattro tipi fondamentali di tessuto animale?",
     ["Osseo, muscolare, nervoso, cartilagineo", "Epiteliale, connettivo, muscolare, nervoso", "Sanguigno, linfatico, nervoso, muscolare", "Adiposo, ghiandolare, muscolare, epiteliale"], 1),

    ("tessuti-animali",
     "Il tessuto epiteliale ha la funzione principale di:",
     ["Contrarsi e produrre movimento", "Rivestire superfici e cavità del corpo e formare ghiandole", "Trasmettere segnali elettrici", "Immagazzinare energia", ], 1),

    ("tessuti-animali",
     "Il collagene è una proteina caratteristica del:",
     ["Tessuto nervoso", "Tessuto muscolare striato", "Tessuto connettivo", "Tessuto epiteliale"], 2),

    ("tessuti-animali",
     "Il tessuto muscolare cardiaco si distingue da quello scheletrico perché:",
     ["È involontario e le cellule sono non ramificate", "È involontario e presenta cellule ramificate con dischi intercalari", "È volontario e multinucleato", "Non si contrae mai spontaneamente"], 1),

    ("tessuti-animali",
     "Le giunzioni strette (tight junctions) tra cellule epiteliali servono a:",
     ["Permettere il libero passaggio di molecole", "Impedire il passaggio paracellulare di sostanze tra le cellule", "Trasmettere segnali elettrici", "Ancorare il citoscheletro alla matrice extracellulare"], 1),

    ("tessuti-animali",
     "Il tessuto connettivo comprende:",
     ["Solo il tessuto osseo e cartilagineo", "Tessuto osseo, cartilagineo, adiposo, sangue e connettivo propriamente detto", "Solo le fibre muscolari lisce", "Solo il sangue e la linfa"], 1),

    # --- BIOLOGY: sistemi-organo ---
    ("sistemi-organo",
     "Il cuore degli mammiferi è diviso in quante camere?",
     ["2 (un atrio e un ventricolo)", "3 (due atri e un ventricolo)", "4 (due atri e due ventricoli)", "6 (tre atri e tre ventricoli)"], 2),

    ("sistemi-organo",
     "Lo scambio gassoso (O2/CO2) nei polmoni avviene a livello degli:",
     ["Bronchi", "Bronchioli", "Alveoli polmonari", "Trachea"], 2),

    ("sistemi-organo",
     "Quale organo produce insulina per regolare la glicemia?",
     ["Fegato", "Stomaco", "Pancreas (isole di Langerhans)", "Surrene"], 2),

    ("sistemi-organo",
     "Il rene filtra il sangue producendo urina: in quale struttura avviene la filtrazione iniziale?",
     ["Ansa di Henle", "Tubulo contorto distale", "Capsula di Bowman (glomerulo)", "Pelvi renale"], 2),

    ("sistemi-organo",
     "Dove viene prodotta la bile, fondamentale per la digestione dei lipidi?",
     ["Stomaco", "Pancreas", "Intestino tenue", "Fegato"], 3),

    ("sistemi-organo",
     "La pressione arteriosa sistolica corrisponde alla pressione:",
     ["Durante il rilassamento del cuore (diastole)", "Durante la contrazione ventricolare (sistole)", "Nella vena cava", "Nel ventricolo destro"], 1),

    # --- BIOLOGY: virus-procarioti ---
    ("virus-procarioti",
     "Quale struttura è ASSENTE nei virus ma presente nelle cellule procariote?",
     ["Capside proteico", "Acido nucleico (DNA o RNA)", "Ribosomi", "Envelope lipidico"], 2),

    ("virus-procarioti",
     "Il ciclo litico virale termina con:",
     ["L'integrazione del genoma virale nel DNA ospite", "La lisi della cellula ospite e rilascio di nuovi virioni", "La trasformazione della cellula in cellula tumorale", "La formazione di uno stato di latenza"], 1),

    ("virus-procarioti",
     "La parete cellulare batterica è composta principalmente da:",
     ["Cellulosa", "Chitina", "Peptidoglicano", "Collagene"], 2),

    ("virus-procarioti",
     "I batteri Gram-positivi si differenziano dai Gram-negativi per:",
     ["Avere un doppio strato di membrana lipidica", "Possedere uno spesso strato di peptidoglicano e nessuna membrana esterna", "Essere tutti patogeni", "Mancanza di parete cellulare"], 1),

    ("virus-procarioti",
     "I procarioti si riproducono principalmente per:",
     ["Mitosi", "Meiosi", "Fissione binaria", "Sporulazione sessuale"], 2),

    ("virus-procarioti",
     "Quale dei seguenti è un esempio di virus a RNA?",
     ["Batteriofago T4", "HIV (virus dell'immunodeficienza umana)", "Adenovirus", "Parvovirus"], 1),

    # --- BIOLOGY: biotecnologie-dna ---
    ("biotecnologie-dna",
     "La PCR (Polymerase Chain Reaction) serve a:",
     ["Sintetizzare proteine in vitro", "Amplificare una specifica sequenza di DNA", "Sequenziare proteine", "Modificare la struttura del DNA per taglio con enzimi"], 1),

    ("biotecnologie-dna",
     "Gli enzimi di restrizione tagliano il DNA:",
     ["In punti casuali lungo il filamento", "In sequenze nucleotidiche specifiche (siti di restrizione)", "Solo in presenza di ATP", "Esclusivamente nei procarioti"], 1),

    ("biotecnologie-dna",
     "L'elettroforesi su gel di agarosio separa i frammenti di DNA in base a:",
     ["La sequenza nucleotidica", "Il contenuto in GC", "La dimensione (lunghezza) e la carica elettrica", "Il peso molecolare delle proteine associate"], 2),

    ("biotecnologie-dna",
     "Un plasmide è utilizzato come vettore nelle biotecnologie perché:",
     ["È un virus che infetta i batteri", "È una molecola di DNA circolare extracromosomica che può replicarsi autonomamente", "È un tipo di RNA ribosomale", "È un enzima di restrizione"], 1),

    ("biotecnologie-dna",
     "La tecnologia CRISPR-Cas9 permette di:",
     ["Amplificare il DNA tramite PCR", "Modificare (editare) sequenze specifiche del genoma con precisione", "Produrre anticorpi monoclonali", "Clonare interi organismi"], 1),

    ("biotecnologie-dna",
     "Il DNA ricombinante si ottiene:",
     ["Dalla mutazione spontanea del DNA cellulare", "Unendo sequenze di DNA di origini diverse tramite enzimi di restrizione e ligasi", "Dalla duplicazione del DNA durante la mitosi", "Dall'ibridazione di due molecole di RNA"], 1),

    # --- CHEMISTRY: atomo-struttura ---
    ("atomo-struttura",
     "Il numero atomico (Z) di un elemento indica il numero di:",
     ["Neutroni nel nucleo", "Protoni nel nucleo (uguale agli elettroni nell'atomo neutro)", "Nucleoni totali (protoni + neutroni)", "Elettroni nel guscio esterno"], 1),

    ("atomo-struttura",
     "Due atomi dello stesso elemento con diverso numero di massa sono detti:",
     ["Isobari", "Isotoni", "Isotopi", "Isomeri"], 2),

    ("atomo-struttura",
     "Qual è la carica elettrica del neutrone?",
     ["Positiva (+1)", "Negativa (-1)", "Nulla (0)", "Variabile in base all'elemento"], 2),

    ("atomo-struttura",
     "Il guscio elettronico più vicino al nucleo può contenere al massimo:",
     ["8 elettroni", "2 elettroni", "18 elettroni", "32 elettroni"], 1),

    ("atomo-struttura",
     "Il numero di massa (A) è definito come:",
     ["Il numero di protoni", "Il numero di neutroni", "Il numero di protoni più il numero di neutroni", "Il numero di elettroni"], 2),

    ("atomo-struttura",
     "In un atomo neutro di carbonio (Z=6), quanti elettroni sono presenti?",
     ["12", "6", "8", "3"], 1),

    # --- CHEMISTRY: tavola-periodica ---
    ("tavola-periodica",
     "Gli elementi del gruppo 1 (IA) della tavola periodica sono chiamati:",
     ["Alogeni", "Gas nobili", "Metalli alcalini", "Metalli alcalino-terrosi"], 2),

    ("tavola-periodica",
     "L'elettronegatività di un elemento tende ad aumentare spostandosi:",
     ["Da sinistra a destra nel periodo e dall'alto verso il basso nel gruppo", "Da destra a sinistra nel periodo e dall'alto verso il basso nel gruppo", "Da sinistra a destra nel periodo e dal basso verso l'alto nel gruppo", "Ugualmente in tutte le direzioni"], 2),

    ("tavola-periodica",
     "Il raggio atomico tende a diminuire spostandosi:",
     ["Da sinistra a destra nel periodo (a parità di periodo)", "Da destra a sinistra nel periodo", "Dall'alto verso il basso nel gruppo", "Non varia nella tavola periodica"], 0),

    ("tavola-periodica",
     "I gas nobili si trovano nel gruppo:",
     ["1 (IA)", "7 (VIIA)", "18 (VIIIA/0)", "17 (VIIA)"], 2),

    ("tavola-periodica",
     "Gli alogeni (Fluoro, Cloro, Bromo, Iodio) appartengono al gruppo:",
     ["1", "2", "16", "17"], 3),

    ("tavola-periodica",
     "Il periodo nella tavola periodica indica:",
     ["Il numero di elettroni del guscio esterno", "Il numero del guscio elettronico più esterno occupato", "Il numero di ossidazione dell'elemento", "Il gruppo di appartenenza"], 1),

    # --- CHEMISTRY: legami-chimici ---
    ("legami-chimici",
     "Quale tipo di legame si forma per condivisione di una coppia di elettroni tra due atomi?",
     ["Legame ionico", "Legame covalente", "Legame idrogeno", "Legame di Van der Waals"], 1),

    ("legami-chimici",
     "Il legame ionico si forma tipicamente tra:",
     ["Due non metalli", "Un metallo e un non metallo", "Due atomi dello stesso elemento", "Due molecole d'acqua"], 1),

    ("legami-chimici",
     "Il legame a idrogeno si forma tra:",
     ["Due atomi di carbonio", "Un atomo di H legato a N, O, o F e un altro atomo elettronegativo", "Due metalli alcalini", "Atomi di gas nobili"], 1),

    ("legami-chimici",
     "Nella molecola di N2, i due atomi di azoto sono uniti da:",
     ["Un legame singolo", "Un legame doppio", "Un legame triplo", "Legame ionico"], 2),

    ("legami-chimici",
     "Le forze di Van der Waals sono:",
     ["Legami covalenti molto forti", "Interazioni deboli tra molecole dovute a dipoli temporanei", "Legami ionici tra ioni opposti", "Legami covalenti polari intramolecolari"], 1),

    # --- CHEMISTRY: acidi-basi-ph ---
    ("acidi-basi-ph",
     "Un acido forte in soluzione acquosa ha un pH:",
     ["Vicino a 7", "Maggiore di 7", "Minore di 7", "Uguale a 14"], 2),

    ("acidi-basi-ph",
     "La costante di dissociazione acida Ka per un acido forte è:",
     ["Molto piccola (Ka << 1)", "Circa uguale a 1", "Molto grande (Ka >> 1)", "Uguale a zero"], 2),

    ("acidi-basi-ph",
     "Il pH di una soluzione con [H+] = 10^-9 mol/L è:",
     ["3", "5", "9", "11"], 2),

    ("acidi-basi-ph",
     "Secondo la teoria di Brønsted-Lowry, un acido è una sostanza che:",
     ["Accetta protoni (H+)", "Dona protoni (H+)", "Libera ioni OH-", "Accetta elettroni"], 1),

    ("acidi-basi-ph",
     "Una soluzione tampone (buffer) è composta da:",
     ["Solo un acido forte e acqua", "Un acido debole e il suo sale (base coniugata)", "Una base forte e un acido forte in concentrazione uguale", "Solo acqua purissima"], 1),

    # --- CHEMISTRY: reazioni-chimiche ---
    ("reazioni-chimiche",
     "In una reazione esotermica, l'energia del sistema:",
     ["Rimane costante", "Aumenta", "Diminuisce, liberando calore nell'ambiente", "Viene assorbita dall'ambiente"], 2),

    ("reazioni-chimiche",
     "Il bilanciamento di una reazione chimica richiede che:",
     ["Il numero di molecole sia uguale a destra e a sinistra", "Il numero di atomi di ogni elemento sia uguale a destra e a sinistra", "La massa molare dei prodotti superi quella dei reagenti", "Si formi sempre acqua come prodotto"], 1),

    ("reazioni-chimiche",
     "Una reazione di sintesi è del tipo:",
     ["A + B → C", "AB → A + B", "A + BC → AC + B", "AB + CD → AD + CB"], 0),

    ("reazioni-chimiche",
     "Il catalizzatore in una reazione chimica:",
     ["Aumenta l'energia di attivazione", "Viene consumato irreversibilmente durante la reazione", "Abbassa l'energia di attivazione e aumenta la velocità di reazione", "Sposta l'equilibrio verso i prodotti"], 2),

    ("reazioni-chimiche",
     "La velocità di una reazione chimica dipende dalla:",
     ["Solo dalla concentrazione dei reagenti", "Solo dalla temperatura", "Da temperatura, concentrazione, superficie di contatto e presenza di catalizzatori", "Solo dalla pressione"], 2),

    # --- CHEMISTRY: ossidoriduzione ---
    ("ossidoriduzione",
     "In una reazione di ossidoriduzione (redox), l'ossidazione consiste nella:",
     ["Perdita di protoni", "Acquisto di elettroni", "Perdita di elettroni", "Acquisto di protoni"], 2),

    ("ossidoriduzione",
     "In una cella galvanica (pila), l'ossidazione avviene all':",
     ["Catodo", "Anodo", "Diaframma", "Ponte salino"], 1),

    ("ossidoriduzione",
     "Nella reazione: Zn + CuSO4 → ZnSO4 + Cu, quale elemento viene ossidato?",
     ["Cu (rame)", "SO4^2- (solfato)", "Zn (zinco)", "Nessuno dei due"], 2),

    ("ossidoriduzione",
     "Il numero di ossidazione dell'ossigeno nei composti è generalmente:",
     ["+2", "0", "-2", "+1"], 2),

    ("ossidoriduzione",
     "Un agente riducente è una sostanza che:",
     ["Acquista elettroni e si riduce", "Cede elettroni e si ossida", "Non partecipa alla reazione redox", "Acquista protoni dalla soluzione"], 1),

    ("ossidoriduzione",
     "Il numero di ossidazione dell'idrogeno nei composti con non metalli è generalmente:",
     ["-1", "0", "+1", "+2"], 2),

    # --- CHEMISTRY: carboidrati ---
    ("carboidrati",
     "I monosaccaridi sono carboidrati:",
     ["Non ulteriormente idrolizzabili", "Formati da due unità zuccherine", "Formati da molte unità zuccherine", "Solubili solo nei solventi organici"], 0),

    ("carboidrati",
     "Il glucosio e il fruttosio hanno la stessa formula molecolare (C6H12O6) ma struttura diversa. Sono quindi:",
     ["Isomeri di posizione", "Enantiomeri", "Isomeri di struttura (isomeri strutturali)", "Polimeri"], 2),

    ("carboidrati",
     "Il saccarosio è un disaccaride composto da:",
     ["Glucosio + Galattosio", "Glucosio + Fruttosio", "Glucosio + Glucosio", "Fruttosio + Galattosio"], 1),

    ("carboidrati",
     "L'amido e il glicogeno sono polisaccaridi di riserva formati da:",
     ["Fruttosio", "Galattosio", "Glucosio", "Ribosio"], 2),

    ("carboidrati",
     "Il legame glicosidico unisce i monosaccaridi nei polisaccaridi con la perdita di:",
     ["Una molecola di CO2", "Una molecola di H2O", "Una molecola di NH3", "Un gruppo fosfato"], 1),

    ("carboidrati",
     "La cellulosa è un polisaccaride strutturale formato da glucosio con legami:",
     ["α(1→4)", "β(1→4)", "α(1→6)", "β(1→6)"], 1),

    # --- CHEMISTRY: lipidi ---
    ("lipidi",
     "I trigliceridi sono formati da una molecola di glicerolo e:",
     ["Tre molecole di colesterolo", "Tre catene di acidi grassi legate da legami estere", "Due molecole di fosfolipidi", "Quattro amminoacidi"], 1),

    ("lipidi",
     "Gli acidi grassi saturi si differenziano da quelli insaturi perché:",
     ["Contengono uno o più doppi legami C=C", "Non contengono doppi legami C=C (catena satura di H)", "Hanno meno atomi di carbonio", "Sono sempre allo stato liquido a temperatura ambiente"], 1),

    ("lipidi",
     "I fosfolipidi sono i principali componenti della membrana cellulare grazie alla loro natura:",
     ["Idrofila", "Idrofoba", "Anfipatica (testa idrofila e coda idrofoba)", "Elettricamente carica"], 2),

    ("lipidi",
     "Il colesterolo è un lipide della classe degli:",
     ["Trigliceridi", "Fosfolipidi", "Steroidi", "Cere"], 2),

    ("lipidi",
     "Quale delle seguenti funzioni NON è svolta dai lipidi?",
     ["Riserva energetica", "Componente strutturale delle membrane", "Trasmissione dell'impulso nervoso diretto", "Sintesi di ormoni steroidei"], 2),

    ("lipidi",
     "Gli acidi grassi omega-3 e omega-6 sono definiti 'essenziali' perché:",
     ["Sono presenti solo nei grassi animali", "L'organismo non è in grado di sintetizzarli e devono essere assunti con la dieta", "Forniscono più energia degli altri acidi grassi", "Sono necessari solo nei bambini"], 1),

    # --- CHEMISTRY: proteine-struttura ---
    ("proteine-struttura",
     "I quattro livelli di struttura proteica sono, nell'ordine:",
     ["Quaternaria, terziaria, secondaria, primaria", "Primaria, secondaria, terziaria, quaternaria", "Secondaria, primaria, quaternaria, terziaria", "Terziaria, secondaria, primaria, quaternaria"], 1),

    ("proteine-struttura",
     "Il legame peptidico si forma tra:",
     ["Il gruppo amminico (-NH2) di un amminoacido e il gruppo carbossilico (-COOH) di un altro", "Due gruppi amminici", "Due gruppi carbossilici", "Il gruppo R di due amminoacidi"], 0),

    ("proteine-struttura",
     "La struttura secondaria α-elica è stabilizzata da:",
     ["Legami covalenti tra catene laterali (R)", "Legami a idrogeno tra il C=O di un residuo e il N-H di un residuo vicino nella stessa catena", "Ponti disolfuro", "Interazioni ioniche"], 1),

    ("proteine-struttura",
     "La denaturazione proteica comporta la perdita della struttura tridimensionale a causa di:",
     ["Idrolisi dei legami peptidici", "Alterazione delle interazioni non covalenti (calore, pH estremi, agenti chimici)", "Mutazione del gene codificante", "Degradazione del mRNA"], 1),

    ("proteine-struttura",
     "Le proteine con struttura quaternaria sono formate da:",
     ["Una singola catena polipeptidica ripiegata", "Due o più catene polipeptidiche (subunità) associate", "Solo aminoacidi apolari", "Sequenze ripetute di amminoacidi identici"], 1),

    ("proteine-struttura",
     "I ponti disolfuro (legami S-S) si formano tra residui di:",
     ["Serina", "Alanina", "Cisteina", "Glicina"], 2),

    # --- CHEMISTRY: enzimi ---
    ("enzimi",
     "Gli enzimi sono principalmente:",
     ["Lipidi con funzione catalitica", "Carboidrati che accelerano le reazioni", "Proteine che fungono da catalizzatori biologici", "Acidi nucleici che catalizzano reazioni di trascrizione"], 2),

    ("enzimi",
     "Il sito attivo di un enzima è:",
     ["L'intera superficie dell'enzima", "La regione dove si lega il substrato e avviene la catalisi", "Il cofattore dell'enzima", "Il sito di regolazione allosterica"], 1),

    ("enzimi",
     "La costante di Michaelis (Km) rappresenta:",
     ["La velocità massima della reazione enzimatica", "La concentrazione di substrato a cui la velocità è il 50% della Vmax", "La concentrazione dell'enzima", "L'energia di attivazione della reazione"], 1),

    ("enzimi",
     "Nell'inibizione competitiva, l'inibitore:",
     ["Si lega al sito attivo competendo con il substrato", "Si lega a un sito diverso dal sito attivo", "Denatura irreversibilmente l'enzima", "Aumenta la Vmax della reazione"], 0),

    ("enzimi",
     "La temperatura ottimale per la maggior parte degli enzimi umani è circa:",
     ["4°C", "25°C", "37°C", "60°C"], 2),

    ("enzimi",
     "I cofattori enzimatici sono:",
     ["Sempre molecole organiche", "Molecole non proteiche (ioni metallici o coenzimi) necessarie per l'attività enzimatica", "Inibitori dell'enzima", "Substrati dell'enzima"], 1),

    # --- CHEMISTRY: soluzioni-proprieta ---
    ("soluzioni-proprieta",
     "La molarità di una soluzione si calcola come:",
     ["grammi di soluto / litri di soluzione", "moli di soluto / litri di soluzione", "moli di soluto / kg di solvente", "grammi di soluto / grammi di solvente × 100"], 1),

    ("soluzioni-proprieta",
     "Quale principio descrive il 'simile scioglie il simile' riguardo la solubilità?",
     ["Le sostanze polari tendono a sciogliersi in solventi polari; le apolari in solventi apolari", "Le sostanze ioniche non si sciolgono mai in acqua", "La solubilità diminuisce sempre con l'aumentare della temperatura", "Le sostanze gassose sono più solubili ad alta temperatura"], 0),

    ("soluzioni-proprieta",
     "L'osmosi è il movimento di:",
     ["Soluto attraverso una membrana permeabile verso la zona a bassa concentrazione", "Acqua (solvente) attraverso una membrana semipermeabile da zona a bassa concentrazione di soluto a zona ad alta concentrazione di soluto", "Ioni attraverso canali proteici", "Molecole di gas attraverso una membrana"], 1),

    ("soluzioni-proprieta",
     "L'aggiunta di un soluto non volatile all'acqua pura causa:",
     ["La diminuzione del punto di ebollizione", "L'abbassamento del punto crioscopico (punto di congelamento) e l'innalzamento del punto di ebollizione", "Nessun cambiamento nelle proprietà fisiche dell'acqua", "Solo l'innalzamento del punto di fusione"], 1),

    ("soluzioni-proprieta",
     "Le proprietà colligative di una soluzione dipendono:",
     ["Dal tipo chimico del soluto", "Solo dalla massa del soluto", "Dal numero di particelle di soluto disciolte (non dalla loro natura chimica)", "Dal pH della soluzione"], 2),

    ("soluzioni-proprieta",
     "Una soluzione satura è quella in cui:",
     ["Il soluto è completamente disciolto", "Il solvente è saturo di vapore acqueo", "Non si può sciogliere altro soluto a quella temperatura (si è raggiunto l'equilibrio di solubilità)", "La concentrazione di soluto supera la Vmax di solubilità"], 2),

    # --- CHEMISTRY: equilibrio-chimico ---
    ("equilibrio-chimico",
     "Il principio di Le Chatelier afferma che se un sistema all'equilibrio è perturbato:",
     ["Raggiunge immediatamente un nuovo equilibrio senza cambiamenti", "Reagisce in modo da minimizzare la perturbazione e ristabilire un equilibrio", "Si sposta sempre verso i reagenti", "La costante di equilibrio Kc cambia"], 1),

    ("equilibrio-chimico",
     "Per la reazione A + B ⇌ C + D, la costante di equilibrio Kc è espressa come:",
     ["Kc = [A][B] / [C][D]", "Kc = [C][D] / [A][B]", "Kc = [A] + [B] / [C] + [D]", "Kc = [C] × [D] + [A] × [B]"], 1),

    ("equilibrio-chimico",
     "L'aumento della temperatura in una reazione endotermica all'equilibrio sposta l'equilibrio:",
     ["Verso i reagenti", "Verso i prodotti", "Non modifica la posizione dell'equilibrio", "Diminuisce Kc"], 1),

    ("equilibrio-chimico",
     "Un sistema tampone (buffer) biologico mantiene il pH costante tramite:",
     ["Aggiunta continua di acido forte", "Una coppia acido debole / base coniugata che neutralizza H+ o OH- aggiunti", "Precipitazione dei sali in eccesso", "Evaporazione del solvente"], 1),

    ("equilibrio-chimico",
     "L'equazione di Henderson-Hasselbalch descrive il pH di una soluzione tampone come:",
     ["pH = pKa + log([acido]/[base coniugata])", "pH = pKa + log([base coniugata]/[acido])", "pH = Ka × [acido] / [base]", "pH = 7 - pKa"], 1),

    ("equilibrio-chimico",
     "L'aumento della pressione in un equilibrio gassoso sposta la reazione verso:",
     ["Sempre verso i prodotti", "Sempre verso i reagenti", "Il lato con meno moli di gas", "Il lato con più moli di gas"], 2),

    # --- CHEMISTRY: nomenclatura-inorganica ---
    ("nomenclatura-inorganica",
     "La formula NaCl corrisponde a:",
     ["Idrossido di sodio", "Cloruro di sodio (sale da cucina)", "Acido cloridrico", "Ipoclorito di sodio"], 1),

    ("nomenclatura-inorganica",
     "H2SO4 è la formula dell':",
     ["Acido cloridrico", "Acido nitrico", "Acido solforico", "Acido fosforico"], 2),

    ("nomenclatura-inorganica",
     "NaOH è il simbolo di:",
     ["Carbonato di sodio", "Cloruro di sodio", "Idrossido di sodio (soda caustica)", "Solfato di sodio"], 2),

    ("nomenclatura-inorganica",
     "Gli ossidi metallici reagendo con l'acqua formano:",
     ["Acidi", "Sali", "Idrossidi (basi)", "Gas inerti"], 2),

    ("nomenclatura-inorganica",
     "CaCO3 (carbonato di calcio) è il componente principale di:",
     ["Sale da cucina", "Marmo e calcare", "Vetro", "Aceto"], 1),

    ("nomenclatura-inorganica",
     "La formula dell'acido cloridrico è:",
     ["HCl", "H2Cl", "NaCl", "HClO4"], 0),

    # --- CHEMISTRY: chimica-organica ---
    ("chimica-organica",
     "La formula molecolare degli alcani (idrocarburi saturi) è:",
     ["CnH2n", "CnH2n+2", "CnH2n-2", "CnHn"], 1),

    ("chimica-organica",
     "Quale gruppo funzionale caratterizza gli alcoli?",
     ["Gruppo carbonilico (C=O)", "Gruppo carbossilico (-COOH)", "Gruppo ossidrile (-OH)", "Gruppo amminico (-NH2)"], 2),

    ("chimica-organica",
     "Gli isomeri di struttura sono composti che:",
     ["Hanno la stessa formula molecolare ma diversa struttura", "Hanno struttura uguale ma formula molecolare diversa", "Sono immagini speculari non sovrapponibili", "Differiscono solo per il numero di doppi legami"], 0),

    ("chimica-organica",
     "Il gruppo funzionale -COOH è caratteristico degli:",
     ["Aldeidici", "Chetoni", "Acidi carbossilici", "Ammine"], 2),

    ("chimica-organica",
     "Gli alcheni si differenziano dagli alcani per:",
     ["Avere un anello aromatico", "Contenere almeno un doppio legame C=C", "Avere un triplo legame C≡C", "Contenere atomi di ossigeno"], 1),

    ("chimica-organica",
     "Il benzene (C6H6) è il composto aromatico prototipico e si caratterizza per:",
     ["Tre doppi legami alternati con delocalizzazione elettronica", "Tre tripli legami nella struttura ad anello", "Presenza di atomi di azoto nell'anello", "Una catena lineare di 6 atomi di carbonio"], 0),

    # --- PHYSICS: grandezze-fisiche ---
    ("grandezze-fisiche",
     "Quali sono le sette grandezze fisiche fondamentali del Sistema Internazionale (SI)?",
     ["Lunghezza, massa, tempo, temperatura, intensità corrente, quantità di sostanza, intensità luminosa",
      "Lunghezza, peso, volume, densità, velocità, accelerazione, forza",
      "Metro, kilogrammo, secondo, ampere, kelvin, candela, volt",
      "Posizione, velocità, accelerazione, forza, energia, potenza, pressione"], 0),

    ("grandezze-fisiche",
     "L'analisi dimensionale viene utilizzata per:",
     ["Misurare la dimensione degli oggetti fisici", "Verificare la correttezza delle equazioni fisiche controllando le dimensioni dei termini", "Calcolare il volume di un solido geometrico", "Determinare il numero di cifre significative"], 1),

    ("grandezze-fisiche",
     "Quale delle seguenti è una grandezza vettoriale?",
     ["Massa", "Temperatura", "Velocità", "Energia cinetica"], 2),

    ("grandezze-fisiche",
     "La notazione scientifica 6,02 × 10^23 rappresenta il numero di:",
     ["Protoni nel nucleo dell'oro", "Molecole in una mole di sostanza (numero di Avogadro)", "Neutroni nell'uranio-238", "Elettroni nell'elio"], 1),

    ("grandezze-fisiche",
     "Le cifre significative indicano:",
     ["Il numero di decimali di un valore", "La precisione di una misura (quante cifre sono affidabili)", "Il numero di unità di misura usate", "La grandezza dell'ordine di grandezza"], 1),

    ("grandezze-fisiche",
     "L'unità SI della forza è:",
     ["Joule (J)", "Pascal (Pa)", "Newton (N)", "Watt (W)"], 2),

    # --- PHYSICS: cinematica ---
    ("cinematica",
     "La velocità media di un oggetto è definita come:",
     ["La velocità istantanea in un dato momento", "Lo spostamento diviso il tempo impiegato (v = Δs/Δt)", "La distanza percorsa diviso la velocità", "L'accelerazione media nel tempo"], 1),

    ("cinematica",
     "Nella caduta libera (trascurando l'attrito dell'aria), l'accelerazione di un corpo è circa:",
     ["9,8 m/s² diretta verso il basso", "9,8 m/s² diretta verso l'alto", "0 m/s² (peso bilancia resistenza)", "Variabile in base alla massa del corpo"], 0),

    ("cinematica",
     "Per un moto uniformemente accelerato che parte da fermo, la relazione tra spazio e tempo è:",
     ["s = v·t", "s = ½·a·t²", "s = a/t²", "s = v·a·t"], 1),

    ("cinematica",
     "In un grafico spazio-tempo (s-t), la pendenza (slope) della curva rappresenta:",
     ["L'accelerazione", "La velocità", "La forza", "L'energia cinetica"], 1),

    ("cinematica",
     "Un oggetto lanciato orizzontalmente da un'altezza h cade al suolo in un tempo t dipendente da:",
     ["Solo dalla velocità orizzontale iniziale", "Solo dall'altezza h e dall'accelerazione gravitazionale g (t = √(2h/g))", "Dalla massa dell'oggetto", "Dalla forma dell'oggetto"], 1),

    ("cinematica",
     "La formula v = v0 + a·t descrive il moto:",
     ["Circolare uniforme", "Uniformemente accelerato (o decelerato)", "Di un proiettile in caduta libera solo", "Oscillatorio"], 1),

    # --- PHYSICS: dinamica ---
    ("dinamica",
     "La prima legge di Newton (principio di inerzia) afferma che un corpo:",
     ["Si muove sempre in cerchio in assenza di forze", "Rimane in quiete o in moto rettilineo uniforme se la forza netta è zero", "Accelera sempre se è in movimento", "Perde velocità nel tempo per inerzia"], 1),

    ("dinamica",
     "La seconda legge di Newton è espressa come:",
     ["F = m/a", "F = m × a (la forza netta è uguale a massa per accelerazione)", "F = m + a", "F = a/m"], 1),

    ("dinamica",
     "Il peso di un corpo di massa m sulla superficie terrestre è:",
     ["W = m/g", "W = m × g (dove g ≈ 9,8 m/s²)", "W = m + g", "W = g/m"], 1),

    ("dinamica",
     "La terza legge di Newton (azione e reazione) afferma che:",
     ["A ogni azione corrisponde una reazione uguale e contraria applicata allo stesso corpo", "A ogni azione corrisponde una reazione uguale e contraria applicata al corpo diverso", "La forza di attrito è sempre uguale alla forza applicata", "Un corpo in moto ha sempre più forza di uno in quiete"], 1),

    ("dinamica",
     "L'energia cinetica di un corpo di massa m e velocità v è:",
     ["Ek = m × v", "Ek = m × g × h", "Ek = ½ × m × v²", "Ek = m × a × v"], 2),

    ("dinamica",
     "La quantità di moto (momento lineare) p di un corpo è:",
     ["p = m + v", "p = m × v (massa per velocità)", "p = ½ × m × v²", "p = F × t / m"], 1),

    ("dinamica",
     "La legge di conservazione della quantità di moto si applica a sistemi:",
     ["Soggetti a forze esterne intense", "Isolati o su cui non agiscono forze esterne nette", "Solo in moto circolare", "Con velocità superiore a quella del suono"], 1),

    # --- PHYSICS: meccanica-fluidi ---
    ("meccanica-fluidi",
     "La pressione è definita come:",
     ["Forza moltiplicata per area (P = F × A)", "Forza divisa per area (P = F/A)", "Massa divisa per volume", "Forza divisa per massa"], 1),

    ("meccanica-fluidi",
     "Il principio di Pascal afferma che la pressione applicata a un fluido confinato si trasmette:",
     ["Solo verso il basso", "Ugualmente in tutte le direzioni", "Solo verso l'alto", "Solo in direzione orizzontale"], 1),

    ("meccanica-fluidi",
     "Il principio di Archimede stabilisce che la spinta di un fluido su un corpo immerso è uguale a:",
     ["Il peso del corpo", "Il peso del fluido spostato dal corpo", "La pressione del fluido moltiplicata per il volume del corpo", "La densità del corpo moltiplicata per g"], 1),

    ("meccanica-fluidi",
     "Un corpo galleggia in un liquido se:",
     ["La sua densità è maggiore di quella del liquido", "La sua densità è uguale a quella del liquido", "La sua densità è minore di quella del liquido", "Il suo volume è molto piccolo"], 2),

    ("meccanica-fluidi",
     "La pressione idrostatica a una profondità h in un fluido di densità ρ è:",
     ["P = ρ × h", "P = ρ × g × h", "P = g / (ρ × h)", "P = ρ / (g × h)"], 1),

    ("meccanica-fluidi",
     "Il principio di Bernoulli afferma che in un fluido in movimento:",
     ["Dove la velocità è maggiore, la pressione è maggiore", "Dove la velocità è maggiore, la pressione è minore", "La pressione è costante in tutto il fluido", "La velocità è inversamente proporzionale alla densità"], 1),

    # --- PHYSICS: termodinamica ---
    ("termodinamica",
     "La conversione tra la scala Celsius e la scala Kelvin è:",
     ["K = °C + 100", "K = °C × 1,8 + 32", "K = °C + 273,15", "°C = K + 273,15"], 2),

    ("termodinamica",
     "La prima legge della termodinamica afferma che:",
     ["Il calore non può fluire spontaneamente da un corpo freddo a uno caldo", "L'energia interna di un sistema isolato rimane costante (ΔU = Q - W)", "L'entropia dell'universo tende a diminuire", "Nessun processo è al 100% efficiente"], 1),

    ("termodinamica",
     "La legge dei gas ideali è PV = nRT, dove R è:",
     ["La resistenza elettrica del gas", "La costante universale dei gas ideali (8,314 J/mol·K)", "Il rapporto calore/lavoro", "La costante di Boltzmann per un singolo atomo"], 1),

    ("termodinamica",
     "La seconda legge della termodinamica afferma che in qualsiasi processo spontaneo:",
     ["L'energia totale dell'universo aumenta", "L'entropia totale dell'universo tende ad aumentare", "Il calore si conserva sempre", "Il lavoro si converte completamente in calore"], 1),

    ("termodinamica",
     "In un processo adiabatico:",
     ["La temperatura rimane costante", "La pressione rimane costante", "Il volume rimane costante", "Non c'è scambio di calore con l'ambiente (Q = 0)"], 3),

    ("termodinamica",
     "Il calore specifico di una sostanza indica:",
     ["La quantità di calore necessaria per fondere 1 g della sostanza", "La quantità di calore necessaria per aumentare di 1°C la temperatura di 1 kg della sostanza", "La temperatura a cui la sostanza bolle", "Il calore liberato in una combustione"], 1),

    # --- PHYSICS: elettromagnetismo ---
    ("elettromagnetismo",
     "La legge di Coulomb descrive la forza tra due cariche elettriche come:",
     ["Proporzionale alla somma delle cariche e alla distanza", "Proporzionale al prodotto delle cariche e inversamente proporzionale al quadrato della distanza", "Proporzionale alla distanza tra le cariche", "Inversamente proporzionale al prodotto delle cariche"], 1),

    ("elettromagnetismo",
     "La legge di Ohm afferma che:",
     ["V = I/R (la tensione è corrente diviso resistenza)", "I = V/R (la corrente è tensione diviso resistenza)", "R = V × I (la resistenza è tensione per corrente)", "V = I² × R"], 1),

    ("elettromagnetismo",
     "In un circuito con resistenze in serie, la resistenza totale è:",
     ["R_tot = R1 × R2 / (R1 + R2)", "R_tot = R1 + R2 + ... (somma delle resistenze)", "1/R_tot = 1/R1 + 1/R2", "R_tot = minima resistenza del circuito"], 1),

    ("elettromagnetismo",
     "In un circuito con resistenze in parallelo, la resistenza totale è:",
     ["R_tot = R1 + R2 + ...", "R_tot = R1 × R2", "1/R_tot = 1/R1 + 1/R2 + ... (minore della resistenza minima)", "R_tot = media aritmetica delle resistenze"], 2),

    ("elettromagnetismo",
     "La legge di Faraday descrive l'induzione elettromagnetica: una forza elettromotrice (f.e.m.) si induce in un circuito quando:",
     ["La temperatura del conduttore varia", "Il flusso del campo magnetico attraverso il circuito varia nel tempo", "La corrente nel circuito è stazionaria", "La resistenza del circuito cambia"], 1),

    ("elettromagnetismo",
     "Il campo elettrico E in un punto è definito come:",
     ["La forza per unità di massa subita da una carica di prova", "La forza per unità di carica subita da una carica di prova positiva (E = F/q)", "La tensione per unità di corrente", "Il potenziale elettrico moltiplicato per la carica"], 1),

    # --- MATH: algebra-aritmetica ---
    ("algebra-aritmetica",
     "La formula quadratica per risolvere ax² + bx + c = 0 è:",
     ["x = (-b ± √(b² - 4ac)) / 2a", "x = (b ± √(b² - 4ac)) / 2a", "x = (-b ± √(b² + 4ac)) / 2a", "x = -b / 2a"], 0),

    ("algebra-aritmetica",
     "La proprietà dei logaritmi log(a × b) è uguale a:",
     ["log(a) × log(b)", "log(a) + log(b)", "log(a) - log(b)", "log(a) / log(b)"], 1),

    ("algebra-aritmetica",
     "La proprietà dei logaritmi log(aⁿ) è uguale a:",
     ["log(a) + n", "n + log(a)", "n × log(a)", "log(a) / n"], 2),

    ("algebra-aritmetica",
     "Il risultato di (2³)² è:",
     ["2^5 = 32", "2^6 = 64", "2^9 = 512", "4^3 = 64"], 1),

    ("algebra-aritmetica",
     "La soluzione dell'equazione lineare 3x + 6 = 0 è:",
     ["x = 2", "x = -2", "x = 6", "x = -6"], 1),

    ("algebra-aritmetica",
     "3,0 × 10^4 + 2,0 × 10^3 in notazione scientifica è:",
     ["5,0 × 10^7", "3,2 × 10^4", "5,0 × 10^4", "2,3 × 10^4"], 1),

    # --- MATH: funzioni ---
    ("funzioni",
     "Una funzione f è invertibile se e solo se è:",
     ["Solo suriettiva (surgettiva)", "Solo iniettiva", "Biiettiva (sia iniettiva che suriettiva)", "Continua in tutto il dominio"], 2),

    ("funzioni",
     "La funzione lineare y = mx + q ha come parametro m:",
     ["L'intercetta sull'asse y", "Il coefficiente angolare (pendenza) della retta", "Il valore massimo della funzione", "La distanza dall'origine"], 1),

    ("funzioni",
     "Il vertice della parabola y = ax² + bx + c si trova per x =:",
     ["-b / a", "b / 2a", "-b / 2a", "√(b² - 4ac) / 2a"], 2),

    ("funzioni",
     "La funzione esponenziale f(x) = a·bˣ con b > 1 descrive:",
     ["Crescita esponenziale", "Decadimento esponenziale", "Funzione lineare con pendenza b", "Funzione periodica"], 0),

    ("funzioni",
     "Nel cerchio unitario, cos(0°) e sen(0°) valgono rispettivamente:",
     ["0 e 1", "1 e 0", "1 e 1", "0 e 0"], 1),

    ("funzioni",
     "La funzione logaritmica y = log_b(x) è l'inversa della funzione:",
     ["y = bx", "y = x^b", "y = b^x", "y = log_x(b)"], 2),

    # --- MATH: geometria ---
    ("geometria",
     "L'area di un cerchio di raggio r è:",
     ["A = 2πr", "A = πr²", "A = πr", "A = 4πr²"], 1),

    ("geometria",
     "Il teorema di Pitagora afferma che in un triangolo rettangolo:",
     ["a + b = c", "a² + b² = c² (la somma dei quadrati dei cateti è uguale al quadrato dell'ipotenusa)", "a × b = c²", "a² - b² = c²"], 1),

    ("geometria",
     "Il volume di una sfera di raggio r è:",
     ["V = πr³", "V = 2πr³", "V = 4/3 × πr³", "V = 4πr²"], 2),

    ("geometria",
     "Due triangoli sono simili se hanno:",
     ["Stessa area", "Stessi lati", "Angoli corrispondenti uguali (e lati proporzionali)", "Stesso perimetro"], 2),

    ("geometria",
     "La formula per la distanza tra due punti P1(x1,y1) e P2(x2,y2) nel piano cartesiano è:",
     ["d = (x2-x1) + (y2-y1)", "d = |x2-x1| × |y2-y1|", "d = √((x2-x1)² + (y2-y1)²)", "d = (x2+x1)/2"], 2),

    ("geometria",
     "Il volume di un cilindro di raggio r e altezza h è:",
     ["V = 2πrh", "V = πr²h", "V = 2πr²h", "V = πrh²"], 1),

    # --- MATH: probabilita-statistica ---
    ("probabilita-statistica",
     "La probabilità classica di un evento A è definita come:",
     ["Numero di esiti sfavorevoli / numero totale di esiti", "Numero di esiti favorevoli / numero totale di esiti equiprobabili", "Numero di prove / numero di successi", "Complemento della probabilità dell'evento B"], 1),

    ("probabilita-statistica",
     "La probabilità del complementare di un evento A è:",
     ["P(A') = P(A) + 1", "P(A') = 1 - P(A)", "P(A') = P(A) × 2", "P(A') = 1 / P(A)"], 1),

    ("probabilita-statistica",
     "Se A e B sono eventi indipendenti, la probabilità che si verifichino entrambi è:",
     ["P(A∩B) = P(A) + P(B)", "P(A∩B) = P(A) × P(B)", "P(A∩B) = P(A) - P(B)", "P(A∩B) = P(A|B) × P(A)"], 1),

    ("probabilita-statistica",
     "La media aritmetica di un insieme di dati si calcola come:",
     ["Il valore che compare più spesso", "Il valore centrale dell'elenco ordinato", "La somma di tutti i valori divisa per il numero di valori", "La differenza tra il valore massimo e minimo"], 2),

    ("probabilita-statistica",
     "La deviazione standard misura:",
     ["Il valore centrale di un insieme di dati", "La dispersione (variabilità) dei dati attorno alla media", "La probabilità di un evento raro", "Il numero di dati nel campione"], 1),

    ("probabilita-statistica",
     "La distribuzione normale (gaussiana) è caratterizzata da:",
     ["Essere asimmetrica con una coda lunga a destra", "Avere media, mediana e moda tutte diverse", "Essere simmetrica a campana con media = mediana = moda", "Avere valori solo tra 0 e 1"], 2),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    inserted = 0
    skipped = 0
    for topic_slug, question_it, choices, correct_index in QUESTIONS:
        existing = conn.execute(
            "SELECT id FROM quiz_questions WHERE topic_slug=? AND question_it=?",
            (topic_slug, question_it)
        ).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO quiz_questions (topic_slug, question_it, choices_json, correct_index) VALUES (?, ?, ?, ?)",
            (topic_slug, question_it, json.dumps(choices, ensure_ascii=False), correct_index)
        )
        inserted += 1
    conn.commit()
    conn.close()
    print(f"Seeded {inserted} questions, skipped {skipped} existing")


if __name__ == "__main__":
    seed()
