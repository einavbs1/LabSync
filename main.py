import os
import sys

class NullWriter:
    def write(self, text):
        pass
    def flush(self):
        pass

if sys.stdout is None:
    sys.stdout = NullWriter()
if sys.stderr is None:
    sys.stderr = NullWriter()



import customtkinter as ctk
import pickle
import time
import dataManager as dm
from customtkinter import CTkInputDialog
from models import Computer, Room, Zone, WorkSpace, Settings
from PIL import Image
import tkinter.messagebox as messagebox
from git import Repo
import git
from pathlib import Path
import re
from typing import Literal
import stat
import shutil
import paramiko
import subprocess



ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
DATA_FILE = "WorkSpace_data.pkl"
appWidth = 1200
appHeight = 600
app = None

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

images_folder_path = os.path.join(base_path,"images")
icon_path = os.path.join(images_folder_path, "LabSyncIcon.ico")

WorkSpace_dict = {}
appSettings = None
unlockPassword = "admin"

class StatusPopup(ctk.CTkToplevel):
    def __init__(self, master, title, initial_message):
        super().__init__(master)
        self.title(title)
        self.geometry("800x200")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        self.label = ctk.CTkLabel(self, text=initial_message, font=("Arial", 14))
        self.label.pack(pady=(30, 10))
        self.labelprogress = ctk.CTkLabel(self, text="0%", font=("Arial", 14))
        self.labelprogress.pack(pady=(30, 10))

        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", width=300)
        self.progress_bar.pack(pady=10)
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)

        self.update()
        self.wait_visibility()

    def update_status(self, message, progress_value):
        print(f"DEBUG: {message} ({int(progress_value * 100)}%)")
        self.label.configure(text=message)
        self.labelprogress.configure(text=f"{int(progress_value * 100)}%")
        self.progress_bar.set(progress_value)
        self.update()
        self.update_idletasks()

    def close_with_delay(self, delay=15000):
        self.after(delay, self.destroy)



class LabSyncDashBoard(ctk.CTk):
    
    

    def __init__ (self):
        super().__init__()
        self.title("LabSync")
        self.geometry(f"{appWidth}x{appHeight}")

        try:
            self.iconbitmap(icon_path)
            print("iconnn")
        except Exception:
            print("EXCEPTIONNN == NO ICON")
            pass

        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=0)
        self.grid_columnconfigure(1,weight=1)
        self.currFrame = None
        self.historyPagesList = []
        self.indexOfHistoryPages = 0

        self.SideBar()
        self.homeWidget()
        self.tempSelectionComboBox = ""
        ctk.set_appearance_mode(appSettings.theme)
        self.dummy_entry = ctk.CTkEntry(self, width=1, height=1, placeholder_text=" ")

        


    ##edit History:
    def enteredNewPage(self, frame):
        self.historyPagesList[:self.indexOfHistoryPages]
        self.historyPagesList.append(frame)
        self.indexOfHistoryPages+=1
        self.BackButton.configure(state="normal", image=self.Real_BackIcon)
        self.ForwardButton.configure(state="disabled", image=self.Gray_ForwardIcon)

    def PressedOnBackBtn(self):
        if (self.indexOfHistoryPages >= 0):
            self.indexOfHistoryPages-=1
        else:
            self.BackButton.configure(state="disabled", image=self.Gray_BackIcon)
        
        self.currFrame = self.historyPagesList[self.indexOfHistoryPages]
        self.ForwardButton.configure(state="normal", image=self.Real_ForwardIcon)

    def pressedOnForwardBtn(self):
        if (len(self.historyPagesList)-1 == self.indexOfHistoryPages):
            self.ForwardButton.configure(state="disabled", image=self.Gray_ForwardIcon)
        
        self.currFrame = self.historyPagesList[self.indexOfHistoryPages]
        self.indexOfHistoryPages+=1
        self.BackButton.configure(state="normal", image=self.Real_BackIcon)

    # def updategui(self, frametoShow):


    

    def SideBar(self):
        #Side Bar
        self.sidebar_nav = ctk.CTkFrame(self, width=250 ,corner_radius=15)
        self.sidebar_nav.grid(row=0, column=0, sticky="nsew")
        self.sidebar_nav.grid_rowconfigure(5,weight=1)
        self.sidebar_nav.grid_rowconfigure(6,weight=1)

        #Logo
        try:
            self.LogoIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, "Logo_light_mode.png")), dark_image=Image.open(os.path.join(images_folder_path, "Logo_dark_mode.png")), size=(300,200))
            self.LogoLabel = ctk.CTkLabel(self.sidebar_nav, text="", compound="left", image=self.LogoIcon)
            self.LogoLabel.grid(row=0, column=0 ,padx=10, pady=10, sticky="ew")
        except Exception as e:
            print(f"\n\n\n err is: {e}\n\n\n")
        
        

        self.HomeIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "home-button.png")), size=(40,40))
        self.HomeButton = ctk.CTkButton(self.sidebar_nav, corner_radius=4, height=40, border_spacing=10, text="  Home",fg_color="transparent", text_color=("gray10", "gray90"), command=self.showHomePage , image=self.HomeIcon ,hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=20, weight="bold"))
        self.HomeButton.grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        self.AppearanceThemeIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, "Appearance_dark_mode.png")), dark_image=Image.open(os.path.join(images_folder_path, "Appearance_light_mode.png")), size=(40,40))
        self.AppearanceButton = ctk.CTkButton(self.sidebar_nav, corner_radius=4, height=40, border_spacing=10, text="  Change Appearance",fg_color="transparent", text_color=("gray10", "gray90"), command=self.changeAppearance , image=self.AppearanceThemeIcon ,hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=20, weight="bold"))
        self.AppearanceButton.grid(row=2, column=0, padx=2, pady=2, sticky="ew")

        self.NavFrameRow = ctk.CTkFrame(self.sidebar_nav)
        self.NavFrameRow.grid_columnconfigure(0, weight=1)
        self.NavFrameRow.grid_columnconfigure(1, weight=1)
        self.NavFrameRow.grid_rowconfigure(0, weight=1)

        self.Real_BackIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "Real_BackArrow.png")), size=(30,30))
        self.Gray_BackIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "Gray_BackArrow.png")), size=(30,30))
        self.BackButton = ctk.CTkButton(self.NavFrameRow, corner_radius=4, height=40, border_spacing=10, text="  Back",fg_color="transparent", text_color=("gray10", "gray90"), command=self.PressedOnBackBtn , image=self.Gray_BackIcon ,hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"), state="disabled")
        self.BackButton.grid(row=0, column=0, padx=0, pady=0, sticky="news")

        self.Real_ForwardIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "Real_ForwardArrow.png")), size=(30,30))
        self.Gray_ForwardIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "Gray_ForwardArrow.png")), size=(30,30))
        self.ForwardButton = ctk.CTkButton(self.NavFrameRow, corner_radius=4, height=40, border_spacing=10, text="  Forward",fg_color="transparent", text_color=("gray10", "gray90"), command=self.pressedOnForwardBtn , image=self.Gray_ForwardIcon ,hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"), state="disabled")
        self.ForwardButton.grid(row=0, column=1, padx=0, pady=0, sticky="news")

        # self.NavFrameRow.grid(row=4, column=0, padx=2, pady=2, sticky="ews")

        self.homepageselectionFrameRow = ctk.CTkFrame(self.sidebar_nav)
        self.homepageselectionFrameRow.grid_columnconfigure(0, weight=1)
        self.homepageselectionFrameRow.grid_columnconfigure(1, weight=1)
        self.homepageselectionFrameRow.grid_rowconfigure(0, weight=1)
        self.homepageselectionFrameRow.grid_rowconfigure(1, weight=1)

        self.homepagelabel = ctk.CTkLabel(self.homepageselectionFrameRow, text= "Startup Page: ")
        # self.homepagelabel.grid(row=0, column=0 , sticky="news")
        self.homepagecombobox = self.comboBoxHomePageCreation()
        # self.homepagecombobox.grid(row=0, column=1 ,sticky="we")

        self.updateHomePageSelectionIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "updateIcon.png")), size=(20,20))
        self.updateHomePageSelectionBTN = ctk.CTkButton(self.homepageselectionFrameRow, corner_radius=4, height=40, border_spacing=10, text=" Update Selection",fg_color="transparent", text_color=("gray10", "gray90"), command=self.updateStartHomePage , image=self.updateHomePageSelectionIcon ,hover_color=("gray70","gray30"), anchor="center", font=ctk.CTkFont(size=12, weight="bold"))
        self.updateHomePageSelectionBTN.grid(row=1, column=0, columnspan=2)
        self.updateHomePageSelectionBTN.configure(state="disable")

        # self.lockHomePageSelectionIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "lockIcon.png")), size=(20,20))
        # self.lockHomePageSelectionBTN = ctk.CTkButton(self.homepageselectionFrameRow, corner_radius=4, height=40, border_spacing=10, text=" Lock Selection",fg_color="transparent", text_color=("gray10", "gray90"), command=self.updateStartHomePage , image=self.updateHomePageSelectionIcon ,hover_color=("gray70","gray30"), anchor="center", font=ctk.CTkFont(size=12, weight="bold"))
        # self.lockHomePageSelectionBTN.grid(row=1, column=1)

        self.unlockHomePageSelectionIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "unlockIcon.png")), size=(20,20))
        self.unlockHomePageSelectionBTN = ctk.CTkButton(self.homepageselectionFrameRow, corner_radius=4, height=40, border_spacing=10, text=" Unlock Selection",fg_color="transparent", text_color=("gray10", "gray90"), command=self.unlockTheSelection , image=self.unlockHomePageSelectionIcon ,hover_color=("gray70","gray30"), anchor="center", font=ctk.CTkFont(size=12, weight="bold"))
        self.unlockHomePageSelectionBTN.grid(row=1, column=0, columnspan=2)
        # self.homepagelabel.grid(row=0, column=0 , sticky="news")
        # self.passwordToUpdateHomePage.grid(row=0, column=1)

        self.passwordToUpdateHomePagelabel = ctk.CTkLabel(self.homepageselectionFrameRow, text= "Enter Password to unlock: ")
        self.passwordToUpdateHomePagelabel.grid(row=0, column=0 , sticky="news")

        self.passwordToUpdateHomePageEntry = ctk.CTkEntry(self.homepageselectionFrameRow, placeholder_text="Enter the Password: ", show="*")
        self.passwordToUpdateHomePageEntry.grid(row=0, column=1)


        self.homepageselectionFrameRow.grid(row=5, column=0, padx=2, pady=2, sticky="news")
        print(f"startHomePage == {appSettings.startHomePage}")
        self.favoritesIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "favoritesIcon.png")), size=(40,40))
        self.favoritesButtonSideBar = ctk.CTkButton(self.sidebar_nav, corner_radius=4, height=40, border_spacing=10, text="  Favorites",fg_color="transparent", text_color=("gray10", "gray90"), command=self.loadFavsPage , image=self.favoritesIcon ,hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=20, weight="bold"))
        self.favoritesButtonSideBar.grid(row=6, column=0, padx=2, pady=2, sticky="ews")


    def unlockTheSelection(self):
        print(f"pass is : {self.passwordToUpdateHomePageEntry.get()}")
        if (self.passwordToUpdateHomePageEntry.get() == unlockPassword):
            self.comboBoxHomePageCreation()
            self.homepagelabel.grid(row=0, column=0 , sticky="news")
            self.homepagecombobox.grid(row=0, column=1 ,sticky="we")
            self.updateHomePageSelectionBTN.grid(row=1, column=0, columnspan=2)
            self.updateHomePageSelectionBTN.configure(state="normal")
            self.unlockHomePageSelectionBTN.grid_forget()
            self.passwordToUpdateHomePagelabel.grid_forget()
            self.passwordToUpdateHomePageEntry.grid_forget()
        else:
            self.dummy_entry.focus_set()
            self.passwordToUpdateHomePageEntry.configure(placeholder_text="Wrong Password..." )
            self.passwordToUpdateHomePageEntry._draw_placeholder()
            self.passwordToUpdateHomePageEntry.insert(0, "")
            self.dummy_entry.focus_set()
            


        self.passwordToUpdateHomePageEntry.delete(0, ctk.END)
        self.passwordToUpdateHomePageEntry.configure(show="*")


    def comboBoxHomePageCreation(self):
        self.favComboBoxOptionsMap = {}
        for ws_name, ws_obj in WorkSpace_dict.items():
            title = f" ♦ws: {ws_name}"
            if(len(self.favComboBoxOptionsMap)) == 0:
                title += " (Default)"
            self.favComboBoxOptionsMap[title] = ws_obj
            for zone_name, zone_obj in ws_obj.Zones.items():
                title = f"     •Zone: {zone_name}"
                self.favComboBoxOptionsMap[title] = zone_obj
        self.favComboBoxOptionsMap[" ♦♦♦ favorites ♦♦♦ "] = " ♦♦♦ favorites ♦♦♦ "
        self.firstarg = list(self.favComboBoxOptionsMap.keys())[0]
        if (appSettings.startHomePage is not None):
            for k,v in self.favComboBoxOptionsMap.items():
                if v == appSettings.startHomePage:
                    self.firstarg = k
            

        self.tempSelectionComboBox = self.firstarg
        print(f"firstarg is {self.firstarg}")

        return ctk.CTkComboBox(self.homepageselectionFrameRow, values=self.favComboBoxOptionsMap.keys(), state="readonly", width=140, height=30, variable= ctk.StringVar (value= self.firstarg))


    def choiceFromComboBoxToRealname(self, choice):
        obj_name = ""
        if isinstance(choice, WorkSpace):
            obj_name = "ws"
        elif isinstance(choice,Zone):
            obj_name = "zone"
        elif (choice == " ♦♦♦ favorites ♦♦♦ "):
            obj_name = " ♦♦♦ favorites ♦♦♦ "

        return obj_name

        # obj_name = ""
        # print(f"choice is: {choice}")
        # if "♦ws: " in choice:
        #     tempres = choice.split(" ♦ws: ")
        #     obj_name = tempres[1]
        #     if(" (Default)" in tempres[1]):
        #         res = tempres[1].split(" (Default)")
        #         obj_name = res[0]
        # elif("•Zone: " in choice):
        #     tempres = choice.split("•Zone: ")
        #     obj_name = tempres[1]
        # elif(" ♦♦♦ favorites ♦♦♦ " in choice):
        #     return " ♦♦♦ favorites ♦♦♦ "
        # print(f"new obj_name is = {obj_name}")
        # return obj_name


    def updateStartHomePage(self):
        print(f" starthome page was = {appSettings.startHomePage} and chnaged to = {self.homepagecombobox.get()}")
        stringFromCombobox= self.homepagecombobox.get()
        real_OBJ = self.favComboBoxOptionsMap[stringFromCombobox]
        appSettings.startHomePage = real_OBJ

        dm.updateDB(WorkSpace_dict, appSettings)
        self.homeWidget()
        self.dummy_entry.focus_set()
        self.unlockHomePageSelectionBTN.grid(row=1, column=0, columnspan=2)
        self.updateHomePageSelectionBTN.configure(state="disable")
        self.passwordToUpdateHomePagelabel.grid(row=0, column=0 , sticky="news")
        self.passwordToUpdateHomePageEntry.grid(row=0, column=1)
        self.passwordToUpdateHomePageEntry.configure(placeholder_text="Enter the Password: " )
        self.passwordToUpdateHomePageEntry._draw_placeholder()
        self.passwordToUpdateHomePageEntry.insert(0, " ")
        # self.passwordToUpdateHomePageEntry.delete(0, ctk.END)
        self.passwordToUpdateHomePageEntry.configure(show="*")
        self.homepagelabel.grid_forget()
        self.homepagecombobox.grid_forget()
        self.updateHomePageSelectionBTN.grid_forget()
        self.dummy_entry.focus_set()
        

    def button_func(self):
        print("Button Pressed")

    def changeAppearance(self):
        print(f"Appearance was: {ctk.get_appearance_mode()}.",end=" ")
        if (appSettings.theme == "Dark") :
            ctk.set_appearance_mode("Light")
            appSettings.theme = "Light"

        else:
            ctk.set_appearance_mode("Dark")
            appSettings.theme = "Dark"
        print(f"\tHas been changed right now to: {ctk.get_appearance_mode()}.")
        dm.updateDB(WorkSpace_dict, appSettings)


    def homeWidget(self):
        self.SideBar()
        self.mainFrame = ctk.CTkFrame(self ,corner_radius=3, bg_color="transparent", fg_color="#7b92a0")
        self.mainFrame.grid(row=0, column=1, sticky="nsew")
        self.mainFrame.grid_rowconfigure(0,weight=0)
        self.mainFrame.grid_rowconfigure(1,weight=1)
        self.mainFrame.grid_rowconfigure(2,weight=0)
        self.mainFrame.grid_columnconfigure(0,weight=1)
        self.searchRow()
        self.tabsWidgetsFunc()
        startuptype = self.choiceFromComboBoxToRealname(appSettings.startHomePage)
        if (startuptype == "ws"):
            self.tabsWidgets.set(appSettings.startHomePage.WorkSpace_name)
            # zone_obj = self.favComboBoxOptionsMap.get(appSettings.startHomePage)
        elif (startuptype == "zone"):
            self.zoneDetailsFrame(appSettings.startHomePage)
        elif (startuptype == " ♦♦♦ favorites ♦♦♦ "):
            self.loadFavsPage()
        
    def searchRow(self):

        self.searchFrame = ctk.CTkFrame(self.mainFrame ,corner_radius=3, bg_color="transparent", fg_color="transparent")
        self.searchFrame.grid_columnconfigure(0,weight=7)
        self.searchFrame.grid_columnconfigure(1,weight=0)
        self.searchFrame.grid(row=0, column=0, sticky="nsew")

        # self.search_var = ctk.StringVar()
        self.searchBarEntry = ctk.CTkEntry(self.searchFrame, placeholder_text="Search Computer or Room:", bg_color="transparent",corner_radius=3)
        self.searchBarEntry.grid(row=0, column=0, sticky="new", padx=10, pady=10)
        self.searchBarEntry.bind("<KeyRelease>", self.update_suggestions)

        self.results_frame = ctk.CTkScrollableFrame(self.searchFrame, width=280, height=0)
        self.results_frame.grid(row=1, column=0, sticky="new", padx=10, pady=10)
        self.results_frame.grid_remove()

        self.searchIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "search.png")), size=(20,20))
        self.searchBtn = ctk.CTkButton(self.searchFrame, corner_radius=5, height=40, border_spacing=10, text=" Search",fg_color="transparent", text_color="#34495E", command=self.button_func, image=self.searchIcon ,hover_color=("gray100","gray100"), anchor="nsew", font=ctk.CTkFont(size=20, weight="bold"))
        # self.searchBtn.grid(row=0,column=1,sticky="nsew")

        self.searchDictCreate()



    def searchDictCreate(self):

        self.searchDict = {}
        for ws_name, ws_obj in WorkSpace_dict.items():
            for zone_name, zone_obj in ws_obj.Zones.items():
                new_name = "Zone: " + zone_name + " (in Workspace: " + ws_name +")"
                self.searchDict[new_name] = zone_obj
                for pc_name, pc_obj in zone_obj.computers.items():
                    new_name = "Pc: " +pc_name + " (in Zone:" + zone_name + ")"
                    self.searchDict[new_name] = zone_obj
        

    def update_suggestions(self, event):
        query = self.searchBarEntry.get().lower()
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if query == "":
            self.results_frame.grid_remove()
            return

        matches = [item for item in self.searchDict.keys() if query in item.lower()]

        if matches:
            self.results_frame.grid()
            self.results_frame.configure(height=min(len(matches) * 35, 200))
            for i, match in enumerate(matches):
                # miniIconObj = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, f"LightMode_zone.png")), dark_image=Image.open(os.path.join(images_folder_path, f"DarkMode_zone.png")), size=(20,20))
                miniIconObj = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"DarkMode_zone.png")), size=(20,20))
                if "Pc: " in match:
                    # miniIconObj = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, f"LightMode_pc.png")), dark_image=Image.open(os.path.join(images_folder_path, f"DarkMode_pc.png")), size=(20,20))
                    miniIconObj = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"DarkMode_pc.png")), size=(20,20))
                btn = ctk.CTkButton(self.results_frame, 
                                            text=match, 
                                            fg_color="transparent",
                                            image = miniIconObj,
                                            text_color=("black", "white"),
                                            hover_color=("gray80", "gray30"),
                                            anchor="w",
                                            command=lambda m=match: self.handle_selection(m))
                btn.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
                self.results_frame.grid_columnconfigure(0, weight=1)
        else:
            self.results_frame.grid_remove()

    
    def handle_selection(self, choice):
        self.searchBarEntry.delete(0,"end")
        self.results_frame.grid_remove()
        
        ObjToOpen = self.searchDict.get(choice)
        if ObjToOpen:
            self.zoneDetailsFrame(ObjToOpen)


    def tabsWidgetsFunc(self):

        self.tabsFrame = ctk.CTkFrame(self.mainFrame, corner_radius=3, bg_color="transparent", fg_color="transparent")
        self.tabsFrame.grid_rowconfigure(0,weight=1)
        self.tabsFrame.grid_columnconfigure(0,weight=1)
        self.tabsFrame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)


        self.tabsWidgets = ctk.CTkTabview(self.tabsFrame, width=500 ,fg_color=("gray85","gray25"), segmented_button_fg_color=("gray85","gray25"))
        pagecount = 0 #page = tab == workspace
        self.tab_frames = {} # key = numberPage(Tab) || # val = ws_obj
        for WS_name, WS_obj in WorkSpace_dict.items():
            self.new_created_tab_temp = self.tabsWidgets.add(WS_name)
            self.scorllTheNewTab = ctk.CTkScrollableFrame(self.new_created_tab_temp)
            self.scorllTheNewTab.pack(expand=True, fill="both")
            
            self.tab_frames[pagecount] = {"ws_Object" : WS_obj , "frame" : self.scorllTheNewTab}

            (self.tab_frames[pagecount]["frame"]).grid_columnconfigure(0,weight=1, uniform="helloCol")
            (self.tab_frames[pagecount]["frame"]).grid_columnconfigure(1,weight=1, uniform="helloCol")
            (self.tab_frames[pagecount]["frame"]).grid_columnconfigure(2,weight=1, uniform="helloCol")
            (self.tab_frames[pagecount]["frame"]).grid_columnconfigure(3,weight=1, uniform="helloCol")
            (self.tab_frames[pagecount]["frame"]).grid_columnconfigure(4,weight=1, uniform="helloCol")
            (self.tab_frames[pagecount]["frame"]).grid_rowconfigure(0,weight=1, uniform="helloRow")
            (self.tab_frames[pagecount]["frame"]).grid_rowconfigure(1,weight=1, uniform="helloRow")
            (self.tab_frames[pagecount]["frame"]).grid_rowconfigure(2,weight=1, uniform="helloRow")
            (self.tab_frames[pagecount]["frame"]).grid_rowconfigure(3,weight=1, uniform="helloRow")
            zonecount=0 # how many zones in one workspace=(tab / page)
            listOfZones = WS_obj.get_all_Zones()
            for zone_obj in listOfZones:
                # print(f"page number {zonecount}, = {zone_obj.Zone_name}")
                
                newCard = self.createCard(self.tab_frames[pagecount]["frame"], name=(zone_obj.Zone_name), cardtype="zone", funcToBtn= lambda x=zone_obj : self.zoneDetailsFrame(x))
                newCard.grid(row=int(zonecount/5), column=int(zonecount%5), padx=10, pady=10)
                zonecount+=1
            
            addingNewZoneCard = self.createCard(self.tab_frames[pagecount]["frame"], name=("Add New Zone"), funcToBtn= lambda x= self.tabsFrame , y=WS_obj : self.AddNewZoneFrameMaking(x,y))
            # newZoneRow = (int(zonecount/5) if int(zonecount%5) == 0  else( 2 if int(zonecount%5) <2 else int(zonecount%5) (int(zonecount/5)+1)))
            newZoneRow = 0
            if zonecount % 5 == 0:
                newZoneRow = int(zonecount / 5)
            elif zonecount < 9 or zonecount % 5 < 2:
                newZoneRow = 2
            else:
                newZoneRow = int(zonecount % 5) + int(zonecount / 5)

            print(newZoneRow)
            addingNewZoneCard.grid(row=newZoneRow, column=4, padx=10, pady=10,sticky="s")
            deleteThisWSCard = self.createCard(self.tab_frames[pagecount]["frame"], name=("Delete This\n WorkSpace"), cardtype="DeleteWS", funcToBtn= lambda x= self.tabsFrame , y=WS_obj : self.deleteThisWSFunc(x,y))
            deleteThisWSCard.grid(row=newZoneRow, column=3, padx=10, pady=10,sticky="s")

            pagecount+=1

        self.tab_frames[pagecount] = {"ws_Object" : WorkSpace("Add New WorkSpace") , "frame" : self.tabsWidgets.add("Add New WorkSpace")}
        self.AddNewWorkSpace(frameToChange=self.tab_frames[len(self.tab_frames)-1]["frame"])
        self.tabsWidgets._segmented_button.configure(height=30, width=500, fg_color=("gray85","gray25"))
        self.tabsWidgets._segmented_button.grid(sticky="ew")
        
        self.tabsWidgets.grid(row=0, column=0,padx=10 ,pady=10 , sticky="nsew")
        if self.currFrame is not None:
            self.historyPagesList.append(self.currFrame)
        self.currFrame = self.tabsWidgets
        self.currFrame.grid(row=0, column=0,padx=10 ,pady=10 , sticky="nsew")

    def deleteThisWSFunc(self, my_master, ws_obj):
        self.deleteThisWSFrame = ctk.CTkFrame(my_master, width=500 ,fg_color=("gray85","gray25"))
        self.deleteThisWSFrame.rowconfigure(0, weight=1)
        self.deleteThisWSFrame.rowconfigure(1, weight=1)
        self.deleteThisWSFrame.rowconfigure(2, weight=1)
        self.deleteThisWSFrame.rowconfigure(3, weight=1)
        self.deleteThisWSFrame.columnconfigure(0, weight=1)
        self.deleteThisWSFrame.columnconfigure(1, weight=1)
        self.deleteThisWSFrame.columnconfigure(2, weight=1)
        self.deleteThisWSFrame.columnconfigure(3, weight=1)
        self.deleteThisWSFrame.columnconfigure(4, weight=1)
        self.deleteThisWSFrame.grid(row=0, column=0,padx=10 ,pady=10 , sticky="nsew")

        # self.delWSIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, f"LightMode_DeleteWS.png")), dark_image=Image.open(os.path.join(images_folder_path, f"DarkMode_DeleteWS.png")), size=(40,40))
        self.delWSIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"DarkMode_DeleteWS.png")), size=(40,40))
        
        self.delWSButtonLabel = ctk.CTkButton(self.deleteThisWSFrame, corner_radius=3,  border_spacing=10, compound="left", text=f"Delete '{ws_obj.WorkSpace_name}' ws", fg_color="transparent", image=self.delWSIcon , anchor="center", border_color="black", font=("Helvetica", 18, "bold"), text_color=("white","white"),state="disable")
        self.delWSButtonLabel.grid(row=0, column=1, columnspan=2)


        self.deleteThisWSLabel = ctk.CTkLabel(self.deleteThisWSFrame, text="Please Write DELETE to confirm delete this ws: ", font=("Helvetica", 15, "bold"))
        self.deleteThisWSLabel.grid(row=1, column=1)

        self.deleteThisWSEntry = ctk.CTkEntry(self.deleteThisWSFrame, placeholder_text="Write DELETE to confirm delete this ws. ", width=300 , font=("Helvetica", 15, "bold"))
        self.deleteThisWSEntry.grid(row=1, column=2)

        self.deleteThisWSLabelWARNING = ctk.CTkLabel(self.deleteThisWSFrame, text=" ▲▲▲▲▲  WARNING!!!  ▲▲▲▲▲ \n-------------------\nYou will delete all the zones and computers that are attached to this WS.\nThis action can't be undo.")
        self.deleteThisWSLabelWARNING.configure(font=("Helvetica", 15, "bold"))
        self.deleteThisWSLabelWARNING.grid(row=2, column=1, columnspan=2)

        self.deleteThisWSERRLabel = ctk.CTkLabel(self.deleteThisWSFrame, text=" ")
        self.deleteThisWSERRLabel.grid(row=4, column=1, columnspan=2)

        self.deleteThisWSIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "deleteIcon.png")), size=(40,40))
        self.deleteThisWSBtn = ctk.CTkButton(self.deleteThisWSFrame, compound="left", text=" Confirm delete this WS.",image = self.deleteThisWSIcon, command= lambda x=self.deleteThisWSEntry , y=ws_obj, z=self.deleteThisWSERRLabel : self.deleteThisWSHanleBtnFunc(x,y,z), border_color="black", fg_color=("gray45","gray75"), anchor="center", text_color=("white","black"), font=("Helvetica", 15, "bold"), hover_color=("gray55","gray65"))
        self.deleteThisWSBtn.grid(row=3, column=1, columnspan=2)


    def deleteThisWSHanleBtnFunc(self, confirmEntry, ws_obj_to_del, errLabel):
        flag=False
        if (confirmEntry.get() == "DELETE"):
            for ws_name, ws_obj in WorkSpace_dict.items():
                if (ws_obj == ws_obj_to_del):
                    try:
                        del WorkSpace_dict[ws_name]
                        print("deleted")
                        flag = True
                        for zone_name , zone_obj in ws_obj.Zones.items():
                            if zone_obj in appSettings.favorites.values():
                                appSettings.removeFav(zone_obj)
                                print("Removed from fav.")

                        if appSettings.startHomePage == ws_obj_to_del:
                            appSettings.startHomePage = None
                            print("Startup Page has been deleted.")
                        dm.updateDB(WorkSpace_dict, appSettings)
                        self.homeWidget()
                        return
                    except Exception as e:
                        errLabel.configure(text=f"Exception is: {e}", text_color = "red", font=("Helvetica", 15, "bold"))
                        print(f"Exception is: {e}")
        else:
            print("You have to write 'DELETE' with CapsLock.")
            errLabel.configure(text="You have to write 'DELETE' with CapsLock.", text_color = "red", font=("Helvetica", 15, "bold"), anchor="center")   


    def AddNewWorkSpace(self, frameToChange):
        frameToChange.rowconfigure(0,weight=1)
        frameToChange.rowconfigure(1,weight=1)
        frameToChange.rowconfigure(2,weight=1)
        frameToChange.rowconfigure(3,weight=1)
        frameToChange.rowconfigure(4,weight=1)
        frameToChange.columnconfigure(0,weight=1)
        frameToChange.columnconfigure(1,weight=1)
        frameToChange.columnconfigure(2,weight=1)
        frameToChange.columnconfigure(3,weight=1)
        frameToChange.columnconfigure(4,weight=1)

        # self.plusIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, f"LightMode_AddObject.png")), dark_image=Image.open(os.path.join(images_folder_path, f"DarkMode_AddObject.png")), size=(40,40))
        self.plusIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"DarkMode_AddObject.png")), size=(40,40))
        
        self.plusButtonLabel = ctk.CTkButton(frameToChange, corner_radius=3,  border_spacing=10, compound="left", text=f"Adding new workspace", fg_color="transparent", image=self.plusIcon , anchor="center", border_color="black", font=("Helvetica", 18, "bold"), text_color=("white","white"),state="disable")
        self.plusButtonLabel.grid(row=0, column=0, columnspan=3)

        self.newNameLabel = ctk.CTkLabel(frameToChange, text="Enter name to the new workspace: ",font=("Helvetica", 16, "bold"))
        self.newNameEntry = ctk.CTkEntry(frameToChange, placeholder_text="Enter name to the new Workspace", corner_radius=3, width=330, font=("Helvetica", 16, "bold"))

        self.saveBtn = ctk.CTkButton(frameToChange, text="Create", width=300, command=self.savebtnWS, corner_radius=3)
        
        self.newNameLabel.grid(row=1, column=0 , sticky="e")
        self.newNameEntry.grid(row=1, column=1, columnspan=2)
        self.saveBtn.grid(row=2, column=0, columnspan=3)

    def savebtnWS(self):
        new_WS_name = self.newNameEntry.get()
        if new_WS_name is None:
            print(f"user canclled operation")
            return None
        elif (len(new_WS_name) < 1):
            messagebox.showwarning("Invalid input", "Please write at least one char to WorkSpace")
            return
        if new_WS_name in WorkSpace_dict.keys():
            messagebox.showwarning("Invalid input", "You Already have workspace with this name. Please enter a NEW name.")
            return
        WorkSpace_dict[new_WS_name] = WorkSpace(new_WS_name)
        # self.tabsFrame.grid_remove()
        # self.tabsWidgets.grid_remove()
        dm.updateDB(WorkSpace_dict, appSettings)
        self.showHomePage()
    
    def AddNewZoneFrameMaking(self, my_master, ws_obj):

        self.addNewZoneFrame = ctk.CTkFrame(my_master, width=500 ,fg_color=("gray85","gray25"))
        self.addNewZoneFrame.rowconfigure(0, weight=1)
        self.addNewZoneFrame.rowconfigure(1, weight=1)
        self.addNewZoneFrame.rowconfigure(2, weight=1)
        self.addNewZoneFrame.rowconfigure(3, weight=1)
        self.addNewZoneFrame.columnconfigure(0, weight=1)
        self.addNewZoneFrame.columnconfigure(1, weight=1)
        self.addNewZoneFrame.columnconfigure(2, weight=1)
        self.addNewZoneFrame.columnconfigure(3, weight=1)
        self.addNewZoneFrame.columnconfigure(4, weight=1)
        self.addNewZoneFrame.grid(row=0, column=0,padx=10 ,pady=10 , sticky="nsew")

        # self.plusIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, f"LightMode_AddObject.png")), dark_image=Image.open(os.path.join(images_folder_path, f"DarkMode_AddObject.png")), size=(40,40))
        self.plusIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"DarkMode_AddObject.png")), size=(40,40))
        
        self.plusButtonLabel = ctk.CTkButton(self.addNewZoneFrame, corner_radius=3,  border_spacing=10, compound="left", text=f"Adding new Zone to '{ws_obj.WorkSpace_name}' ws", fg_color="transparent", image=self.plusIcon , anchor="center", border_color="black", font=("Helvetica", 18, "bold"), text_color=("white","white"),state="disable")
        self.plusButtonLabel.grid(row=0, column=1, columnspan=2)


        self.newZonenameLabel = ctk.CTkLabel(self.addNewZoneFrame, text="Enter the Zone(Room) name: ", font=("Helvetica", 15, "bold"))
        self.newZonenameLabel.grid(row=1, column=1)

        self.newZonenameEntry = ctk.CTkEntry(self.addNewZoneFrame, placeholder_text="Enter the Zone(Room) name. ", width=300 , font=("Helvetica", 15, "bold"))
        self.newZonenameEntry.grid(row=1, column=2)

        self.newZonenameERRLabel = ctk.CTkLabel(self.addNewZoneFrame, text=" ")
        self.newZonenameERRLabel.grid(row=3, column=1, columnspan=2)

        self.addToListIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"addToList.png")), size=(40,40))
        self.saveNewZoneBtn = ctk.CTkButton(self.addNewZoneFrame, compound="left", text=" Create New Zone",image = self.addToListIcon, command= lambda x=self.newZonenameEntry , y=ws_obj, z=self.newZonenameERRLabel : self.createNewZoneFunc(x,y,z), border_color="black", fg_color=("gray45","gray75"), anchor="center", text_color=("white","black"), font=("Helvetica", 15, "bold"), hover_color=("gray55","gray65"))
        self.saveNewZoneBtn.grid(row=2, column=1, columnspan=2)



    def createNewZoneFunc(self, newZonenameEntry, ws_obj, errlbl):
        tempZone = None
        zone_name = newZonenameEntry.get()
        if(any(c.isalpha() for c in zone_name)):
            if(zone_name not in ws_obj.Zones.keys() ):
                tempZone = Zone(Zone_name = zone_name)
                ws_obj.addZone(tempZone)
                dm.updateDB(WorkSpace_dict, appSettings)
                self.showHomePage()
            else:
                errlbl.configure(text=f"Already have zone with this name in {ws_obj.WorkSpace_name} ws, please choose a different name.", text_color = "red", font=("Helvetica", 15, "bold") )
                print("Already have zone with this name")
        else:
            errlbl.configure(text="Zone name should be with at least one letter.", text_color = "red", font=("Helvetica", 15, "bold"))
            print("Zone name should be with at least one letter.")

        


        # self.Zone_name = Zone_name
        # self.computers = {}
        # self.isFav = False






    def createCard(self, my_master, name="Empty", cardtype: ["zone","AddObject","DeleteWS"]= "AddObject", funcToBtn = None):
        
        if funcToBtn is None:
            funcToBtn = self.button_func

        self.newCard = ctk.CTkFrame(my_master, corner_radius=5, border_color="gray65", border_width=1, width=135, height=110,fg_color="gray75")
        self.newCard.rowconfigure(0,weight=1)
        # self.newCard.rowconfigure(1,weight=1)
        self.newCard.columnconfigure(0,weight=1)
        
        # self.newIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, f"LightMode_{cardtype}.png")), dark_image=Image.open(os.path.join(images_folder_path, f"DarkMode_{cardtype}.png")), size=(40,40))
        self.newIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"DarkMode_{cardtype}.png")), size=(40,40))
        
        self.newButton = ctk.CTkButton(self.newCard, corner_radius=3,  border_spacing=10, compound="top", text=name, fg_color="transparent", command=funcToBtn , image=self.newIcon , anchor="center", border_color="black", hover_color=("gray85","gray45"), font=ctk.CTkFont(weight="bold"), text_color=("#5C6D78","#424242"))
        self.newButton.grid(row=0, column=0, padx=10, pady=10)

        return self.newCard


    def zoneDetailsFrame(self, zone_obj, master = None):
        if (master is None):
            master = self.tabsFrame
        
        self.ThisZoneFrame = ctk.CTkFrame(master, width=500 ,fg_color=("#BABABA","#474747"))
        self.ThisZoneFrame.grid_columnconfigure(0,weight=1)
        self.ThisZoneFrame.grid_columnconfigure(1,weight=3)
        self.ThisZoneFrame.grid_rowconfigure(0, weight=1)
        self.ThisZoneFrame.grid_rowconfigure(1, weight=0)

        self.pc_Frames = ctk.CTkScrollableFrame(self.ThisZoneFrame, width=220 , height=200)
        computerCount=0
        computersList = zone_obj.get_all_computers()
        
        #Computers scorrlable frame:
        self.checked_Pc_objs = []
        self.checkBoxesZone = []
        self.deleteBoxesZone = []
        for pc_obj in computersList:
            self.pcrow = ctk.CTkFrame(self.pc_Frames, bg_color="transparent")
            self.pcrow.grid(row = computerCount, column=0, padx=0, pady=0, sticky="nesw")
            self.pcCheckBox = ctk.CTkCheckBox(self.pcrow,width=30, height=30, checkbox_width=30, checkbox_height=30, text="", command=lambda x=pc_obj : self.pc_checkBox_selected(x))
            self.pcCheckBox.grid(row = 0, column=0, padx=0, pady=0, sticky="nesw")
            self.checkBoxesZone.append(self.pcCheckBox)
            if pc_obj.isChecked:
                self.checked_Pc_objs.append(pc_obj)
                self.pcCheckBox.select()

            self.newpcCard = self.createPcRow(self.pcrow, name=(pc_obj.pc_name), cardtype="pc", funcToBtn= lambda x= pc_obj, z=zone_obj: self.pc_settings_popUp(x,z), host_name=pc_obj.host_name)
            self.newpcCard.grid(row = 0, column=1, padx=3, pady=3, sticky="nesw")

            self.deletepcRowIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "deleteIcon.png")), size=(30,30)) 
            self.deletepcRowBtn = ctk.CTkButton(self.pcrow, corner_radius=5, width=30, height=30,compound="top", text=" ",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=pc_obj, y=zone_obj, z=self.pcrow, w=self.checked_Pc_objs : self.deleteThisPcRowFromZone(x,y,z,w) , image=self.deletepcRowIcon ,hover_color=("gray70","gray30"), anchor="nesw", font=ctk.CTkFont(size=15, weight="bold"))
            self.deleteBoxesZone.append(self.deletepcRowBtn)
            #self.deletepcRowBtn.grid(row=0, column=3, padx=10, pady=10, sticky="news")
            computerCount+=1
        
        self.addingNewPc = self.createPcRow(self.pc_Frames, name=("Add New Computer"), funcToBtn= lambda x=zone_obj : self.addNewPcToThisZoneHandleFunc(x))
        self.addingNewPc.grid(row=computerCount, column=0, columnspan=2, padx=10, pady=10,sticky="s")
        
        self.pc_Frames.grid(row=0, column=0, padx=10, pady=10, sticky="nesw")

        ## Adding last frame to BackBtn & update self.currFrame
        self.historyPagesList.append(self.currFrame)
        self.currFrame = self.ThisZoneFrame
        
        self.currFrame.grid(row=0, column=0 ,padx=10, pady=10, sticky="nesw")


        #Push And Commit section:

        self.git_Frame = ctk.CTkFrame(self.ThisZoneFrame, width=200 , height=200, fg_color=("gray85","gray15"))
        self.git_Frame.grid_columnconfigure(0,weight=1)
        self.git_Frame.grid_columnconfigure(1,weight=1)
        self.git_Frame.grid_columnconfigure(2,weight=1)
        self.git_Frame.grid_columnconfigure(3,weight=1)
        self.git_Frame.grid_columnconfigure(4,weight=1)
        self.git_Frame.grid_columnconfigure(5,weight=1)
        self.git_Frame.grid_rowconfigure(0, weight=1)
        self.git_Frame.grid_rowconfigure(1, weight=1)
        self.git_Frame.grid_rowconfigure(2, weight=1)
        self.git_Frame.grid_rowconfigure(3, weight=1)
        self.git_Frame.grid_rowconfigure(4, weight=1)
        self.git_Frame.grid_rowconfigure(5, weight=1)
        self.git_Frame.grid(row=0, column=1, padx=10, pady=10, sticky="nesw")

        self.zone_title_Label = ctk.CTkLabel(self.git_Frame, text=f"You are controlling: {zone_obj.Zone_name}", font=ctk.CTkFont(size=20, weight="bold"),text_color="white", bg_color="blue")
        self.zone_title_Label.grid(row=0, column=1, columnspan=4, padx=0, pady=0, sticky="s")
        
        self.markASFavIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"noFavIcon.png")), size=(50,50))
        self.markASFavButton = ctk.CTkButton(self.git_Frame, text="", fg_color="gray35" ,image=self.markASFavIcon, width=50)
        

        self.unmarkFavIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"yesFavIcon.png")), size=(50,50))
        self.unmarkFavButton = ctk.CTkButton(self.git_Frame, text="", fg_color="gray35" ,image=self.unmarkFavIcon, width=50)

        self.markASFavButton.configure(command= lambda x=zone_obj, y=self.markASFavButton, z=self.unmarkFavButton: self.addToFavs(x,y,z))

        self.unmarkFavButton.configure(command= lambda x=zone_obj, y=self.unmarkFavButton ,z=self.markASFavButton: self.removeFromFavs(x,y,z))
        print(f"isFav = {zone_obj.isFav}")
        if(zone_obj.isFav):
            self.unmarkFavButton.grid(row=0, column=5, sticky="sw")
        else:
            self.markASFavButton.grid(row=0, column=5, sticky="sw")
            
        self.editRowFrame = ctk.CTkFrame(self.ThisZoneFrame, height=70)
        self.editRowFrame.grid(row=1, column=0, columnspan=2, sticky="news")


        self.git_title_Label = ctk.CTkLabel(self.git_Frame, text="Please write your commit to update the repo:",font=("Helvetica", 18, "bold"))
        self.git_title_Label.grid(row=1, column=1, columnspan=4, padx=10, pady=10, sticky="s")

        self.git_comment_Textbox = ctk.CTkTextbox(self.git_Frame, width=400, height=100, wrap="word", font=("Helvetica", 18, "bold"))
        self.git_comment_Textbox.grid(row=2, column=1, columnspan=4, padx=10, pady=10, sticky="n")

        self.errMsgPush = ctk.CTkLabel(self.editRowFrame, text="", text_color="red", font=ctk.CTkFont(weight="bold"))
        self.errMsgPush.grid(row=0, column=1, columnspan=3, sticky="news")


        # self.push_n_commit_icon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, "LightMode_PushnCommit.png")), dark_image=Image.open(os.path.join(images_folder_path, "DarkMode_PushnCommit.png")), size=(40,40))
        self.push_n_commit_icon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "DarkMode_PushnCommit.png")), size=(40,40))
        
        self.Push_n_Commit_Btn = ctk.CTkButton(self.git_Frame, corner_radius=5,  border_spacing=10, compound="top", text="Push & Commit", fg_color="gray75", command= lambda x =self.errMsgPush, y = self.git_comment_Textbox: self.push_n_commit_Btn_Func(x,y) , image=self.push_n_commit_icon , anchor="center", border_color="black", hover_color=("gray55","gray45"), font=ctk.CTkFont(weight="bold"), text_color=("#5C6D78","#424242"))
        self.Push_n_Commit_Btn.grid(row=3, column=2, columnspan=2, padx=10, pady=10, sticky="n")

        self.git_progressbar = ctk.CTkProgressBar(self.git_Frame, width=400, height=5)
        #self.git_progressbar.configure(mode="indeterminate")
    

        self.deleteThisZoneLabel = ctk.CTkLabel(self.editRowFrame, text=f"   Please write DELETE (with CapsLock) to confirm delete this zone: " )
        self.deleteThisZoneEntry = ctk.CTkEntry(self.editRowFrame, placeholder_text=f"Write DELETE to confirm. ", width=100)

        self.deleteThisZoneerrLabel = ctk.CTkLabel(self.editRowFrame, text=f" " )

        self.deleteThisZoneIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "deleteIcon.png")), size=(30,30)) 
        self.deleteThisZoneBTN = ctk.CTkButton(self.editRowFrame, corner_radius=3, height=40, border_spacing=10, text=" Delete This Zone",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=zone_obj, y=self.deleteThisZoneEntry, z=self.deleteThisZoneerrLabel : self.deleteThisZoneFunction(x,y,z) , image=self.deleteThisZoneIcon ,hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"))
        
        

        self.DoneEditZoneIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "DoneEdit.png")), size=(30,30))
        self.DoneEditZoneBtn = ctk.CTkButton(self.editRowFrame, corner_radius=3, height=40, border_spacing=10, text="  Done Edit",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=zone_obj, y=master : self.zoneDetailsFrame(x,y) , image=self.DoneEditZoneIcon ,hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"))


        self.EditZoneIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "EditBtn.png")), size=(30,30))
        self.EditZoneBtn = ctk.CTkButton(self.editRowFrame, corner_radius=3, height=40, border_spacing=10, text="  Edit",fg_color="transparent", text_color=("gray10", "gray90") , image=self.EditZoneIcon ,hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"))
        listToShow = [self.DoneEditZoneBtn, self.deleteThisZoneBTN,self.deleteThisZoneLabel,self.deleteThisZoneEntry, self.deleteThisZoneerrLabel]
        self.EditZoneBtn.configure(command=lambda x=self.checkBoxesZone, y=self.deleteBoxesZone, z=listToShow, w=[self.EditZoneBtn] : self.makeThisZoneFrameEditable(x,y,z,w))
        self.EditZoneBtn.grid(row=0, column=0, sticky="news")
        
        print(f"Entered Zone: {zone_obj.Zone_name}. ")



# self.deletepcRowBtn = ctk.CTkButton(self.pcrow, corner_radius=5, width=60, height=40, border_spacing=10,
# text="",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=zone_obj, y=self.pcrow, z=self.checked_Pc_objs : self. , image=deletepcRowIcon
# ,hover_color=("gray70","gray30"), anchor="nesw", font=ctk.CTkFont(size=15, weight="bold"))

    def addNewPcToThisZoneHandleFunc(self, zone_obj):
        pc_count = zone_obj.get_computer_count()
        temp_pc = Computer(pc_name = f"NewPC{pc_count+1} ☼")
        zone_obj.addComputer(temp_pc)
        dm.updateDB(WorkSpace_dict, appSettings)
        self.zoneDetailsFrame(zone_obj)

    def deleteThisPcRowFromZone(self, pc_obj, zone_obj, rowToHide, checked_Pc_objs):
        flag=False
        try:
            zone_obj.removeComputer(pc_obj)
            flag = True
            rowToHide.grid_forget()
            if pc_obj in checked_Pc_objs:
                checked_Pc_objs.remove(pc_obj)
            dm.updateDB(WorkSpace_dict, appSettings)

        except Exception as e:
            print(f"Exception is: {e}.")
        

        #   self.checked_Pc_objs = []
        # self.checkBoxesZone = {}
        # self.deleteBoxesZone = {}  
        
    def makeThisZoneFrameEditable(self, checkBoxesZone, deleteBoxesZone, btnsToShow, btnsToHide):
        for checkBox in checkBoxesZone:
            checkBox.grid_forget()

        for deleteBox in deleteBoxesZone:
            deleteBox.grid(row=0, column=0, padx=0, pady=0, sticky="nesw")
        for btnToHide in btnsToHide:
            btnToHide.grid_forget()

        for i, btnToShow in enumerate(btnsToShow):
            btnToShow.grid(row=int(i/4), column=int(i%4), columnspan=int(i/4)+1,padx=0, pady=0, sticky="nesw")

       



    def deleteThisZoneFunction(self, zone_obj, confirmEntry, errLabel):
        flag=False
        if (confirmEntry.get() == "DELETE"):
            for ws_name, ws_obj in WorkSpace_dict.items():
                if (zone_obj.Zone_name in ws_obj.Zones.keys()):
                    foundzone = ws_obj.Zones[zone_obj.Zone_name]
                    if (foundzone == zone_obj):
                        try:
                            ws_obj.removeZone(zone_obj)
                            print("deleted")
                            flag = True
                            if zone_obj in appSettings.favorites.values():
                                appSettings.removeFav(zone_obj)
                                print("Removed from fav.")
                            if appSettings.startHomePage == zone_obj:
                                appSettings.startHomePage = None
                                print("Startup Page has been deleted.")
                            dm.updateDB(WorkSpace_dict, appSettings)
                            self.homeWidget()
                        except Exception as e:
                            errLabel.configure(text=f"Exception is: {e}", text_color = "red", font=("Helvetica", 15, "bold"))
                            print(f"Exception is: {e}")
        else:
            print("You have to write 'DELETE' with CapsLock.")
            errLabel.configure(text="You have to write 'DELETE' with CapsLock.", text_color = "red", font=("Helvetica", 15, "bold"), anchor="center")        




    def addToFavs(self, zone, currBtn ,otherBtn):
        print("Adding this zone to favs.")
        try:
            appSettings.addFav(zone)
            zone.isFav = True
            dm.updateDB(WorkSpace_dict, appSettings)
        except Exception as e:
            print(f"cant add zone to favs: {e}")
        finally:
            currBtn.grid_forget()
            otherBtn.grid(row=0, column=5, sticky="sw")




    def removeFromFavs(self, zone, currBtn ,otherBtn):
        print("Removing this zone from favs.")
        try:
            appSettings.removeFav(zone)
            zone.isFav = False
            dm.updateDB(WorkSpace_dict, appSettings)
        except Exception as e:
            print(f"cant remove zone from favs: {e}")
        finally:
            currBtn.grid_forget()
            otherBtn.grid(row=0, column=5, sticky="sw")




    def createPcRow(self, my_master, name="Empty", cardtype: ["pc","AddObject"] = "AddObject", funcToBtn = None, host_name = ""):
        if funcToBtn is None:
            funcToBtn = self.button_func
        res = False
        self.newCard = ctk.CTkFrame(my_master, corner_radius=5, border_color="gray65", border_width=1, width=135, height=110,fg_color="gray75")
        self.newCard.rowconfigure(0,weight=1)
        # self.newCard.rowconfigure(1,weight=1)
        self.newCard.columnconfigure(0,weight=1)
        self.newCard.columnconfigure(1,weight=0)
        
        # self.newIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, f"LightMode_{cardtype}.png")), dark_image=Image.open(os.path.join(images_folder_path, f"DarkMode_{cardtype}.png")), size=(40,40))
        self.newIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"DarkMode_{cardtype}.png")), size=(40,40))
        if(host_name != "" and cardtype == "pc"):
            res = self.checkPingStatus(host_name)
            if (res):
                self.greenIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"greenWifi.png")), size=(30,30))
                self.greenButton = ctk.CTkButton(self.newCard, text="", fg_color="transparent",image=self.greenIcon, state="disable", width=10)
                self.greenButton.grid(row=0, column=1, sticky="w")

            else:
                self.redIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"redWifi.png")), size=(30,30))
                self.redButton = ctk.CTkButton(self.newCard, text="", fg_color="transparent", image=self.redIcon, state="disable", width=10)
                self.redButton.grid(row=0, column=1, sticky="w")
        
        
        self.newButton = ctk.CTkButton(self.newCard, corner_radius=3,  border_spacing=10, compound="left", text=name, fg_color="transparent", command=funcToBtn , image=self.newIcon , anchor="center", border_color="black", hover_color=("gray85","gray45"), font=ctk.CTkFont(weight="bold"), text_color=("#5C6D78","#424242"))
        self.newButton.grid(row=0, column=0, padx=0, pady=10)

        return self.newCard


    def checkPingStatus(self, host_name, count = 1):
        if (host_name=="null" or host_name==""):
            return False
        print("pinging..")
        command = f"ping -n 1 -w 3 {host_name}"
        try:
            result = subprocess.run(command, capture_output = True, text=True, timeout=1, shell=True)
            output = result.stdout
            print(f"look at this: {output}")
            if not output:
                return False

            if "Reply from" in output or "TTL=" in output or "time<" in output:
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Err with ping: {e}")
            return False     


    def showHomePage(self):
        self.tabsWidgetsFunc()

    def pc_checkBox_selected(self, pc_obj):
        if(pc_obj in self.checked_Pc_objs):
            self.checked_Pc_objs.remove(pc_obj)
            pc_obj.isChecked = False
        else:
            self.checked_Pc_objs.append(pc_obj)
            pc_obj.isChecked = True

        dm.updateDB(WorkSpace_dict, appSettings)


    # def updateLabelWithColor(self, Label, msg, color = "red"){
    #     label.configure(text= " ")
    # }

    def push_n_commit_Btn_Func(self, errMsgLabel, commit_box):
        def handle_error(text = " ", ssh_client = None):
            if ssh_client:
                ssh_client.close()
            messagebox.showwarning("Invalid input", text)
            errMsgLabel.configure(text=text, text_color="red")
            print(text)
            self.git_progressbar.stop()
            self.git_progressbar.configure(mode="determinate")
            self.git_progressbar.set(0)
            commit_box.configure(state='normal')
            commit_box.delete("0.0","end")
            return
        errMsgLabel.configure(text=" ", text_color="red")

        # self.git_progressbar.grid(row=4, column=2, columnspan=2, padx=10, pady=10, sticky="n")        
        if len(self.checked_Pc_objs) < 1:
            handle_error(text="You should select at least one PC.")
            return

        commit_msg = commit_box.get(0.0,"end")
        if  not bool(re.search(r'[a-zA-Z]', commit_msg)):
            handle_error(text="You should write a commit to push.")
            # self.git_progressbar.stop()
            # self.git_progressbar.configure(mode="determinate")
            # self.git_progressbar.set(0)
            return
        currstatpopup = StatusPopup(self, "Updates: ", "Starting...")
        
#----------------------------------------------------
        #first Count loop:
        print("first Count loop")
        currstatpopup.update_status("Counting how many Files/Folders needs to be copy", 0.1)
        firstCount = 0
        self.reposPaths = {}
        isMoreThanOneRepo = False
        allrepos_Sets = set()
        for pc in self.checked_Pc_objs:
            thispcRepos_Set = set()
            for pathToDo in (pc.pathFiles.values()):
                ssh_client = None
                try:
                    
                    ssh_client = self.create_ssh_connection(pc.host_name, pc.user_name, pc.password)
                    if ssh_client:
                        print("Connection test successful")
                        input_folder=repr(pathToDo['inputfolder'])[1:-1]
                        output_dir=repr(pathToDo['OutputDir'])[1:-1]
                        print(f"inputfolder == {input_folder}\n outputdir == {output_dir}")
                        firstCount+= self.count_only_files(ssh_client, input_folder, file_type=pathToDo['FileType'])
                        currstatpopup.update_status(f"found {firstCount} files/folders", 0.15)
                        try:
                            currRepo = self.find_nearest_git_root_remote(ssh_client, output_dir)
                            if (currRepo is not None):
                                allrepos_Sets.add(currRepo)
                                thispcRepos_Set.add(currRepo)
                                ###ONLY FOR DEBUGGING:::
                                # print(f"found this repo: {currRepo}")
                                

                            else:
                                handle_error(f"couldn't find repo?? (NO Exception)", ssh_client)
                                return
                        except Exception as e:
                            handle_error(f"couldn't find repo?? : {e}" , ssh_client)
                            return

                    else:
                            handle_error(f"failed to connect to the pc: {pc.pc_name}",ssh_client)
                            return

                except Exception as e:
                    handle_error(f"{e}",ssh_client)
                    return
                finally:
                    if ssh_client:
                        ssh_client.close()

                        
            if len(thispcRepos_Set) > 0:
                self.reposPaths[pc] = thispcRepos_Set

        if firstCount == 0:
            currstatpopup.update_status("No such files found to copy, please check if you already copied your data.", 0.2)
            handle_error("No such files found to copy, please check if you already copied your data.")


        currstatpopup.update_status(f"found {firstCount} files/folders to copy.", 0.2)
        #self.git_progressbar.start()
        commit_box.configure(state='disabled')


        # -----------------------------------------------------------------
        # Fetch and pull first:
        currstatpopup.update_status(f"Fetch and pull first to update.", 0.25)
        for pc, repo_set in self.reposPaths.items():
                for repo_path in repo_set:
                    try:
                        ssh_client = self.create_ssh_connection(pc.host_name, pc.user_name, pc.password)
                        branch_name = self.get_current_branch_remote(ssh_client, repo_path)
                        print(f"branch_name found to fetch and pull: {branch_name}")
                        currstatpopup.update_status(f"Fetch and pull first to update\n you currect in branch name = {branch_name}", 0.25)                                             
                        pulled = self.remote_fetch_and_pull(ssh_client, repo_path, branch_name)
                        
                        if pulled:
                            print(f"Fetched and Pulled")
                            currstatpopup.update_status(f"Fetched and Pulled in branch name = {branch_name}", 0.3) 
                        else:
                            print(f"err while trying to pull ? (or nothing to pull)")
                            handle_error(f"err while trying to pull ? (or nothing to pull)")
                            currstatpopup.update_status(f"err while trying to pull ? (or nothing to pull) in branch name = {branch_name}", 0.3)


                        ssh_client.close()
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        handle_error(f"An error occurred: {e}")
                        errMsgLabel.configure(text=f"An error occurred: {e}")
                        commit_box.configure(state='normal')
                        self.git_progressbar.stop()
                        self.git_progressbar.configure(mode="determinate")
                        self.git_progressbar.set(0)
        


        #----------------------------------------------------
        #copy files loop: (after we validate that at least 1 file to copy)
        # self.reposPaths = {}
        # isMoreThanOneRepo = False
        # allrepos_Sets = set()
        currstatpopup.update_status(f"starting copy files", 0.35)
        count = 0
        for pc in self.checked_Pc_objs:
            # thispcRepos_Set = set()
            for pathToDo in (pc.pathFiles.values()):
                try:
                    inputdir =repr(pathToDo['inputfolder'])[1:-1]
                    output_dir=repr(pathToDo['OutputDir'])[1:-1]
                    if(firstCount):
                        currstatpopup.update_status(f"starting copy files\n From = {inputdir}\n To = {output_dir} ", 0.35+(count/firstCount)*0.5)
                    else:
                        currstatpopup.update_status(f"starting copy files\n From = {inputdir}\n To = {output_dir} ", 0.85)
                    try:
                        ssh_client = self.create_ssh_connection(pc.host_name, pc.user_name, pc.password)
                        if ssh_client:
                            print("Connection test successful")
                            count+= self.copy_files_by_type(ssh_client, source_folder=inputdir, file_type=pathToDo['FileType'], destination_folder=output_dir)
                            # self.git_progressbar.set((count/firstCount)*0.5)
                            
                        else:
                            handle_error(f"failed to connect to the pc: {pc.pc_name}", ssh_client)
                            
                    except Exception as e:
                        handle_error(f"{e}", ssh_client)
                    
                        
                except Exception as e:
                    handle_error(f"Copied {count} / {firstCount} files until ---> {e}", ssh_client)
                    currstatpopup.update_status(f"Copied {count} / {firstCount} files until ---> {e}", 0.35)

                finally:
                    if ssh_client:
                        ssh_client.close()
            
        
        if (len(allrepos_Sets) > 1):
            currstatpopup.close_with_delay(delay=1)
            handle_error("Please check your gits folder' you have to pick only one to commit.")
            self.repoWarningPopup(self.reposPaths)

            return 0

        else:
            if (count < 1) or (len(self.reposPaths) < 1):
                handle_error(text="You have to configure 'destination file path' inside a git folder to commit & push.")
                errMsgLabel.configure(text="You have to configure 'destination file path' inside a git folder to commit & push.")
                commit_box.configure(state='normal')
                self.git_progressbar.stop()
                self.git_progressbar.configure(mode="determinate")
                self.git_progressbar.set(0)
                return
            currstatpopup.update_status(f"Checking the changes to push and commit", 0.85)
            for pc, repo_set in self.reposPaths.items():
                for repo_path in repo_set:
                    ssh_client = None
                    try:
                        ssh_client = self.create_ssh_connection(pc.host_name, pc.user_name, pc.password)
                        
                        is_dirty , self.diffsToAdd = self.check_repo_status_remote(ssh_client,repo_path)
                        
                        current_branch = self.get_current_branch_remote(ssh_client, repo_path)
                        print(f"curr_branch is: = {current_branch}")
                        
                        if current_branch is None:
                            return
                        
                        if (is_dirty):
                            errMsgLabel.configure(text=" ")
                            self.WantToContinue = False
                            popup_window = self.gitShowUnstaggedFiles(self.diffsToAdd, errMsgLabel)
                            self.wait_window(popup_window)
                            if (self.WantToContinue is None) or (self.WantToContinue is not True):

                                errMsgLabel.configure(text="User cancelled operation")
                                commit_box.configure(state='normal')
                                self.git_progressbar.stop()
                                self.git_progressbar.configure(mode="determinate")
                                self.git_progressbar.set(0)
                                return
                            else:
                                currstatpopup.update_status(f"Pushing & Commit Please wait", 0.9)
                                errMsgLabel.configure(text="Pushing & Commit Please wait")
                                try:
                                    posted = self.commit_and_push_remote(ssh_client, repo_path, current_branch, commit_msg)
                                
                                    if posted:
                                        self.git_progressbar.stop()
                                        self.git_progressbar.configure(mode="determinate")
                                        self.git_progressbar.set(100)
                                        currstatpopup.update_status(f"Successfull", 1.0)
                                        errMsgLabel.configure(text="Successfull", text_color="green")
                                        commit_box.configure(state='normal')
                                        commit_box.delete("0.0", "end")
                                        currstatpopup.close_with_delay()
                                    else:
                                        print("Didnt pushed. posted = False.")
                                except Exception as e:
                                    print(f"err??? -> {e}")
                                    errMsgLabel.configure(text=f"err??? -> {e}")
                                    commit_box.configure(state='normal')
                                    self.git_progressbar.stop()
                                    self.git_progressbar.configure(mode="determinate")
                                    self.git_progressbar.set(0)
                                    return
                        else:
                            currstatpopup.update_status(f"No changes to commit.", 0.9)
                            errMsgLabel.configure(text="No changes to commit.", text_color="red")
                            currstatpopup.close_with_delay()
                            commit_box.configure(state='normal')
                            self.git_progressbar.stop()
                            self.git_progressbar.configure(mode="determinate")
                            self.git_progressbar.set(0)
                        ssh_client.close()
                    except Exception as e:
                        print(f"An error occurred hereee line 575: {e}")
                        errMsgLabel.configure(text=f"An error occurred: {e}")
                        commit_box.configure(state='normal')
                        self.git_progressbar.stop()
                        self.git_progressbar.configure(mode="determinate")
                        self.git_progressbar.set(0)
                    finally:
                        if ssh_client:
                            ssh_client.close()
                        try:
                            currstatpopup.close_with_delay()
                        except Excepetion as e:
                            print(e)

            return count


    def check_repo_status_remote(self, ssh_client: paramiko.SSHClient, repo_path: str):
        OUTPUT_LIMIT = 100
        escaped_path = repo_path.replace("'", "''")
        
        powershell_command = (
        f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        f"\"Set-Location -Path '{escaped_path}'; "
        f"git status --porcelain\""
        )
        
        stdin, stdout, stderr = ssh_client.exec_command(powershell_command)
        status_output = stdout.read().decode('utf-8').strip()
        is_dirty = bool(status_output)
        # count_command = f'Set-Location -Path "{escaped_path}" ; git status --porcelain | wc -l'
        # stdin, stdout, stderr = ssh_client.exec_command(count_command)
        
        # count_output = stdout.read().decode('utf-8').strip()

        all_changes_by_path = {}

        if not is_dirty:
            return False, all_changes_by_path

        changes_as_lines = status_output.strip().splitlines()
        for line in changes_as_lines:
            splittedLine = line.split(maxsplit=1)
            if len(splittedLine) >= 2:
                    change_type = splittedLine[0]
                    if(change_type.upper() == 'M'):
                        change_type = "Modified"
                    elif(change_type.upper() == '??'):
                        change_type = "New"
                    elif(change_type.upper() == 'U'):
                        change_type = "Untracked (New)"
                    elif(change_type.upper() == 'D'):
                        change_type = "Deleted"

            all_changes_by_path[splittedLine[1]] = {
                        'file': splittedLine[1], 
                        'type': change_type, 
                    }

        return True, all_changes_by_path

    
    def get_current_branch_remote(self, ssh_client: paramiko.SSHClient, repo_path: str):
        escaped_path = repo_path.replace("'", "''")
        
        powershell_command = (
            f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"Set-Location -Path '{escaped_path}'; "
            f"git rev-parse --abbrev-ref HEAD\""
        )
        
        stdin, stdout, stderr = ssh_client.exec_command(powershell_command)
        
        error_output = stderr.read().decode('utf-8').strip()
        if error_output:
            print(f"error_output = {error_output}")
            return None
            
        branch_name = stdout.read().decode('utf-8').strip()
        return branch_name


    def remote_fetch_and_pull(self, ssh_client, repo_path, branch_name):
        print(f"DEBUG: Starting remote_fetch_and_pull for branch: {branch_name} in path: {repo_path}")
        escaped_path = repo_path.replace("/", "\\").replace("'", "''")
        
        fetch_command = (
            f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"Set-Location -Path '{escaped_path}'; git fetch --all\""
        )
        print(f"DEBUG: Executing fetch command: {fetch_command}")
        
        stdin, stdout, stderr = ssh_client.exec_command(fetch_command)
        fetch_errors = stderr.read().decode('utf-8').strip()
        fetch_output = stdout.read().decode('utf-8').strip()
        
        print(f"DEBUG: Fetch Output (stdout): {fetch_output}")
        print(f"DEBUG: Fetch Errors (stderr): {fetch_errors}")

        if fetch_errors and any(keyword in fetch_errors.lower() for keyword in ["fatal", "error", "failed", "permission denied"]):
            raise Exception(f"Git Fetch failed: {fetch_errors}")

        pull_command = (
            f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"Set-Location -Path '{escaped_path}'; git pull origin {branch_name}\""
        )
        print(f"DEBUG: Executing explicit pull command: {pull_command}")
        
        stdin, stdout, stderr = ssh_client.exec_command(pull_command)
        pull_output = stdout.read().decode('utf-8').strip()
        pull_errors = stderr.read().decode('utf-8').strip()
        
        print(f"DEBUG: Pull Output (stdout): {pull_output}")
        print(f"DEBUG: Pull Errors (stderr): {pull_errors}")

        if pull_errors and any(keyword in pull_errors.lower() for keyword in ["fatal", "error", "failed", "permission denied"]):
            raise Exception(f"Git Pull failed: {pull_errors}")
            
        if "conflict" in pull_output.lower():
            print("DEBUG: WARNING: Merge conflict detected!")
            return False
            
        print(f"DEBUG: Fetch and Pull completed successfully for branch: {branch_name}")
        return True

        # escaped_path = repo_path.replace("'", "''")
        
        # fetch_command = f'Set-Location -Path "{escaped_path}" ; git fetch --all'
        # try:
        #     stdin, stdout, stderr = ssh_client.exec_command(fetch_command)
        #     fetch_errors = stderr.read().decode('utf-8').strip()
        #     if fetch_errors:
        #         return False
        # except Exception as e:
        #     raise Exception (f"expection= {e}")

        # pull_command = f'Set-Location -Path "{escaped_path}" ; git pull'
        # try:
        #     stdin, stdout, stderr = ssh_client.exec_command(pull_command)
        #     pull_output = stdout.read().decode('utf-8').strip()
        #     pull_errors = stderr.read().decode('utf-8').strip()
        # except Exception as e:
        #     raise Exception (f"expection= {e}")

        # if pull_errors:
        #     return False
            
        # if "conflict" in pull_output.lower():
        #     return False
        # return True


    def commit_and_push_remote(self, ssh_client: paramiko.SSHClient, repo_path: str, branch_name: str, commit_message: str):
        print(f"Now we are trying to commit with folder: {repo_path}")
        escaped_path = repo_path.replace("'", "''")

        clean_message = commit_message.strip().replace('\n', ' ').replace('\r',' ')
        escaped_message = clean_message.replace('"', '\"')
        
        powershell_command = (
        f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        f"\"Set-Location -Path '{escaped_path}'; "
        f"git add --all; "
        f"if (git status --porcelain) {{ git commit -m '{escaped_message}' }}; "
        f"git push origin {branch_name}\""
        )
        
        print(f"DEBUG: Executing command: {powershell_command}")
    
        stdin, stdout, stderr = ssh_client.exec_command(powershell_command)
        
        stderr_output = stderr.read().decode('utf-8').strip()

        if (stderr_output) and (f'{branch_name} -> {branch_name}' in stderr_output) and ('To http' in stderr_output):
            # print(f"Pushed and commit = {stderr_output}")
            return True

        else:
            print(f"probally failed: {stderr_output}")
            return False
        
        print(f"Please check if successed. - output is empty")
        return True

    def repoWarningPopup(self, repoPaths):
        repoWarningPopupToplevel = ctk.CTkToplevel(self)
        repoWarningPopupToplevel.geometry("300x600")
        repoWarningPopupToplevel.title("Repo Warning")
        repoWarningPopupToplevel.attributes("-topmost", True)
        repoWarningPopupToplevel.after(100, repoWarningPopupToplevel.lift)
        repoWarningPopupToplevel.after(100, repoWarningPopupToplevel.focus_set)

        repoWarningPopupToplevel.grab_set()

        repoWarningPopupToplevel.grid_rowconfigure(0,weight=1)
        repoWarningPopupToplevel.grid_rowconfigure(1,weight=1)
        repoWarningPopupToplevel.grid_rowconfigure(2,weight=1)
        repoWarningPopupToplevel.grid_rowconfigure(3,weight=1)
        repoWarningPopupToplevel.grid_columnconfigure(0, weight=1)

        repolabelwarning = ctk.CTkLabel(repoWarningPopupToplevel, text="Warning!!\n You selected to copy files to more than one repo folder.")
        repolabelwarning.grid(row=0, column=0, padx=10, pady=10, sticky="news")
        
        #Table:
        reposTable = ctk.CTkScrollableFrame(repoWarningPopupToplevel)
        reposTable.grid_columnconfigure(0, weight=1)

        for index, (pc_key, pc_repos_set) in enumerate(repoPaths.items()):
            text_label = f"{pc_key.pc_name}: "
            for i, repo_val in enumerate(pc_repos_set):
                text_label += f"\n {i+1}. {repo_val}"
            addThisText = ctk.CTkLabel(reposTable, text= text_label, wraplength=170)
            addThisText.grid(row=index, column=0, padx=10, pady=10, sticky="news")
        reposTable.grid(row=1, column=0, padx=10, pady=10, sticky="news")

        repolabelwarningSecond = ctk.CTkLabel(repoWarningPopupToplevel, text="Please fix the problem and try to commit again.")
        repolabelwarningSecond.grid(row=2, column=0, padx=10, pady=10, sticky="news")


        fixIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"fixIcon.png")), size=(60,60))
        fixBtn = ctk.CTkButton(repoWarningPopupToplevel, corner_radius=3, height=40, border_spacing=10, text="  Add More Path",fg_color="transparent", text_color=("gray10", "gray90"), command= repoWarningPopupToplevel.destroy , image=fixIcon ,hover_color=("gray70","gray30"), font=ctk.CTkFont(size=15, weight="bold"))


        #Needs to show all unstaged files and select the diffs to commit

        
    def gitShowUnstaggedFiles(self, diffsToAdd, errMsgLabel):

        repoWarningPopupToplevel = ctk.CTkToplevel(self)
        repoWarningPopupToplevel.geometry("600x800")
        repoWarningPopupToplevel.title("Unstaged Files")
        repoWarningPopupToplevel.attributes("-topmost", True)
        repoWarningPopupToplevel.after(100, repoWarningPopupToplevel.lift)
        repoWarningPopupToplevel.after(100, repoWarningPopupToplevel.focus_set)

        repoWarningPopupToplevel.grab_set()

        repoWarningPopupToplevel.grid_rowconfigure(0,weight=1)
        repoWarningPopupToplevel.grid_rowconfigure(1,weight=1)
        repoWarningPopupToplevel.grid_rowconfigure(2,weight=1)
        repoWarningPopupToplevel.grid_rowconfigure(3,weight=1)
        repoWarningPopupToplevel.grid_columnconfigure(0, weight=1)


        repolabelwarning = ctk.CTkLabel(repoWarningPopupToplevel, text="Please make sure you want to commit this files before you continue:\n Note - You can see up to 100 files.")
        repolabelwarning.grid(row=0, column=0, padx=10, pady=10, sticky="news")
        
        
        #Table:
        diffFilesTable = ctk.CTkScrollableFrame(repoWarningPopupToplevel)
        diffFilesTable.grid_columnconfigure(0, weight=1)

        for count, (fileName, fileDict) in enumerate(diffsToAdd.items()):
            text_label = f"{count}: {fileDict['file']}, with Status: {fileDict['type']}"
            addThisText = ctk.CTkLabel(diffFilesTable, text= text_label, wraplength=700)
            addThisText.grid(row=count, column=0, padx=10, pady=10, sticky="news")
        diffFilesTable.grid(row=1, column=0, padx=10, pady=10, sticky="news")

        repolabelwarningSecond = ctk.CTkLabel(repoWarningPopupToplevel, text=" Please confirm to commit & Push.")
        repolabelwarningSecond.grid(row=2, column=0, padx=10, pady=10, sticky="news")

        btnRowFrame = ctk.CTkFrame(repoWarningPopupToplevel)
        btnRowFrame.grid_rowconfigure(1,weight=0)
        btnRowFrame.grid_columnconfigure(0, weight=1)
        btnRowFrame.grid_columnconfigure(1, weight=1)
        btnRowFrame.grid(row=3, column=0, padx=10, pady=10, sticky="news")

        CancelIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "CancelBtn.png")), size=(30,30))
        CancelBtn = ctk.CTkButton(btnRowFrame, corner_radius=3, height=40, border_spacing=10, compound="top", text="  Cancel", fg_color="transparent", text_color=("gray10", "gray90"), command=repoWarningPopupToplevel.destroy , image=CancelIcon, hover_color=("gray70","gray30"), anchor="center", font=ctk.CTkFont(size=15, weight="bold"), )
        CancelBtn.grid(row=0, column=0, padx=10, pady=10, sticky="news")

        # push_n_commit_icon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, "LightMode_PushnCommit.png")), dark_image=Image.open(os.path.join(images_folder_path, "DarkMode_PushnCommit.png")), size=(40,40))
        push_n_commit_icon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "DarkMode_PushnCommit.png")), size=(40,40))
        Push_n_Commit_Btn = ctk.CTkButton(btnRowFrame, corner_radius=5,  border_spacing=10, compound="top", text="Push & Commit", fg_color="gray75", command=lambda x=repoWarningPopupToplevel, y= errMsgLabel : self.confirmTheCommit(x,y)  , image=self.push_n_commit_icon , anchor="center", border_color="black", hover_color=("gray85","gray45"), font=ctk.CTkFont(weight="bold"), text_color=("#5C6D78","#424242"))
        Push_n_Commit_Btn.grid(row=0, column=1, padx=10, pady=10, sticky="news")

        return repoWarningPopupToplevel

    def confirmTheCommit(self, repoWarningPopupToplevel, errMsgLabel):
        errMsgLabel.configure(text="Pushing & Commit Please wait")
        print("Pushing & Commit Please wait")
        self.WantToContinue = True
        repoWarningPopupToplevel.destroy()
            

        




        











        


    def pc_settings_popUp(self, pc_obj, zone_obj):
        
        popup = ctk.CTkToplevel(self)
        popup.geometry("800x880")
        popup.title(f"Manage {pc_obj.pc_name}")
        popup.attributes("-topmost", True)
        popup.after(100, popup.lift)
        popup.after(100, popup.focus_set)

        popup.grab_set()


        popup.grid_rowconfigure(0,weight=0)
        popup.grid_rowconfigure(1,weight=0)
        popup.grid_rowconfigure(2,weight=0)
        popup.grid_rowconfigure(3,weight=0)
        popup.grid_rowconfigure(4,weight=0)
        popup.grid_rowconfigure(5,weight=0)
        # popup.grid_rowconfigure(6,weight=0)
        # popup.grid_rowconfigure(7,weight=0)
        # popup.grid_rowconfigure(8,weight=0)
        popup.grid_columnconfigure(0,weight=1)
        popup.grid_columnconfigure(1,weight=1)
        popup.grid_columnconfigure(2,weight=1)
        popup.grid_columnconfigure(3,weight=1)
        popup.grid_columnconfigure(4,weight=1)
        popup.grid_columnconfigure(5,weight=1)

        # pcIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, f"LightMode_pc.png")), dark_image=Image.open(os.path.join(images_folder_path, f"DarkMode_pc.png")), size=(60,60))
        pcIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"DarkMode_pc.png")), size=(60,60))
        pcIconLabel = ctk.CTkLabel(popup, text="", compound="center", image=pcIcon)
        pcIconLabel.grid(row=0, column=2, columnspan=2, padx=10, pady=10, sticky="news")


        pcnameRow = ctk.CTkFrame(popup)
        pcnameRow.grid_rowconfigure(0,weight=1)
        pcnameRow.grid_columnconfigure(0,weight=1)
        
        pcnamelabel = ctk.CTkLabel(pcnameRow, text="PC Name: ",font=ctk.CTkFont(size=17, weight="bold"))
        pcnamelabel.grid(row=0, column=0, padx=10, pady=10, sticky="news")
        self.pcnameEntry = ctk.CTkEntry(pcnameRow, width=150)
        oldpcname = pc_obj.pc_name
        self.pcnameEntry.insert(0, oldpcname)
        self.pcnameEntry.configure(state="disabled")
        self.pcnameEntry.grid(row=0, column=1, padx=10, pady=10, sticky="news")

        pcnameRow.grid(row=1, column=2, columnspan=2, padx=10, pady=10, sticky="news")


        hostnameRow = ctk.CTkFrame(popup)
        hostnameRow.grid_rowconfigure(0,weight=1)
        hostnameRow.grid_columnconfigure(0,weight=1)

        hostnamelabel = ctk.CTkLabel(hostnameRow, text="HostName (or ip address): ",font=ctk.CTkFont(size=17, weight="bold"))
        hostnamelabel.grid(row=0, column=0, padx=10, pady=10, sticky="news")
        self.hostnameEntry = ctk.CTkEntry(hostnameRow, width=150)
        self.hostnameEntry.insert(0, pc_obj.host_name)
        self.hostnameEntry.configure(state="disabled")
        self.hostnameEntry.grid(row=0, column=1, padx=10, pady=10, sticky="news")

        hostnameRow.grid(row=2, column=2, columnspan=2, padx=10, pady=10, sticky="news")

        # self.user_name = user_name
        user_nameRow = ctk.CTkFrame(popup)
        user_nameRow.grid_rowconfigure(0,weight=1)
        user_nameRow.grid_columnconfigure(0,weight=1)

        user_namelabel = ctk.CTkLabel(user_nameRow, text="user_name (full with domain): ",font=ctk.CTkFont(size=17, weight="bold"))
        user_namelabel.grid(row=0, column=0, padx=10, pady=10, sticky="news")
        self.user_nameEntry = ctk.CTkEntry(user_nameRow, width=150)
        self.user_nameEntry.insert(0, pc_obj.user_name)
        self.user_nameEntry.configure(state="disabled")
        self.user_nameEntry.grid(row=0, column=1, padx=10, pady=10, sticky="news")

        user_nameRow.grid(row=3, column=2, columnspan=2, padx=10, pady=10, sticky="news")

        # self.password = password
        passwordRow = ctk.CTkFrame(popup)
        passwordRow.grid_rowconfigure(0,weight=1)
        passwordRow.grid_columnconfigure(0,weight=1)

        passwordlabel = ctk.CTkLabel(passwordRow, text="password: ",font=ctk.CTkFont(size=17, weight="bold"))
        passwordlabel.grid(row=0, column=0, padx=10, pady=10, sticky="news")
        self.passwordEntry = ctk.CTkEntry(passwordRow, width=150)
        self.passwordEntry.insert(0, pc_obj.password)
        self.passwordEntry.configure(state="disabled")
        self.passwordEntry.grid(row=0, column=1, padx=10, pady=10, sticky="news")

        passwordRow.grid(row=4, column=2, columnspan=2, padx=10, pady=10, sticky="news")
        
        #Frame for the path table:
        pathfilesMainTableFrame = ctk.CTkFrame(popup, border_width=1, border_color=("black","white"))
        pathfilesMainTableFrame.grid_rowconfigure(0,weight=1)
        pathfilesMainTableFrame.grid_rowconfigure(1,weight=1)
        pathfilesMainTableFrame.grid_rowconfigure(2,weight=1)
        pathfilesMainTableFrame.grid_columnconfigure(0,weight=1)
        pathfilesMainTableFrame.grid_columnconfigure(1,weight=1)
        pathfilesMainTableFrame.grid_columnconfigure(2,weight=1)

        #Title for table:
        TitleTableRow = ctk.CTkFrame(pathfilesMainTableFrame)
        TitleTableRow.grid_rowconfigure(0, weight=1)
        TitleTableRow.grid_columnconfigure(0, weight=1)
        TitleTableRow.grid_columnconfigure(1, weight=1)
        TitleTableRow.grid_columnconfigure(2, weight=1)
        TitleTableRow.grid_columnconfigure(3, weight=1)

        inputLabel = ctk.CTkLabel(TitleTableRow, text="inputfolder",font=ctk.CTkFont(size=17, weight="bold"))
        inputLabel.grid(row=0, column=0, padx=10, pady=10, sticky="nwes")

        FileTypeLabel = ctk.CTkLabel(TitleTableRow, text="FileType",font=ctk.CTkFont(size=17, weight="bold"))
        FileTypeLabel.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

        OutoutDirLabel = ctk.CTkLabel(TitleTableRow, text="OutputDir",font=ctk.CTkFont(size=17, weight="bold"))
        OutoutDirLabel.grid(row=0, column=2, padx=10, pady=10, sticky="news")

        deletePathLabel = ctk.CTkLabel(TitleTableRow, text="Delete path",font=ctk.CTkFont(size=17, weight="bold"))
        deletePathLabel.grid(row=0, column=3, padx=10, pady=10, sticky="news")

        TitleTableRow.grid(row=0 , column=0, columnspan=4, padx=10, pady=10, sticky="news")

        # self.pathFiles = pathFiles
        self.intoTablePathFiles_frames = ctk.CTkScrollableFrame(pathfilesMainTableFrame, border_width=1, border_color=("black","white"))
        self.intoTablePathFiles_frames.grid_rowconfigure(0,weight=1)
        self.intoTablePathFiles_frames.grid_columnconfigure(0,weight=1)
        self.intoTablePathFiles_frames.grid_columnconfigure(1,weight=1)
        self.intoTablePathFiles_frames.grid_columnconfigure(2,weight=1)
        self.intoTablePathFiles_frames.grid_columnconfigure(3,weight=1)

        
        

        

        self.filesPathCount = 1
        self.pathsElements = {}
        for path in pc_obj.pathFiles.values():

            newPathRow = self.addingPathRowToTable(pathsElements= self.pathsElements, path=path)
            for strKey, elem in self.pathsElements[newPathRow].items():
                elem.configure(state="disabled")
            # self.pathsElements[newPathRow]['inputEntry'].configure(state="disabled")
            # self.pathsElements[newPathRow]['FileTypeEntry'].configure(state="disabled")
            # self.pathsElements[newPathRow]['OutputDirEntry'].configure(state="disabled")
        
        self.intoTablePathFiles_frames.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="news")

        # self.addMorePathIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, f"LightMode_AddObject.png")), dark_image=Image.open(os.path.join(images_folder_path, f"DarkMode_AddObject.png")), size=(40,40))
        self.addMorePathIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"DarkMode_AddObject.png")), size=(40,40))
        self.addMorePathBtn = ctk.CTkButton(pathfilesMainTableFrame, corner_radius=3, height=40, border_spacing=10, text="  Add More Path",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=self.pathsElements : self.addingPathRowToTable(x) , image=self.addMorePathIcon ,hover_color=("gray70","gray30"), font=ctk.CTkFont(size=15, weight="bold"))
        self.addMorePathBtn.configure(state="disabled")
        self.addMorePathBtn.grid(row=2, column=1, padx=10, pady=10, sticky="news")
        
        
        pathfilesMainTableFrame.grid(row=5, column=1, columnspan=4, padx=10, pady=10, sticky="news")

        

        self.PcBtnsRow = ctk.CTkFrame(popup)#, fg_color="transparent")
        self.PcBtnsRow.grid_rowconfigure(0, weight=1)
        self.PcBtnsRow.grid_columnconfigure(0, weight=1)
        self.PcBtnsRow.grid_columnconfigure(1, weight=1)

        self.savePcInformationIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "SaveBtn.png")), size=(30,30))
        self.savePcInformationBtn = ctk.CTkButton(self.PcBtnsRow, corner_radius=3, height=40, border_spacing=10, text="  Save",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=pc_obj, y=popup, z=zone_obj, w= self.pathsElements, t=oldpcname : self.HandleWithSavePcBtn(x,y,z,w,t) , image=self.savePcInformationIcon ,hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"))
        self.savePcInformationBtn.grid(row=0, column=1, padx=10, pady=10, sticky="news")

        self.EditPcInformationIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "EditBtn.png")), size=(30,30))
        self.EditPcInformationBtn = ctk.CTkButton(self.PcBtnsRow, corner_radius=3, height=40, border_spacing=10, text="  Edit",fg_color="transparent", text_color=("gray10", "gray90"), command=lambda x=self.pathsElements : self.HandleWithEditBtn(x) , image=self.EditPcInformationIcon ,hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"))
        self.EditPcInformationBtn.grid(row=0, column=0, padx=10, pady=10, sticky="news")

        self.CancelPcInformationIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "CancelBtn.png")), size=(30,30))
        self.CancelPcInformationBtn = ctk.CTkButton(self.PcBtnsRow, corner_radius=3, height=40, border_spacing=10, text="  Cancel", fg_color="transparent", text_color=("gray10", "gray90"), command=popup.destroy , image=self.CancelPcInformationIcon, hover_color=("gray70","gray30"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"), )
        # self.CancelPcInformationBtn.grid(row=0, column=0, padx=0, pady=0, sticky="news")

        self.PcBtnsRow.grid(row=6, column=2, columnspan=2, padx=10, pady=10, sticky="news")



    def addingPathRowToTable(self,pathsElements, path={"inputfolder": "Empty", "FileType": "ALL", "OutputDir": "Empty",}):

        PathRow = ctk.CTkFrame(self.intoTablePathFiles_frames, border_width=1, border_color=("black","white"))
        PathRow.grid_rowconfigure(0, weight=1)
        PathRow.grid_columnconfigure(0, weight=1)
        PathRow.grid_columnconfigure(1, weight=1)
        PathRow.grid_columnconfigure(2, weight=1)
        PathRow.grid_columnconfigure(3, weight=1)

        inputEntry = ctk.CTkEntry(PathRow, width=200)
        inputEntry.insert(0, path["inputfolder"])
        inputEntry.grid(row=0, column=0, padx=10, pady=10, sticky="nws")
        # inputTextBox.configure(state="disabled")

        FileTypeEntry = ctk.CTkEntry(PathRow, width=50)
        FileTypeEntry.insert(0, path["FileType"])
        FileTypeEntry.grid(row=0, column=1, padx=10, pady=10, sticky="nws")
        # FileTypeTextBox.configure(state="disabled")

        OutputDirEntry = ctk.CTkEntry(PathRow, width=200)
        OutputDirEntry.insert(0, path["OutputDir"])
        OutputDirEntry.grid(row=0, column=2, padx=10, pady=10, sticky="nes")
        # OutputDirTextBox.configure(state="disabled")

        deletePathRowImage = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "deleteIcon.png")), size=(30,30))
        deletePathRowBtn = ctk.CTkButton(PathRow, corner_radius=5, width=60, height=40, border_spacing=10, text="",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=pathsElements, y=PathRow : self.deleteRowFromTable(x,y) , image=deletePathRowImage ,hover_color=("gray70","gray30"), anchor="nesw", font=ctk.CTkFont(size=15, weight="bold"))
        deletePathRowBtn.grid(row=0, column=3, padx=10, pady=10, sticky="news")

        pathsElements[PathRow] = {  'inputEntry'    :   inputEntry,
                                    'FileTypeEntry' :   FileTypeEntry,
                                    'OutputDirEntry':   OutputDirEntry,
                                    'deletePathRowBtn': deletePathRowBtn}

        PathRow.grid(row= self.filesPathCount , column=0, columnspan=3, padx=10, pady=10, sticky="news")
        self.filesPathCount += 1        
        return PathRow

    def deleteRowFromTable(self, pathElements, pathToDelete):
        print(f"Before:::::: {pathElements}")
        pathToDelete.grid_forget()
        del pathElements[pathToDelete]
        print(f"afterrr: {pathElements}")
        

    def HandleWithEditBtn(self, pathsElements):
        self.CancelPcInformationBtn.grid(row=0, column=0, padx=10, pady=10, sticky="news")
        self.pcnameEntry.configure(state="normal")
        self.hostnameEntry.configure(state="normal")
        # self.domainEntry.configure(state="normal")
        self.user_nameEntry.configure(state="normal")
        self.passwordEntry.configure(state="normal")
        for rowFrame, rowElemsdict in pathsElements.items():
            for entryname, elem in rowElemsdict.items():
                elem.configure(state="normal")
        self.addMorePathBtn.configure(state="normal")



    def HandleWithSavePcBtn(self, pc_obj, popup, zone_obj, pathsElements, oldPCname):
        pc_obj.pc_name = self.pcnameEntry.get()
        newPCname = self.pcnameEntry.get()
        pc_obj.host_name = self.hostnameEntry.get()
        # pc_obj.domain = self.domainEntry.get()
        pc_obj.user_name = self.user_nameEntry.get()
        pc_obj.password = self.passwordEntry.get()

        count=0
        pathsNewDict = {}
        for rowFrame, rowElemsdict in pathsElements.items():
            tempPath = {}
            tempPath["inputfolder"] = rowElemsdict["inputEntry"].get()
            tempPath["FileType"] = rowElemsdict["FileTypeEntry"].get()
            tempPath["OutputDir"] = rowElemsdict["OutputDirEntry"].get()
            pathsNewDict[count] = tempPath
            count+=1
        pc_obj.pathFiles = pathsNewDict
        ## if pc_name has been changed we have to changed the key but we want to keep it on place so we building a new dict.
        if (oldPCname != newPCname):
            new_dict = {}
            for k,v in zone_obj.computers.items():
                if k==oldPCname:
                    new_dict[newPCname] = v
                else:
                    new_dict[k] = v
            zone_obj.computers = new_dict
            
        dm.updateDB(WorkSpace_dict, appSettings)
        popup.destroy()
        self.zoneDetailsFrame(zone_obj)

    # def find_nearest_git_root_remote(self, ssh_client, path):
    #     curr_path_escaped = path.replace("/", "\\").replace("'", "''")
        
    #     powershell_command = (
    #         f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
    #         f"\"$curr = '{curr_path_escaped}'; "
    #         f"while ($curr) {{ "
    #         f"  if ((Test-Path \\\"$curr\\.git\\\") -or (Test-Path \\\"$curr\\.gitignore\\\")) {{ "
    #         f"    Write-Output $curr; return; "
    #         f"  }}; "
    #         f"  $parent = Split-Path -Path $curr -Parent; "
    #         f"  if (!$parent -or $parent -eq $curr) {{ break }}; "
    #         f"  $curr = $parent; "
    #         f"}}\""
    #     )
        
    #     stdin, stdout, stderr = ssh_client.exec_command(powershell_command)
    #     raw_output = stdout.read().decode('utf-8').strip()
        
    #     if raw_output:
    #         return raw_output.splitlines()[0].strip()
            
    #     return None
    

    def find_nearest_git_root_remote(self, ssh_client, path):
        print(f"DEBUG: Finding Git root for: {path}")
        folder = path.replace("/", "\\").rstrip("\\").replace("'", "''")
        
        command = (
            f"powershell.exe -NoProfile -Command "
            f"\"Set-Location -Path '{folder}'; git rev-parse --show-toplevel\""
        )
        
        stdin, stdout, stderr = ssh_client.exec_command(command)
        out = stdout.read().decode('utf-8').strip()
        err = stderr.read().decode('utf-8').strip()
        
        if out:
            fixed_path = out.replace("/", "\\")
            print(f"DEBUG: Git root found: {fixed_path}")
            return fixed_path
            
        print(f"DEBUG: No Git root found. Error: {err}")
        return None
        

    # def find_nearest_git_root_remote(self, ssh_client: paramiko.SSHClient, path):
    #     curr_path = path
        
    #     while curr_path and os.path.dirname(curr_path) != curr_path:
    #         print(f"Trying to find git folder in: {curr_path}")
    #         remote_path_ps = curr_path.replace("\\", "/").replace("'", "''")
            
    #         powershell_command = (
    #             f"If ((Test-Path '{curr_path}/.git' -PathType Container) -or "
    #             f"(Test-Path '{curr_path}/.gitignore' -PathType Leaf)) {{ "
    #             f"Write-Host 'FOUND' }} Else {{ Write-Host 'NOT_FOUND' }}"
    #         )
            
    #         stdin, stdout, stderr = ssh_client.exec_command(powershell_command)
            
    #         output = stdout.read().decode('utf-8').strip()
    #         print(output)

    #         if output == 'FOUND':
    #             print(f"found == {curr_path}")
    #             return curr_path

    #         parent_path = os.path.dirname(curr_path)
            
    #         if parent_path == curr_path:
    #             break

    #         curr_path = parent_path
    #     print(f"not found????? == {curr_path}")
    #     return None

# -----------------------------------
        # # Convert the path to a Path object
        # current_path = Path(path).resolve()
        
        # # Traverse up the directory tree
        # while current_path != current_path.parent:
        #     # Check if the .git folder or .gitignore file exists
        #     if (current_path / '.git').exists() or (current_path / '.gitignore').exists():
        #         return current_path
        #     # Move to the parent directory
        #     current_path = current_path.parent
        
        # # If no .git folder or .gitignore file is found, return None
        # return None


    # def count_only_files(self, ssh_client: paramiko.SSHClient, input_folder: str, file_type: str | Literal["ALL"]) -> int:

    #     escaped_folder = input_folder.replace("'", "''")
    #     normalized_file_type = file_type.upper().lstrip('.')

    #     if normalized_file_type == "ALL":
    #         powershell_command = (
    #             f"gci -Path '{escaped_folder}' -Recurse | Measure-Object | "
    #             f"Select-Object -ExpandProperty Count"
    #         )
        
    #     else:
    #         file_filter = f'*.{normalized_file_type}'
    #         powershell_command = (
    #             f"gci -Path '{escaped_folder}' -Filter '{file_filter}' "
    #             f"-File -Recurse | Measure-Object | Select-Object -ExpandProperty Count"
    #         )
            
    #     stdin, stdout, stderr = ssh_client.exec_command(powershell_command)
        
    #     stderr_output = stderr.read().decode('utf-8').strip()
        
    #     if stderr_output:
    #         if "Cannot find path" in stderr_output or "FileNotFoundError" in stderr_output:
    #             raise FileNotFoundError(f"Error: Input folder not found or is not accessible on remote server: {input_folder}")
    #         else:
    #             raise IOError(f"An error occurred during counting files in {input_folder}: {stderr_output}")

    #     stdout_output = stdout.read().decode('utf-8').strip()

    #     try:
    #         if not stdout_output:
    #             return 0
    #         return int(stdout_output)

    #     except ValueError:
    #         raise IOError(f"Could not parse count from remote output: {stdout_output}")


    def count_only_files(self, ssh_client, input_folder, file_type="ALL"):
        print(f"DEBUG: Counting files in: {input_folder}")
        folder = input_folder.replace("/", "\\").rstrip("\\").replace("'", "''")
        filter_str = "*" if file_type.upper() == "ALL" else f"*.{file_type.lstrip('.')}"
        
        command = (
            f"powershell.exe -NoProfile -Command "
            f"\"(Get-ChildItem -Path '{folder}' -Filter '{filter_str}' -File -Recurse -ErrorAction SilentlyContinue).Count\""
        )
        
        print(f"DEBUG: Executing: {command}")
        stdin, stdout, stderr = ssh_client.exec_command(command)
        
        out = stdout.read().decode('utf-8').strip()
        print(f"DEBUG: Count result: '{out}'")
        
        return int(out) if out.isdigit() else 0
        

    def create_ssh_connection(self, ip_address, username, password):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"Attempting to connect to {ip_address} as {username}...")
        
        try:
            ssh_client.connect(hostname=ip_address, username=username, password=password, port=22)
            print("SSH Connection established successfully. You are connected!")
            return ssh_client
            
        except paramiko.AuthenticationException:
            print("AUTHENTICATION FAILED: Check username and password.")
            raise Exception("AUTHENTICATION FAILED: Check username and password.")
            return None
        except paramiko.SSHException as e:
            print(f"SSH ERROR: Could not establish connection. Details: {e}")
            raise Exception(f"SSH ERROR: Could not establish connection. Details: {e}")
            return None
        except Exception as e:
            print(f"AN UNEXPECTED ERROR OCCURRED: {e}")
            raise Exception(f"AN UNEXPECTED ERROR OCCURRED: {e}")
            return None
          

        
    # def copy_files_by_type(self, ssh_client: paramiko.SSHClient, input_folder, file_type, output_folder):
        
    #     escaped_input = input_folder.replace("'", "''")
    #     normalized_file_type = file_type.upper().lstrip('.')

    #     # Check if the output folder exists and create it if it doesn't
    #     check_and_create_folder_command = (
    #         f"if (-Not (Test-Path -Path '{output_folder}')) {{ New-Item -ItemType Directory -Path '{output_folder}' }}"
    #     )
    #     ssh_client.exec_command(check_and_create_folder_command)

    #     if normalized_file_type == "ALL":
    #         count_command = (
    #             f"gci -Path '{escaped_input}' -Recurse | Measure-Object | "
    #             f"Select-Object -ExpandProperty Count"
    #         )
    #     else:
    #         file_filter = f'*.{normalized_file_type}'
    #         count_command = (
    #             f"gci -Path '{escaped_input}' -Filter '{file_filter}' "
    #             f"-File | Measure-Object | Select-Object -ExpandProperty Count"
    #         )
            
    #     stdin, stdout, stderr = ssh_client.exec_command(count_command)
        
    #     if stderr.read().decode('utf-8').strip():
    #         raise IOError("Error during pre-copy count operation.")
            
    #     count_output = stdout.read().decode('utf-8').strip()
    #     try:
    #         files_to_copy_count = int(count_output)
    #     except ValueError:
    #         files_to_copy_count = 0 
            
    #     if files_to_copy_count == 0:
    #         return 0

    #     escaped_output = output_folder.replace("'", "''")

    #     if normalized_file_type == "ALL":
    #         powershell_command = (
    #             f"Copy-Item -Path '{escaped_input}\\*' -Destination '{escaped_output}' -Recurse -Force"
    #         )
    #     else:
    #         file_filter = f'*.{normalized_file_type}'
    #         powershell_command = (
    #             f"Get-ChildItem -Path '{escaped_input}' -Filter '{file_filter}' -File | "
    #             f"Copy-Item -Destination '{escaped_output}' -Force"
    #         )
            
    #     stdin, stdout, stderr = ssh_client.exec_command(powershell_command)
        
    #     stderr_output = stderr.read().decode('utf-8').strip()
        
    #     if stderr_output:
    #         if "Cannot find path" in stderr_output:
    #             raise FileNotFoundError(f"Error: Input or Output folder not accessible on remote server.")
    #         else:
    #             raise IOError(f"Remote copy failed: {stderr_output}")
        
    #     return files_to_copy_count



    def copy_files_by_type(self, ssh_client, source_folder, destination_folder, file_type="ALL"):
        print(f"DEBUG: Copying files via CMD from {source_folder} to {destination_folder}")
        
        src = source_folder.replace("/", "\\").rstrip("\\")
        dst = destination_folder.replace("/", "\\").rstrip("\\")
        file_pattern = "*" if file_type.upper() == "ALL" else f"*.{file_type.lstrip('.')}"
        
        command = f'xcopy "{src}\\{file_pattern}" "{dst}\\" /s /e /y /i'
        print(f"DEBUG: Executing CMD: {command}")
        
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode('utf-8').splitlines()
        
        for line in reversed(output):
            line = line.strip()
            if "File(s) copied" in line:
                match = re.search(r'(\d+)', line)
                if match:
                    count = int(match.group(1))
                    print(f"DEBUG: Copied {count} files")
                    return count
                    
        return 0

    def loadFavsPage(self):
        self.FavsPage = ctk.CTkFrame(self.mainFrame ,corner_radius=3)
        self.FavsPage.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.FavsPage.grid_columnconfigure(0,weight=1)
        self.FavsPage.grid_rowconfigure(0,weight=1)

        self.FavFrame = ctk.CTkFrame(self.FavsPage ,corner_radius=3)
        self.FavFrame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.FavFrame.grid_columnconfigure(0,weight=1)
        self.FavFrame.grid_rowconfigure(0,weight=0)
        self.FavFrame.grid_rowconfigure(1,weight=1)
        
        favoritesIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "favoritesIcon.png")), size=(40,40))
        favoritesButton = ctk.CTkButton(self.FavFrame, corner_radius=4, height=40, border_spacing=10, text="  Favorites",fg_color="transparent", text_color=("gray10", "gray90"), image=self.favoritesIcon , anchor="w", font=ctk.CTkFont(size=20, weight="bold"), state="disable")
        favoritesButton.grid(row=0, column=0, padx=10, pady=10)

        
        self.FavsScroll = ctk.CTkScrollableFrame(self.FavFrame)
        self.FavsScroll.grid(row=1, column=0, sticky="nsew")

        

        self.FavsScroll.grid_columnconfigure(0,weight=1, uniform="helloCol")
        self.FavsScroll.grid_columnconfigure(1,weight=1, uniform="helloCol")
        self.FavsScroll.grid_columnconfigure(2,weight=1, uniform="helloCol")
        self.FavsScroll.grid_columnconfigure(3,weight=1, uniform="helloCol")
        self.FavsScroll.grid_columnconfigure(4,weight=1, uniform="helloCol")
        self.FavsScroll.grid_rowconfigure(0,weight=1, uniform="helloRow")
        self.FavsScroll.grid_rowconfigure(1,weight=1, uniform="helloRow")
        self.FavsScroll.grid_rowconfigure(2,weight=1, uniform="helloRow")
        self.FavsScroll.grid_rowconfigure(3,weight=1, uniform="helloRow")
        zonecount=0 # how many zones in one workspace=(tab / page)
        listOfZones = appSettings.favorites
        print(f"favorites is: {listOfZones}")
        for zone_name, zone_obj in listOfZones.items():
            # print(f"page number {zonecount}, = {zone_obj.Zone_name}")
            newCard = self.createCard(self.FavsScroll, name=(zone_obj.Zone_name), cardtype="zone", funcToBtn= lambda x=zone_obj, y=self.FavsPage : self.zoneDetailsFrame(x,y))
            newCard.grid(row=int(zonecount/5), column=int(zonecount%5), padx=10, pady=10)
            zonecount+=1

    
        
        

    


      

if __name__ == "__main__":
    
    # manager = None
    pklDict =  dm.load_data_from_file()
    if pklDict is not None:
        for key, val in pklDict.items():
            print(f"key is {key}, val is {val}")
        if pklDict:
            print("got the pkldict?")
            WorkSpace_dict = pklDict['data']
            appSettings = pklDict['settings']
        else:
            print("pklDict is wrong... ???")
        
        
        if WorkSpace_dict is not None:
            app = LabSyncDashBoard()
            app.mainloop()
            



