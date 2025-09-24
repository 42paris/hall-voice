import json
import os
import sys

if __name__ == '__main__':
    # Foreach json file, open it and re-create it with beautifull indentation
    for file in os.listdir("./custom/"):
        # Check to be sure that the filename end with json and it's not the example json
        if file.endswith(".json") is True and file != "_Example.json":
            try:
                # Open JSON file and load json in var `data`
                with open(f"custom/{file}", 'r') as json_file:
                    data = json.load(json_file)
                # Delete the non-beautifull JSON file
                os.remove(f"custom/{file}")

                # Write the JSON file new file with indentation
                with open(f"custom/{file}", 'w') as new_file:
                    json.dump(data, new_file, indent=4)
            except Exception as e:
                print(f"Random Exeption for file {file}:\n{e}")
                exit(1)

    # Again, foreach json file open it and check if mp3/folder files exist
    # TODO Make sur the path start with login and ends with `/`
    for file in os.listdir("./custom/"):
        if file.endswith(".json") and file != "_Example.json":
            try:
                with open(f"custom/{file}", 'r') as json_file:
                    j = json.load(json_file)
                    # Is key `welcome` present in json?
                    if "welcome" in j:
                        # Is key `mp3` in key `welcome`?
                        if "mp3" in j["welcome"]:
                            # Is the value of key `mp3` in key `welcome` ends with `mp3` ?
                            if j["welcome"]["mp3"].endswith(".mp3") is True:
                                # Is the value of key `mp3` in key `welcome` exists and it is a file ?
                                if os.path.isfile(f"mp3/{j["welcome"]["mp3"]}") is False or os.path.exists(f"mp3/{j["welcome"]["mp3"]}") is False:
                                    print(f"For custom {file}: mp3/{j['welcome']['mp3']} doesnt exist or is not a mp3 file.")
                            if j["welcome"]["mp3"].endswith("/") is True:
                                if os.path.isdir(f"mp3/{j['welcome']['mp3']}") is False or os.path.exists(f"mp3/{j['welcome']['mp3']}") is False:
                                    print(f"For custom file {file}: folder mp3/{j['welcome']['mp3']} doesnt exist")
                                # Script is in WIP?
                                # mp3 = os.listdir("mp3/" + j["welcome"]["mp3"])
                                # print(f"Folder mp3/{j["welcome"]["mp3"]} doesnt exist: {mp3}")
            except Exception as e:
                print(f"Random Exeption for file {file}:\n{e}")
                exit(1)