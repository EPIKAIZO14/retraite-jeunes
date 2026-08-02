import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from supabase import create_client, Client
from io import StringIO
import csv

app = Flask(__name__)
app.secret_key = 'retraite_jeunes_cle_sec్రete'
MOT_DE_PASSE_ADMIN = "1234"

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


# ---------------------------------------------------------
# ROUTES PUBLIQUES
# ---------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ajouter', methods=['POST'])
def ajouter():
    try:
        supabase.table("jeunes").insert({
            "nom": request.form.get('nom'),
            "postnom": request.form.get('postnom'),
            "prenom": request.form.get('prenom'),
            "genre": request.form.get('genre'),
            "telephone": request.form.get('telephone'),
            "adresse": request.form.get('adresse')
        }).execute()
        flash("Enregistrement effectué avec succès ! Pense à finaliser les frais.", "success")
        return redirect(url_for('guide'))
    except Exception as e:
        flash(f"Erreur : {e}", "danger")
        return redirect(url_for('index'))

# ---------------------------------------------------------
# ROUTES ADMINISTRATION & AUTHENTIFICATION
# ---------------------------------------------------------

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        mdp_saisi = request.form.get('password')
        if mdp_saisi == MOT_DE_PASSE_ADMIN:
            session['connecte'] = True
            return redirect(url_for('liste'))
        else:
            flash("Mot de passe incorrect !", "danger")

    return render_template('admin.html')


@app.route('/logout')
def logout():
    session.pop('connecte', None)
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for('admin'))

@app.route('/guide')
def guide():
    return render_template('guide.html')


# ---------------------------------------------------------
# ROUTES PROTÉGÉES (GESTION & EXPORT)
# ---------------------------------------------------------
@app.route('/liste')
def liste():
    if not session.get('connecte'):
        return "Accès refusé ! Vous n'avez pas l'autorisation.", 403

    response = supabase.table("jeunes").select("*").execute()
    enregistrements = response.data
    return render_template('liste.html', jeunes=enregistrements)
 
@app.route('/exporter_excel')
def exporter_excel():
    if not session.get('connecte'):
        return "Accès refusé !", 403
        response =supabase.table("jeunes").select("*").execute()
         enregistrements = response.data

    si = StringIO()
    cw = csv.writer(si, delimiter=';')
    cw.writerow(['ID', 'Nom', 'Post-nom', 'Prénom', 'Genre', 'Téléphone', 'Adresse'])

    for j in enregistrements:
        cw.writerow([j['id'], j['nom'], j['postnom'], j['prenom'], j['genre'], j['telephone'], j['adresse']])

    output = si.getvalue()
    return Response(
        "\ufeff" + output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=Liste_Jeunes_Retraite.csv"}
    )


@app.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    if not session.get('connecte'):
        return "Accès refusé !", 403

   if request.method == 'POST':
        supabase.table("jeunes").update({
            "nom": request.form.get('nom'),
            "postnom": request.form.get('postnom'),
            "prenom": request.form.get('prenom'),
            "genre": request.form.get('genre'),
            "telephone": request.form.get('telephone'),
            "adresse": request.form.get('adresse')
        }).eq("id", id).execute()
        
        flash("Informations modifiées avec succès !", "success")
        return redirect(url_for('liste'))

           response = supabase.table("jeunes").select("*").eq("id", id).execute()
    jeune = response.data[0] if response.data else None
    return render_template('modifier.html', jeune=jeune)

@app.route('/supprimer/<int:id>', methods=['POST'])
def supprimer(id):
    if not session.get('connecte'):
        return "Accès refusé !", 403

   supabase.table("jeunes").delete().eq("id", id).execute()

    flash("Inscrit supprimé avec succès !", "success")
    return redirect(url_for('liste'))


@app.route('/image.png')
def servir_logo():
    return send_from_directory('.', 'image.png')


if __name__ == '__main__':
    app.run(debug=True)