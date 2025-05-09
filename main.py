import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import webbrowser 
import re
from PIL import Image, ImageTk

class WarThunderTestDriveGUI:
    def __init__(self, master):
        self.master = master
        master.title("Ask3lad War Thunder Test Drive GUI 1.0")
        master.geometry("400x375")

        icon_path = os.path.join("Assets", "Tank_Icons", "Ask3lad.ico")
        if os.path.exists(icon_path):
            master.iconbitmap(icon_path)
        else:
            print(f"Icon file not found: {icon_path}")

        # Add a button to locate the War Thunder directory
        self.locate_button = ttk.Button(master, text="Locate War Thunder Directory", command=self.locate_test_drive_file)
        self.locate_button.pack(pady=20)

        # Initialize tank_data as an empty list
        self.tank_data = []

        # Initialize the Assets folder button (hidden initially)
        self.assets_button = ttk.Button(master, text="Locate Assets Folder", command=self.locate_assets_folder)

        # Initialize the image label (hidden initially)
        self.image_label = None

        # Initialize the Treeview (hidden initially)
        self.tree = ttk.Treeview(master, columns=("name",), show="headings")
        self.tree.heading("name", text="Vehicle Name")
        self.tree.bind("<<TreeviewSelect>>", self.select_test_vehicle)

        # Add a scrollbar to the Treeview
        self.scrollbar = ttk.Scrollbar(master, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Initialize the search entry (hidden initially)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.search_vehicles)
        self.search_frame = ttk.Frame(master)
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)

        # Where the file and folder data are stored
        self.test_drive_file = None
        self.test_drive_vehicle_file = None
        self.assets_folder = None
        self.Selected_Vehicle_ID = None
        self.Current_Test_Vehicle = None

        # Check for config file
        self.check_config()

    def check_config(self):
        config_path = os.path.join("Assets", "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as config_file:
                    config = json.load(config_file)
                    print(f"Debug: Config file contents: {config}")  # Debug print
                if isinstance(config, dict):
                    wt_dir = config.get("WT_DIR")
                    assets_dir = config.get("WT_Assets")
            
                    if wt_dir:
                        if os.path.exists(wt_dir):
                            print(f"WT_DIR found in config: {wt_dir}")
                            self.locate_test_drive_file(wt_dir)
                        else:
                            print(f"WT_DIR in config doesn't exist: {wt_dir}")
                    else:
                        print("WT_DIR is empty or not present in the config file.")
            
                    if assets_dir:
                        if os.path.exists(assets_dir):
                            print(f"WT_Assets found in config: {assets_dir}")
                            self.locate_assets_folder(assets_dir)
                        else:
                            print(f"WT_Assets in config doesn't exist: {assets_dir}")
                    else:
                        print("WT_Assets is empty or not present in the config file.")
                else:
                    print(f"Unexpected config type: {type(config)}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {str(e)}")
            except Exception as e:
                print(f"Error reading config file: {str(e)}")
        else:
            print("Config file not found.")

    def locate_test_drive_file(self, wt_path=None):
        if wt_path is None:
            # Ask the user to select the War Thunder directory
            wt_path = filedialog.askdirectory(title="Select War Thunder Directory")

        # If the user cancels the selection or path is empty, return without proceeding
        if not wt_path:
            messagebox.showerror("Error", "War Thunder directory not selected. Cannot proceed.")
            return

        # Construct the path to the test drive file
        self.test_drive_file = os.path.join(wt_path, "UserMissions", "Ask3lad", "ask3lad_testdrive.blk")

        # Construct the path to the test drive vehicle file
        self.test_drive_vehicle_file = os.path.join(wt_path, "content", "pkg_local", "gameData", "units", "tankModels", "userVehicles", "us_m2a4.blk")

        # Check if the test drive file exists in the selected directory 
        if not os.path.exists(self.test_drive_file):
            messagebox.showerror("Error", f"Make sure this is the War Thunder Directory. Cannot proceed. Test Drive UserMisson not found.")
            return

        # Check if the test drive vehicle file exists in the selected directory 
        if not os.path.exists(self.test_drive_vehicle_file):
            messagebox.showerror("Error", f"Make sure this is the War Thunder Directory. Cannot proceed. Test Drive Vehicle File not found.")
            return

        # After successfully locating the test drive file
        self.find_current_test_vehicle()

        # Update or create the config.json file
        self.update_config(wt_path)

        # Make the "Locate War Thunder Directory" button disappear
        self.locate_button.pack_forget()

        # Make the "Locate Assets Folder" button appear
        self.assets_button.pack(pady=20)

    def locate_assets_folder(self, assets_path=None):
        if assets_path is None:
        # Ask the user to select the Assets folder
            assets_path = filedialog.askdirectory(title="Select Assets Folder")

        # If the user cancels the selection, return without proceeding
        if not assets_path:
            messagebox.showerror("Error", "Assets folder not selected. Cannot proceed.")
            return

        # Read the Tank_DB.json file
        tank_db_path = os.path.join(assets_path, "Tank_DB.json")
        if not os.path.exists(tank_db_path):
            messagebox.showerror("Error", "Tank_DB.json not found in the selected folder.")
            return

        # Update the assets folder path
        self.assets_folder = assets_path

        # Update the config file with the new assets path
        self.update_config(assets_path=assets_path)

        # Make the "Locate Assets Folder" button disappear
        self.assets_button.pack_forget()

        # Display the search bar
        self.search_frame.pack(pady=5)
        self.search_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
    
        # Load and display the tank data
        self.load_tank_data(tank_db_path)

        # Create and display the "Apply" button
        self.apply_button = ttk.Button(self.master, text="Apply", command=self.apply_changes)
        self.apply_button.pack(pady=10)

        # Create the image label (it will be hidden until an image is loaded)
        self.image_label = ttk.Label(self.master)

        # Create and display the social buttons
        self.YouTube_button = ttk.Button(self.master, text="YouTube", command=self.open_youtube)
        self.YouTube_button.pack(pady=10)
        self.Discord_button = ttk.Button(self.master, text="Join the Discord", command=self.open_discord)
        self.Discord_button.pack(pady=10)
        self.Support_button = ttk.Button(self.master, text="Support Me", command=self.open_support)
        self.Support_button.pack(pady=10)
        self.Decal_button = ttk.Button(self.master, text="Decal", command=self.open_decal)
        self.Decal_button.pack(pady=10)

    def update_config(self, wt_path=None, assets_path=None):
        config_path = os.path.join("Assets", "config.json")
    
        # Read existing config if it exists
        if os.path.exists(config_path):
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
        else:
            config = {}
    
        # Update config with new values if provided
        if wt_path:
            config["WT_DIR"] = wt_path
        if assets_path:
            config["WT_Assets"] = assets_path
    
        print(f"Attempting to update config: {config}")
    
        try:
            # Ensure the Assets directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
            # Write the config file
            with open(config_path, 'w') as config_file:
                json.dump(config, config_file, indent=4)
        
            # Verify the file was written correctly
            if os.path.exists(config_path):
                with open(config_path, 'r') as config_file:
                    written_config = json.load(config_file)
                if written_config == config:
                    print(f"Successfully updated config.json: {config}")
                else:
                    print(f"Config file was written, but contents don't match. Written: {written_config}")
            else:
                print("Config file was not created successfully.")
        except Exception as e:
            print(f"An error occurred while writing to config.json: {str(e)}")

    def find_current_test_vehicle(self):
        if not self.test_drive_file or not os.path.exists(self.test_drive_file):
            messagebox.showerror("Error", "Test drive file not found.")
            return
        # Read the content of the file
        try:
            with open(self.test_drive_file, 'r') as file:
                content = file.read()

            # Find the "tankModels" section
            tank_models_start = content.find("tankModels")
            if tank_models_start == -1:
                messagebox.showerror("Error", "tankModels section not found in the file.")
                return

            # Find the vehicle with name:t="You"
            you_vehicle_start = content.find('name:t="You"', tank_models_start)
            if you_vehicle_start == -1:
                messagebox.showerror("Error", "Current test vehicle not found.")
                return

            # Find the start of the vehicle block
            block_start = content.rfind("{", 0, you_vehicle_start)
            if block_start == -1:
                messagebox.showerror("Error", "Unable to locate the start of the vehicle block.")
                return

            # Find the end of the vehicle block
            block_end = content.find("}", you_vehicle_start)
            if block_end == -1:
                messagebox.showerror("Error", "Unable to locate the end of the vehicle block.")
                return

            # Extract the current test vehicle block
            self.Current_Test_Vehicle = content[block_start:block_end+1]

            # Find the weapons:t= within the Current_Test_Vehicle
            weapons_start = self.Current_Test_Vehicle.find("weapons:t=")
            if weapons_start != -1:
                weapons_end = self.Current_Test_Vehicle.find("\n", weapons_start)
                self.Current_Test_Vehicle_Weapons = self.Current_Test_Vehicle[weapons_start:weapons_end].strip()

                print(f"Current Test Vehicle Weapons: {self.Current_Test_Vehicle_Weapons}")
            else:
                print("No weapons found for the current test vehicle.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while reading the test drive file: {str(e)}")

    def open_youtube(self): # Opens YouTube channel
        webbrowser.open("https://www.youtube.com/@Ask3lad")

    def open_discord(self): # Opens the Discord server
        webbrowser.open("https://discord.com/invite/f3nsgypbh7")

    def open_support(self): # Opens YouTube Membership page
        webbrowser.open("https://www.youtube.com/@Ask3lad/join")

    def open_decal(self): # Opens the Gaijin Store page with the Ask3lad Decal
        webbrowser.open("https://store.gaijin.net/catalog.php?category=WarThunder&partner=Ask3lad&partner_val=lpzjtauw")

    def load_tank_data(self, tank_db_path):
        try:
            with open(tank_db_path, 'r') as file:
                self.tank_data = json.load(file)  # Store tank_data as an instance variable

            # Clear any existing items in the Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Populate the Treeview with tank names
            for tank in self.tank_data:
                if "name" in tank:
                    self.tree.insert("", "end", values=(tank["name"],))

            # Display the Treeview and scrollbar
            self.tree.pack(side="left", fill="both", expand=True)
            self.scrollbar.pack(side="right", fill="y")

        except json.JSONDecodeError:
            messagebox.showerror("Error", "Failed to parse Tank_DB.json. The file may be corrupted.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading tank data: {str(e)}")

    def search_vehicles(self, *args):
        # Get the search term from the Entry widget
        search_term = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for tank in self.tank_data:
            if "name" in tank and search_term in tank["name"].lower():
                self.tree.insert("", "end", values=(tank["name"],))

    def select_test_vehicle(self, event):
        # Get the selected item
        selected_item = self.tree.selection()

        if selected_item:  # If an item is selected
            # Get the values of the selected item
            values = self.tree.item(selected_item)['values']

            # Extract the name of the selected vehicle
            if len(values) >= 1:  # Ensure we have at least the name
                selected_name = values[0]

                # Find the corresponding vehicle in the tank_data
                for tank in self.tank_data:
                    if tank["name"] == selected_name:
                        self.Selected_Vehicle_ID = tank["ID"]
                        print(f"Selected Vehicle ID: {self.Selected_Vehicle_ID}")

                        # Load and display the image
                        self.load_and_display_image()
                        break
                else:
                    print("Error: Selected vehicle not found in tank data.")
            else:
                print("Error: Selected item does not have a name.")
        else:
            print("No vehicle selected.")

    def load_and_display_image(self):
        if self.assets_folder and self.Selected_Vehicle_ID:
            image_path = os.path.join(self.assets_folder, "Tank_Icons", f"{self.Selected_Vehicle_ID}.png")
            if not os.path.exists(image_path):
                print(f"Image not found: {image_path}")
                # Use the default image instead
                image_path = os.path.join(self.assets_folder, "Tank_Icons", "default.png")
        
            if os.path.exists(image_path):
                # Load the image
                image = Image.open(image_path)
        
                # Resize the image to 75x75 pixels
                image = image.resize((75, 75), Image.Resampling.LANCZOS)
        
                # Convert the image for Tkinter
                photo = ImageTk.PhotoImage(image)
        
                # Update the image in the label
                self.image_label.config(image=photo)
                self.image_label.image = photo  # Keep a reference
        
                # Display the image label above the Apply button
                self.image_label.pack_forget()  # Remove from current position
                self.image_label.pack(before=self.apply_button, pady=(10, 5))
            else:
                print(f"Default image not found: {image_path}")
                self.image_label.pack_forget()  # Hide the image label if no image is found
        else:
            print("Assets folder or Selected Vehicle ID is not set")
            self.image_label.pack_forget()  # Hide the image label if necessary data is missing

    def apply_changes(self):
        print("Apply button clicked")
        
        # Check if a vehicle has been selected
        if not self.Selected_Vehicle_ID:
            messagebox.showerror("Error", "No vehicle selected. Please select a vehicle before applying changes.")
            return
        
        # Check if the test drive vehicle file exists and is readable
        if not self.test_drive_vehicle_file or not os.path.exists(self.test_drive_vehicle_file):
            messagebox.showerror("Error", "Test drive vehicle file not found.")
            return
        
        # Check if the test drive file exists and is readable
        if not self.test_drive_file or not os.path.exists(self.test_drive_file):
            messagebox.showerror("Error", "Test drive file not found.")
            return
        
        try:
            # Find the corresponding weapons_default in the tank_data
            weapons_default = None
            for tank in self.tank_data:
                if tank["ID"] == self.Selected_Vehicle_ID:
                    weapons_default = tank.get("weapons_default")
                    break
        
            if not weapons_default:
                messagebox.showerror("Error", f"No weapons_default found for vehicle ID: {self.Selected_Vehicle_ID}")
                return
    
            # Update test_drive_vehicle_file
            with open(self.test_drive_vehicle_file, 'r') as file:
                content = file.readlines()
        
            # Find the "include" line in the test_drive_vehicle_file
            if content and content[0].startswith('include "#/develop/gameBase/gameData/units/tankModels/'):
                content[0] = f'include "#/develop/gameBase/gameData/units/tankModels/{self.Selected_Vehicle_ID}.blk"\n'
    
                # Write the updated content back to the file
                with open(self.test_drive_vehicle_file, 'w') as file:
                    file.writelines(content)
            else:
                messagebox.showerror("Error", "The test drive vehicle file does not have the expected format.")
                return
    
            # Update test_drive_file
            with open(self.test_drive_file, 'r') as file:
                content = file.read()
    
            # Update the main test vehicle and AI shooting vehicles
            content = self.update_vehicle_in_content(content, "You", self.Selected_Vehicle_ID, weapons_default)
            for i in range(1, 5):
                content = self.update_vehicle_in_content(content, f"AI_Shooting_0{i}", self.Selected_Vehicle_ID, weapons_default)
    
            # Write the updated content back to the file
            with open(self.test_drive_file, 'w') as file:
                file.write(content)
    
            # Show success message
            messagebox.showinfo("Success", f"Vehicle ID updated to {self.Selected_Vehicle_ID} and weapons updated to {weapons_default}")
        except Exception as e:
            # Show error message if an error occurs while updating the vehicle and weapon IDs
            messagebox.showerror("Error", f"An error occurred while updating the vehicle and weapon IDs: {str(e)}")
    
    def update_vehicle_in_content(self, content, vehicle_name, new_vehicle_id, new_weapons):
        # Find the vehicle block
        vehicle_start = content.find(f'name:t="{vehicle_name}"')
        if vehicle_start == -1:
            print(f"Vehicle {vehicle_name} not found in the content.")
            return content
    
        # Find the end of the vehicle block
        block_end = content.find("}", vehicle_start)
        if block_end == -1:
            print(f"Unable to find the end of the vehicle block for {vehicle_name}.")
            return content
    
        # Extract the vehicle block
        vehicle_block = content[vehicle_start:block_end]
    
        # Update the unit_class only for AI Shooting vehicles
        if vehicle_name.startswith("AI_Shooting_"):
            unit_class_start = vehicle_block.find("unit_class:t=")
            if unit_class_start != -1:
                unit_class_end = vehicle_block.find("\n", unit_class_start)
                old_unit_class = vehicle_block[unit_class_start:unit_class_end]
                new_unit_class = f'unit_class:t="{new_vehicle_id}"'
                vehicle_block = vehicle_block.replace(old_unit_class, new_unit_class)
    
        # Update the weapons for all vehicles
        weapons_start = vehicle_block.find("weapons:t=")
        if weapons_start != -1:
            weapons_end = vehicle_block.find("\n", weapons_start)
            old_weapons = vehicle_block[weapons_start:weapons_end]
            new_weapons_line = f'weapons:t="{new_weapons}"'
            vehicle_block = vehicle_block.replace(old_weapons, new_weapons_line)
    
        # Replace the old vehicle block with the updated one
        return content[:vehicle_start] + vehicle_block + content[block_end:]

# Create the GUI application
if __name__ == "__main__":
    root = tk.Tk()
    gui = WarThunderTestDriveGUI(root)
    root.mainloop()
