# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 11:30:57 2017
@author: Zazou
"""
import pyqtgraph as pg
import sys
import pyaudio
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import numpy as np
from threading import Thread
import os
from os import mkdir

taux = 44100 #Hz (Sampling Rate)

#listes définies en global mais qui peuvent passer dans la classe Interface

liste_notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
touches = ['w','s','x','d','c','v','g','b','h','n','j','k']
R = {}
for i,clef in enumerate(('w','s','x','d','c','v','g','b','h','n','j','k')):
    R[clef] = 261.63*2**(i/12.)


########## TIMBRE ##########    
repertoire_timbres = {}
taille_std, fondamental_std = 10000,1000 # Valeurs standard arbitraires
class Timbre:
    """
    Produit un tableau de longueur taille_std, avec le fondamental en fondamental_std-ième position.
    """
    def __init__(self,parametre=0.01):
        if type(parametre) is list:
            self.array = np.zeros(taille_std)
            for i,amplitude in enumerate(parametre):
                self.array[fondamental_std*(i+2)/(i+1)] += amplitude
        # Pour créer un timbre gaussien :
        elif type(parametre) is float or int:
            self.array = np.exp(-(np.arange(taille_std)-fondamental_std)**2/(2*parametre**2))
        # Pour créer un timbre tout simple :
        elif not parametre:
            self.array = np.zeros(taille_std)
            self.array[fondamental_std-1] = 1
        # Pour identifier le timbre à un timbre pré-enregistré :
        elif repertoire_timbres.has_key(parametre):
            self.array = repertoire_timbres[parametre]
        # Pour créer un timbre à partir de l'enregistrement sonore d'une note :
        elif type(parametre) is str: 
            SR, extrait_sonore = scipy.io.wavfile.read(parametre+'.wav')  
            spectre_extrait = np.fft.rfft(extrait_sonore[:,0])
            if np.argmax(spectre_extrait)<fondamental_std:
                self.array = np.concatenate((np.zeros(fondamental_std-np.argmax(np.abs(spectre_extrait))),spectre_extrait[:taille_std-fondamental_std+np.argmax(spectre_extrait)]))
            else:
                self.array = spectre_extrait[:taille_std]
        else:
            print """Veuillez entrer un paramètre : 
                clé du répertoire de timbres, ou nom d'un extrait sonore,
                ou largeur d'une gaussienne, ou liste d'harmoniques, ou aucun paramètre."""
            
    def filtre(self,type_filtre,frequence_coupure,largeur=200):
        if type_filtre is 'passe-bas':
            sens = -1
        elif type_filtre is 'passe-haut':
            sens = 1
        elif type_filtre is 'aucun':
            return self
        self.array *= profil_filtre(frequence_coupure,largeur,taille_std)[::sens]
        return self
        
        
########## REVERB ##########  
class Reverb:
    """
    Produit un tableau de longueur taux contenant la TF de l'Impulse Response demandée.
    """
    def __init__(self,IRname):
        if IRname is False:
            self.array = np.ones(taux)
        else:
            SR, impulse_response = scipy.io.wavfile.read(IRname+'.wav')
            self.array = ajuste(np.real(np.fft.rfft(impulse_response)),taux,1)
            
            
########## ENVELOPPE ##########
class Enveloppe:
    """
    Produit un tableau de longueur taille_std formant l'enveloppe voulue.
    """
    def __init__(self,profil):
        if profil=='sinusoidale':
            self.array = np.sin(np.pi*np.linspace(0,1,taille_std))
        elif profil=='lineaire':
            self.array = np.concatenate((np.linspace(0,1,taille_std//2),1-np.linspace(0,1,taille_std-taille_std//2)))
#        elif profil=='piano':
#            self.array = 
        
        
########## SON ##########
class Son:
    """
    Possède comme attributs les caractéristiques du son voulu.
    self.signal est le tableau numérique correspondant au son final.
    """  
    def __init__(self, hauteur, timbre, enveloppe, reverb=False, vibrato=False, duree=3, debut=0):
        # Attributs constants        
        self.debut = debut*taux # Seulement en mode partition
        self.duree = duree*taux
        self.volume = 0.2
        # Timbre
        self.timbre = timbre.array
        # Enveloppe    
        self.enveloppe = ajuste(enveloppe.array,duree*taux)
        # Création du spectre
        self.spectre = ajuste(np.real(self.timbre[fondamental_std - np.floor(R[hauteur]):]),(duree*taux)//2+1,duree)
        if reverb is not False:
            self.spectre *= ajuste(reverb.array,(duree*taux)//2+1,duree)
        # Création du signal
        self.signal = np.fft.irfft(self.spectre)*self.enveloppe*self.vibrato(vibrato)
        self.signal *= self.volume/np.max(self.signal)
                
    def vibrato(self,vibrato):
        if vibrato:
            frequence, amplitude = 6, 0.1
            return 1 + amplitude*np.sin(2*np.pi*np.arange(self.duree)*frequence)
        else:
            return np.ones(self.duree)
            
            
########## FONCTION JOUER ##########
def jouer(partition):
    """
    Joue, via la carte son, un Son ou une liste de Sons.
    """
    signal = np.array([])
    # Si la partition ne contient qu'une note, ce qui est toujours le cas en jouant via l'interface.
    if type(partition) is not tuple: 
        signal = partition.signal
    else :
        for son in partition:
            if len(signal)<son.debut+son.duree: # Rallonge signal au besoin
                signal = np.concatenate((signal,np.zeros(son.debut+son.duree-len(signal))))
            signal[son.debut:son.debut+len(son.signal)] += son.signal
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=1)
    stream.write(signal.astype(np.float32).tostring())
    stream.close()
    p.terminate()
#    return signal


    
########## AUTRES FONCTIONS ##########
def sortie(hauteur, timbre, enveloppe, reverb=False, vibrato=False, duree=3, debut=0):
    """C'est la fonction appelée par le Thread, qui appelle a son tour la fonction jouer.
    On ne peut pas appeler directement la fonction jouer avec le Thread car il ne prend pas la CLasse Son comme argument"""
    jouer(Son(hauteur, timbre, enveloppe,reverb,vibrato,duree,debut))
    
def profil_filtre(coupure, largeur, taille):
    return np.concatenate((np.zeros(coupure-largeur),np.linspace(0,1,largeur),np.ones(taille-coupure)))
    
def ajuste(array,taille,ratio='null'):
    """
    Renvoie un tableau de longueur 'taille' contenant l'homothétie de facteur 'ratio' du tableau 'array'.
    """
    if ratio is 'null':
        ratio = taille/len(array)
    homothetie = np.interp(np.linspace(0,len(array)-1,np.floor(len(array)*ratio)),np.linspace(0,len(array)-1,len(array)),array)
    if taille>len(homothetie):
        return np.concatenate((homothetie,np.zeros(taille-len(homothetie))))
    else:
        return homothetie[:taille]
        
        
########## INTERFACE ##########        
class Interface(QWidget,Thread):
    def __init__(self,parent):       
        Thread.__init__(self)       
        QWidget.__init__(self,parent =None)
 
        self.setWindowTitle(u"Synthé")
        self.parent = parent   #on garde une trace du parent
        self.setGeometry(5, 50,500,300) #geometrie initiale de la fenetre
        self.setStyleSheet('Interface {background-color: black}')
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        
        self.initialisation()
        self.show()
    
    def initialisation(self):
        
        self.cadre_bouton = QFrame()
        self.grid.addWidget(self.cadre_bouton, 0,0)
        self.cadre_bouton.setStyleSheet('QFrame {background-color: brown}')
        self.cadre_bouton.setFrameShadow(QFrame.Sunken)
        self.cadre_bouton.setFrameShape(QFrame.StyledPanel)
        self.cadre_bouton.setFixedWidth(200)
        self.cadre_bouton.setFixedHeight(200)
        
        self.grid0 = QGridLayout(self.cadre_bouton)
        
        self.jouer = QPushButton("Jouer")
        self.grid0.addWidget(self.jouer, 0,0)
        self.jouer.clicked.connect(self.f_interface)
        
        self.aide = QPushButton("Aide")
        self.grid0.addWidget(self.aide,1,0)
        self.aide.clicked.connect(self.f_aide)
        
        self.quitter = QPushButton("Quitter")
        self.grid0.addWidget(self.quitter,2,0)
        self.quitter.clicked.connect(self.f_quit)
     
    def f_interface(self):

        #on enleve le boutton jouer
        self.jouer.close()

#CADRE REGLAGE coeffs harmoniques      
        
        #creation d'un cadre pour les reglages
        self.cadre_reglage = QFrame()
        self.grid.addWidget(self.cadre_reglage, 0,1)
        self.cadre_reglage.setStyleSheet('QFrame {background-color: brown}')
        self.cadre_reglage.setFrameShadow(QFrame.Sunken)
        self.cadre_reglage.setFrameShape(QFrame.StyledPanel)
        self.cadre_reglage.setFixedWidth(550)
        self.cadre_reglage.setFixedHeight(200)
        
        #On utilisera grid3 pour placer des objets dans le cadre_reglage
        self.grid3 = QGridLayout(self.cadre_reglage)
        
        self.volume = QSlider(Qt.Vertical)
        self.grid3.addWidget(self.volume,1,0)
        self.volume.setMinimum(0)
        self.volume.setMaximum(100)
        self.volume.setValue(5)
        label_volume = QLabel("Volume")
        self.grid3.addWidget(label_volume,0,0,1,2)
        self.label_volume = QLabel("")
        self.volume.valueChanged.connect(self.f_valuechange)

        self.liste_barre = []
        for i in range(4):
            
            #creation de barre de reglage (on utilisera pour les différents parametres physiques)
            self.barre_reglage = QSlider(Qt.Vertical)     
            self.barre_reglage.setMinimum(0)
            self.barre_reglage.setMaximum(100)
            self.barre_reglage.setValue(10)
            self.liste_barre.append(self.barre_reglage)
            self.grid3.addWidget(self.barre_reglage,1,i+1)
    
#CADRE FILTRES 
        
        self.cadre_filtre = QFrame()
        self.grid.addWidget(self.cadre_filtre,0,2)
        self.cadre_filtre.setStyleSheet('QFrame {background-color: brown}')
        self.cadre_filtre.setFrameShadow(QFrame.Sunken)
        self.cadre_filtre.setFrameShape(QFrame.StyledPanel)
        self.cadre_filtre.setFixedWidth(550)
        self.cadre_filtre.setFixedHeight(200)

        self.grid4 = QGridLayout(self.cadre_filtre)#on utilisera grod2 pour placer des widget dans cadre_filtre
  
        self.passehaut = QCheckBox("Filtre passe-haut")
        self.passehaut.clicked.connect(lambda:self.btnstate(self.passehaut))
        self.grid4.addWidget(self.passehaut,0,0)
        
        self.passebas = QCheckBox("Filtre passe-bas")
        self.passebas.clicked.connect(lambda:self.btnstate(self.passebas))
        self.grid4.addWidget(self.passebas,1,0)
        
        self.sans_filtre = QCheckBox("Aucun")
        self.sans_filtre.clicked.connect(lambda:self.btnstate(self.sans_filtre))
        self.grid4.addWidget(self.sans_filtre,2,0)
        
        self.bg = QButtonGroup()
        self.bg.addButton(self.passehaut,1)
        self.bg.addButton(self.passebas,2)
        self.bg.addButton(self.sans_filtre,3)
        
        label_filtre = QLabel(u"          Fréquence de coupure du filtre")
        self.grid4.addWidget(label_filtre,0,1)
        self.coupure = QLineEdit("line1")
        self.coupure.setMaxLength(7)
        self.coupure.setText("")
        self.grid4.addWidget(self.coupure,0,2)
        
        label_filtre2 = QLabel(u"          Largeur du filtre :")
        self.grid4.addWidget(label_filtre2,1,1)
        self.largeur_filtre = QLineEdit("line1")
        self.largeur_filtre.setMaxLength(7)
        self.largeur_filtre.setText("")
        self.grid4.addWidget(self.largeur_filtre,1,2)
        
        label_filtre3 = QLabel(u"          taille du filtre :")
        self.grid4.addWidget(label_filtre3,2,1)
        self.taille_filtre = QLineEdit("line1")
        self.taille_filtre.setMaxLength(7)
        self.taille_filtre.setText("")
        self.grid4.addWidget(self.taille_filtre,2,2)
        
#CADRE ENVELOPPE        

        self.cadre_enveloppe = QFrame()
        self.grid.addWidget(self.cadre_enveloppe,0,3)
        self.cadre_enveloppe.setStyleSheet('QFrame {background-color: brown}')
        self.cadre_enveloppe.setFrameShadow(QFrame.Sunken)
        self.cadre_enveloppe.setFrameShape(QFrame.StyledPanel)
        self.cadre_enveloppe.setFixedWidth(200)
        self.cadre_enveloppe.setFixedHeight(200)
        
        self.grid5 = QGridLayout(self.cadre_enveloppe)#on utilisera grod2 pour placer des widget dans cadre_filtre
        
        self.sin = QCheckBox("Sinusoidale")       
        self.sin.clicked.connect(lambda:self.btnstate(self.sin))
        self.grid5.addWidget(self.sin,0,0) 
        
        
        self.lin = QCheckBox("lineaire")
        self.lin.clicked.connect(lambda:self.btnstate(self.lin))
        self.grid5.addWidget(self.lin,1,0)
        self.bg2 = QButtonGroup()
        self.bg2.addButton(self.sin,1)
        self.bg2.addButton(self.lin,2)
        
        self.effet_reverb = QCheckBox("reverb")
        self.effet_reverb.clicked.connect(lambda:self.btnstate(self.effet_reverb))
        self.grid5.addWidget(self.effet_reverb,0,1)
        
        self.effet_vibrato = QCheckBox("vibrato")
        self.effet_vibrato.clicked.connect(lambda:self.btnstate(self.effet_vibrato))
        self.grid5.addWidget(self.effet_vibrato,1,1)
        
# CADRE SAUVEGARDE & ENREGISTREMENT
        
        self.cadre_rec = QFrame()
        self.grid.addWidget(self.cadre_rec,2,0,1,2)
        self.cadre_rec.setStyleSheet('QFrame {background-color: green}')
        self.cadre_rec.setFrameShadow(QFrame.Sunken)
        self.cadre_rec.setFrameShape(QFrame.StyledPanel)
        self.cadre_rec.setFixedWidth(650)
        self.cadre_rec.setFixedHeight(400)
        self.grid6 = QGridLayout(self.cadre_rec)   
        
        rec_button = QPushButton("Enregistrer")
        self.grid6.addWidget(rec_button, 3,0)
        rec_button.clicked.connect(self.f_test_rec)
        
        rec = QLabel(u"Durée de l'enregistrement (en s)")
        self.grid6.addWidget(rec,0,0)
        self.rec_value = QLineEdit("line1")
        self.rec_value.setMaxLength(7)
        self.rec_value.setText("")
        self.grid6.addWidget(self.rec_value,0,1)
        
        rec_name = QLabel(u"Nom de l'enregistrement")
        self.grid6.addWidget(rec_name,1,0)
        self.rec_name = QLineEdit("line1")
        self.rec_name.setMaxLength(20)
        self.rec_name.setText("")
        self.grid6.addWidget(self.rec_name,1,1)
        
        rec_rep = QLabel(u"Emplacement")
        self.grid6.addWidget(rec_rep,2,0)
        self.rec_rep = QLineEdit("line1")
        self.rec_rep.setMaxLength(200)
        self.rec_rep.setText(os.path.expanduser('~'))
        self.grid6.addWidget(self.rec_rep,2,1)       
# CADRE PIANO
        
        #creation d'un cadre dans lequel seront les touches de piano
        self.cadre_touche = QFrame()
        self.grid.addWidget(self.cadre_touche,1,0,1,2)
        self.cadre_touche.setStyleSheet('QFrame {background-color: brown}')
        self.cadre_touche.setFrameShadow(QFrame.Sunken)
        self.cadre_touche.setFrameShape(QFrame.StyledPanel)
        self.cadre_touche.setFixedWidth(650)
        self.cadre_touche.setFixedHeight(400)
        self.grid2 = QGridLayout(self.cadre_touche)#on utilisera grod2 pour placer des widget dans cadre_touche

        for i,k,l in zip(liste_notes,range(12),touches):
            if i.find("#")==1: #si la note contient un dieze
                self.touche = QPushButton(i)
                self.touche.setStyleSheet('QPushButton {background-color: black; color: grey;}')
                self.touche.setFixedSize(40,300)
                self.grid2.addWidget(self.touche,0,k)                
            else:
                self.touche = QPushButton(i)
                self.touche.setStyleSheet('QPushButton {background-color: white; color: grey;}')
                self.touche.setFixedSize(60,300)
                self.grid2.addWidget(self.touche,0,k) 
            
            self.touche.clicked.connect(lambda event, a=l : self.f_call(a))#si on clique, on appelle f_call qui permet de jouer avec un Thread
    
# CONNEXION DU FILTRE & ENVELOPPE
    
    def btnstate(self,b):  
        """Fonction qui verifie l'etat des checkButton correspondant au type de filtre choisi. Elle appelera la fonction filtre de la classe physique
        correspondante, avec les arguments donnés"""                     

        if b.text() == 'Filtre passe-haut':
            if b.isChecked() == True:               
                if int(self.taille_filtre.text()) > int(self.coupure.text()) and int(self.coupure.text()) > int(self.largeur_filtre.text()) :
                    self.type_filtre = 'passe-haut'
                    #("passe-haut",int(self.coupure.text()),int(self.largeur_filtre.text()),int(self.taille_filtre.text()),[self.liste_barre[0].value(),self.liste_barre[1].value(),self.liste_barre[2].value()])
                    self.graphique()
                else:
                    self.erreur_filtre()
                                 
        if b.text() == 'Filtre passe-bas':
            if b.isChecked() == True:
                if int(self.taille_filtre.text()) > int(self.coupure.text()) and int(self.coupure.text()) > int(self.largeur_filtre.text()) :
                    self.type_filtre = 'passe-bas'
                    #("passe-bas",int(self.coupure.text()),int(self.largeur_filtre.text()),int(self.taille_filtre.text()),[self.liste_barre[0].value(),self.liste_barre[1].value(),self.liste_barre[2].value()])
                    self.graphique()
                else:
                    self.erreur_filtre()
                
        if b.text() == 'Aucun':
            if b.isChecked() == True:
                self.type_filtre = 'aucun'
                self.graphique()
        if b.text() =="Sinusoidale":
            if b.isChecked() == True:
                self.enveloppe = 'sinusoidale'
                self.graphique()
        if b.text() == "lineaire":
            if b.isChecked() == True:
                self.enveloppe = 'lineaire'
                self.graphique()
        if b.text() == "vibrato":
            if b.isChecked() == True:
                self.vibrato = True
                self.graphique()
        if b.text() == "reverb":
            if b.isChecked() == True:
                self.reverb = 'ir1'
                self.graphique()                
        
                
# CONNEXION CLAVIER
    
    def keyPressEvent(self,event):
        modifiers = QApplication.keyboardModifiers()
        if type(event) == QKeyEvent:
            key = event.text()
            if key in touches:
                self.hauteur = key
                self.f_call(key)
        if modifiers == Qt.ShiftModifier:
#            self.reverb = 'ir1'
            print "Shift enfoncé"
#            
#    def keyReleaseEvent(self,event):
#        modifiers = QApplication.keyboardModifiers()
#        if modifiers == Qt.ShiftModifier:
#            self.reverb = False
#            print "shit relaché"
            
    def f_call(self,a):
        Thread(target = sortie, args = (a,Timbre([self.liste_barre[0].value(),self.liste_barre[1].value(),self.liste_barre[2].value()]).filtre(self.type_filtre,self.coupure.text(),self.largeur_filtre.text()),Enveloppe(self.enveloppe))).start()          

    def f_valuechange(self):
        self.label_volume.setText(str(self.volume.value()))
        self.grid3.addWidget(self.label_volume,2,0)
        
    def graphique(self):
                
        fen_graphe = pg.GraphicsLayoutWidget()#créé un widget d'affichage de graphe
        self.grid.addWidget(fen_graphe,1,2,1,2)
        
        graph_harmonique = fen_graphe.addPlot(row=0, col=0)#ajoute un graphe a gen_graphe
        x=range(10000)
        c = graph_harmonique.plot(y=Enveloppe.array[x])
        
        graph_filtre = fen_graphe.addPlot(row = 0,col=1)
        c2 = graph_filtre.plot(y=range(6))

# ENREGISTREMENT
    def f_test_rec(self):
        self.rep = str(self.rec_rep.text()) 
        self.a=1
        if os.path.isdir(self.rep) ==0:
            
            message_erreur = QMessageBox(self)
            message_erreur.setText(u"""
            Il semblerait que le repertoire indiqué n'existe pas. 
            Si vous en êtes conscientet que vous voulez créer 
            un nouveau repertoire selon le chemin indiqué, 
            cliquez sur "Apply".
            
            Sinon, chercher l'erreur dans votre chemin d'accès 
            ou que son chemin d'accés soit mal écrit.
            
            
#                    """)

            message_erreur.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if QMessageBox.Save :
                print "ok"
                mkdir(os.path.expanduser(str(self.rec_rep.text())))
                self.rep = str(self.rec_rep.text())
                self.a = 0                
            message_erreur.show()
            self.f_rec()
        else:
            self.a = 0
            self.f_rec()
   
    def f_rec(self):
        if self.a ==0:
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 2
            RATE = 44100
            RECORD_SECONDS = int(self.rec_value.text())
            repertoire = self.rep
            WAVE_OUTPUT_FILENAME = repertoire +'/'+ str(self.rec_name.text())+".wav"
    
            p = pyaudio.PyAudio()
    
            stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
            print("* recording")
    
            frames = []
    
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    frames.append(data)
    
            print("* done recording")
    
            stream.stop_stream()
            stream.close()
            p.terminate()
    
            wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            

# DIFFERENTES FENETRES D'ERREURS  
    
    def erreur_filtre(self):
        message_erreur = QMessageBox(self)
        message_erreur.setText(u"""
            Vos valeurs ne sont pas adaptées, veuillez 
            vérifier les conditions suivantes :
                    
            - taille du filtre > frequence de coupure > largeur du filtre
                        
            Reesayez ;-)
                    """)
        message_erreur.show()
        
    def f_aide(self):
        pop_up = QMessageBox(self)
        pop_up.setText(u"""
        Pour jouer, utiliser les touches suivantes : 
        
        'w','s','x','d','c','v','g','b','h','n','j','k'
        
        ou cliquer simplement sur la touche de votre 
        choix.
      
        """)
        pop_up.show()  
     
    def f_quit_reglage(self):
        self.cadre_reglage.close()
        
    def f_quit(self):
        app.closeAllWindows()#ferme la fenetre principale et stoppe la boucle

#class Graphique()
#On verifie si il existe une instance de QApplication, si non on en crée une

app = QApplication.instance() 
if not app:
    
    app = QApplication(sys.argv)
    
fen = Interface(None)
app.exec_()

