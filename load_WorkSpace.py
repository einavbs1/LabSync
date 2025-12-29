import pickle
import sys
from models import WorkSpace, Zone, Room, Computer, Settings
from tkinter import messagebox
import mock_create_workspace
from customtkinter import CTkInputDialog
import customtkinter as ctk

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
        print_loaded_data(loaded_data)
        return loaded_data
        
    except Exception as e:
        print(f"--- ERROR! ---")
        print(f"File not found: '{INPUT_FILE}'")
        print("Starting first_time_setup")
        first_time_setup(INPUT_FILE)
        

def first_time_setup(INPUT_FILE):
    user_agree = ""
    while (user_agree!="I agree"):
        dialog = ctk.CTkInputDialog(title="First time setup", text=f"First time setup\n\n File not found: '{INPUT_FILE}'  -  Couldn't find DB\n\n Do you want to create a new workspace?\n It will destroy any previous DB, type 'I agree'.")
        user_agree = dialog.get_input()
        if user_agree is None:
            print(f"user canclled operation")
            return None
        elif user_agree != "I agree":
            messagebox.showwarning("Invalid input", "Please write 'I agree' to continue, or cancel to exit.")
    if user_agree is not None:
        print("creating mock DB")
        mock_create_workspace()
        print("Loading new DB")
        res = load_data_from_file()
        return res



def print_loaded_data(pklFile):
    """
    מדפיס ייצוג יפה של הנתונים שנטענו
    """
    if not data_dictionary:
        print("No data to display.")
        return
    settings_dict = None
    data_dictionary = None
    print("\n--- Contents of Loaded Data ---")
    for symbol, obj in pklFile.items():
        print(f"key is {symbol}, val is {obj}")
        if (settings_dict is None):
            settings_dict = obj
        else:
            data_dictionary = obj

    # settings_dict        = pklFile['settings']
    print(f"\n  ► Settings (Type: {type(settings_dict)})")
    for key, val in settings_dict.items():
        print(f"    - {key}: {val}")

    # data_dictionary = pklFile['data']

    print(f"Type of loaded data: {type(data_dictionary)}")
    print(f"Found {len(data_dictionary)} WorkSpaces:")
    dataDict = {}
    # data_dictionary הוא המילון ששמרנו: { "שם": <אובייקט WorkSpace> }
    for ws_name, ws_obj in data_dictionary.items():
        print(f"\n  ► WorkSpace: {ws_name} (Type: {type(ws_obj)})")
        dataDict[ws_name]=  ws_obj
        # אנחנו יכולים לקרוא לפונקציות של האובייקט שנטען!
        zones = ws_obj.get_all_Zones()
        print(f"    Contains {len(zones)} zones:")
        
        for zone in zones:
            print(f"    - Zone: {zone.Zone_name}")
            rooms = zone.get_all_rooms()
            for room in rooms:
                print(f"      - Room: {room.room_name} ({room.get_computer_count()} computers)")

    dictToTransfer ={
        'data' : dataDict,
        'settings' : settings_dict
    }
    return dictToTransfer


# --- הבלוק הראשי שמריץ את הסקריפט ---
if __name__ == "__main__":
    all_data = load_data_from_file()
    
    if all_data:
        print_loaded_data(all_data)

