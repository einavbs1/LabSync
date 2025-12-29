###################################################################
###################################################################
###################################################################

class Computer:
    """ Class to make computer objects """
    def __init__(self, pc_name="null", host_name="null", user_name="null", password="null", pathFiles={}):
        self.pc_name = pc_name
        self.host_name = host_name
        self.user_name = user_name
        self.password = password
        self.pathFiles = pathFiles
        self.isChecked = True
        # self.pathFiles = {0 : {"inputfolder"    : "C://Users//Lab01//Desktop//ThisFolderToBackup",
        #                         "FileType"      : "ALL",
        #                         "OutputDir"     : "D://repoFiles//NewChangesHere"},
                        
        #                   1 : {"inputfolder"    : "C://Users//Lab01//Desktop//AnotherFolder",
        #                         "FileType"      : ".ssf",
        #                         "OutputDir"     : "D://repoFiles//NewChangesHere"},
        #                 #SAME FOLDER BUT NOT SAME FILETYPE :)
        #                   2 : {"inputfolder"    : "C://Users//Lab01//Desktop//AnotherFolder",
        #                         "FileType"      : ".Bak",
        #                         "OutputDir"     : "D://repoFiles//NewChangesHere"},
        #                 #AGAINNN: SAME FOLDER BUT NOT SAME FILETYPE :)      
        #                   3 : {"inputfolder"    : "C://Users//Lab01//Desktop//AnotherFolder",
        #                         "FileType"      : ".ppt",
        #                         "OutputDir"     : "D://repoFiles//NewChangesHere"},
        #                 }

        def pathfilesLens(self):
            return len(pathFiles)

        def addPathFile(self,inputfolder,outputdir ,typefile = "ALL"):
            tempPath = {}
            tempPath["inputfolder"] = inputfolder
            tempPath["FileType"] = typefile
            tempPath["OutputDir"] = outputdir
            self.pathFiles[self.pathfilesLens()] = tempPath
###################################################################
###################################################################
###################################################################
class Room:
    """ Class to make computer objects """
    def __init__(self, room_name):
        self.room_name = room_name
        self.computers = {}

    # def _name(self):
    #     return self.room_name

    # def addComputer(self, Computer_obj):
    #     pc_name = Computer_obj.host_name
    #     if pc_name in self.computers:
    #         raise ValueError(f"The computer: '{pc_name}' is already exists in '{self.room_name}'. ")
    #     else:
    #         self.computers[pc_name] = Computer_obj
    #         return True
        
    # def removeComputer(self, Computer_obj):
    #     pc_name = Computer_obj.host_name
    #     if pc_name not in self.computers:
    #         raise ValueError(f"The computer: '{pc_name}' is not exists in '{self.room_name}'. ")
    #     else:
    #         del self.computers[pc_name]
    #         return True

    # def get_all_computers(self):
    #     return list(self.computers.values())

    # def get_computer_count(self):
    #     return len(self.computers)
###################################################################
###################################################################
###################################################################
class Zone:
    def __init__(self, Zone_name):
        self.Zone_name = Zone_name
        self.computers = {}
        self.isFav = False

    def addComputer(self, Computer_obj):
        pc_name = Computer_obj.pc_name
        if pc_name in self.computers:
            raise ValueError(f"The computer: '{pc_name}' is already exists in '{self.Zone_name}'. ")
        else:
            self.computers[pc_name] = Computer_obj
            return True
        
    def removeComputer(self, Computer_obj):
        pc_name = Computer_obj.pc_name
        if pc_name not in self.computers:
            raise ValueError(f"The computer: '{pc_name}' is not exists in '{self.Zone_name}'. ")
        else:
            del self.computers[pc_name]
            return True

    def get_all_computers(self):
        return list(self.computers.values())

    def get_computer_count(self):
        return len(self.computers)

    def editRepoPath(self, repoPath):
        self.repoPath = repoPath

    # def addRoom(self, Room_Obj):
    #     room_name = Room_Obj.room_name
    #     if room_name in self.rooms:
    #         raise ValueError(f"The room: '{room_name}' is already exists in '{self.Zone_name}'. ")
    #     else:
    #         self.rooms[room_name] = Room_Obj
    #         return True
        
    # def removeRoom(self, Computer_obj):
    #     room_name = Room_Obj.room_name
    #     if room_name not in self.rooms:
    #         raise ValueError(f"The room: '{room_name}' is not exists in '{self.Zone_name}'. ")
    #     else:
    #         del self.rooms[room_name]
    #         return True

    # def get_room_by_name(self, room_name):
    #     return self.rooms.get(room_name)

    # def get_all_rooms(self):
    #     return list(self.rooms.values())
###################################################################
###################################################################
###################################################################
class WorkSpace:
    def __init__(self, WorkSpace_name):
        self.WorkSpace_name = WorkSpace_name
        self.Zones = {}

    def addZone(self, Zone_obj):
        Zone_name = Zone_obj.Zone_name
        if Zone_name in self.Zones:
            raise ValueError(f"The room: '{Zone_name}' is already exists in '{self.WorkSpace_name}'. ")
        else:
            self.Zones[Zone_name] = Zone_obj
            return True

    def removeZone(self, Zone_obj):
        Zone_name = Zone_obj.Zone_name
        if Zone_name not in self.Zones:
            raise ValueError(f"The room: '{Zone_name}' is not exists in '{self.WorkSpace_name}'. ")
        else:
            del self.Zones[Zone_name]
            return True

    def get_Zone_by_name(self, Zone_name):
        return self.Zones.get(Zone_name)

    def get_all_Zones(self):
        return list(self.Zones.values())
###################################################################
###################################################################
###################################################################
# class Settings(dict):
#     def __init__(self, *args, **kwargs):

class Settings():
    def __init__(self):
        # super().__init__(*args, **kwargs)
        # self.__dict__ = self
        self.startHomePage = ""
        self.theme = "Dark"
        self.dataPath = ""
        self.favorites = {}

    def addFav(self, Zone_obj):
        Zone_name = Zone_obj.Zone_name
        if Zone_name in self.favorites:
            raise ValueError(f"The room: '{Zone_name}' is already exists in favorites settings. ")
        else:
            self.favorites[Zone_name] = Zone_obj
            return True

    def removeFav(self, Zone_obj):
        Zone_name = Zone_obj.Zone_name
        if Zone_name not in self.favorites:
            raise ValueError(f"The room: '{Zone_name}' is not exists in favorites settings. ")
        else:
            del self.favorites[Zone_name]
            return True