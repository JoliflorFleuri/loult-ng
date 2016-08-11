La partie client est en HTML/CSS/JS statique et la partie serveur en Python.

# Mise en place

* Installer nginx, python3-autobahn, mbrola (avec voix fr+es+us), espeak
* Créer un fichier `salt.py` contenant `SALT = 'valeur arbitraire'`
* Configurer nginx avec `nginx.conf`, adapter le chemin de $static
* Lancer `poke.py`

D'après une œuvre de *@DrEmixam*.
