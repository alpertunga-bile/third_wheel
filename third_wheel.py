from os.path import exists, join
from os import getcwd, makedirs, rename, remove
from platform import system
from shutil import rmtree
from argparse import ArgumentParser
from json import load
from dataclasses import dataclass

# --------------------------------------------------------------------------------
# -- Package Class


@dataclass
class Package:
    name: str
    github_url: str
    version: str
    file_ext: str
    install_location: str

    def __init__(self, target_folder: str, package_info) -> None:
        self.name = package_info["name"]
        self.github_url = package_info["github_url"]

        self.version = (
            get_version_from_github(self.github_url)
            if package_info["version"] is None
            else package_info["version"]
        )

        """
            mostly Linux files are stored with tar.gz extension and
            Windows files are stored with zip extension. There are some exceptions
            like the glfw library. Different OSs are stored with zip extension.
        """
        self.file_ext = (
            (".zip" if system() == "Windows" else ".tar.gz")
            if package_info["file_ext"] is None
            else package_info["file_ext"]
        )

        if self.file_ext.startswith(".") is False:
            self.file_ext = "." + self.file_ext

        self.install_location = join(target_folder, self.name)


# --------------------------------------------------------------------------------
# -- Environment Functions


def prepare_env(venv_foldername: str) -> None:
    from subprocess import run
    from sys import executable as python_exec

    if exists(venv_foldername):
        print(f"/_\ {venv_foldername} is already created")
        return

    print(f"/_\ Creating {venv_foldername} environment")

    """
        Can't use the python exec for downloading packages because there are no virtual environments to use
        so we can't initialize the venv and assign python_exec to that
    """
    if system() == "Windows":
        venv_python_exec = join(venv_foldername, "Scripts", "python.exe")
    elif system() == "Linux":
        venv_python_exec = join(venv_foldername, "bin", "python")

    process = run(
        f"{python_exec} -m venv {venv_foldername}",
        shell=True,
        capture_output=True,
        check=True,
    )

    if process.returncode != 0:
        print(f"/_\ Creating {venv_foldername} is failed")
        return

    print("/_\ Installing required packages")

    process = run(
        f"{venv_python_exec} -m pip install requests tqdm beautifulsoup4 lxml",
        shell=True,
        capture_output=True,
        check=True,
    )

    if process.returncode != 0:
        print("/_\ Installing required packages is failed")
        return


# --------------------------------------------------------------------------------
# -- Repository Preparetion Functions


def get_version_from_github(github_url: str) -> str:
    from bs4 import BeautifulSoup
    from requests import get

    doc = BeautifulSoup(get(f"{github_url}/tags").content, features="lxml")

    return doc.find("a", {"class": "Link--primary Link"}).get_text().replace("v", "")


def download_zip_file(target_folder: str, zip_filename: str, package: Package) -> None:
    from requests import get
    from tqdm import tqdm

    response = get(
        f"{package.github_url}/releases/download/v{package.version}/{zip_filename}"
    )

    """
        some repositories didn't use the 'v' character for the package version
        so trying to get the zip file with other formats
    """
    if response.ok is False:
        response = get(
            f"{package.github_url}/releases/download/{package.version}/{zip_filename}"
        )

    if response.ok is False:
        raise ValueError(f"Cannot install the {zip_filename}")

    total_size = int(response.headers.get("content-length"))
    zip_filepath = join(target_folder, zip_filename)

    with open(zip_filepath, "wb") as f:
        with tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=f"/_\ Installing {package.name} {package.version}",
        ) as pbar:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))


def extract_zip_file(
    zip_filepath: str, target_folder: str, extracted_folder_path: str, package_name: str
) -> None:

    folder_path = target_folder
    is_contain_root_folder = False
    os_name = system()

    if os_name == "Windows":
        from zipfile import ZipFile

        zip_file = ZipFile(zip_filepath, "r")
    elif os_name == "Linux":
        from tarfile import tar_open

        if zip_filepath.endswith("tar.gz"):
            zip_file = tar_open(zip_filepath, mode="r:gz")
        elif zip_filepath.endswith("tar"):
            zip_file = tar_open(zip_filepath, mode="r")

    """
        get root level directory names to determine 
        if it has root folder that contains all of the content
        or the contents are stored without root folder
    """
    dirnames = set(
        [info.filename.split("/")[0] for info in zip_file.infolist() if info.is_dir()]
    )

    """
        determine if there is a root folder 
    """
    for dirname in dirnames:
        if package_name in dirname:
            is_contain_root_folder = True
            break

    """
        if there is no root folder create the expected folder and 
        extract all the content to this folder
        to fix the pipeline of the progress
    """
    if is_contain_root_folder is False:
        folder_path = extracted_folder_path
        makedirs(folder_path)

    zip_file.extractall(folder_path)

    zip_file.close()


def prepare_packages(target_folder: str, packages) -> None:
    os_name = system()

    for pkg in packages:
        package = Package(target_folder, pkg)

        if os_name == "Windows":
            file_format = pkg["win_format"]
        elif os_name == "Linux":
            file_format = pkg["linux_format"]

        print(f"/_\ Preparing {package.name}")

        if exists(package.install_location):
            print(f"/_\ {package.install_location} is already exists | Skipping ...")
            continue

        zip_filename = (
            file_format.replace("{name}", package.name)
            .replace("{version}", package.version)
            .replace("{os}", os_name.lower())
        ) + package.file_ext

        zip_filepath = join(target_folder, zip_filename)

        """
            maybe the file will be there because of the early termination
            so we don't need to install it again
        """
        if exists(zip_filepath) is False:
            download_zip_file(target_folder, zip_filename, package)

        extracted_folderpath = zip_filepath.replace(package.file_ext, "")

        extract_zip_file(
            zip_filepath, target_folder, extracted_folderpath, package.name
        )

        if exists(package.install_location) is False:
            rename(extracted_folderpath, package.install_location)

        if exists(zip_filepath):
            remove(zip_filepath)

        print(f"/_\ Preparing {package.name} is completed")


# --------------------------------------------------------------------------------
# -- Main


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="third wheel - setup the precompiled third party projects from Github"
    )
    parser.add_argument(
        "--package_file",
        action="store",
        default="packages.json",
        help="The json file that stores the informations",
    )
    parser.add_argument(
        "--setup_venv",
        action="store_true",
        default=False,
        help="Just create the virtual environment",
    )
    parser.add_argument(
        "--delete_all",
        action="store_true",
        default=False,
        help="Delete the created packages, folders and files",
    )
    args = parser.parse_args()

    package_file = args.package_file

    if exists(package_file) is False:
        raise ValueError(f"{package_file} is not exists in the {getcwd()} directory")

    with open(package_file, "r") as json_file:
        package_infos = load(json_file)

    venv_folder = package_infos["venv_folder"]
    target_folder = package_infos["target_folder"]

    if args.delete_all:
        print(f"/_\ Deleting {venv_folder}")
        rmtree(venv_folder)
        print(f"/_\ Deleting {target_folder}")
        rmtree(target_folder)
        exit(0)

    if args.setup_venv:
        prepare_env(venv_folder)
        exit(0)

    prepare_env(venv_folder)

    makedirs(target_folder, exist_ok=True)

    prepare_packages(target_folder, package_infos["packages"])
