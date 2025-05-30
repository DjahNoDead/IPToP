from flask import Flask, render_template, request, redirect, url_for, session, flash
import subprocess
import os

app = Flask(__name__)
app.secret_key = 'votre_clef_secrete_a_modifier'

# Utilisateur par défaut
USERNAME = "admin"
PASSWORD = "admin123"

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))

@app.route('/status')
def status():
    output = subprocess.getoutput("systemctl status xray | head -n 10")
    return render_template('status.html', status=output)

@app.route('/add-user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        protocole = request.form['protocole']
        subprocess.call(["bash", "xray/commands.sh", "add_user", protocole])
        flash("Utilisateur ajouté avec succès.")
    return render_template('add_user.html')

@app.route('/remove-user', methods=['GET', 'POST'])
def remove_user():
    if request.method == 'POST':
        protocole = request.form['protocole']
        subprocess.call(["bash", "xray/commands.sh", "remove_user", protocole])
        flash("Utilisateur supprimé.")
    return render_template('remove_user.html')

@app.route('/generate')
def generate():
    subprocess.call(["bash", "xray/commands.sh", "generate_links"])
    with open("config_clients.txt", "r") as f:
        liens = f.read()
    return render_template('generate.html', liens=liens)

@app.route('/restart')
def restart():
    subprocess.call(["systemctl", "restart", "xray"])
    flash("Xray redémarré avec succès.")
    return redirect(url_for('home'))

@app.route('/domain', methods=['GET', 'POST'])
def domain():
    if request.method == 'POST':
        domaine = request.form['domaine']
        subprocess.call(["bash", "xray/commands.sh", "change_domain", domaine])
        flash("Domaine changé avec succès.")
    return render_template('domain.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Connexion - Panneau Xray</title>
</head>
<body>
    <h2>Connexion</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
          {% for message in messages %}
            <li style="color:red">{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="post">
        <label>Nom d'utilisateur :</label><br>
        <input type="text" name="username"><br><br>
        <label>Mot de passe :</label><br>
        <input type="password" name="password"><br><br>
        <input type="submit" value="Se connecter">
    </form>
</body>
</html>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Panneau Xray</title>
</head>
<body>
    <h1>🎛️ Panneau de gestion Xray</h1>
    <p>Bienvenue, {{ session['logged_in'] and 'admin' or '' }} !</p>

    <ul>
        <li><a href="{{ url_for('status') }}">🔍 Voir le statut de Xray</a></li>
        <li><a href="{{ url_for('add_user') }}">➕ Ajouter un utilisateur</a></li>
        <li><a href="{{ url_for('remove_user') }}">❌ Supprimer un utilisateur</a></li>
        <li><a href="{{ url_for('generate') }}">🔗 Générer les liens de configuration</a></li>
        <li><a href="{{ url_for('domain') }}">🌐 Changer de domaine</a></li>
        <li><a href="{{ url_for('restart') }}">🔄 Redémarrer Xray</a></li>
        <li><a href="{{ url_for('logout') }}">🚪 Déconnexion</a></li>
    </ul>
</body>
</html>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Statut du service Xray</title>
</head>
<body>
    <h2>📊 Statut de Xray</h2>
    <pre>{{ status }}</pre>
    <a href="/">⬅ Retour</a>
</body>
</html>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Ajouter un utilisateur</title>
</head>
<body>
    <h2>➕ Ajouter un utilisateur</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
          {% for message in messages %}
            <li style="color:green">{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="post">
        <label for="protocole">Protocole :</label><br>
        <select name="protocole" id="protocole">
            <option value="vless">VLESS</option>
            <option value="trojan">Trojan</option>
            <option value="vmess">VMess</option>
        </select><br><br>
        <input type="submit" value="Ajouter">
    </form>
    <a href="/">⬅ Retour</a>
</body>
</html>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Supprimer un utilisateur</title>
</head>
<body>
    <h2>❌ Supprimer un utilisateur</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
          {% for message in messages %}
            <li style="color:green">{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="post">
        <label for="protocole">Protocole :</label><br>
        <select name="protocole" id="protocole">
            <option value="vless">VLESS</option>
            <option value="trojan">Trojan</option>
            <option value="vmess">VMess</option>
        </select><br><br>
        <input type="submit" value="Supprimer">
    </form>
    <a href="/">⬅ Retour</a>
</body>
</html>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Liens de configuration</title>
</head>
<body>
    <h2>🔗 Liens de configuration générés</h2>
    <pre>{{ liens }}</pre>
    <a href="/">⬅ Retour</a>
</body>
</html>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Changer le domaine</title>
</head>
<body>
    <h2>🌐 Changer le domaine fronted</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
          {% for message in messages %}
            <li style="color:green">{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="post">
        <label for="domaine">Nouveau domaine :</label><br>
        <input type="text" name="domaine" id="domaine"><br><br>
        <input type="submit" value="Mettre à jour">
    </form>
    <a href="/">⬅ Retour</a>
</body>
</html>

#!/bin/bash

CONFIG_PATH="/etc/xray/config.json"
CLIENTS_PATH="/etc/xray/clients"
OUTPUT_LINKS="config_clients.txt"

function add_user() {
    protocole=$1
    uuid=$(cat /proc/sys/kernel/random/uuid)
    echo "Ajout d'un utilisateur pour le protocole $protocole avec UUID $uuid"

    case $protocole in
        vless)
            jq --arg uuid "$uuid" '.inbounds[0].settings.clients += [{"id": $uuid,"flow":"xtls-rprx-direct","level":0,"email":"user-'$uuid'"}]' $CONFIG_PATH > tmp.json && mv tmp.json $CONFIG_PATH
            ;;
        trojan)
            jq --arg uuid "$uuid" '.inbounds[1].settings.clients += [{"password": $uuid,"email":"user-'$uuid'"}]' $CONFIG_PATH > tmp.json && mv tmp.json $CONFIG_PATH
            ;;
        vmess)
            jq --arg uuid "$uuid" '.inbounds[2].settings.clients += [{"id": $uuid,"alterId":0,"email":"user-'$uuid'"}]' $CONFIG_PATH > tmp.json && mv tmp.json $CONFIG_PATH
            ;;
        *)
            echo "Protocole inconnu"
            exit 1
            ;;
    esac

    systemctl restart xray
    echo "Utilisateur ajouté."
}

function remove_user() {
    protocole=$1
    echo "Liste des utilisateurs pour $protocole :"
    case $protocole in
        vless)
            jq -r '.inbounds[0].settings.clients[].email' $CONFIG_PATH
            ;;
        trojan)
            jq -r '.inbounds[1].settings.clients[].email' $CONFIG_PATH
            ;;
        vmess)
            jq -r '.inbounds[2].settings.clients[].email' $CONFIG_PATH
            ;;
        *)
            echo "Protocole inconnu"
            exit 1
            ;;
    esac

    read -p "Entrez l'email de l'utilisateur à supprimer : " email

    case $protocole in
        vless)
            jq --arg email "$email" '.inbounds[0].settings.clients |= map(select(.email != $email))' $CONFIG_PATH > tmp.json && mv tmp.json $CONFIG_PATH
            ;;
        trojan)
            jq --arg email "$email" '.inbounds[1].settings.clients |= map(select(.email != $email))' $CONFIG_PATH > tmp.json && mv tmp.json $CONFIG_PATH
            ;;
        vmess)
            jq --arg email "$email" '.inbounds[2].settings.clients |= map(select(.email != $email))' $CONFIG_PATH > tmp.json && mv tmp.json $CONFIG_PATH
            ;;
    esac

    systemctl restart xray
    echo "Utilisateur supprimé."
}

function generate_links() {
    echo "Génération des liens de configuration..."

    > $OUTPUT_LINKS
    # Exemples basiques : il faut adapter selon la config exacte et protocole.
    # Ici on extrait les UUID et construit un lien VLESS en mode wsh.

    vless_clients=$(jq -c '.inbounds[0].settings.clients[]' $CONFIG_PATH)
    for client in $vless_clients; do
        id=$(echo $client | jq -r '.id')
        email=$(echo $client | jq -r '.email')
        link="vless://${id}@votre.domaine.com:443?type=ws&security=tls&host=votre.domaine.com&path=/wsh#$email"
        echo $link >> $OUTPUT_LINKS
    done

    trojan_clients=$(jq -c '.inbounds[1].settings.clients[]' $CONFIG_PATH)
    for client in $trojan_clients; do
        password=$(echo $client | jq -r '.password')
        email=$(echo $client | jq -r '.email')
        link="trojan://${password}@votre.domaine.com:443?security=tls&host=votre.domaine.com&path=/wsh#$email"
        echo $link >> $OUTPUT_LINKS
    done

    vmess_clients=$(jq -c '.inbounds[2].settings.clients[]' $CONFIG_PATH)
    for client in $vmess_clients; do
        id=$(echo $client | jq -r '.id')
        email=$(echo $client | jq -r '.email')
        # Format VMess base64 (simplifié)
        config="{\"v\":\"2\",\"ps\":\"$email\",\"add\":\"votre.domaine.com\",\"port\":\"443\",\"id\":\"$id\",\"aid\":\"0\",\"net\":\"ws\",\"type\":\"none\",\"host\":\"votre.domaine.com\",\"path\":\"/wsh\",\"tls\":\"tls\"}"
        link="vmess://$(echo -n $config | base64 -w 0)"
        echo $link >> $OUTPUT_LINKS
    done

    echo "Liens générés dans $OUTPUT_LINKS"
}

function change_domain() {
    new_domain=$1
    echo "Mise à jour du domaine fronted vers $new_domain"
    jq --arg domain "$new_domain" '.inbounds[].streamSettings.wsSettings.headers.Host = $domain' $CONFIG_PATH > tmp.json && mv tmp.json $CONFIG_PATH
    systemctl restart xray
    echo "Domaine mis à jour et service redémarré."
}

case $1 in
    add_user)
        add_user $2
        ;;
    remove_user)
        remove_user $2
        ;;
    generate_links)
        generate_links
        ;;
    change_domain)
        change_domain $2
        ;;
    *)
        echo "Usage: $0 {add_user|remove_user|generate_links|change_domain} [args]"
        ;;
esac