import pickle, time
import sys
from models import Computer, Room, Zone, WorkSpace, Settings
from customtkinter import CTkInputDialog
import customtkinter as ctk
import runpy
from tkinter import messagebox

class NullWriter:
    def write(self, text):
        pass
    def flush(self):
        pass

if sys.stdout is None:
    sys.stdout = NullWriter()
if sys.stderr is None:
    sys.stderr = NullWriter()



INPUT_FILE = "sync_lab_workspace.pkl"

def load_data_from_file():
    
    try:
        with open(INPUT_FILE, "rb") as f:
            loaded_data = pickle.load(f)
            
        print(f"--- SUCCESS! ---")
        print(f"Data successfully loaded from '{INPUT_FILE}'")
        try:
            # print_loaded_data(loaded_data)
            return print_loaded_data(loaded_data)
        except Exception as e:
            print(f"- new err- {e}")
        
    except Exception as e:
        print(f"--- ERROR! --- {e}")
        print(f"File not found: '{INPUT_FILE}'")
        print("Starting first_time_setup")
        # first_time_setup(INPUT_FILE)
        datapkl = {
        'settings'  : Settings(),
        'data'      : {}
        }
        return print_loaded_data(datapkl)
        return None
        

def first_time_setup(INPUT_FILE):
    user_agree = ""
    while (user_agree!="I agree"):
        dialog = ctk.CTkInputDialog(title="First time setup", text=f"Couldn't find DB\n Error: File not found: '{INPUT_FILE}'\n\n Do you want to create a new workspace?\n It will destroy any previous DB, type 'I agree'.")
        user_agree = dialog.get_input()
        if user_agree is None:
            print(f"user canclled operation")
            return None
        elif user_agree != "I agree":
            messagebox.showwarning("Invalid input", "Please write 'I agree' to continue, or cancel to exit.")
    if user_agree is not None:
        dialog.destroy()
        print("creating mock DB")
        mock_create_workspace.main()
        print("Loading new DB")
 
        
        



def print_loaded_data(loaded_data):
    """
    מדפיס ייצוג יפה של הנתונים שנטענו
    """
    if not loaded_data:
        print("No data to display.")
        return

    print("\n--- Contents of Loaded Data ---")
    settings_dict = loaded_data['settings']
    data_dictionary = loaded_data['data']

    print(f"\n  ► Settings (Type: {type(settings_dict)})")
    print(f"    - startHomePage: {settings_dict.startHomePage}")
    print(f"    - theme: {settings_dict.theme}")
    print(f"    - dataPath: {settings_dict.dataPath}")
    print(f"    - favorites: {settings_dict.favorites}")

    # data_dictionary = pklFile['data']
    print(f"Type of loaded data: {type(data_dictionary)}")
    print(f"Found {len(data_dictionary)} WorkSpaces:")
    dataDict = {}
    # data_dictionary הוא המילון ששמרנו: { "שם": <אובייקט WorkSpace> }
    for ws_name, ws_obj in data_dictionary.items():
        print(f"\n  ► WorkSpace: {ws_name} (Type: {type(ws_obj)})")
        dataDict[ws_name] = ws_obj
        zones = ws_obj.get_all_Zones()
        print(f"    Contains {len(zones)} zones:")
        
        for zone in zones:
            print(f"    - Zone: {zone.Zone_name} ({zone.get_computer_count()} computers)")
            computers = zone.get_all_computers()
            for computer_obj in computers:
                print(f"      - pc: {computer_obj.pc_name} ")
                
    dictToTransfer ={
        'data' : dataDict,
        'settings' : settings_dict
    }

    return dictToTransfer


def updateDB(data_dict, settings_dict):
    DB_dict = {
        'data'      : data_dict,
        'settings'  : settings_dict
    }
    try:
        with open(INPUT_FILE, "wb") as f:
            pickle.dump(DB_dict, f)
            succ_msg = "Data saved successfully" ################################
            print(f"{succ_msg}")  ################################
            return True

    except Exception as e:
        err_msg = f"Failed to save data: {e}" ################################
        print(f"We got a problem with savinggg: {err_msg}")  ################################
        return err_msg