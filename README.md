# third_wheel

- [third\_wheel](#third_wheel)
  - [Usage](#usage)
    - [Packages.json](#packagesjson)
      - [Packages](#packages)
  - [Example](#example)

third_wheel is an automation tool to download the precompiled binaries from the Github repositories to the local workspaces

The program will download the required zip file based on your operating system, extract it to the specified location and make it ready for final usage

## Usage

- There is a ```packages.json``` file need to be filled. See [this section](#packagesjson)
- Run the program with

```bash
python third_wheel.py --setup_venv
```

command to create the virtual environment with given folder name to the **venv_folder** in the ```packages.json``` file

- Activate the created virtual environment
- Then run the program with

```bash
python third_wheel.py
```

command

### Packages.json

|   Variable    |  Type  | Definition                                                              |
| :-----------: | :----: | :---------------------------------------------------------------------- |
|  venv_folder  | string | The name of the folder to use it as the virtual environment folder name |
| target_folder | string | The folder name of the install location                                 |
|   packages    | array  | Contains the packages need to be downloaded                             |

#### Packages

|   Variable   |  Type  | Definition                                                                                          |
| :----------: | :----: | :-------------------------------------------------------------------------------------------------- |
|     name     | string | Name of the package                                                                                 |
|  github_url  | string | Github url of the package                                                                           |
|  win_format  | string | Format for the zip file for the Windows OS                                                          |
| linux_format | string | Format for the zip file for the Linux OS                                                            |
|   version    | string | Wanted version of the package, leave it null for the latest version                                 |
|   file_ext   | string | File extension of the zip file that is going to be downloaded, leave it null for the automatic fill |

- For the format part you can use:
  - {name}    : name of the package
  - {version} : version of the package
  - {os}      : current operating system. **windows** for the Windows OS, **linux** for the Linux OS

- The version is selected automatically from the **tags** part of the Github repository
- The file extension is selected automatically with **zip** for the Windows OS and **tar.gz** for the Linux OS

## Example

- You can find the example in the ```packages.json``` file
