# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 19:27:36 2017

@author: Zazou
"""
import Tkinter
import pyaudio
import numpy as np

SR = 44100 #Hz (Sampling Rate)

#listes définies en global mais qui peuvent passer dans la classe Interface
liste_notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
liste_frequence = [262.,277.,294.,311.,330.,349.,370.,392.,415.,440.,466.,494.]
touches = ['w','s','x','d','c','v','g','b','h','n','j',',']

class Physique():
    """Cette classe contiendra toutes les methodes relevant de la physique"""
    
    def __init__(self):
        pass
        
    def note(self,f,t):
        """la fonction note genere une note a partir de la fonction sinus.
        Cette note est composée d'harmonique superieure, dont les coefficient d'intensité
        seront donnés par a,b,c,... On pourra plus tard choisir le nombre d'harmonique de la note""" 
        
        return (self.sinus(f,t)/100. + 0.5*self.sinus(2*f,t)*0 + 0.125*self.sinus(4*f,t)*0)
        
    def sinus(self,f,t):
        """la fonction sinus renvoie une sinusoidale de frequence f et de durée t, 
        echantillonnée tous les 1/SR"""    
        return np.sin(2*np.pi*f*np.arange((t*SR))/SR)
    
    def sortie(self,F,V):
        """appelle la fonction note et genere le son.
        Prend en entrée une frequence F et le niveau du volume general V.
        """
        T=1#temps en sec
        n=1
        son = self.note(F,T)       
        #la variable volume n'est pas indispensable et est juste utilisée comme exmple ici.
        volume = np.sin(2*np.pi*np.arange(n*T*SR)/(n*T*SR))
        son = son*volume*V   

        #jeu du son
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=1)
        stream.write(son.astype(np.float32).tostring())
        stream.close()
        p.terminate()


class Interface(Tkinter.Tk):
    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        
        self.parent = parent   #on garde une trace du parent
        self.physique = Physique()   #on crée une instance de classe Physique
        
        self.initiallisation()   #methode dans laquelle on creera tous les widgets de la classe
        
    
    def initiallisation(self):
        self.grid() #l'attribut .grid servira à inclure et positionner les differents widget
        
        self.commencer = Tkinter.Button(self, text = "Jouer", command = self.f_interface)
        self.commencer.grid(column = 0,row=0)
        
        self.aide = Tkinter.Button(self, text = "Aide", command = self.f_aide)
        self.aide.grid(column = 2, row =0)
        
        self.quitter = Tkinter.Button(self, text = "Quitter", command =self.quit)
        self.quitter.grid(column = 15, row =4, sticky = 'se')
        
    def f_interface(self):
        
        #Enlever le bouton de demarrage "jouer"
        self.commencer.destroy()
        
        self.reglage = Tkinter.Button(self, text="Réglages", command = self.f_reglage)
        self.reglage.grid(column =1, row=0)
        
        #creation d'un cadre dans lequel on aura une barre permettant de controler le volume
        self.cadre_volume = Tkinter.Frame(self,width =100, height = 400, bd = 2, relief = "groove",bg = "red")
        self.cadre_volume.grid(column = 0, row =1)  
        self.cadre_volume.grid_propagate(0)#le cadre ne s'adapte pas a son contenu
        label = Tkinter.Label(self.cadre_volume, text = "Volume",bg="red")
        label.grid(column = 0, row =0)               
        self.control_volume = Tkinter.Scale(self.cadre_volume,from_=0,to=100,bg="red",highlightbackground="red")
        self.control_volume.grid(column =1, row =10)
        
        #le volume est controlable avec la molette quelque soit le focus
        self.count=0        
        self.bind("<MouseWheel>",self.f_volume)
        
        #creation d'un cadre dans lequel on aura les boutons de touches
        self.cadre_touche = Tkinter.Frame(self,width =1110, height = 400, bd = 4, highlightbackground="black",relief = "groove")
        self.cadre_touche.grid(column = 1, row =1)
        self.cadre_touche.grid_propagate(0)#le cadre ne s'adapte pas a la taille du contenu
        
        for i,j,k in zip(liste_notes,liste_frequence,range(12)):
            if i.find("#")==1: #si la note contient un dieze
                self.touche = Tkinter.Button(self.cadre_touche,text = i,bg = "black",width =5, height=10)
            else:
                self.touche = Tkinter.Button(self.cadre_touche,text = i,width =10, height=15)
            self.touche.grid(column=k, row =0,rowspan =1 )
        
            #si on clique, ou appuie sur les bonnes touches clavier, la note coresspondante est jouée
            self.touche.bind("<Button-1>", lambda event,a=j :self.physique.sortie(a,self.control_volume.get()))            
            self.touche.bind_all(touches[k],lambda event,a=j :self.physique.sortie(a,self.control_volume.get()))

        
    def f_reglage(self):
        """cette fonction crée un cadre dans lequel se trouve 6 barre de reglage 
        afin de controler les intensités respectives des 6 harmonqiues)
        NON TERMINE
        """
        
        self.cadre_reglage = Tkinter.Frame(self,bd =2, relief ="groove", height =200, width =900, bg ="grey")
        self.cadre_reglage.grid(column=1,row=2)
        self.cadre_reglage.grid_propagate(0)
        quitter_reglage = Tkinter.Button(self.cadre_reglage, text = 'X', command = self.f_quit)
        quitter_reglage.grid(sticky='ne')
        for i in range(6):
            self.barre_reglage = Tkinter.Scale(self.cadre_reglage, label = "harmonique"+str(i))
            self.barre_reglage.grid(column=i+1, row =1)
        
        
    def f_volume(self,event):
        """permet de regler le volume general avec la molette de la souris"""
        
        def delta(event):
            if event.num == 5 or event.delta < 0: #indique un sens de rotation de l'event "tourner molette"
                return -1 
            return 1      
        self.count += delta(event)
        if self.count < 0: #sinon on descend dans les negatifs si on tourne trop la molette
            self.count =0  #--> pas tres utile ni pratique pour remonter
        
        elif self.count > 100: #de meme si on a trop tourner dans l'autre sens.
            self.count =100 
            
        self.control_volume.set(self.count) #On attribut la nouvelle valeur à "control_volume"
            
    def f_quit(self):
        self.cadre_reglage.destroy()
            
    def f_aide(self):
        fenetre = Tkinter.Toplevel()   #fenetre est une instance de la classe Toplevel
        fenetre.title("Page d'aide")
        texte_aide = Tkinter.Label(fenetre, text = """
        Pour jouer au clavier, taper sur les touches 'w','s','x','d','c','v','g','b','h','n','j' et ','
        (Pour le moment, je n'ai pas reussi à jouer deux notes en meme temps, car l'appui de deux touches 'lettre' simultanement
        ne signifie rien pour l'ordinateur.)  
        
        POur jouer à la souris, cliquer sur la note de votre choix.
               
        Pour monter le son, tourner ou baisser la molette de la souris ou utiliser la barre de volume.
        
        POur afficher les reglages, cliquer sur reglage (Cette partie n'est pas vraiment à jour et necessite la combinaison des 
        deux programmes.)
        
        La durée du son, son timbre et toutes les autres caracteristiques physiques seront normalement modifiables une fois
        les deux parties du programme reunies.
        """)
        texte_aide.grid()
        
        
if __name__ == "__main__":
    app = Interface(None)   #on cree une instance de la classe Interface
    app.title("Synthétiseur")
    app.mainloop()   #On boucle en attente d'evenement
    app.destroy()   #Si on sort de la boucle, la fenetre principale se ferme