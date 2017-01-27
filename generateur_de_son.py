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
        self.duree = duree*taux
        if type(timbre) is str:
            self.timbre = R[timbre]
        else:
            self.timbre = timbre
        self.spectre = np.zeros(self.duree//2+1)
        timbre_transpose = self.timbre.freq[1000-np.floor(R[hauteur]):]
        self.spectre[:duree*len(timbre_transpose):duree] = timbre_transpose
        self.enveloppe = Enveloppe(enveloppe,self.duree).profil # Evolution de l'intensité au cours du son
        self.signal = np.fft.irfft(self.spectre)*self.enveloppe
        self.signal *= 0.2/np.max(self.signal)
        
class Timbre:
    """
    Fréquences de 0 à 9999 Hz, avec la hauteur principale (note entendue) à 1000 Hz.
    """
    def __init__(self,parametre=0.01):
        # Pour créer un timbre à partir de l'enregistrement sonore d'une note
        if type(parametre) is str: 
            SR, extrait_sonore = scipy.io.wavfile.read(parametre+'.wav')  
            spectre_extrait = np.fft.rfft(extrait_sonore[:,0])
            self.test = extrait_sonore
            if np.argmax(spectre_extrait)<1000:
                self.freq = np.concatenate((np.zeros(1000-np.argmax(spectre_extrait)),spectre_extrait[:9000+np.argmax(spectre_extrait)]))
            else:
                self.freq = spectre_extrait[:10000]
        # Pour créer un timbre constitué d'un fondamental éventuellement gaussien
        else:
            self.freq = np.exp(-(np.arange(10000)-999)**2/(2*parametre**2))
        
    def harmoniques(self,coefs):
        for i,amplitude in enumerate(coefs):
            self.freq[1000*(i+2)/(i+1)] += amplitude
        return self
            
    def passe_bas(self,frequence_coupure,largeur=200):
        self.freq *= filtre(frequence_coupure,largeur,10000)[::-1]
        return self
        
    def passe_haut(self,frequence_coupure,largeur=200):
        self.freq *= filtre(frequence_coupure,largeur,10000)
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
R.update({'3':Timbre()})
R.update({'4':Timbre().harmoniques((0.1,0.05,0.1,0.05))})
R.update({'voix':Timbre('1')})
   # Notes
for i,clef in enumerate(('a','z','e','r','t','y','u','i','o','p','q','s','d','f','g','h','j','k','l')):
    R.update({clef:261.63*2**(i/12)})
R.update({'w':60,'s':60/(2**(1/12))})

#partition = Son(0,'e',Timbre('sifflement'),'sin')
partition = Son(0,'a',Timbre('sifflement'),'sin'),Son(0,'i',Timbre('sifflement'),'sin'),Son(3,'p',Timbre('sifflement'),'sin'),Son(3,'a',Timbre('sifflement'),'sin'),Son(6,'a',Timbre('sifflement'),'sin'),Son(6,'d',Timbre('sifflement'),'sin'),Son(6,'r',Timbre('sifflement'),'sin'),
#partition = (Son(0,'e','3','sin',duree=4),Son(2,'i','3','sin'),Son(3,'p','3','sin'),Son(4,'e','3','sin',duree=4),Son(5,'q','4','lin',duree=3),Son(6,'s','4','sin',duree=4),Son(8,'e','voix','lin'),Son(10,'y','voix','lin'))
#partition = (Son(0,'a', '1', 'sin'),Son(1,'a','2','lin',4),Son(3,'r','1','sin'),Son(4,'p','3','sin'))
s = jouer(partition)
#plt.plot(s)
