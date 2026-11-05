import cv2 
import base64
from openai import OpenAI
import os
import sqlite3
from datetime import datetime
import json
from dotenv import load_dotenv
import shutil
import requests

load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("api key needed")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
base_path = os.path.dirname(os.path.abspath(__file__)) # c:\Users\nelio\Documents\VScode\+\SOCIAL_BOT
root = os.path.join(base_path, "CLIENTS") # c:\Users\nelio\Documents\VScode\+\SOCIAL_BOT\CLIENTS
langue = 'francais' # anglais / francais / à definir comme option

def prendre_5_images(path:str):
    vid = cv2.VideoCapture(path)
    liste_frames = []
    total_frames = vid.get(cv2.CAP_PROP_FRAME_COUNT)

    cursor = 2 # dangerous
    intervalle = total_frames // 6

    
    for _ in range (5):
        vid.set(cv2.CAP_PROP_POS_FRAMES, cursor)
        cursor+=intervalle
        ret, frame = vid.read()

        if ret :
            ret2, frame_encode = cv2.imencode('.jpg', frame) # tab[bytes] type:numpy.ndarray (JPEG)
            if not ret2 : print('encode issue'), quit()
            else : 
                encoded = base64.b64encode(frame_encode).decode('utf-8') 
                liste_frames.append(encoded)
        else :
            print('video read issue')
            quit()
    
    vid.release()
    return liste_frames
    
    
#print(prendre_5_images(path))

def demander_a_gpt(liste_images:list):
    """
    faire une consigne globale
    mettre un parametre avancé dans le logiciel :
    préférence de contenu : (user rentre ce sur quoi il travaillera souvent pour avoir un gpt plus accurate sur les descriptions)
    risque : si il change de contenu entre deux videos et que gpt se fie plus au prompt quaux images, on aura une description erronée 
    solution : faire un prompt spécial si cette option est activée et qu'un champ est entré de plus de 10 caracteres, qui dit :
    'voici une précision de l'auteur de cette vidéo, elle peut correspondre au contenu de celle-ci. Si oui aides en toi, sinon n'en prends pas compte'
    """

    #(prompt fait par ia)
    prompt = f""" 
Analyse ces images extraites d'une vidéo.

Ta réponse doit être STRICTEMENT un JSON valide, sans aucun texte avant ou après.

Format attendu :
{{
  "titre": "...",
  "description": "...",
  "hashtags": ["...", "..."]
}}

Contraintes :

- Titre court et accrocheur (max 12 mots)

- Description : 1 seule phrase maximum
- Style TikTok : réaction naturelle, spontanée, comme un joueur qui commente en direct
- Doit décrire précisément un moment visible de la vidéo (action, réaction, événement)
- Priorité à l’émotion brute (surprise, drôle, rage, WTF…)
- Phrases très courtes, langage oral autorisé (style réaction)
- Évite absolument les formulations génériques ou “marketing”
- Si possible, fais référence à un détail précis (moment, action, erreur, retournement)
- Interdiction d’utiliser des formulations de type "Regarde", "Découvrez", "Plongez", ou toute phrase adressée à un spectateur
- La description doit être une réaction directe, comme si la personne parlait à chaud

- 3 à 6 hashtags pertinents (sans #)

- Langue : {langue}

Important :
- Aucun commentaire
- Aucun texte hors JSON
- JSON strictement valide
"""
    
    contenu = [
        {
        "type" : "text", 
        "text" : prompt
        }
    ]
    
    for frame in liste_images : 
        contenu.append({
            "type": "image_url",
            "image_url": {"url" : f"data:image/jpeg;base64,{frame}"}
        })


    try :
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                    {
                        "role": "user",
                        "content": contenu
                    }
                ],
                response_format={"type": "json_object"},
        )

        reponse =  response.choices[0].message.content
        data = json.loads(reponse)

        return (True, data)

    except Exception as e:
        print(f"gpt error : {e}")
        return (False, str(e))


def configure_file(nom:str):
    path = os.path.join(root, nom)
    #os.path.join(path, /, *paths) :  '/' included
    sub_folder_input = os.path.join(path, "videos_input")
    sub_folder_done = os.path.join(path, "videos_done")

    try:
        '''
        quoting : Par défaut, si le dossier final (celui à la droite du chemin) existe déjà, 
        la fonction makedirs produira une erreur. 
        Il est cependant possible de changer ce comportement en fixant le paramètre exist_ok à True : 
        dans ce cas aucune erreur ne sera produite.
        source : https://koor.fr/Python/API/python/os/makedirs.wp

        conclusion : si le dossier existe déjà, le code continue 
        en contre partie : on a pas de gestion de 'path already exist'
        '''
        os.makedirs(path, exist_ok=True)
        os.makedirs(sub_folder_input, exist_ok=True) 
        os.makedirs(sub_folder_done, exist_ok=True)
        return True
    except OSError as e :
        return f"Impossible de créer les dossiers manquants ! error : {e}"


#print (configure_file("nuage"))

def get_vid(nom:str): 
    sub_folder_input = os.path.join(root, nom, "videos_input")
    videos = []
    for video in os.listdir(sub_folder_input):
        if video.endswith(".mp4") :
            video_path = os.path.join(sub_folder_input, video)
            try : 
                '''
                os.path.getmtime(path, /)

                Return the time of last modification of path. 
                The return value is a floating-point number giving the number of seconds since the epoch 
                    (ex: 1754407669.337401 représente le 05/08/2025 à 17:27)
                    (The epoch is the point where the time starts, the return value of time.gmtime(0) is 
                        January 1, 1970, 00:00:00 (UTC) on all platforms.)
                (see the time module). Raise OSError if the file does not exist or is inaccessible.
                
                https://docs.python.org/3/library/os.path.html#os.path.getctime
                '''
                epoch = os.path.getmtime(video_path)
                videos.append((epoch, video_path))
            except OSError as e :
                return f"Impossible d'accéder aux fichiers demandées ! error : {e}"
    videos.sort() #par défaut le premier elt du tuple
    return [item[1] for item in videos]


#print(get_vid("client_test"))

def init_db(nom:str):
    try:
        con = sqlite3.connect(os.path.join(root, nom, "conf.db"))
    except sqlite3.OperationalError as e :
        return f"Impossible de créer le fichier de configuration ! \n Essayez de vérifier les dossiers de profils. error : {e}" 
        # option de recover à activer plus tard

    cur = con.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS historique(id INTEGER PRIMARY KEY AUTOINCREMENT, nom_video TEXT, date_post TEXT, titre TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS config(jours_post TEXT, heure_post TEXT, prompt TEXT, titre TEXT, to_use BOOL)")


    #ici on demandera a l'utilisateur ses parametres avec une interface ( cases cocher pour prompts et mini calendrier pour jours / h )
    #jours, horaires = list(input("entrez la planificartion souhaitée.. JOURS / 'Lu', 'Ma', 'Me', 'Je', 'Ve', 'Sa', 'Di' ")),
    #list(input("entrez la planificartion souhaitée.. HEURES / '8', '9', '16', '20'"))

    #default 
    # on part du principe quon crée une table avec lundi : rowid = 1 etc avec tous les jours de la semaine
    # on a plus qua ajouter les horaires pour chaque jour individuellement selon l'user (dict)
    # et on rajoute a la table un attribut 'use_day' bool, qui indique si on prend en compte ce jour 

    horaires = {
        'monday' : 8,
        'tuesday' : 16,
        'wednesday' : 8,
        'thursday' : 12,
        'friday': 16,
        'saturday' : 8,
        'sunday' : 16
    }

    vide = cur.execute("SELECT * FROM config")
    vide = bool(vide.fetchone())
    if not vide:
        for jour, heures in horaires.items():
            cur.execute("INSERT INTO config VALUES(?, ?, ?, ?, ?)", (jour, heures, 'prompt', 'titre', True))
            con.commit()
            print("did")
    con.close()
    return True


#print(init_db("nuage"))

def get_config(nom:str):
    try:
        con = sqlite3.connect(os.path.join(root, nom, "conf.db"))
    except sqlite3.OperationalError as e :
        return f"Impossible de rentrer dans votre base ! \n Essayez de vérifier les dossiers de config. error : {e}" 
    
    cur = con.cursor()

    #heures
    today = datetime.now().strftime('%A').lower()
    cur.execute("SELECT * FROM config WHERE jours_post = ?", (today,)) # tuple
    infos = cur.fetchone()
    dico = {}
    tags = ['jour', 'heures', 'prompt', 'titre', 'use']
    for idx in range(len(infos)) :
        dico[tags[idx]] = infos[idx]
    print(dico)
    return dico
      

#print(get_config("nuage"))

def run_bot(nom:str):
    #===== tests =============================================================================

    if not os.path.exists(root) :
        setup_client(nom)
        if not os.path.exists(root) : 
            return 'go get a config'

    try:
        con = sqlite3.connect(os.path.join(root, nom, "conf.db"))
    except sqlite3.OperationalError as e :
        return f"Impossible de rentrer dans votre base ! \n Essayez de vérifier les dossiers de config. error : {e}"
    
    cur = con.cursor()     
    dico = get_config(nom)
    heure = datetime.now().hour
    if int(dico['heures']) != heure : 
        return 'not rn'
    clock=datetime.strptime(str(datetime.now()),
                     '%Y-%m-%d %H:%M:%S.%f')
    now = (clock.strftime('%d/%m/%Y %H:')) 

    #{'jour': 'thursday', 'heures': '12', 'prompt': 'prompt', 'titre': 'titre', 'use': 1}
    cur.execute("SELECT * FROM historique WHERE date_post LIKE ?", (f"{now}%",))
    if bool(cur.fetchone()) :
        return 'already posted'
    
    #===========================================================================================

    clock=datetime.strptime(str(datetime.now()), '%Y-%m-%d %H:%M:%S.%f')
    liste_videos = get_vid(nom) 
    for video in liste_videos : # video -> path : ['c:(...)\\CLIENTS\\client_test\\videos_input\\VALORANT__2025-08-05__01-54-23_trim.mp4']
        cur.execute("SELECT * FROM historique WHERE nom_video = ?", (video,))
        if bool(cur.fetchone()) :
            continue
        liste_frames = prendre_5_images(video)
        success, data = demander_a_gpt(liste_frames) # une fois dans cette fonction, on envoie tout a gpt puis le resultat est envoyé a docker (n8n), pas encore config(ni la fonction ni le docker)
        if success :
            if success:    
                #pas besoin de préciser l'id, voir help.txt
                cur.execute("INSERT INTO historique (nom_video, date_post, titre) VALUES (?, ?, ?)", 
                            (video, clock.strftime('%d/%m/%Y %H:%M'), data["titre"]))
                con.commit()
                destination = os.path.join(root, nom, "videos_done", os.path.basename(video))
                shutil.move(video, destination)
                upload_short(destination, data)
    #PRPOBLEME DE LOGIQUE : si on fait plusieurs videos a la meme heure cette fonction ne fera la premiere 
    # de la liste : il faudra lancer en permanent run_bot tan t quil ne reste
    # aucune video a faire pour le mooment, soit le bot entier (infini / 30 min) 
    

def setup_client(nom:str):
    setup = {
        "folders" : False,
        "database" : False, 
        "config_loaded" : False
    }
    ret = configure_file(nom)
    if ret :
        setup["folders"] = True
        ret2 = init_db(nom)
        if ret2 : 
            setup["database"] = True
            setup["config_loaded"] = True
        else : 
            print('data manager installation unable to process')
    else : 
        print('file config unable to process')

    return setup


def scan_folders():
    for name in os.listdir(root) : 
        run_bot(name)


def upload_short(pathVideo, data):
    path = pathVideo.rsplit('.', 1)[0]+"_infos.txt"
    with open(path, 'w', encoding="utf-8") as f:
        f.write(f"TITRE : {data['titre']}\n\n")
        f.write(f"DESCRIPTION : {data['description']}\n\n")
        f.write(f"HASHTAGS : {' '.join(data['hashtags'])}\n")
        
    print(f"Fiche de livraison créée : {path}")

'''
if __name__ == "__main__":
    nom_test = "nuage"
    print(f"test start for {nom_test}")
    setup_client(nom_test)
    resultat = run_bot(nom_test)
    print(f"resultat : {resultat}")
'''