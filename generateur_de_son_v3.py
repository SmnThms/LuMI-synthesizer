# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 22:11:08 2017

@author: Simon
"""

from __future__ import division
import numpy as np
import pyaudio   # python -m pip install pyaudio
import scipy.io.wavfile
from matplotlib import pyplot as plt
taux = 44100

# Fonctionnement du programme :
# lecture d'une partition (liste de sons), par correspondance avec un répertoire,
# produisant un signal joué par la carte son.


####### CLASSES #######
class Son:
    """
    (Doc à écrire)
    Amélioration possible : ajouter une étape de convolution du son pour moduler l'attaque et l'évolution du son
    """  
    def __init__(self, debut, hauteur, timbre, enveloppe, duree=3):
        self.debut = debut*taux
        self.duree = duree*taux + 1 # Pour la fréquence 0 de la TF
        self.positives = np.concatenate((R[timbre].positives[1000-np.floor(R[hauteur]):],np.zeros(self.duree))) # Fréquences positives du timbre,transposées
        self.negatives = np.concatenate((R[timbre].negatives[1000-np.floor(R[hauteur]):],np.zeros(self.duree))) # Fréquences négatives du timbre,transposées
        self.spectre = np.concatenate((np.array([0]),self.positives[:self.duree//2],self.negatives[:self.duree//2])) # Assemblage du spectre
        self.enveloppe = Enveloppe(enveloppe,self.duree).profil # Evolution de l'intensité au cours du son
        self.signal = np.fft.ifft(self.spectre)*self.enveloppe
        
class Timbre:
    """
    Fréquences de 0 à 9999 Hz, avec la hauteur principale (note entendue) à 1000 Hz.
    """
    def __init__(self,parametre=0.01):
        # Pour créer un timbre à partir de l'enregistrement sonore d'une note
        if type(parametre) is str: 
            SR, extrait_sonore = scipy.io.wavfile.read(parametre+'.wav')            
            spectre_extrait = np.fft.fft(extrait_sonore)
            if np.argmax(spectre_extrait)<1000:
                self.positives = np.concatenate((np.zeros(1000-np.argmax(spectre_extrait)),spectre_extrait[:9000+np.argmax(spectre_extrait)]))
            else:
                self.positives = spectre_extrait[np.argmax(spectre_extrait):10000]
         # Pour créer un timbre constitué d'un fondamental éventuellement gaussien
        else:
            self.positives = np.exp(-(np.arange(10000)-999)**2/(2*parametre**2))
        self.negatives = self.positives
        
    def harmoniques(self,coefs):
        for i,amplitude in enumerate(coefs):
            self.positives[1000*(i+2)/(i+1)] += amplitude
            self.negatives[1000*(i+2)/(i+1)] += amplitude
        return self
            
    def passe_bas(self,frequence_coupure,largeur=200):
        self.positives *= filtre(frequence_coupure,largeur,10000)[::-1]
        self.negatives *= filtre(frequence_coupure,largeur,10000)[::-1]
        return self
        
    def passe_haut(self,frequence_coupure,largeur=200):
        self.positives *= filtre(frequence_coupure,largeur,10000)
        self.negatives *= filtre(frequence_coupure,largeur,10000)
        return self
    
class Enveloppe:
    """
    (Doc à écrire)
    """
    def __init__(self,profil,duree):
        self.duree = duree
        if profil=='sin':
            self.profil = np.sin(np.pi*np.linspace(0,1,self.duree))
        elif profil=='lin':
            self.profil = np.concatenate((np.linspace(0,1,self.duree/2),1-np.linspace(0,1,self.duree/2)))
    
    def vibrato(self, frequence,amplitude):
        self.get += amplitude*np.sin(2*np.pi*frequence*np.arange(self.duree))
        return self


####### FONCTIONS #######
def jouer(partition):
    """
    (Doc à écrire)
    """
    signal = np.array([])
    if type(partition) is not tuple: # Si la partition ne contient qu'une note
        signal = partition.signal
    else :
        for son in partition:
            if len(signal)<son.debut+son.duree:
                signal = np.concatenate((signal,np.zeros(son.debut+son.duree-len(signal))))
            signal[son.debut:son.debut+len(son.signal)] += son.signal
    signal *= 0.2/np.max(signal) # Normalisation du volume
# La syntaxe qui suit est tirée de davywybiral.blogspot.fr/2010/09/procedural-music-with-pyaudio-and-numpy.html
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=1)
    stream.write(signal.astype(np.float32).tostring())
    stream.close()
    p.terminate()
    return signal
        
def filtre(coupure, largeur, taille):
    return np.concatenate((np.zeros(coupure-largeur),np.linspace(0,1,largeur),np.ones(taille-coupure)))
        
        
####### REPERTOIRE #######
   # Timbres
R={'1':Timbre(10).harmoniques((0.5,0.2,0.2,0.1,0.04,0.06))}
R.update({'2':Timbre(70).harmoniques((0,0,0.2,0.1,0.5,0.6,0.4,0.2,0.1))})
R.update({'3':Timbre(0.01).harmoniques((0.5,0,0.1,0,0.04,0,0.01,0,0.01)).passe_bas(350)})
   # Notes
for i,clef in enumerate(('a','z','e','r','t','y','u','i','o','p')):
    R.update({clef:261.63*2**(i/12)})



partition = (Son(0,'a', '1', 'sin'),Son(1,'a','2','lin',4),Son(3,'r','1','sin'),Son(4,'p','3','sin'))
s = jouer(partition)
plt.plot(s)