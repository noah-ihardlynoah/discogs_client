import discogs_client
from tkinter import *
from tkinter import filedialog, messagebox
import mutagen

class Window(Tk):
    # to create an instance: Window(title,geometry) OR Window(title,geometry,icon)
    def __init__(self,*args):
        super().__init__()
        self.title(args[0])
        if len(args) == 2:
            if args[1].find(".") == -1:
                self.geometry(args[1])
            else:
                img = PhotoImage("photo", file=args[1])
                self.call('wm', 'iconphoto', self._w, img)
        elif len(args) == 3:
            self.geometry(args[1])
            img = PhotoImage("photo", file=args[2])
            self.call('wm', 'iconphoto', self._w, img)

class LoginWindow(Window):
    def __init__(self,*args):
        if len(args) == 1:
            super().__init__(args[0])
        elif len(args) == 2:
            super().__init__(args[0],args[1])
        else:
            super().__init__(args[0],args[1],args[2])
        
        # Widget grid
        self.heading_label = Label(self, text="Login Using User Token", font=("San Francisco", 15, "bold"))
        self.heading_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        self.key_label = Label(self, text="Token:", font=("San Francisco", 13))
        self.key_label.grid(row=1, column=0,padx=(5,0), pady=5, sticky=E)
        self.key_entry = Entry(self)
        self.key_entry.grid(row=1, column=1,padx=(0,5), pady=5)
        self.login_button = Button(self, text="Login", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
    def login(self):
        key = self.key_entry.get()
        if key:
            try:
                global client
                client = discogs_client.Client("Discogs Metadata Tool/1.0", user_token=key)
                MainWindow()
            except Exception as e:
                messagebox.showerror("Login Error", f"Login failed: {str(e)}")
        else:
            messagebox.showerror("Login Error", "Please enter a user token to login.")
        
class MainWindow(Window):
    def __init__(self):
        user = client.identity()
        super().__init__(f"Discogs Metadata Tool: {user.username}: Logged In")        
        # self.welcome_label = Label(self, text=f"Welcome, {self.username}!", font=("San Francisco", 14), justify=LEFT)
        # self.welcome_label.grid(row=0, column=0, padx=5, pady=5)
        self.resizable(False, False)
        self.collection_label = Label(self, text="Collection:", font=("San Francisco", 12), justify=LEFT)
        self.collection_label.grid(row=1, column=0, padx=5, pady=5)
        self.collection_listbox = Listbox(self, width=50, height=10)
        self.collection_listbox.grid(row=2, column=0,columnspan=4, padx=5,pady=5)
        self.collection_list = []
        for item in user.collection_folders[0].releases:
            self.collection_list.append(item)
        self.collection_list.sort(key=(lambda x: (x.release.artists[0].name, x.release.title)))
        for item in self.collection_list:
            self.collection_listbox.insert(END, f"{item.release.artists[0].name} - {item.release.title}")
        self.collection_scrollbar = Scrollbar(self, orient=VERTICAL, command=self.collection_listbox.yview)
        self.collection_scrollbar.grid(row=2, column=4, sticky=NS)
        self.collection_listbox.config(yscrollcommand=self.collection_scrollbar.set)
        self.collection_listbox.bind("<<ListboxSelect>>", self.show_release_details)

        self.release_details_frame = Frame(self, height=15)
        # self.release_details_frame.geometry("300x300") DOESNT WORK
        self.release_details_frame.grid(row=4, column=2, rowspan=2, padx=5, pady=5)
        self.release_details_label = Label(self.release_details_frame, text="Release Metadata:", font=("San Francisco", 12), justify=LEFT)
        self.release_details_label.grid(row=0, padx=5, pady=5)
        self.release_details_text = Text(self.release_details_frame, wrap=WORD, width=25, height=12, font=("San Francisco", 11, "italic"))
        self.release_details_text.grid(row=2, padx=5, pady=5)
        self.release_details_text.insert(END, "Select a release from your collection to view details.")
        self.release_details_text.config(state=DISABLED)

        self.uploadfile_button = Button(self, text="Upload File", command=self.upload_file)
        self.uploadfile_button.grid(row=3, column=0, padx=5, pady=5)
        self.uploaded_metadata_label = Label(self, text="Existing Metadata:", font=("San Francisco", 12), justify=LEFT)
        self.uploaded_metadata_label.grid(row=4, column=0, padx=5, pady=5)
        self.uploaded_metadata_text = Text(self, wrap=WORD, width=25, height=12, font=("San Francisco", 11, "italic"))
        self.uploaded_metadata_text.grid(row=5, column=0, padx=5, pady=5)
        self.uploaded_metadata_text.insert(END, "Upload a file to view its metadata.")
        self.uploaded_metadata_text.config(state=DISABLED)
        self.apply_button = Button(self, text="Apply Discogs Data", command=self.apply_discogs_data)
        self.apply_button.grid(row=3, column=1, padx=5, pady=5)


        self.title_config_frame = Frame(self)
        self.title_config_frame.grid(row=3, column=2, padx=5, pady=5)
        self.title_config_label = Label(self.title_config_frame, text="Side:", font=("San Francisco", 12), justify=LEFT)
        self.title_config_label.grid(column=0, row=0, padx=(0,5), pady=5)

        self.selected_release = None
        self.current_file_path = None

        self.title_config_entry = Entry(self.title_config_frame,width=1,validate="key",validatecommand=(self.register(self.limit_input_length), "%P"),font=("San Francisco", 12))
        self.title_config_entry.grid(column=1, row=0)

    def limit_input_length(self, input_text):
            if len(input_text) > 1:
                return False
            return True 
    
    def upload_file(self):
        file_path = filedialog.askopenfilename(title="Select a file", filetypes=[("Audio Files", "*.mp3 *.flac *.wav"), ("All Files", "*.*")])
        if file_path:
            self.display_file_metadata(file_path)

    def display_file_metadata(self, file_path):
        file = mutagen.File(file_path)
        if file is not None:
            title = file.get("TIT2", "Unknown Title")
            artist = file.get("TPE1", "Unknown Artist")
            album = file.get("TALB", "Unknown Album")
            metadata_info = f"Title: {title}\nArtist: {artist}\nAlbum: {album}"
            self.uploaded_metadata_text.config(state=NORMAL, font=("San Francisco", 11))
            self.uploaded_metadata_text.delete(1.0, END)
            self.uploaded_metadata_text.insert(END, metadata_info)
            self.uploaded_metadata_text.config(state=DISABLED)
        else:
            messagebox.showerror("File Error", "Could not read the selected file. Please select a valid audio file.")
        
    def apply_discogs_data(self):
        if not self.current_file_path:
            messagebox.showerror("No File Selected", "Please upload a file first.")
            return
        if not self.selected_release:
            messagebox.showerror("No Release Selected", "Please select a release from your collection.")
            return
        
        try:
            file = mutagen.File(self.current_file_path, easy=True)
            if file is None:
                messagebox.showerror("File Error", "Could not read the selected file.")
                return
            
            # Apply Discogs data to the file
            file['title'] = self.selected_release.title+f"(Side {self.title_config_entry.get()})"  # Add side info if provided
            file['artist'] = self.selected_release.artists[0].name
            for artist in self.selected_release.artists[0:]:
                file['artist'] += f", {artist.name}"
            file['album'] = self.selected_release.title  # Assuming album is the release title
            file['date'] = str(self.selected_release.year)
            file['genre'] = ', '.join(self.selected_release.genres)
            
            file.save()
            messagebox.showinfo("Success", "Discogs data has been applied to the file.")
           
            self.display_file_metadata(self.current_file_path)  # Refresh displayed metadata
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply data: {str(e)}")
        
        
    def show_release_details(self, event) -> None:    
        selection = self.collection_listbox.curselection()
        if selection:
            self.release_details_text.config(font=("San Francisco", 11))
            index = selection[0]
            release = self.collection_list[index].release
            self.selected_release = release
            details = f"Title: {release.title}\nArtist: {release.artists[0].name}\nYear: {release.year}\nGenre: {', '.join(release.genres)}\nStyle: {', '.join(release.styles)}"
            self.release_details_text.config(state=NORMAL)
            self.release_details_text.delete(1.0, END)
            self.release_details_text.insert(END, details)
            self.release_details_text.config(state=DISABLED)
    

login_window = LoginWindow("Discogs Metadata Tool: Login")
login_window.mainloop()