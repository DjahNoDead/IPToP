#!/bin/bash

print_menu() {
    echo "🛡️  Gestionnaire Admin ARIEL.COM"
    echo "1️⃣  📊 Voir les logs de l'application"
    echo "2️⃣  🔄 Redémarrer l'application" 
    echo "3️⃣  🛑 Arrêter l'application"
    echo "4️⃣  🚀 Démarrer l'application"
    echo "5️⃣  📈 Statut de l'application"
    echo "6️⃣  🔐 Changer le mot de passe admin"
    echo "7️⃣  💾 Sauvegarder la base de données"
    echo "8️⃣  🗑️  Désinstaller l'application"
    echo "0️⃣  ❌ Quitter"
}

case $1 in
    1) sudo -u ariel pm2 logs ariel-admin ;;
    2) sudo -u ariel pm2 restart ariel-admin ;;
    3) sudo -u ariel pm2 stop ariel-admin ;;
    4) sudo -u ariel pm2 start ariel-admin ;;
    5) sudo -u ariel pm2 status ariel-admin ;;
    6) echo "Fonctionnalité à implémenter" ;;
    7) sudo -u ariel cp /home/ariel/ariel-admin.db /home/ariel/backup-$(date +%Y%m%d).db ;;
    8) echo "Désinstallation..." ;;
    *) print_menu && read choice && bash $0 $choice ;;
esac
