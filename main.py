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


import hashlib
import customtkinter as ctk
import pickle
import time
import dataManager as dm
from customtkinter import CTkInputDialog
from models import Computer, Room, Zone, WorkSpace, Settings
from PIL import Image
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
from git import Repo
import git
from pathlib import Path
import re
from typing import Literal
import stat
import shutil
import paramiko
import subprocess
import threading
import queue



ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Tuple fonts only — never use ctk.CTkFont() at import time (needs a root window first).
UI_FONT_FAMILY = "Segoe UI"
UI_FONT_BODY = (UI_FONT_FAMILY, 13)
UI_FONT_BODY_BOLD = (UI_FONT_FAMILY, 13, "bold")
UI_FONT_TITLE = (UI_FONT_FAMILY, 18, "bold")
UI_FONT_SMALL = (UI_FONT_FAMILY, 11)

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
    """Modern progress dialog for long-running sync operations."""

    def __init__(self, master, title, initial_message):
        super().__init__(master)
        self.title(title)
        self.geometry("820x440")
        self.attributes("-topmost", True)
        self.resizable(True, True)
        self.minsize(720, 650)

        self.configure(fg_color=("gray92", "gray14"))

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=18, pady=18)

        self._card = ctk.CTkFrame(
            outer,
            corner_radius=22,
            fg_color=("gray98", "gray17"),
            border_width=1,
            border_color=("gray85", "gray32"),
        )
        self._card.pack(fill="both", expand=True)

        hero = ctk.CTkFrame(
            self._card,
            corner_radius=16,
            fg_color=("#1d4ed8", "#1d4ed8"),
            height=72,
        )
        hero.pack(fill="x", padx=14, pady=(14, 0))
        hero.pack_propagate(False)

        hero_pad = ctk.CTkFrame(hero, fg_color="transparent")
        hero_pad.pack(fill="both", expand=True, padx=22, pady=14)
        ctk.CTkLabel(
            hero_pad,
            text="Synchronization",
            text_color=("white", "white"),
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            hero_pad,
            text="Git fetch, files, commit & push",
            text_color=("#bfdbfe", "#bfdbfe"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        body = ctk.CTkFrame(self._card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=22, pady=(18, 18))

        self.stage_label = ctk.CTkLabel(
            body,
            text="Step — / —",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#2563eb", "#60a5fa"),
            anchor="w",
        )
        self.stage_label.pack(fill="x", pady=(0, 6))

        self.label = ctk.CTkLabel(
            body,
            text=initial_message,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=("gray20", "gray90"),
            wraplength=720,
            justify="left",
            anchor="w",
        )
        self.label.pack(fill="x", pady=(0, 14))

        prog_row = ctk.CTkFrame(body, fg_color="transparent")
        prog_row.pack(fill="x", pady=(0, 12))
        prog_row.grid_columnconfigure(0, weight=1)

        bar_wrap = ctk.CTkFrame(prog_row, fg_color="transparent")
        bar_wrap.grid(row=0, column=0, sticky="ew", padx=(0, 16))

        self.progress_bar = ctk.CTkProgressBar(
            bar_wrap,
            orientation="horizontal",
            height=16,
            corner_radius=8,
            progress_color=("#2563eb", "#3b82f6"),
            fg_color=("gray82", "gray35"),
            border_width=0,
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)

        pct_col = ctk.CTkFrame(prog_row, fg_color="transparent", width=88)
        pct_col.grid(row=0, column=1, sticky="e")
        pct_col.grid_propagate(False)

        self.labelprogress = ctk.CTkLabel(
            pct_col,
            text="0%",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color=("gray25", "gray95"),
        )
        self.labelprogress.pack(anchor="e")

        self._pct_sub = ctk.CTkLabel(
            pct_col,
            text="complete",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("gray50", "gray60"),
        )
        self._pct_sub.pack(anchor="e")

        log_outer = ctk.CTkFrame(
            body,
            corner_radius=14,
            fg_color=("gray90", "gray22"),
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        log_outer.pack(fill="both", expand=True)

        log_head = ctk.CTkFrame(log_outer, fg_color="transparent", height=28)
        log_head.pack(fill="x", padx=14, pady=(12, 6))

        ctk.CTkLabel(
            log_head,
            text="Activity log",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("gray35", "gray80"),
        ).pack(side="left")
        ctk.CTkLabel(
            log_head,
            text="Live updates",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("gray55", "gray60"),
        ).pack(side="left", padx=(10, 0))

        self.log_box = ctk.CTkTextbox(
            log_outer,
            height=300,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=("gray95", "gray12"),
            text_color=("gray15", "gray88"),
            border_width=0,
            corner_radius=10,
        )
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 12))
        self.log_box.configure(state="disabled")
        self._last_stage_text = None

        self.update()
        self.wait_visibility()

    def append_log(self, line):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", line + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def update_status(self, message, progress_value, stage_text=None):
        print(f"DEBUG: {message} ({int(progress_value * 100)}%)")
        if stage_text:
            self.stage_label.configure(text=stage_text)
            if stage_text != self._last_stage_text:
                self.append_log("")
                self.append_log("=============")
                self.append_log(stage_text)
                self.append_log("=============")
                self._last_stage_text = stage_text
        self.label.configure(text=message)
        pct = int(progress_value * 100)
        self.labelprogress.configure(text=f"{pct}%")
        self.progress_bar.set(progress_value)
        self.append_log(message)
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

        self._sync_job_queue = queue.Queue()
        self._sync_worker_running = False

        


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
            # self.LogoIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, "Logo_light_mode.png")), dark_image=Image.open(os.path.join(images_folder_path, "Logo_dark_mode.png")), size=(300,200))
            self.LogoIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "LabSyncIcon-WithoutBG.png")), size=(300,200))
            self.LogoLabel = ctk.CTkLabel(self.sidebar_nav, text="", compound="left", image=self.LogoIcon)
            self.LogoLabel.grid(row=0, column=0 ,padx=10, pady=10, sticky="ew")
        except Exception as e:
            print(f"\n\n\n err is: {e}\n\n\n")
        
        

        self.HomeIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "home-button.png")), size=(40,40))
        self.HomeButton = ctk.CTkButton(self.sidebar_nav, corner_radius=4, height=40, border_spacing=10, text="  Home",fg_color="transparent", text_color=("gray10", "gray90"), command=self.showHomePage , image=self.HomeIcon ,hover_color=("gray55","gray55"), anchor="w", font=ctk.CTkFont(size=20, weight="bold"))
        self.HomeButton.grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        self.AppearanceThemeIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, "Appearance_dark_mode.png")), dark_image=Image.open(os.path.join(images_folder_path, "Appearance_light_mode.png")), size=(40,40))
        self.AppearanceButton = ctk.CTkButton(self.sidebar_nav, corner_radius=4, height=40, border_spacing=10, text="  Change Appearance",fg_color="transparent", text_color=("gray10", "gray90"), command=self.changeAppearance , image=self.AppearanceThemeIcon ,hover_color=("gray55","gray55"), anchor="w", font=ctk.CTkFont(size=20, weight="bold"))
        self.AppearanceButton.grid(row=2, column=0, padx=2, pady=2, sticky="ew")

        self.NavFrameRow = ctk.CTkFrame(self.sidebar_nav)
        self.NavFrameRow.grid_columnconfigure(0, weight=1)
        self.NavFrameRow.grid_columnconfigure(1, weight=1)
        self.NavFrameRow.grid_rowconfigure(0, weight=1)

        self.Real_BackIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "Real_BackArrow.png")), size=(30,30))
        self.Gray_BackIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "Gray_BackArrow.png")), size=(30,30))
        self.BackButton = ctk.CTkButton(self.NavFrameRow, corner_radius=4, height=40, border_spacing=10, text="  Back",fg_color="transparent", text_color=("gray10", "gray90"), command=self.PressedOnBackBtn , image=self.Gray_BackIcon ,hover_color=("gray55","gray55"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"), state="disabled")
        self.BackButton.grid(row=0, column=0, padx=0, pady=0, sticky="news")

        self.Real_ForwardIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "Real_ForwardArrow.png")), size=(30,30))
        self.Gray_ForwardIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "Gray_ForwardArrow.png")), size=(30,30))
        self.ForwardButton = ctk.CTkButton(self.NavFrameRow, corner_radius=4, height=40, border_spacing=10, text="  Forward",fg_color="transparent", text_color=("gray10", "gray90"), command=self.pressedOnForwardBtn , image=self.Gray_ForwardIcon ,hover_color=("gray55","gray55"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"), state="disabled")
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
        self.updateHomePageSelectionBTN = ctk.CTkButton(self.homepageselectionFrameRow, corner_radius=4, height=40, border_spacing=10, text=" Update Selection",fg_color="transparent", text_color=("gray10", "gray90"), command=self.updateStartHomePage , image=self.updateHomePageSelectionIcon ,hover_color=("gray55","gray55"), anchor="center", font=ctk.CTkFont(size=12, weight="bold"))
        self.updateHomePageSelectionBTN.grid(row=1, column=0, columnspan=2)
        self.updateHomePageSelectionBTN.configure(state="disable")

        # self.lockHomePageSelectionIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "lockIcon.png")), size=(20,20))
        # self.lockHomePageSelectionBTN = ctk.CTkButton(self.homepageselectionFrameRow, corner_radius=4, height=40, border_spacing=10, text=" Lock Selection",fg_color="transparent", text_color=("gray10", "gray90"), command=self.updateStartHomePage , image=self.updateHomePageSelectionIcon ,hover_color=("gray55","gray55"), anchor="center", font=ctk.CTkFont(size=12, weight="bold"))
        # self.lockHomePageSelectionBTN.grid(row=1, column=1)

        self.unlockHomePageSelectionIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "unlockIcon.png")), size=(20,20))
        self.unlockHomePageSelectionBTN = ctk.CTkButton(self.homepageselectionFrameRow, corner_radius=4, height=40, border_spacing=10, text=" Unlock Selection",fg_color="transparent", text_color=("gray10", "gray90"), command=self.unlockTheSelection , image=self.unlockHomePageSelectionIcon ,hover_color=("gray55","gray55"), anchor="center", font=ctk.CTkFont(size=12, weight="bold"))
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
        self.favoritesButtonSideBar = ctk.CTkButton(self.sidebar_nav, corner_radius=4, height=40, border_spacing=10, text="  Favorites",fg_color="transparent", text_color=("gray10", "gray90"), command=self.loadFavsPage , image=self.favoritesIcon ,hover_color=("gray55","gray55"), anchor="w", font=ctk.CTkFont(size=20, weight="bold"))
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
        self.mainFrame.configure(fg_color=("#FFFFFF", "#121212"))
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
        self.searchBtn = ctk.CTkButton(self.searchFrame, corner_radius=5, height=40, border_spacing=10, text=" Search",fg_color="transparent", text_color="#34495E", command=self.button_func, image=self.searchIcon ,hover_color=("gray55","gray55"), anchor="nsew", font=ctk.CTkFont(size=20, weight="bold"))
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
                                            hover_color=("gray55","gray55"),
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
        self.deleteThisWSBtn = ctk.CTkButton(self.deleteThisWSFrame, compound="left", text=" Confirm delete this WS.",image = self.deleteThisWSIcon, command= lambda x=self.deleteThisWSEntry , y=ws_obj, z=self.deleteThisWSERRLabel : self.deleteThisWSHanleBtnFunc(x,y,z), border_color="black", fg_color=("gray45","gray75"), anchor="center", text_color=("white","black"), font=("Helvetica", 15, "bold"), hover_color=("gray55","gray55"))
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
        self.saveNewZoneBtn = ctk.CTkButton(self.addNewZoneFrame, compound="left", text=" Create New Zone",image = self.addToListIcon, command= lambda x=self.newZonenameEntry , y=ws_obj, z=self.newZonenameERRLabel : self.createNewZoneFunc(x,y,z), border_color="black", fg_color=("gray45","gray75"), anchor="center", text_color=("white","black"), font=("Helvetica", 15, "bold"), hover_color=("gray55","gray55"))
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

        self.newCard = ctk.CTkFrame(
            my_master,
            corner_radius=14,
            border_color=("gray78", "gray38"),
            border_width=1,
            width=135,
            height=110,
            fg_color=("gray88", "gray22"),
        )
        self.newCard.rowconfigure(0,weight=1)
        # self.newCard.rowconfigure(1,weight=1)
        self.newCard.columnconfigure(0,weight=1)
        
        # self.newIcon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, f"LightMode_{cardtype}.png")), dark_image=Image.open(os.path.join(images_folder_path, f"DarkMode_{cardtype}.png")), size=(40,40))
        self.newIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"DarkMode_{cardtype}.png")), size=(40,40))
        
        self.newButton = ctk.CTkButton(
            self.newCard,
            corner_radius=10,
            border_spacing=10,
            compound="top",
            text=name,
            fg_color="transparent",
            command=funcToBtn,
            image=self.newIcon,
            anchor="center",
            hover_color=("gray70", "gray32"),
            font=UI_FONT_BODY_BOLD,
            text_color=("gray25", "gray90"),
        )
        self.newButton.grid(row=0, column=0, padx=6, pady=6)

        return self.newCard


    def zoneDetailsFrame(self, zone_obj, master = None):
        if (master is None):
            master = self.tabsFrame
        
        self.ThisZoneFrame = ctk.CTkFrame(master, width=500, fg_color=("gray90", "gray16"), corner_radius=0)
        self.ThisZoneFrame.grid_columnconfigure(0,weight=1)
        self.ThisZoneFrame.grid_columnconfigure(1,weight=3)
        self.ThisZoneFrame.grid_rowconfigure(0, weight=1)
        self.ThisZoneFrame.grid_rowconfigure(1, weight=0)

        self.pc_Frames = ctk.CTkScrollableFrame(
            self.ThisZoneFrame,
            width=240,
            height=200,
            corner_radius=16,
            fg_color=("gray92", "gray18"),
            border_width=1,
            border_color=("gray80", "gray30"),
        )
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
            self.deletepcRowBtn = ctk.CTkButton(self.pcrow, corner_radius=5, width=30, height=30,compound="top", text=" ",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=pc_obj, y=zone_obj, z=self.pcrow, w=self.checked_Pc_objs : self.deleteThisPcRowFromZone(x,y,z,w) , image=self.deletepcRowIcon ,hover_color=("gray55","gray55"), anchor="nesw", font=ctk.CTkFont(size=15, weight="bold"))
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

        self.git_Frame = ctk.CTkFrame(
            self.ThisZoneFrame,
            width=200,
            height=200,
            corner_radius=18,
            fg_color=("gray95", "gray17"),
            border_width=1,
            border_color=("gray82", "gray30"),
        )
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
        self.git_Frame.grid(row=0, column=1, padx=12, pady=12, sticky="nesw")

        self.zone_title_Label = ctk.CTkLabel(
            self.git_Frame,
            text=f"Zone · {zone_obj.Zone_name}",
            font=UI_FONT_TITLE,
            text_color=("white", "white"),
            fg_color=("#1d4ed8", "#1d4ed8"),
            corner_radius=12,
            pady=12,
            padx=16,
        )
        self.zone_title_Label.grid(row=0, column=1, columnspan=4, padx=12, pady=(12, 8), sticky="ew")
        
        self.markASFavIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"noFavIcon.png")), size=(50,50))
        self.markASFavButton = ctk.CTkButton(self.git_Frame, text="", fg_color=("gray82", "gray32"), image=self.markASFavIcon, width=50, corner_radius=12, hover_color=("gray70", "gray40"))

        self.unmarkFavIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, f"yesFavIcon.png")), size=(50,50))
        self.unmarkFavButton = ctk.CTkButton(self.git_Frame, text="", fg_color=("gray82", "gray32"), image=self.unmarkFavIcon, width=50, corner_radius=12, hover_color=("gray70", "gray40"))

        self.markASFavButton.configure(command= lambda x=zone_obj, y=self.markASFavButton, z=self.unmarkFavButton: self.addToFavs(x,y,z))

        self.unmarkFavButton.configure(command= lambda x=zone_obj, y=self.unmarkFavButton ,z=self.markASFavButton: self.removeFromFavs(x,y,z))
        print(f"isFav = {zone_obj.isFav}")
        if(zone_obj.isFav):
            self.unmarkFavButton.grid(row=0, column=5, sticky="sw")
        else:
            self.markASFavButton.grid(row=0, column=5, sticky="sw")
            
        self.editRowFrame = ctk.CTkFrame(self.ThisZoneFrame, height=70, fg_color="transparent")
        self.editRowFrame.grid(row=1, column=0, columnspan=2, sticky="news")


        # Block Selection Dropdown
        self.block_label = ctk.CTkLabel(
            self.git_Frame,
            text="Block:",
            font=UI_FONT_BODY_BOLD,
            text_color=("gray20", "gray90"),
        )
        self.block_label.grid(row=1, column=1, padx=12, pady=(4, 6), sticky="w")

        self.block_dropdown = ctk.CTkComboBox(
            self.git_Frame,
            values=["", "Block 2", "Block 3"],
            state="readonly",
            width=100,
            font=UI_FONT_BODY,
            corner_radius=8,
            fg_color=("gray98", "gray12"),
            border_color=("gray80", "gray35"),
        )
        self.block_dropdown.grid(row=1, column=2, padx=12, pady=(4, 6), sticky="w")
        self.block_dropdown.set("")

        # Checkbox for "Not using this parameter"
        self.not_using_param_checkbox = ctk.CTkCheckBox(
            self.git_Frame,
            text="Not using this parameter",
            font=UI_FONT_BODY,
            checkbox_width=20,
            checkbox_height=20,
            command=self._on_not_using_param_toggle,
        )
        self.not_using_param_checkbox.grid(row=1, column=3, columnspan=2, padx=12, pady=(4, 6), sticky="w")

        self.git_title_Label = ctk.CTkLabel(
            self.git_Frame,
            text="Commit message",
            font=UI_FONT_BODY_BOLD,
            text_color=("gray20", "gray90"),
        )
        self.git_title_Label.grid(row=2, column=1, columnspan=4, padx=12, pady=(4, 6), sticky="w")

        self.git_comment_Textbox = ctk.CTkTextbox(
            self.git_Frame,
            width=400,
            height=100,
            wrap="word",
            font=UI_FONT_BODY,
            corner_radius=12,
            fg_color=("gray98", "gray12"),
            border_width=1,
            border_color=("gray80", "gray35"),
        )
        self.git_comment_Textbox.grid(row=3, column=1, columnspan=4, padx=12, pady=(0, 8), sticky="n")

        self.errMsgPush = ctk.CTkLabel(self.editRowFrame, text="", text_color="red", font=ctk.CTkFont(weight="bold"))
        self.errMsgPush.grid(row=0, column=1, columnspan=3, sticky="news")


        # self.push_n_commit_icon = ctk.CTkImage(light_image=Image.open(os.path.join(images_folder_path, "LightMode_PushnCommit.png")), dark_image=Image.open(os.path.join(images_folder_path, "DarkMode_PushnCommit.png")), size=(40,40))
        self.push_n_commit_icon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "DarkMode_PushnCommit.png")), size=(40,40))
        
        self.Push_n_Commit_Btn = ctk.CTkButton(
            self.git_Frame,
            corner_radius=12,
            border_spacing=10,
            compound="top",
            text="Push & Commit",
            fg_color=("#2563eb", "#3b82f6"),
            command=lambda x=self.errMsgPush, y=self.git_comment_Textbox: self.push_n_commit_Btn_Func(x, y),
            image=self.push_n_commit_icon,
            anchor="center",
            hover_color=("#1d4ed8", "#2563eb"),
            font=UI_FONT_BODY_BOLD,
            text_color=("white", "white"),
        )
        self.Push_n_Commit_Btn.grid(row=4, column=2, columnspan=2, padx=12, pady=8, sticky="n")

        self.git_progressbar = ctk.CTkProgressBar(self.git_Frame, width=400, height=8, corner_radius=6, progress_color=("#2563eb", "#3b82f6"))
        #self.git_progressbar.configure(mode="indeterminate")
    

        self.deleteThisZoneLabel = ctk.CTkLabel(self.editRowFrame, text=f"   Please write DELETE (with CapsLock) to confirm delete this zone: " )
        self.deleteThisZoneEntry = ctk.CTkEntry(self.editRowFrame, placeholder_text=f"Write DELETE to confirm. ", width=100)

        self.deleteThisZoneerrLabel = ctk.CTkLabel(self.editRowFrame, text=f" " )

        self.deleteThisZoneIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "deleteIcon.png")), size=(30,30)) 
        self.deleteThisZoneBTN = ctk.CTkButton(self.editRowFrame, corner_radius=3, height=40, border_spacing=10, text=" Delete This Zone",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=zone_obj, y=self.deleteThisZoneEntry, z=self.deleteThisZoneerrLabel : self.deleteThisZoneFunction(x,y,z) , image=self.deleteThisZoneIcon ,hover_color=("gray55","gray55"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"))
        
        

        self.DoneEditZoneIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "DoneEdit.png")), size=(30,30))
        self.DoneEditZoneBtn = ctk.CTkButton(self.editRowFrame, corner_radius=3, height=40, border_spacing=10, text="  Done Edit",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=zone_obj, y=master : self.zoneDetailsFrame(x,y) , image=self.DoneEditZoneIcon ,hover_color=("gray55","gray55"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"))


        self.EditZoneIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "EditBtn.png")), size=(30,30))
        self.EditZoneBtn = ctk.CTkButton(self.editRowFrame, corner_radius=3, height=40, border_spacing=10, text="  Edit",fg_color="transparent", text_color=("gray10", "gray90") , image=self.EditZoneIcon ,hover_color=("gray55","gray55"), anchor="w", font=ctk.CTkFont(size=15, weight="bold"))
        listToShow = [self.DoneEditZoneBtn, self.deleteThisZoneBTN,self.deleteThisZoneLabel,self.deleteThisZoneEntry, self.deleteThisZoneerrLabel]
        self.EditZoneBtn.configure(command=lambda x=self.checkBoxesZone, y=self.deleteBoxesZone, z=listToShow, w=[self.EditZoneBtn] : self.makeThisZoneFrameEditable(x,y,z,w))
        self.EditZoneBtn.grid(row=0, column=0, sticky="news")
        
        print(f"Entered Zone: {zone_obj.Zone_name}. ")



# self.deletepcRowBtn = ctk.CTkButton(self.pcrow, corner_radius=5, width=60, height=40, border_spacing=10,
# text="",fg_color="transparent", text_color=("gray10", "gray90"), command= lambda x=zone_obj, y=self.pcrow, z=self.checked_Pc_objs : self. , image=deletepcRowIcon
# ,hover_color=("gray55","gray55"), anchor="nesw", font=ctk.CTkFont(size=15, weight="bold"))

    def addNewPcToThisZoneHandleFunc(self, zone_obj):
        pc_count = zone_obj.get_computer_count()
        temp_pc = Computer(pc_name = f"NewPC{pc_count+1} ☼")
        zone_obj.addComputer(temp_pc)
        dm.updateDB(WorkSpace_dict, appSettings)
        self.homeWidget()
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
            self.searchDictCreate()

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
        self.newCard = ctk.CTkFrame(
            my_master,
            corner_radius=14,
            border_color=("gray78", "gray38"),
            border_width=1,
            width=135,
            height=110,
            fg_color=("gray88", "gray22"),
        )
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
        
        
        self.newButton = ctk.CTkButton(
            self.newCard,
            corner_radius=10,
            border_spacing=10,
            compound="left",
            text=name,
            fg_color="transparent",
            command=funcToBtn,
            image=self.newIcon,
            anchor="center",
            hover_color=("gray70", "gray32"),
            font=UI_FONT_BODY_BOLD,
            text_color=("gray25", "gray90"),
        )
        self.newButton.grid(row=0, column=0, padx=6, pady=6)

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
        self.homeWidget()
        self.tabsWidgetsFunc()

    def pc_checkBox_selected(self, pc_obj):
        if(pc_obj in self.checked_Pc_objs):
            self.checked_Pc_objs.remove(pc_obj)
            pc_obj.isChecked = False
        else:
            self.checked_Pc_objs.append(pc_obj)
            pc_obj.isChecked = True

        dm.updateDB(WorkSpace_dict, appSettings)

    def pick_local_folder_into_entry(self, entry: ctk.CTkEntry, title: str = "Select folder"):
        """Opens the OS folder picker and writes the path into the entry (paste still works)."""
        folder = filedialog.askdirectory(parent=self, title=title, mustexist=True)
        if not folder:
            return
        normalized = os.path.normpath(folder)
        try:
            was_disabled = str(entry.cget("state") or "").lower() == "disabled"
        except Exception:
            was_disabled = False
        if was_disabled:
            entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, normalized)
        if was_disabled:
            entry.configure(state="disabled")

    def _make_path_browse_button(self, parent, entry: ctk.CTkEntry, dialog_title: str):
        return ctk.CTkButton(
            parent,
            text="Browse…",
            width=92,
            height=34,
            corner_radius=10,
            font=UI_FONT_SMALL,
            fg_color=("#2563eb", "#3b82f6"),
            text_color=("white", "white"),
            hover_color=("#1d4ed8", "#2563eb"),
            command=lambda: self.pick_local_folder_into_entry(entry, dialog_title),
        )

    # def updateLabelWithColor(self, Label, msg, color = "red"){
    #     label.configure(text= " ")
    # }

    def _enqueue_ui(self, fn):
        self._sync_job_queue.put(fn)

    def _drain_sync_jobs(self):
        try:
            while True:
                fn = self._sync_job_queue.get_nowait()
                fn()
        except queue.Empty:
            pass
        if self._sync_worker_running:
            self.after(50, self._drain_sync_jobs)

    def _set_git_sync_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        try:
            self.Push_n_Commit_Btn.configure(state=state)
        except Exception:
            pass
        try:
            self.git_comment_Textbox.configure(state=state)
        except Exception:
            pass
        try:
            self.block_dropdown.configure(state="disabled" if busy else "readonly")
        except Exception:
            pass
        try:
            self.not_using_param_checkbox.configure(state=state)
        except Exception:
            pass

    def _sync_ui_status(self, popup, msg, prog, stage):
        self._enqueue_ui(lambda p=popup, m=msg, pr=prog, s=stage: p.update_status(m, pr, s))

    def _display_path(self, path_value):
        if path_value is None:
            return ""
        return os.path.normpath(str(path_value))

    def _show_topmost_warning(self, title, text):
        """Show a warning dialog above all app windows so it does not hide behind progress popups."""
        owner = None
        try:
            owner = ctk.CTkToplevel(self)
            owner.withdraw()
            owner.attributes("-topmost", True)
            owner.lift()
            owner.focus_force()
            messagebox.showwarning(title, text, parent=owner)
        except Exception:
            messagebox.showwarning(title, text)
        finally:
            if owner is not None:
                try:
                    owner.destroy()
                except Exception:
                    pass

    def _sync_pipeline_error(self, text, errMsgLabel, commit_box, currstatpopup, ssh_client=None):
        if ssh_client:
            try:
                ssh_client.close()
            except Exception:
                pass

        def run():
            try:
                currstatpopup.destroy()
            except Exception:
                pass
            self._show_topmost_warning("Invalid input", text)
            errMsgLabel.configure(text=text, text_color="red")
            print(text)
            self.git_progressbar.stop()
            self.git_progressbar.configure(mode="determinate")
            self.git_progressbar.set(0)

        self._enqueue_ui(run)

    def _on_not_using_param_toggle(self):
        """Ask for password when the 'Not using this parameter' checkbox is toggled on."""
        if self.not_using_param_checkbox.get():  # just got checked
            dialog = CTkInputDialog(
                text="Enter password to enable this option:",
                title="Password Required",
            )
            password = dialog.get_input()
            if password != "admin":
                self.not_using_param_checkbox.deselect()
                return
            # Correct password — disable and gray the block dropdown
            self.block_dropdown.configure(state="disabled")
        else:
            # Unchecked — re-enable the block dropdown
            self.block_dropdown.configure(state="readonly")

    def _sync_pipeline_success(self, errMsgLabel, commit_box, currstatpopup):
        def run():
            self.git_progressbar.stop()
            self.git_progressbar.configure(mode="determinate")
            self.git_progressbar.set(1.0)
            currstatpopup.update_status("Successful", 1.0, "Done")
            errMsgLabel.configure(text="Successfull", text_color="green")
            commit_box.delete("0.0", "end")
            # Reset checkbox and re-enable dropdown after successful push
            self.not_using_param_checkbox.deselect()
            self.block_dropdown.configure(state="readonly")
            currstatpopup.close_with_delay()

        self._enqueue_ui(run)

    def _finish_commit_confirm_dialog(self, win, on_result, confirmed):
        try:
            win.destroy()
        except Exception:
            pass
        if on_result:
            on_result(confirmed)

    def _wait_for_commit_confirmation(self, diffsToAdd, errMsgLabel):
        done_event = threading.Event()
        holder = {"ok": False}

        def on_result(confirmed):
            holder["ok"] = confirmed
            done_event.set()

        self._enqueue_ui(lambda: self.gitShowUnstaggedFiles(diffsToAdd, errMsgLabel, on_result=on_result))
        done_event.wait()
        return holder["ok"]

    def _wait_for_folder_diff_confirmation(self, folder_diffs, errMsgLabel):
        done_event = threading.Event()
        holder = {"ok": False}

        def on_result(confirmed):
            holder["ok"] = confirmed
            done_event.set()

        self._enqueue_ui(lambda: self.showFolderDiffPopup(folder_diffs, errMsgLabel, on_result=on_result))
        done_event.wait()
        return holder["ok"]

    def push_n_commit_Btn_Func(self, errMsgLabel, commit_box):
        errMsgLabel.configure(text=" ", text_color="red")

        if len(self.checked_Pc_objs) < 1:
            messagebox.showwarning("Invalid input", "You should select at least one PC.")
            errMsgLabel.configure(text="You should select at least one PC.", text_color="red")
            return

        commit_msg = commit_box.get(0.0, "end")
        if not bool(re.search(r"[a-zA-Z]", commit_msg)):
            messagebox.showwarning("Invalid input", "You should write a commit to push.")
            errMsgLabel.configure(text="You should write a commit to push.", text_color="red")
            return

        # Get the selected block and checkbox state
        selected_block = self.block_dropdown.get()
        is_not_using_param = self.not_using_param_checkbox.get()

        # Validate that a block is selected when not using parameter is unchecked
        if not is_not_using_param and not selected_block.strip():
            messagebox.showwarning("Invalid input", "You must select a block or check 'Not using this parameter'.")
            errMsgLabel.configure(text="You must select a block.", text_color="red")
            return

        # If checkbox is not checked, prepend the block to the comment
        if not is_not_using_param:
            commit_msg = f"{selected_block.strip()}: {commit_msg}"

        currstatpopup = StatusPopup(self, "Updates: ", "Starting…")
        currstatpopup.update_status("Starting synchronization…", 0.0, "Step 1/6: Fetch & Pull")

        self._set_git_sync_busy(True)
        commit_box.configure(state="disabled")

        self._sync_worker_running = True
        self.after(50, self._drain_sync_jobs)

        def worker():
            try:
                self._run_git_sync_pipeline(currstatpopup, errMsgLabel, commit_box, commit_msg)
            finally:
                self._sync_worker_running = False
                self._enqueue_ui(lambda: self._set_git_sync_busy(False))
                self._enqueue_ui(lambda: commit_box.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _run_git_sync_pipeline(self, currstatpopup, errMsgLabel, commit_box, commit_msg):
        commit_confirm_already_done = False
        self._sync_ui_status(currstatpopup, "Fetching and pulling remote repositories…", 0.05, "Step 1: Fetching and pulling")

        repos_fetched = set()
        for pc in self.checked_Pc_objs:
            for pathToDo in pc.pathFiles.values():
                ssh_client = None
                try:
                    ssh_client = self.create_ssh_connection(pc.host_name, pc.user_name, pc.password)
                    if not ssh_client:
                        self._sync_pipeline_error(
                            f"failed to connect to the pc: {pc.pc_name}",
                            errMsgLabel,
                            commit_box,
                            currstatpopup,
                        )
                        return
                    output_dir = self._display_path(pathToDo["OutputDir"])
                    self._sync_ui_status(
                        currstatpopup,
                        f"Checking Git at destination…\nPC: {pc.pc_name}\nOutput: {output_dir}",
                        0.08,
                        "Step 1/6: Fetch & Pull",
                    )
                    repo_path, dest_err = self.check_destination_git_before_sync_remote(
                        ssh_client, output_dir
                    )
                    if dest_err:
                        self._sync_pipeline_error(
                            dest_err,
                            errMsgLabel,
                            commit_box,
                            currstatpopup,
                            ssh_client,
                        )
                        return
                    if repo_path in repos_fetched:
                        self._sync_ui_status(
                            currstatpopup,
                            f"Already updated this repo (skipping duplicate fetch).\n"
                            f"PC: {pc.pc_name}\nRepo: {repo_path}\nDestination: {output_dir}",
                            0.12,
                            "Step 1/6: Fetch & Pull",
                        )
                        continue
                    branch_name = self.get_current_branch_remote(ssh_client, repo_path)
                    if branch_name is None:
                        self._sync_pipeline_error(
                            "Could not determine current branch.",
                            errMsgLabel,
                            commit_box,
                            currstatpopup,
                            ssh_client,
                        )
                        return
                    self._sync_ui_status(
                        currstatpopup,
                        f"Fetching & pulling remote…\n"
                        f"PC: {pc.pc_name}\n"
                        f"Git repo (root): {repo_path}\n"
                        f"Branch: {branch_name}\n"
                        f"Destination used to locate repo: {output_dir}",
                        0.14,
                        "Step 1/6: Fetch & Pull",
                    )
                    pulled = self.remote_fetch_and_pull(ssh_client, repo_path, branch_name)
                    if not pulled:
                        self._sync_pipeline_error(
                            f"Git pull could not complete for {repo_path} (merge conflict or remote issue). Resolve on the remote PC and retry.",
                            errMsgLabel,
                            commit_box,
                            currstatpopup,
                            ssh_client,
                        )
                        return
                    repos_fetched.add(repo_path)
                    self._sync_ui_status(
                        currstatpopup,
                        f"Fetch & pull finished.\n"
                        f"PC: {pc.pc_name}\n"
                        f"Repository: {repo_path}\n"
                        f"Branch: {branch_name}",
                        0.18,
                        "Step 1/6: Fetch & Pull",
                    )
                except Exception as e:
                    self._sync_pipeline_error(
                        f"An error occurred during fetch/pull: {e}",
                        errMsgLabel,
                        commit_box,
                        currstatpopup,
                        ssh_client,
                    )
                    return
                finally:
                    if ssh_client:
                        ssh_client.close()

        self._sync_ui_status(currstatpopup, "Counting files scheduled to copy…", 0.24, "Step 2/6: Count")
        firstCount = 0
        self.reposPaths = {}
        allrepos_Sets = set()
        for pc in self.checked_Pc_objs:
            thispcRepos_Set = set()
            for pathToDo in pc.pathFiles.values():
                ssh_client = None
                try:
                    ssh_client = self.create_ssh_connection(pc.host_name, pc.user_name, pc.password)
                    if not ssh_client:
                        self._sync_pipeline_error(
                            f"failed to connect to the pc: {pc.pc_name}",
                            errMsgLabel,
                            commit_box,
                            currstatpopup,
                        )
                        return
                    input_folder = self._display_path(pathToDo["inputfolder"])
                    output_dir = self._display_path(pathToDo["OutputDir"])
                    firstCount += self.count_only_files(ssh_client, input_folder, file_type=pathToDo["FileType"])
                    self._sync_ui_status(
                        currstatpopup,
                        f"Counted {firstCount} file(s)/folder(s) scheduled so far…",
                        0.30,
                        "Step 2/6: Count",
                    )
                    currRepo = self.find_nearest_git_root_remote(ssh_client, output_dir)
                    if currRepo is None:
                        self._sync_pipeline_error(
                            "couldn't find repo?? (NO Exception)",
                            errMsgLabel,
                            commit_box,
                            currstatpopup,
                            ssh_client,
                        )
                        return
                    allrepos_Sets.add(currRepo)
                    thispcRepos_Set.add(currRepo)
                except Exception as e:
                    self._sync_pipeline_error(str(e), errMsgLabel, commit_box, currstatpopup, ssh_client)
                    return
                finally:
                    if ssh_client:
                        ssh_client.close()
            if len(thispcRepos_Set) > 0:
                self.reposPaths[pc] = thispcRepos_Set

        if firstCount == 0:
            self._sync_ui_status(
                currstatpopup,
                "No files found to copy (inputs may be empty). Skipping delete/copy.",
                0.32,
                "Step 2/6: Count",
            )

        if len(allrepos_Sets) > 1:
            self._enqueue_ui(lambda: currstatpopup.close_with_delay(delay=1))
            self._sync_pipeline_error(
                "Please check your gits folder' you have to pick only one to commit.",
                errMsgLabel,
                commit_box,
                currstatpopup,
            )
            self._enqueue_ui(lambda: self.repoWarningPopup(self.reposPaths))
            return

        # ── Step 2.5: Folder diff ──────────────────────────────────────────
        self._sync_ui_status(
            currstatpopup,
            "Comparing source vs destination folders…",
            0.34,
            "Step 3/6: Folder diff",
        )
        all_folder_diffs = {}
        folder_diff_jobs = []
        total_diff_ops = 0
        for pc in self.checked_Pc_objs:
            for pathToDo in pc.pathFiles.values():
                ssh_client = None
                try:
                    ssh_client = self.create_ssh_connection(pc.host_name, pc.user_name, pc.password)
                    if not ssh_client:
                        self._sync_pipeline_error(
                            f"failed to connect to the pc: {pc.pc_name}",
                            errMsgLabel,
                            commit_box,
                            currstatpopup,
                        )
                        return
                    inputdir = self._display_path(pathToDo["inputfolder"])
                    output_dir = self._display_path(pathToDo["OutputDir"])
                    diffs = self.compare_folders_remote(
                        ssh_client, inputdir, output_dir, pathToDo["FileType"]
                    )
                    folder_diff_jobs.append(
                        {
                            "pc": pc,
                            "inputdir": inputdir,
                            "output_dir": output_dir,
                            "diffs": diffs,
                        }
                    )
                    total_diff_ops += len(diffs)
                    for rel_path, info in diffs.items():
                        key = f"[{pc.pc_name}]  {output_dir} :: {rel_path}"
                        all_folder_diffs[key] = {
                            "file": key,
                            "type": info["type"],
                        }
                except Exception as e:
                    self._sync_pipeline_error(
                        str(e), errMsgLabel, commit_box, currstatpopup, ssh_client
                    )
                    return
                finally:
                    if ssh_client:
                        ssh_client.close()

        if total_diff_ops > 0:
            if not self._wait_for_folder_diff_confirmation(all_folder_diffs, errMsgLabel):

                def diff_cancelled():
                    errMsgLabel.configure(text="User cancelled operation")
                    self.git_progressbar.stop()
                    self.git_progressbar.configure(mode="determinate")
                    self.git_progressbar.set(0)
                    try:
                        currstatpopup.destroy()
                    except Exception:
                        pass

                self._enqueue_ui(diff_cancelled)
                return
            # User already approved the exact file operations for this run.
            commit_confirm_already_done = True
        # ──────────────────────────────────────────────────────────────────

        count = 0
        if total_diff_ops > 0:
            self._sync_ui_status(
                currstatpopup,
                "Applying folder diffs…",
                0.38,
                "Step 3/6: File operations",
            )
            ops_done = 0
            denom = total_diff_ops if total_diff_ops else 1
            for job in folder_diff_jobs:
                if len(job["diffs"]) == 0:
                    continue
                ssh_client = None
                try:
                    pc = job["pc"]
                    inputdir = job["inputdir"]
                    output_dir = job["output_dir"]
                    prog = 0.38 + (ops_done / denom) * 0.32
                    self._sync_ui_status(
                        currstatpopup,
                        f"Applying diffs…\nFrom: {inputdir}\nTo: {output_dir}",
                        min(prog, 0.70),
                        "Step 3/6: File operations",
                    )
                    ssh_client = self.create_ssh_connection(pc.host_name, pc.user_name, pc.password)
                    if not ssh_client:
                        self._sync_pipeline_error(
                            f"failed to connect to the pc: {pc.pc_name}",
                            errMsgLabel,
                            commit_box,
                            currstatpopup,
                        )
                        return
                    count += self.apply_folder_diffs_remote(
                        ssh_client,
                        source_folder=inputdir,
                        destination_folder=output_dir,
                        diffs=job["diffs"],
                    )
                    ops_done += len(job["diffs"])
                except Exception as e:
                    self._sync_pipeline_error(str(e), errMsgLabel, commit_box, currstatpopup, ssh_client)
                    return
                finally:
                    if ssh_client:
                        ssh_client.close()
        else:
            self._sync_ui_status(
                currstatpopup,
                "No folder differences detected. Skipping file operations.",
                0.40,
                "Step 3/6: File operations",
            )

        if len(self.reposPaths) < 1:

            def run():
                messagebox.showwarning(
                    "Invalid input",
                    "You have to configure 'destination file path' inside a git folder to commit & push.",
                )
                errMsgLabel.configure(
                    text="You have to configure 'destination file path' inside a git folder to commit & push.",
                    text_color="red",
                )
                self.git_progressbar.stop()
                self.git_progressbar.configure(mode="determinate")
                self.git_progressbar.set(0)
                try:
                    currstatpopup.destroy()
                except Exception:
                    pass

            self._enqueue_ui(run)
            return

        for pc, repo_set in self.reposPaths.items():
            for repo_path in repo_set:
                ssh_client = None
                try:
                    ssh_client = self.create_ssh_connection(pc.host_name, pc.user_name, pc.password)
                    if not ssh_client:
                        self._sync_pipeline_error(
                            f"failed to connect to the pc: {pc.pc_name}",
                            errMsgLabel,
                            commit_box,
                            currstatpopup,
                        )
                        return

                    self._sync_ui_status(
                        currstatpopup,
                        "Checking repository changes…",
                        0.72,
                        "Step 4/6: Confirm commit",
                    )
                    is_dirty, self.diffsToAdd = self.check_repo_status_remote(ssh_client, repo_path)
                    current_branch = self.get_current_branch_remote(ssh_client, repo_path)
                    print(f"curr_branch is: = {current_branch}")

                    if current_branch is None:
                        self._sync_pipeline_error(
                            "Could not determine current branch.",
                            errMsgLabel,
                            commit_box,
                            currstatpopup,
                            ssh_client,
                        )
                        return

                    if is_dirty:
                        self._enqueue_ui(lambda: errMsgLabel.configure(text=" "))
                        if (not commit_confirm_already_done) and (not self._wait_for_commit_confirmation(self.diffsToAdd, errMsgLabel)):

                            def cancelled():
                                errMsgLabel.configure(text="User cancelled operation")
                                self.git_progressbar.stop()
                                self.git_progressbar.configure(mode="determinate")
                                self.git_progressbar.set(0)
                                try:
                                    currstatpopup.destroy()
                                except Exception:
                                    pass

                            self._enqueue_ui(cancelled)
                            return
                        elif commit_confirm_already_done:
                            self._sync_ui_status(
                                currstatpopup,
                                "Commit preview skipped (already confirmed folder diff).",
                                0.80,
                                "Step 4/6: Confirm commit",
                            )

                        self._sync_ui_status(
                            currstatpopup,
                            "Committing changes…",
                            0.86,
                            "Step 5/6: Commit",
                        )
                        self._enqueue_ui(lambda: errMsgLabel.configure(text="Committing…"))

                        try:
                            committed_ok = self.commit_remote(ssh_client, repo_path, current_branch, commit_msg)
                            if not committed_ok:
                                self._sync_pipeline_error(
                                    "Commit failed or did not complete.",
                                    errMsgLabel,
                                    commit_box,
                                    currstatpopup,
                                    ssh_client,
                                )
                                return
                        except Exception as e:
                            self._sync_pipeline_error(
                                f"Commit error: {e}",
                                errMsgLabel,
                                commit_box,
                                currstatpopup,
                                ssh_client,
                            )
                            return

                        self._sync_ui_status(
                            currstatpopup,
                            "Pushing to remote…",
                            0.94,
                            "Step 6/6: Push",
                        )
                        self._enqueue_ui(lambda: errMsgLabel.configure(text="Pushing…"))

                        try:
                            pushed_ok = self.push_remote(ssh_client, repo_path, current_branch)
                            if pushed_ok:
                                self._sync_pipeline_success(errMsgLabel, commit_box, currstatpopup)
                            else:
                                self._sync_pipeline_error(
                                    "Push failed or did not complete.",
                                    errMsgLabel,
                                    commit_box,
                                    currstatpopup,
                                    ssh_client,
                                )
                                return
                        except Exception as e:
                            self._sync_pipeline_error(
                                f"Push error: {e}",
                                errMsgLabel,
                                commit_box,
                                currstatpopup,
                                ssh_client,
                            )
                            return
                    else:

                        def no_changes():
                            currstatpopup.update_status("No changes to commit.", 1.0, "Done")
                            errMsgLabel.configure(text="No changes to commit.", text_color="#d97706")
                            try:
                                currstatpopup.destroy()
                            except Exception:
                                pass
                            self.git_progressbar.stop()
                            self.git_progressbar.configure(mode="determinate")
                            self.git_progressbar.set(0)

                        self._enqueue_ui(no_changes)
                except Exception as e:
                    print(f"An error occurred in git sync pipeline: {e}")
                    self._sync_pipeline_error(
                        f"An error occurred: {e}",
                        errMsgLabel,
                        commit_box,
                        currstatpopup,
                        ssh_client,
                    )
                    return
                finally:
                    if ssh_client:
                        ssh_client.close()

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
        fetch_out = stdout.read().decode("utf-8", errors="replace").strip()
        fetch_err = stderr.read().decode("utf-8", errors="replace").strip()
        fetch_code = stdout.channel.recv_exit_status()

        print(f"DEBUG: Fetch stdout: {fetch_out}")
        print(f"DEBUG: Fetch stderr: {fetch_err}")
        print(f"DEBUG: Fetch exit: {fetch_code}")

        if fetch_code != 0:
            raise Exception(f"Git Fetch failed (exit {fetch_code}): {fetch_err or fetch_out}")

        pull_command = (
            f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"Set-Location -Path '{escaped_path}'; git pull origin {branch_name}\""
        )
        print(f"DEBUG: Executing explicit pull command: {pull_command}")

        stdin, stdout, stderr = ssh_client.exec_command(pull_command)
        pull_out = stdout.read().decode("utf-8", errors="replace").strip()
        pull_err = stderr.read().decode("utf-8", errors="replace").strip()
        pull_code = stdout.channel.recv_exit_status()
        combined_pull = f"{pull_out}\n{pull_err}".strip()

        print(f"DEBUG: Pull stdout: {pull_out}")
        print(f"DEBUG: Pull stderr: {pull_err}")
        print(f"DEBUG: Pull exit: {pull_code}")

        if pull_code != 0:
            raise Exception(f"Git Pull failed (exit {pull_code}): {combined_pull}")

        if "conflict" in combined_pull.lower():
            print("DEBUG: WARNING: Merge conflict detected!")
            return False

        print(f"DEBUG: Fetch and Pull completed successfully for branch: {branch_name}")
        return True

    def commit_remote(self, ssh_client: paramiko.SSHClient, repo_path: str, branch_name: str, commit_message: str) -> bool:
        print(f"Remote commit in folder: {repo_path} (branch {branch_name})")
        escaped_path = repo_path.replace("'", "''")

        clean_message = commit_message.strip().replace("\n", " ").replace("\r", " ")
        escaped_message = clean_message.replace("'", "''")

        powershell_command = (
            f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"Set-Location -Path '{escaped_path}'; "
            f"git add --all; "
            f"if (git status --porcelain) {{ git commit -m '{escaped_message}' }}\""
        )

        print(f"DEBUG: Executing commit command: {powershell_command}")

        stdin, stdout, stderr = ssh_client.exec_command(powershell_command)
        stdout.read()
        stderr.read()
        code = stdout.channel.recv_exit_status()
        return code == 0

    def push_remote(self, ssh_client: paramiko.SSHClient, repo_path: str, branch_name: str) -> bool:
        escaped_path = repo_path.replace("'", "''")

        powershell_command = (
            f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"Set-Location -Path '{escaped_path}'; git push origin {branch_name}\""
        )

        print(f"DEBUG: Executing push command: {powershell_command}")

        stdin, stdout, stderr = ssh_client.exec_command(powershell_command)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        code = stdout.channel.recv_exit_status()
        combined = f"{out}\n{err}".strip()
        if code != 0:
            print(f"push_remote failed (exit {code}): {combined}")
            return False
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
        fixBtn = ctk.CTkButton(repoWarningPopupToplevel, corner_radius=3, height=40, border_spacing=10, text="  Add More Path",fg_color="transparent", text_color=("gray10", "gray90"), command= repoWarningPopupToplevel.destroy , image=fixIcon ,hover_color=("gray55","gray55"), font=ctk.CTkFont(size=15, weight="bold"))


        #Needs to show all unstaged files and select the diffs to commit

        
    def gitShowUnstaggedFiles(self, diffsToAdd, errMsgLabel, on_result=None):
        win = ctk.CTkToplevel(self)
        win.geometry("760x700")
        win.minsize(640, 500)
        win.title("Commit Preview")
        win.attributes("-topmost", True)
        win.after(100, win.lift)
        win.after(100, win.focus_set)
        win.grab_set()
        win.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._finish_commit_confirm_dialog(win, on_result, False),
        )
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(win, fg_color=("#1d4ed8", "#1d4ed8"), corner_radius=14, height=64)
        hdr.pack(fill="x", padx=14, pady=(14, 0))
        hdr.pack_propagate(False)
        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="both", expand=True, padx=18, pady=10)
        ctk.CTkLabel(
            hdr_inner,
            text="Commit Preview",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="white",
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            hdr_inner,
            text="Review changed files before commit and push",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#bfdbfe",
            anchor="w",
        ).pack(anchor="w")

        legend = ctk.CTkFrame(win, fg_color="transparent")
        legend.pack(fill="x", padx=18, pady=(10, 2))
        type_colors = {"New": "#16a34a", "Modified": "#d97706", "Deleted": "#dc2626", "Untracked (New)": "#2563eb"}
        for label, color in type_colors.items():
            ctk.CTkLabel(
                legend,
                text=f"  {label}  ",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="white",
                fg_color=color,
                corner_radius=6,
            ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            legend,
            text=f"  {len(diffsToAdd)} file(s) to commit",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray40", "gray65"),
        ).pack(side="left")

        table_outer = ctk.CTkFrame(
            win,
            corner_radius=12,
            fg_color=("gray92", "gray18"),
            border_width=1,
            border_color=("gray82", "gray30"),
        )
        table_outer.pack(fill="both", expand=True, padx=14, pady=(6, 6))
        table = ctk.CTkScrollableFrame(table_outer, fg_color="transparent")
        table.grid_columnconfigure(0, weight=1)
        table.pack(fill="both", expand=True, padx=6, pady=6)

        sorted_items = sorted(diffsToAdd.items(), key=lambda item: item[1].get("file", ""))
        for idx, (_fileName, fileDict) in enumerate(sorted_items):
            status = fileDict.get("type", "Unknown")
            color = type_colors.get(status, "gray")
            row_f = ctk.CTkFrame(table, fg_color=("gray96", "gray22"), corner_radius=8)
            row_f.grid_columnconfigure(1, weight=1)
            row_f.grid(row=idx, column=0, padx=4, pady=3, sticky="ew")
            ctk.CTkLabel(
                row_f,
                text=f" {status} ",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="white",
                fg_color=color,
                corner_radius=5,
                width=108,
            ).grid(row=0, column=0, padx=(8, 10), pady=6, sticky="w")
            ctk.CTkLabel(
                row_f,
                text=fileDict.get("file", ""),
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color=("gray10", "gray88"),
                anchor="w",
                wraplength=560,
                justify="left",
            ).grid(row=0, column=1, padx=4, pady=6, sticky="ew")

        info_lbl = ctk.CTkLabel(
            win,
            text="Confirm to commit these files and push to remote.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray35", "gray70"),
        )
        info_lbl.pack(fill="x", padx=16, pady=(0, 6))

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)
        btn_row.pack(fill="x", padx=14, pady=(0, 14))

        cancel_icon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "CancelBtn.png")), size=(26, 26))
        ctk.CTkButton(
            btn_row,
            text="Cancel",
            image=cancel_icon,
            compound="left",
            corner_radius=10,
            height=42,
            fg_color=("gray88", "gray30"),
            text_color=("gray20", "gray90"),
            hover_color=("gray75", "gray40"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=lambda: self._finish_commit_confirm_dialog(win, on_result, False),
        ).grid(row=0, column=0, padx=(0, 6), pady=4, sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Confirm commit & push",
            image=self.push_n_commit_icon,
            compound="left",
            corner_radius=10,
            height=42,
            fg_color=("#2563eb", "#3b82f6"),
            text_color=("white", "white"),
            hover_color=("#1d4ed8", "#2563eb"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=lambda: self._finish_commit_confirm_dialog(win, on_result, True),
        ).grid(row=0, column=1, padx=(6, 0), pady=4, sticky="ew")

        return win
            


    def showFolderDiffPopup(self, folder_diffs, errMsgLabel, on_result=None):
        """Show a diff popup comparing source vs destination before copy."""
        win = ctk.CTkToplevel(self)
        win.geometry("760x680")
        win.minsize(640, 480)
        win.title("Folder Diff — confirm copy")
        win.attributes("-topmost", True)
        win.after(100, win.lift)
        win.after(100, win.focus_set)
        win.grab_set()
        win.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._finish_commit_confirm_dialog(win, on_result, False),
        )
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(1, weight=1)

        # ── header ──────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(win, fg_color=("#1d4ed8", "#1d4ed8"), corner_radius=14, height=64)
        hdr.pack(fill="x", padx=14, pady=(14, 0))
        hdr.pack_propagate(False)
        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="both", expand=True, padx=18, pady=10)
        ctk.CTkLabel(
            hdr_inner, text="Folder Diff",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="white", anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            hdr_inner, text="Files that will change when copy runs",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#bfdbfe", anchor="w",
        ).pack(anchor="w")

        # ── legend ──────────────────────────────────────────────────────
        legend = ctk.CTkFrame(win, fg_color="transparent")
        legend.pack(fill="x", padx=18, pady=(10, 2))
        TYPE_COLORS = {"New": "#16a34a", "Modified": "#d97706", "Deleted": "#dc2626"}
        for label, color in TYPE_COLORS.items():
            ctk.CTkLabel(
                legend, text=f"  {label}  ",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="white", fg_color=color, corner_radius=6,
            ).pack(side="left", padx=(0, 8))
        total = len(folder_diffs)
        ctk.CTkLabel(
            legend,
            text=f"  {total} file(s) differ" if total else "  Source and destination are identical",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray40", "gray65"),
        ).pack(side="left")

        # ── scrollable file list ─────────────────────────────────────────
        table_outer = ctk.CTkFrame(
            win, corner_radius=12, fg_color=("gray92", "gray18"),
            border_width=1, border_color=("gray82", "gray30"),
        )
        table_outer.pack(fill="both", expand=True, padx=14, pady=(6, 6))
        table = ctk.CTkScrollableFrame(table_outer, fg_color="transparent")
        table.grid_columnconfigure(0, weight=1)
        table.pack(fill="both", expand=True, padx=6, pady=6)

        if not folder_diffs:
            ctk.CTkLabel(
                table,
                text="No differences found — nothing will change.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=("gray40", "gray65"),
            ).grid(row=0, column=0, padx=12, pady=24, sticky="w")
        else:
            for idx, (key, info) in enumerate(sorted(folder_diffs.items())):
                status = info["type"]
                color = TYPE_COLORS.get(status, "gray")
                row_f = ctk.CTkFrame(
                    table, fg_color=("gray96", "gray22"), corner_radius=8,
                )
                row_f.grid_columnconfigure(1, weight=1)
                row_f.grid(row=idx, column=0, padx=4, pady=3, sticky="ew")
                ctk.CTkLabel(
                    row_f, text=f" {status} ",
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    text_color="white", fg_color=color,
                    corner_radius=5, width=72,
                ).grid(row=0, column=0, padx=(8, 10), pady=6, sticky="w")
                ctk.CTkLabel(
                    row_f, text=info["file"],
                    font=ctk.CTkFont(family="Consolas", size=12),
                    text_color=("gray10", "gray88"),
                    anchor="w", wraplength=560, justify="left",
                ).grid(row=0, column=1, padx=4, pady=6, sticky="ew")

        # ── buttons ─────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)
        btn_row.pack(fill="x", padx=14, pady=(0, 14))

        CancelIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "CancelBtn.png")), size=(26, 26))
        ctk.CTkButton(
            btn_row, text="Cancel", image=CancelIcon, compound="left",
            corner_radius=10, height=42,
            fg_color=("gray88", "gray30"), text_color=("gray20", "gray90"),
            hover_color=("gray75", "gray40"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=lambda: self._finish_commit_confirm_dialog(win, on_result, False),
        ).grid(row=0, column=0, padx=(0, 6), pady=4, sticky="ew")

        copy_icon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "DarkMode_PushnCommit.png")), size=(26, 26))
        ctk.CTkButton(
            btn_row, text="Proceed with copy", image=copy_icon, compound="left",
            corner_radius=10, height=42,
            fg_color=("#2563eb", "#3b82f6"), text_color=("white", "white"),
            hover_color=("#1d4ed8", "#2563eb"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=lambda: self._finish_commit_confirm_dialog(win, on_result, True),
        ).grid(row=0, column=1, padx=(6, 0), pady=4, sticky="ew")

        return win


    def pc_settings_popUp(self, pc_obj, zone_obj):

        popup = ctk.CTkToplevel(self)
        popup.geometry("920x960")
        popup.minsize(860, 720)
        popup.title(f"Computer · {pc_obj.pc_name}")
        popup.configure(fg_color=("gray92", "gray14"))
        popup.attributes("-topmost", True)
        popup.after(100, popup.lift)
        popup.after(100, popup.focus_set)
        popup.grab_set()

        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(popup, fg_color=("gray92", "gray14"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        banner = ctk.CTkFrame(header, fg_color=("#1d4ed8", "#1d4ed8"), corner_radius=16, height=100)
        banner.pack(fill="x", padx=18, pady=(18, 8))
        banner.pack_propagate(False)
        banner_inner = ctk.CTkFrame(banner, fg_color="transparent")
        banner_inner.pack(fill="both", expand=True, padx=22, pady=14)

        pcIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "DarkMode_pc.png")), size=(52, 52))
        top_row = ctk.CTkFrame(banner_inner, fg_color="transparent")
        top_row.pack(fill="x")
        ctk.CTkLabel(top_row, text="", image=pcIcon).pack(side="left", padx=(0, 14))
        title_stack = ctk.CTkFrame(top_row, fg_color="transparent")
        title_stack.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_stack,
            text="Manage computer",
            font=UI_FONT_TITLE,
            text_color=("white", "white"),
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            title_stack,
            text=f"{pc_obj.pc_name}  ·  Zone: {zone_obj.Zone_name}",
            font=UI_FONT_SMALL,
            text_color=("#bfdbfe", "#bfdbfe"),
            anchor="w",
        ).pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(
            banner_inner,
            text=(
                "Paths are used on the remote PC over SSH. Use Browse to pick a folder on this PC, "
                "or paste a path (including UNC). Edit the value if the remote layout is different."
            ),
            font=UI_FONT_SMALL,
            text_color=("#e0e7ff", "#e0e7ff"),
            anchor="w",
            wraplength=820,
            justify="left",
        ).pack(fill="x", pady=(10, 0))

        conn_card = ctk.CTkFrame(
            popup,
            corner_radius=16,
            fg_color=("gray98", "gray17"),
            border_width=1,
            border_color=("gray85", "gray32"),
        )
        conn_card.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        conn_card.grid_columnconfigure(1, weight=1)
        oldpcname = pc_obj.pc_name

        def _conn_row(r, label_text, widget_factory):
            ctk.CTkLabel(conn_card, text=label_text, font=UI_FONT_BODY_BOLD, anchor="w").grid(
                row=r, column=0, padx=(16, 10), pady=8, sticky="w"
            )
            w = widget_factory()
            w.grid(row=r, column=1, padx=(0, 16), pady=8, sticky="ew")
            return w

        self.pcnameEntry = _conn_row(
            0,
            "PC name",
            lambda: ctk.CTkEntry(conn_card, font=UI_FONT_BODY, height=36, corner_radius=10),
        )
        self.pcnameEntry.insert(0, oldpcname)
        self.pcnameEntry.configure(state="disabled")

        self.hostnameEntry = _conn_row(
            1,
            "Host / IP",
            lambda: ctk.CTkEntry(conn_card, font=UI_FONT_BODY, height=36, corner_radius=10),
        )
        self.hostnameEntry.insert(0, pc_obj.host_name)
        self.hostnameEntry.configure(state="disabled")

        self.user_nameEntry = _conn_row(
            2,
            r"User (domain\user)",
            lambda: ctk.CTkEntry(conn_card, font=UI_FONT_BODY, height=36, corner_radius=10),
        )
        self.user_nameEntry.insert(0, pc_obj.user_name)
        self.user_nameEntry.configure(state="disabled")

        self.passwordEntry = _conn_row(
            3,
            "Password",
            lambda: ctk.CTkEntry(conn_card, font=UI_FONT_BODY, height=36, corner_radius=10, show="*"),
        )
        self.passwordEntry.insert(0, pc_obj.password)
        self.passwordEntry.configure(state="disabled")

        path_card = ctk.CTkFrame(
            popup,
            corner_radius=16,
            fg_color=("gray98", "gray17"),
            border_width=1,
            border_color=("gray85", "gray32"),
        )
        path_card.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 10))
        path_card.grid_columnconfigure(0, weight=1)
        path_card.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(path_card, text="Folder paths", font=UI_FONT_BODY_BOLD, anchor="w").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 4)
        )
        ctk.CTkLabel(
            path_card,
            text="Source · Browse or paste  ·  File type (e.g. ALL, csv)  ·  Output / Git folder · Browse or paste",
            font=UI_FONT_SMALL,
            text_color=("gray40", "gray65"),
            anchor="w",
            wraplength=840,
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))

        TitleTableRow = ctk.CTkFrame(path_card, fg_color="transparent")
        TitleTableRow.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 4))
        for col, wt in ((0, 1), (1, 0), (2, 0), (3, 1), (4, 0), (5, 0)):
            TitleTableRow.grid_columnconfigure(col, weight=wt)

        hdr = [
            (0, "Source path"),
            (1, ""),
            (2, "Type"),
            (3, "Output (Git)"),
            (4, ""),
            (5, ""),
        ]
        for col, txt in hdr:
            ctk.CTkLabel(
                TitleTableRow,
                text=txt,
                font=UI_FONT_SMALL,
                text_color=("gray45", "gray60"),
            ).grid(row=0, column=col, padx=4, pady=4, sticky="w")

        self.intoTablePathFiles_frames = ctk.CTkScrollableFrame(
            path_card,
            corner_radius=12,
            fg_color=("gray96", "gray15"),
            border_width=1,
            border_color=("gray82", "gray30"),
            height=300,
        )
        self.intoTablePathFiles_frames.grid_columnconfigure(0, weight=1)
        self.intoTablePathFiles_frames.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 10))

        self.filesPathCount = 1
        self.pathsElements = {}
        for path in pc_obj.pathFiles.values():
            newPathRow = self.addingPathRowToTable(pathsElements=self.pathsElements, path=path)
            for _k, elem in self.pathsElements[newPathRow].items():
                elem.configure(state="disabled")

        self.addMorePathIcon = ctk.CTkImage(
            Image.open(os.path.join(images_folder_path, "DarkMode_AddObject.png")), size=(36, 36)
        )
        self.addMorePathBtn = ctk.CTkButton(
            path_card,
            corner_radius=12,
            height=42,
            border_spacing=10,
            text="  Add path row",
            fg_color=("gray88", "gray28"),
            text_color=("gray15", "gray90"),
            command=lambda x=self.pathsElements: self.addingPathRowToTable(x),
            image=self.addMorePathIcon,
            hover_color=("gray75", "gray38"),
            font=UI_FONT_BODY_BOLD,
        )
        self.addMorePathBtn.configure(state="disabled")
        self.addMorePathBtn.grid(row=4, column=0, padx=12, pady=(0, 14), sticky="w")

        self.PcBtnsRow = ctk.CTkFrame(popup, fg_color="transparent")
        self.PcBtnsRow.grid_rowconfigure(0, weight=1)
        for c in (0, 1, 2):
            self.PcBtnsRow.grid_columnconfigure(c, weight=0)

        self.savePcInformationIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "SaveBtn.png")), size=(28, 28))
        self.savePcInformationBtn = ctk.CTkButton(
            self.PcBtnsRow,
            corner_radius=12,
            height=44,
            border_spacing=10,
            text="Save",
            fg_color=("#16a34a", "#22c55e"),
            text_color=("white", "white"),
            command=lambda x=pc_obj, y=popup, z=zone_obj, w=self.pathsElements, t=oldpcname: self.HandleWithSavePcBtn(
                x, y, z, w, t
            ),
            image=self.savePcInformationIcon,
            hover_color=("#15803d", "#16a34a"),
            font=UI_FONT_BODY_BOLD,
        )
        self.savePcInformationBtn.grid(row=0, column=2, padx=8, pady=16, sticky="e")

        self.EditPcInformationIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "EditBtn.png")), size=(28, 28))
        self.EditPcInformationBtn = ctk.CTkButton(
            self.PcBtnsRow,
            corner_radius=12,
            height=44,
            border_spacing=10,
            text="Edit",
            fg_color=("#2563eb", "#3b82f6"),
            text_color=("white", "white"),
            command=lambda x=self.pathsElements: self.HandleWithEditBtn(x),
            image=self.EditPcInformationIcon,
            hover_color=("#1d4ed8", "#2563eb"),
            font=UI_FONT_BODY_BOLD,
        )
        self.EditPcInformationBtn.grid(row=0, column=1, padx=8, pady=16, sticky="e")

        self.CancelPcInformationIcon = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "CancelBtn.png")), size=(28, 28))
        self.CancelPcInformationBtn = ctk.CTkButton(
            self.PcBtnsRow,
            corner_radius=12,
            height=44,
            border_spacing=10,
            text="Cancel",
            fg_color=("gray88", "gray30"),
            text_color=("gray20", "gray90"),
            command=popup.destroy,
            image=self.CancelPcInformationIcon,
            hover_color=("gray75", "gray40"),
            font=UI_FONT_BODY_BOLD,
        )

        self.PcBtnsRow.grid(row=3, column=0, sticky="e", padx=18, pady=(0, 18))

    def addingPathRowToTable(self, pathsElements, path=None):
        if path is None:
            path = {"inputfolder": "Empty", "FileType": "ALL", "OutputDir": "Empty"}

        PathRow = ctk.CTkFrame(
            self.intoTablePathFiles_frames,
            corner_radius=12,
            fg_color=("gray94", "gray20"),
            border_width=1,
            border_color=("gray82", "gray32"),
        )
        PathRow.grid_rowconfigure(0, weight=1)
        for col, wt in ((0, 1), (1, 0), (2, 0), (3, 1), (4, 0), (5, 0)):
            PathRow.grid_columnconfigure(col, weight=wt)

        inputEntry = ctk.CTkEntry(
            PathRow,
            font=UI_FONT_BODY,
            height=34,
            corner_radius=10,
            placeholder_text="Paste or Browse…",
        )
        inputEntry.insert(0, path["inputfolder"])
        inputEntry.grid(row=0, column=0, padx=(8, 4), pady=10, sticky="ew")

        inputBrowseBtn = self._make_path_browse_button(
            PathRow, inputEntry, "Select source folder"
        )
        inputBrowseBtn.grid(row=0, column=1, padx=(0, 8), pady=10, sticky="ew")

        FileTypeEntry = ctk.CTkEntry(
            PathRow,
            width=80,
            font=UI_FONT_BODY,
            height=34,
            corner_radius=10,
            placeholder_text="ALL",
        )
        FileTypeEntry.insert(0, path["FileType"])
        FileTypeEntry.grid(row=0, column=2, padx=4, pady=10, sticky="ew")

        OutputDirEntry = ctk.CTkEntry(
            PathRow,
            font=UI_FONT_BODY,
            height=34,
            corner_radius=10,
            placeholder_text="Git / output folder",
        )
        OutputDirEntry.insert(0, path["OutputDir"])
        OutputDirEntry.grid(row=0, column=3, padx=(8, 4), pady=10, sticky="ew")

        outputBrowseBtn = self._make_path_browse_button(
            PathRow, OutputDirEntry, "Select output (Git) folder"
        )
        outputBrowseBtn.grid(row=0, column=4, padx=(0, 4), pady=10, sticky="ew")

        deletePathRowImage = ctk.CTkImage(Image.open(os.path.join(images_folder_path, "deleteIcon.png")), size=(28, 28))
        deletePathRowBtn = ctk.CTkButton(
            PathRow,
            corner_radius=10,
            width=44,
            height=34,
            border_spacing=6,
            text="",
            fg_color=("gray88", "gray30"),
            text_color=("gray15", "gray90"),
            command=lambda x=pathsElements, y=PathRow: self.deleteRowFromTable(x, y),
            image=deletePathRowImage,
            hover_color=("#b91c1c", "#dc2626"),
            anchor="center",
        )
        deletePathRowBtn.grid(row=0, column=5, padx=8, pady=10, sticky="e")

        pathsElements[PathRow] = {
            "inputEntry": inputEntry,
            "inputBrowseBtn": inputBrowseBtn,
            "FileTypeEntry": FileTypeEntry,
            "OutputDirEntry": OutputDirEntry,
            "outputBrowseBtn": outputBrowseBtn,
            "deletePathRowBtn": deletePathRowBtn,
        }

        PathRow.grid(row=self.filesPathCount, column=0, sticky="ew", padx=4, pady=6)
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
    
    def saltThePassword(self, password):
        salt = "EinavsAPP"
        new_pass = password + salt
        hashOBJ = hashlib.sha256()
        hashOBJ.update(new_pass.encode('utf-8'))
        return hashOBJ.hexdigest()


    def find_nearest_git_root_remote(self, ssh_client, path):
        print(f"DEBUG: Finding Git root for: {path}")
        folder = path.replace("/", "\\").rstrip("\\").replace("'", "''")
        
        command = (
            f"powershell.exe -NoProfile -Command "
            f"\"Set-Location -Path '{folder}'; git rev-parse --show-toplevel\""
        )
        
        stdin, stdout, stderr = ssh_client.exec_command(command)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        
        if out:
            fixed_path = out.replace("/", "\\")
            print(f"DEBUG: Git root found: {fixed_path}")
            return fixed_path
            
        print(f"DEBUG: No Git root found. Error: {err}")
        return None

    def check_destination_git_before_sync_remote(self, ssh_client, output_dir: str):
        """
        Before fetch/pull: ensure the destination path exists, lies inside a Git work tree,
        and the repository root has a .git entry (directory or gitfile).

        Returns (repo_root: str | None, error_message: str | None).
        """
        ps_folder = output_dir.replace("/", "\\").rstrip("\\").replace("'", "''")

        exists_cmd = (
            f"powershell.exe -NoProfile -Command "
            f"\"if (Test-Path -LiteralPath '{ps_folder}') {{ '1' }} else {{ '0' }}\""
        )
        stdin, stdout, stderr = ssh_client.exec_command(exists_cmd)
        if stdout.read().decode("utf-8", errors="replace").strip() != "1":
            return None, f"Destination folder does not exist on the remote PC: {output_dir}"

        inside_cmd = (
            f"powershell.exe -NoProfile -Command "
            f"\"Set-Location -LiteralPath '{ps_folder}'; "
            f"git rev-parse --is-inside-work-tree 2>$null\""
        )
        stdin, stdout, stderr = ssh_client.exec_command(inside_cmd)
        inside = stdout.read().decode("utf-8", errors="replace").strip().lower()
        if inside != "true":
            return None, (
                f"Destination is not inside a Git repository. "
                f"Pick an output folder under a cloned repo (.git). Path: {output_dir}"
            )

        repo_root = self.find_nearest_git_root_remote(ssh_client, output_dir)
        if not repo_root:
            return None, f"Could not resolve Git repository root for destination: {output_dir}"

        escaped_root = repo_root.rstrip("\\").replace("'", "''")
        gitmeta_cmd = (
            f"powershell.exe -NoProfile -Command "
            f"\"if (Test-Path -LiteralPath '{escaped_root}\\.git') {{ '1' }} else {{ '0' }}\""
        )
        stdin, stdout, stderr = ssh_client.exec_command(gitmeta_cmd)
        if stdout.read().decode("utf-8", errors="replace").strip() != "1":
            return None, (
                f"No .git metadata at repository root (invalid or incomplete repo): {repo_root}"
            )

        return repo_root, None

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

    def compare_folders_remote(self, ssh_client, source_folder, dest_folder, file_type="ALL"):
        """Compare source vs destination on the remote PC.
        Returns {relative_path: {'file': relative_path, 'type': 'New'|'Modified'|'Deleted'}}.
        'New'      – exists in source, not in dest.
        'Modified' – exists in both but different file size.
        'Deleted'  – exists in dest but not in source (will be removed by diff apply step).
        """
        src = source_folder.replace("/", "\\").rstrip("\\").replace("'", "''")
        dst = dest_folder.replace("/", "\\").rstrip("\\").replace("'", "''")
        filter_str = "*" if file_type.upper() == "ALL" else f"*.{file_type.lstrip('.')}"

        def _list_files(folder_escaped):
            cmd = (
                f"powershell.exe -NoProfile -Command "
                f"\"Get-ChildItem -Path '{folder_escaped}' -Filter '{filter_str}' "
                f"-File -Recurse -ErrorAction SilentlyContinue "
                f"| ForEach-Object {{ "
                f"  $rel = $_.FullName.Substring('{folder_escaped}'.Length).TrimStart('\\\\'); "
                f"  $rel + '|' + $_.Length "
                f"}}\""
            )
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            raw = stdout.read().decode('utf-8', errors='replace').strip()
            result = {}
            for line in raw.splitlines():
                line = line.strip()
                if '|' in line:
                    parts = line.rsplit('|', 1)
                    rel = parts[0].strip()
                    size = parts[1].strip() if len(parts) > 1 else '0'
                    if rel:
                        result[rel] = size
            return result

        src_files = _list_files(src)
        dst_files = _list_files(dst)

        diffs = {}
        for rel, size in src_files.items():
            if rel not in dst_files:
                diffs[rel] = {'file': rel, 'type': 'New'}
            elif size != dst_files[rel]:
                diffs[rel] = {'file': rel, 'type': 'Modified'}
        for rel in dst_files:
            if rel not in src_files:
                diffs[rel] = {'file': rel, 'type': 'Deleted'}
        return diffs

    def apply_folder_diffs_remote(self, ssh_client, source_folder, destination_folder, diffs, batch_size=100):
        """Apply New/Modified/Deleted operations based on compare_folders_remote output, batching to avoid command line length limits."""
        src = source_folder.replace("/", "\\").rstrip("\\").replace("'", "''")
        dst = destination_folder.replace("/", "\\").rstrip("\\").replace("'", "''")

        copy_list = []
        delete_list = []
        for rel_path, info in diffs.items():
            status = str(info.get("type", "")).strip().lower()
            if status in ("new", "modified"):
                copy_list.append(rel_path)
            elif status == "deleted":
                delete_list.append(rel_path)

        def _to_ps_array(values):
            if len(values) == 0:
                return "@()"
            escaped = ["'" + str(v).replace("'", "''") + "'" for v in values]
            return "@(" + ",".join(escaped) + ")"

        total_copied = 0
        total_deleted = 0

        # Helper to run a batch of copy/delete
        def run_batch(copy_batch, delete_batch):
            copy_arr = _to_ps_array(copy_batch)
            delete_arr = _to_ps_array(delete_batch)
            powershell_command = (
                f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
                f"\"$src='{src}'; $dst='{dst}'; "
                f"$copyList={copy_arr}; $deleteList={delete_arr}; "
                f"$copied=0; $deleted=0; "
                f"foreach ($rel in $deleteList) {{ "
                f"  $target = Join-Path $dst $rel; "
                f"  if (Test-Path -LiteralPath $target) {{ Remove-Item -LiteralPath $target -Force; $deleted++ }} "
                f"}}; "
                f"foreach ($rel in $copyList) {{ "
                f"  $srcFile = Join-Path $src $rel; "
                f"  if (Test-Path -LiteralPath $srcFile) {{ "
                f"    $dstFile = Join-Path $dst $rel; "
                f"    $dstDir = Split-Path -Path $dstFile -Parent; "
                f"    if ($dstDir -and -not (Test-Path -LiteralPath $dstDir)) {{ New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }}; "
                f"    Copy-Item -LiteralPath $srcFile -Destination $dstFile -Force; $copied++ "
                f"  }} "
                f"}}; "
                f"Write-Output ('COPIED=' + $copied + ';DELETED=' + $deleted)\""
            )
            stdin, stdout, stderr = ssh_client.exec_command(powershell_command)
            out = stdout.read().decode("utf-8", errors="replace").strip()
            err = stderr.read().decode("utf-8", errors="replace").strip()
            code = stdout.channel.recv_exit_status()
            if code != 0:
                raise Exception(f"Apply folder diffs failed (exit {code}): {err or out}")
            copied = 0
            deleted = 0
            m = re.search(r"COPIED=(\\d+);DELETED=(\\d+)", out)
            if m:
                copied = int(m.group(1))
                deleted = int(m.group(2))
            return copied, deleted

        # Process deletes in batches
        for i in range(0, len(delete_list), batch_size):
            batch = delete_list[i:i+batch_size]
            c, d = run_batch([], batch)
            total_deleted += d

        # Process copies in batches
        for i in range(0, len(copy_list), batch_size):
            batch = copy_list[i:i+batch_size]
            c, d = run_batch(batch, [])
            total_copied += c

        return total_copied + total_deleted

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


    def clear_remote_folder(self, ssh_client, folder_path):
        print(f"DEBUG: Clearing remote folder: {folder_path}")
        escaped_path = folder_path.replace("/", "\\").rstrip("\\").replace("'", "''")
        command = (
            f"powershell.exe -NoProfile -Command "
            f"\"if (Test-Path '{escaped_path}') {{ Get-ChildItem -Path '{escaped_path}' | Remove-Item -Recurse -Force }}\""
        )
        try:
            stdin, stdout, stderr = ssh_client.exec_command(command)
            stdout.read() # המתנה לסיום הפעולה
        except Exception as e:
            print(f"DEBUG: Failed to clear folder {folder_path}: {e}")



    def copy_files_by_type(self, ssh_client, source_folder, destination_folder, file_type="ALL"):
        print(f"DEBUG: Copying files via CMD from {source_folder} to {destination_folder}")
        
        src = source_folder.replace("/", "\\").rstrip("\\")
        dst = destination_folder.replace("/", "\\").rstrip("\\")
        file_pattern = "*" if file_type.upper() == "ALL" else f"*.{file_type.lstrip('.')}"
        
        command = f'xcopy "{src}\\{file_pattern}" "{dst}\\" /s /e /y /i'
        print(f"DEBUG: Executing CMD: {command}")
        
        stdin, stdout, stderr = ssh_client.exec_command(command)

        try:
            raw_output = stdout.read()
            # מנסים לפענח כ-utf-8, אם נכשל עוברים ל-cp1252 (סטנדרטי ל-Windows)
            output = raw_output.decode('utf-8', errors='replace').splitlines()
        except Exception as e:
            print(f"Decoding error: {e}")
            return 0
        
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