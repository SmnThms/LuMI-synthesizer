# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 11:30:57 2017

@author: Zazou
"""

import sys
import pyaudio
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import numpy as np

SR = 44100 #Hz (Sampling Rate)

#listes définies en global mais qui peuvent passer dans la classe Interface
octave = {'w':262.,'s':277.,'x':294.,'d':311.,'c':330.,'v':349.,'g':370.,'b':392.,'h':415.,'n':440.,'j':466.,'k':494.}
liste_notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
liste_frequence = [262.,277.,294.,311.,330.,349.,370.,392.,415.,440.,466.,494.]
touches = ['w','s','x','d','c','v','g','b','h','n','j','k']

class Physique():
    """Cette classe contiendra toutes les methodes relevant de la physique"""
    
    def __init__(self):
        pass
        
    def note(self,f,t):
        """la fonction note genere une note a partir de la fonction sinus.
        Cette note est composée d'harmonique superieure, dont les coefficient d'intensité
        seront donnés par a,b,c,... On pourra plus tard choisir le nombre d'harmonique de la note""" 
        
        return (self.sinus(f,t) + 0.5*self.sinus(2*f,t) + 0.125*self.sinus(4*f,t))
        
    def sinus(self,f,t):
        """la fonction sinus renvoie une sinusoidale de frequence f et de durée t, 
        echantillonnée tous les 1/SR"""    
        return np.sin(2*np.pi*f*np.arange((t*SR))/SR)
    
    def sortie(self,F,V):
        """appelle la fonction note et genere le son.
        Prend en entrée une frequence F et le niveau du volume general V.
        """
        T=0.1#temps en sec
        son = self.note(F,T)       
        son = son*V   

        #jeu du son
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=1)
        stream.write(son.astype(np.float32).tostring())
        stream.close()
        p.terminate()

class Interface(QWidget):
    def __init__(self,parent):
        QWidget.__init__(self,parent =None)
        self.setWindowTitle(u"Synthé")
        self.parent = parent   #on garde une trace du parent
        self.setGeometry(5, 50,500,300) #geometrie initiale de la fenetre
        
        self.physique = Physique() #creation d'une instance de la classe Physique
        
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        
        self.initialisation()
        
        self.show()
    
    def initialisation(self):
        
        self.jouer = QPushButton("Jouer")
        self.grid.addWidget(self.jouer, 0,0)
        self.jouer.clicked.connect(self.f_interface)
        
        self.aide = QPushButton("Aide")
        self.grid.addWidget(self.aide,1,0)
        self.aide.clicked.connect(self.f_aide)
        
        self.quitter = QPushButton("Quitter")
        self.grid.addWidget(self.quitter,2,0)
        self.quitter.clicked.connect(self.f_quit)
        
    def f_interface(self):
        #on enleve le boutton jouer
        self.jouer.close()
        
        self.reglage = QPushButton(u"Réglage")
        self.grid.addWidget(self.reglage, 0,0)
        self.reglage.clicked.connect(self.f_reglage)
        
        #creation d'une barre de reglage pour le volume general
        self.volume = QSlider(Qt.Vertical)
        self.grid.addWidget(self.volume,0,2)
        self.volume.setMinimum(0)
        self.volume.setMaximum(100)
        self.volume.setValue(50)
        
        self.label_volume = QLabel("")
        self.volume.valueChanged.connect(self.f_valuechange)
        
        #creation d'un cadre dans lequel seront les touches de piano
        self.cadre_touche = QFrame()
        self.grid.addWidget(self.cadre_touche,0,1)
        self.cadre_touche.setStyleSheet('QFrame {background-color: brown}')
        self.cadre_touche.setFrameShadow(QFrame.Sunken)
        self.cadre_touche.setFrameShape(QFrame.StyledPanel)
        self.cadre_touche.setFixedWidth(650)
        self.cadre_touche.setFixedHeight(400)
        
        self.grid2 = QGridLayout(self.cadre_touche)#on utilisera grod2 pour placer des widget dans cadre_touche
        for i,j,k,l in zip(liste_notes,liste_frequence,range(12),touches):
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
            
            self.touche.clicked.connect(lambda event,a=j : self.physique.sortie(a,self.volume.value()))
            
    def keyPressEvent(self,event):
        """fonction qui permet de jouer la note desirée grace au clavier, quelque soit le focus"""
        
        
        if type(event) == QKeyEvent:     #test sur l'evenement == on est bien en train d'appuyer sur une lettre
            if event.text() in touches :  #si la touche appuyer fait partie de notre liste
                self.physique.sortie(octave[event.text()],self.volume.value())
            
            
    def f_valuechange(self):
               
        self.label_volume.setText('Volume =' + str(self.volume.value()))
        self.grid.addWidget(self.label_volume,0,3)        
        
    def f_reglage(self):
        
        #creation d'un cadre pour les reglages
        self.cadre_reglage = QFrame()
        self.grid.addWidget(self.cadre_reglage, 1,1)
        self.cadre_reglage.setFrameShadow(QFrame.Sunken)
        self.cadre_reglage.setFrameShape(QFrame.StyledPanel)
        self.cadre_reglage.setFixedWidth(650)
        self.cadre_reglage.setFixedHeight(200)
        
        quit_reglage = QPushButton('X')   #bouton qui permet de fermer le cadre reglage
        quit_reglage.clicked.connect(self.f_quit_reglage)
        
        #On utilisera grid3 pour placer des objets dans le cadre_reglage
        self.grid3 = QGridLayout(self.cadre_reglage)
        self.grid3.addWidget(quit_reglage,0,0)
        
        for i in range(4):
            
            #creation de barre de reglage (on utilisera pour les différents parametres physiques)
            self.barre_reglage = QSlider(Qt.Vertical)       
            self.barre_reglage.setMinimum(0)
            self.barre_reglage.setMaximum(100)
            
            self.grid3.addWidget(self.barre_reglage,1,i)
            self.barre_reglage.valueChanged.connect(self.f_reglage_valuechange)
            
        
    def f_reglage_valuechange(self):
        pass
    
    def f_aide(self):
        pop_up = QMessageBox(self)
        pop_up.setText(u"""
        Pour jouer, utiliser les touches suivantes : 
        
        'w','s','x','d','c','v','g','b','h','n','j','k'
        
        ou cliquer simplement sur la touche de votre 
        choix.
        
        Le volume est reglable avec la barre de droite.
        
        Acceder aux réglages en cliquant sur "réglage" 
        (pour l'instant ils ne servent à rien)""")
        pop_up.show()  
     
    def f_quit_reglage(self):
        self.cadre_reglage.close()
        
    def f_quit(self):
        app.closeAllWindows()#ferme la fenetre principale et stoppe la boucle


#On verifie si il existe une instance de QApplication, si non on en crée une
app = QApplication.instance() 
if not app:
    app = QApplication(sys.argv)
        
fen = Interface(None)
app.exec_()

