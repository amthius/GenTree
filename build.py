import json
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE_SRC = "src"
PROJECT_FILE = "default.project.json"

def get_base_project():
    return {
        "name": "gen-tree",
        "emitLegacyScripts": False,
        "tree": {
            "$className": "DataModel",
            "ReplicatedStorage": {
                "src": {
                    "$className": "Folder",
                    "client": {
                        "$className": "Folder",
                        "$path": "src/client", 
                        "Client": {"$path": "loaders/Client.client.luau"}
                    },
                    "shared": {"$className": "Folder", "$path": "src/shared"},
                    "server": {
                        "$className": "Camera",
                        "$path": "src/server",
                        "Server": {"$path": "loaders/Server.server.luau"}
                    }
                },
                "Packages": {
                    "$path": "packages"
                }
            }
        }
    }

def build_tree():
    project = get_base_project()
    client_tree = project["tree"]["ReplicatedStorage"]["src"]["client"]
    server_tree = project["tree"]["ReplicatedStorage"]["src"]["server"]

    for root, dirs, files in os.walk(BASE_SRC):
        rel_path = os.path.relpath(root, BASE_SRC)
        path_parts = [] if rel_path == "." else rel_path.split(os.sep)

        for file in files:
            if not file.endswith(".luau"):
                continue

            target_tree = None
            if file.endswith("Server.luau"):
                target_tree = server_tree
            elif file.endswith("Client.luau"):
                target_tree = client_tree
            
            if target_tree is not None:
                current_node = target_tree
                for part in path_parts:
                    if part not in current_node:
                        current_node[part] = {"$className": "Folder"}
                    current_node = current_node[part]
                
                module_name = file.replace(".luau", "")
                current_node[module_name] = {
                    "$path": os.path.join(root, file)
                }
    return project

def update():
    try:
        new_config = build_tree()
        with open(PROJECT_FILE, "w") as f:
            json.dump(new_config, f, indent=2)
        print(f"[{time.strftime('%H:%M:%S')}] project updated.")
    except Exception as e:
        print(f"Error updating project file: {e}")

class RojoWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory: update()

    def on_deleted(self, event):
        if not event.is_directory: update()

    def on_moved(self, event):
        update()

if __name__ == "__main__":
    update()

    observer = Observer()
    observer.schedule(RojoWatcher(), BASE_SRC, recursive=True)
    observer.start()
    
    print(f"Watching {BASE_SRC} for changes... (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
