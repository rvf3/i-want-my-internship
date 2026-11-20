import csv
from datetime import date
import json
import os
import ollama

with open("cv_fr.txt", "r", encoding="utf-8") as f:
    cv_fr = f.read()

with open("cv_en.txt", "r", encoding="utf-8") as f:
    cv_en = f.read()

with open("offres.txt", "r", encoding="utf-8") as f:
    offres = [o.strip() for o in f.read().split("---") if o.strip()]

fichier_csv = "suivi_candidatures.csv"
nouveau_fichier = not os.path.exists(fichier_csv)

with open(fichier_csv, "a", newline="", encoding="utf-8-sig") as f_csv, \
     open("candidatures_pretes.md", "w", encoding="utf-8") as f_md:

    writer = csv.writer(f_csv, delimiter=";")
    if nouveau_fichier:
        writer.writerow(["Date", "Langue", "Entreprise", "Poste", "Note /10", "Lien", "Statut", "Justification"])

    for i, offre in enumerate(offres, 1):
        print(f"Analyse de l'offre {i}/{len(offres)}...")
        prompt = (
            "You are a strict recruitment assistant. Analyze the match between my profile and the internship offer.\n"
            "CRITICAL RULES:\n"
            "1. LANGUAGE: Detect the language of the JOB OFFER. If the offer is in English, 'langue' MUST be 'EN', and both 'justification' and 'lettre' MUST be written 100% in English using my ENGLISH CV. If the offer is in French, 'langue' MUST be 'FR', and both MUST be in French using my FRENCH CV.\n"
            "2. HONESTY: Never invent a skill, tool, or experience missing from my CV.\n"
            "3. COVER LETTER STYLE (if note >= 7): Write 3 concise, impactful paragraphs (130-160 words). Avoid clichés like 'Je me permets de postuler'. Highlight concrete achievements from my CV (Python CTI tool at CNRS, CPE Lyon engineering track, Root-Me/TryHackMe) and mention my exact availability (3-month internship from June 5 to August 31, 2027).\n\n"
            f"FRENCH CV:\n{cv_fr}\n\n"
            f"ENGLISH CV:\n{cv_en}\n\n"
            f"JOB OFFER:\n{offre}\n\n"
            "Respond ONLY in valid JSON with these exact keys:\n"
            '- "langue": "FR" or "EN"\n'
            '- "entreprise": company name (or "Non précisé")\n'
            '- "poste": internship title\n'
            '- "lien": URL found in the offer text (or "À ajouter")\n'
            '- "note": integer from 1 to 10\n'
            '- "justification": 2-sentence explanation in the language of the offer\n'
            '- "lettre": cover letter in the language of the offer if note >= 7, otherwise ""'
        )

        reponse = ollama.chat(
            model="qwen2.5",
            messages=[{"role": "user", "content": prompt}],
            format="json",
        )

        data = json.loads(reponse["message"]["content"])

        writer.writerow([
            date.today().strftime("%d/%m/%Y"),
            data.get("langue", ""),
            data.get("entreprise", ""),
            data.get("poste", ""),
            data.get("note", ""),
            data.get("lien", "À ajouter"),
            "À envoyer" if data.get("lettre") else "Écartée",
            data.get("justification", ""),
        ])

        if data.get("lettre"):
            f_md.write(f"## {i}. [{data.get('langue')}] {data.get('poste')} - {data.get('entreprise')} ({data.get('note')}/10)\n\n")
            f_md.write(f"**Lien :** {data.get('lien', 'À ajouter')}\n\n")
            f_md.write(f"**Analyse :** {data.get('justification')}\n\n")
            f_md.write(f"{data.get('lettre')}\n\n---\n\n")

print("Terminé.")
