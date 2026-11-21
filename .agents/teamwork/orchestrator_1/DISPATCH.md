# DISPATCH LOG

## 2026-11-04T09:58:18Z
Sviluppare uno strumento che estragga e verifichi tutte le alternative reali per la settimana a Genova e provincia per un'uscita informale moderna, consentendo all'utente di visualizzare l'elenco completo, spuntare le opzioni di proprio interesse e generare il messaggio WhatsApp finale pronto all'invio. Le proposte devono riguardare attività concrete e verificate (es. cinema d'essai, mostre, lezioni di prova, laboratori, biblioteche o passeggiate) senza essere esplicitamente etichettate come "date".

Working directory: /Users/dany/genova
Integrity mode: development

## Requirements
### R1. Script di estrazione e catalogo completo delle alternative
Creare uno script che estragga l'elenco completo delle alternative disponibili per la settimana combinando i dataset locali nel workspace (/Users/dany/genova) con verifiche o ricerche web live per eventi, mostre e orari effettivi a Genova e provincia, riportando per ciascuna voce luogo, giorno, orario e fonte verificabile.

### R2. Selezione interattiva delle alternative ("spunta")
Offrire all'utente la possibilità di visionare l'elenco completo delle alternative della settimana e spuntare (tramite selezione interattiva da terminale o interfaccia leggera con checkbox/elenchi numerati selezionabili) quelle di proprio interesse da includere nel messaggio.

### R3. Output del messaggio WhatsApp
Generare il testo del messaggio contenente le sole alternative spuntate, formattato specificamente per WhatsApp (spaziatura, grassetti, emoji sobrie), pronto per il copia-incolla.

### R4. Stile di scrittura e tono (/plain-writing)
Il testo del messaggio deve seguire lo stile plain writing: scrittura naturale, diretta e informale, senza trattini lunghi (— o –), senza termini promozionali o buzzword, e senza riferimenti espliciti a "date" o appuntamenti romantici.

### R5. Accuratezza e verificabilità delle fonti
Tutti i luoghi, gli orari, le mostre o gli eventi censiti devono essere reali e attivi durante la settimana corrente, supportati da fonti verificabili (URL ufficiale, sito del locale/ente, o riscontro accertato nei dataset/web).

## Acceptance Criteria
### Funzionalità dello Strumento e Flusso Utente
- [ ] Lo strumento estrae ed elenca tutte le alternative verificate disponibili per la settimana su Genova e provincia.
- [ ] L'utente può visualizzare l'elenco completo e spuntare/selezionare le alternative desiderate prima della generazione.
- [ ] Lo strumento produce il testo finale del messaggio WhatsApp formattato con le sole opzioni spuntate, pronto per il copia-incolla.

### Veridicità e Accuratezza dei Dati
- [ ] Tutte le alternative proposte corrispondono a luoghi reali di Genova o provincia effettivamente aperti e con programmazione o orari attivi nella settimana corrente.
- [ ] Ciascuna alternativa include luogo, giorno/fascia oraria e una fonte verificabile (URL o riscontro ufficiale) documentata nell'output o nei log di verifica.
- [ ] Nel testo e nei dati generati non sono presenti dati fittizi, placeholder o allucinazioni.

### Conformità Stilistica
- [ ] Il messaggio per WhatsApp non contiene la parola "date" o espressioni esplicite di appuntamento galante.
- [ ] Il testo rispetta il vincolo di plain writing: assenza di trattini lunghi (— o –) e assenza di formule promozionali o enfatiche.
