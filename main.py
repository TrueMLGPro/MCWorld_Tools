import math
import os
import re
import zipfile

import inquirer
from rich import print as rprint
from rich.progress import Progress
from rich.prompt import Prompt, IntPrompt
from rich import traceback

# Initialize the rich traceback handler
_ = traceback.install()

version = "v1.0"
WORLD_FOLDER_TO_MCWORLD: str = "Convert world folder to .mcworld"
MCWORLD_TO_WORLD_FOLDER: str = "Convert .mcworld to world folder"

CURRENT_DIR: str = os.path.realpath(os.getcwd())
DEFAULT_PACKED_WORLD_OUTPUT_DIR: str = os.path.join(CURRENT_DIR, "Packed_Worlds")
DEFAULT_UNPACKED_WORLD_OUTPUT_DIR: str = os.path.join(CURRENT_DIR, "Unpacked_Worlds")

LOCAL_DIRECTORY_TYPE: str = f"Local directory (list all directories in {CURRENT_DIR})"
CUSTOM_PATH_DIRECTORY_TYPE: str = "Custom path to Directory"

LOCAL_MCWORLD_TYPE: str = "Local directory (list all .mcworld files)"
CUSTOM_PATH_MCWORLD_TYPE: str = "Custom path to .mcworld"

def create_folder_if_absent(directory: str) -> None:
	if not os.path.exists(directory):
		os.mkdir(directory)

def is_valid_path(path: str) -> bool:
    return len(path.strip()) > 0 and os.path.exists(path)

def get_folder_size(folder_path: str) -> int:
    total_size: int = 0

    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path: str = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)

    return total_size

def convert_size(size_bytes: int) -> str:
	if size_bytes == 0:
		return "0 B"
	size_name: tuple = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(math.floor(math.log(size_bytes, 1024)))
	p = math.pow(1024, i)
	s = round(size_bytes / p, 2)
	return f"{s} {size_name[i]}"

def init_operation_type() -> str:
	operation_type_prompt = [
        inquirer.List(
            "selected_operation_type",
            message="Choose an operation",
            choices=[
                WORLD_FOLDER_TO_MCWORLD,
				MCWORLD_TO_WORLD_FOLDER
            ],
			carousel=True
        )
    ]
	operation_type = inquirer.prompt(operation_type_prompt)
	rprint(f"📃 You chose [bold green]{operation_type['selected_operation_type']}[/]")

	return operation_type["selected_operation_type"]

# Change file extension zip to mcworld
def change_ext_to_mcworld(zip_file) -> None:
	base_name = os.path.splitext(zip_file)[0]
	new_name = f"{base_name}.mcworld"
	os.rename(zip_file, new_name)

class FolderToMcWorld():
	def init_input_dir(self) -> str:
		dir_type_prompt = [
			inquirer.List(
				"selected_dir_type",
				message="📂 Choose the Minecraft Bedrock world folder location",
				choices=[
					LOCAL_DIRECTORY_TYPE,
					CUSTOM_PATH_DIRECTORY_TYPE
				],
				carousel=True
			)
		]
		dir_type = inquirer.prompt(dir_type_prompt)
		rprint(f"📃 You chose [bold green]{dir_type['selected_dir_type']}[/]")

		return dir_type['selected_dir_type']

	def select_local_world_folder(self) -> str:
		folders = [
			folder for folder in os.listdir(CURRENT_DIR) if os.path.isdir(os.path.join(CURRENT_DIR, folder)) and not folder.startswith(".")
		]

		folder_prompt = [
			inquirer.List(
				"selected_folder",
				message="📂 Choose the world folder",
				choices=folders,
				carousel=True
			)
		]
		selected_folder = inquirer.prompt(folder_prompt)
		rprint(f"📁 You chose [bold green]{selected_folder['selected_folder']}[/]")

		return selected_folder['selected_folder']

	def select_custom_world_folder_path(self) -> str:
		selected_folder = ""
		while not is_valid_path(selected_folder):
			selected_folder = Prompt.ask(
				"📁 Enter the path to the world folder",
				default=DEFAULT_PACKED_WORLD_OUTPUT_DIR
			)

			if not is_valid_path(selected_folder):
				rprint("[red]Invalid path. Please enter a valid path.[/]")

		rprint(f"📁 You chose [bold green]{selected_folder}[/]")
		return selected_folder

	def select_output_folder(self) -> str:
		output_folder_path = ""
		while not is_valid_path(output_folder_path):
			output_folder_path = Prompt.ask(
				"📂 Enter the output folder path",
				default=DEFAULT_PACKED_WORLD_OUTPUT_DIR
			)

			if not is_valid_path(output_folder_path):
				rprint("[red]Invalid path. Please enter a valid path.[/]")

		rprint(f"📁 You chose [bold green]{output_folder_path}[/]")
		return output_folder_path

	def select_output_filename(self) -> str:
		default_filename = "output"
		output_filename = ""

		while not output_filename.strip():
			output_filename = Prompt.ask(
				"📂 Enter the output ZIP file name (without extension)",
				default=default_filename
			)

			if not output_filename.strip():
				rprint("[red]Filename cannot be empty. Please enter a valid filename.[/]")

		rprint(f"📁 You chose [bold green]{output_filename}[/]")
		return output_filename

	def pack_mcworld(self, input_dir: str, output_path: str, compression_level: int) -> None:
		with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zip_file:
			file_count = sum(len(files) for _, _, files in os.walk(input_dir))

			with Progress() as progress:
				archived_file_count = 0
				task = progress.add_task("🔧 [cyan]Archiving files...[/cyan]", total=file_count)
				for root, dir_names, files in os.walk(input_dir):
					for file in files:
						file_path = os.path.join(root, file)
						# Construct paths to files
						arcname = os.path.relpath(file_path, input_dir)
						# Write files to the zip archive
						zip_file.write(file_path, arcname=arcname)
						# Store file sizes to display in progress
						zip_structured_arcname = os.path.relpath(file_path, input_dir).replace(os.path.sep, '/')
						original_size = convert_size(os.path.getsize(file_path))
						compressed_size = convert_size(zip_file.getinfo(zip_structured_arcname).compress_size)
						# Print out the progress of file archiving
						archived_file_count += 1
						progress.console.print(f"Archiving file {archived_file_count} / {file_count} - [bold blue]{zip_structured_arcname}[/] [bold green]({original_size} -> {compressed_size})[/]")
						progress.advance(task)

class McWorldToFolder():
	def init_input_mcworld(self) -> str:
		dir_type_prompt = [
			inquirer.List(
				"selected_mcworld_type",
				message="Choose the .mcworld file location type",
				choices=[
					LOCAL_MCWORLD_TYPE,
					CUSTOM_PATH_MCWORLD_TYPE
				],
				carousel=True
			)
		]
		mcworld_type = inquirer.prompt(dir_type_prompt)
		rprint(f"📃 You chose [bold green]{mcworld_type['selected_mcworld_type']}[/]")

		return mcworld_type['selected_mcworld_type']

	def select_local_mcworld_file(self) -> str:
		mcworld_files = [
			file for file in os.listdir(CURRENT_DIR) if file.endswith(".mcworld")
		]

		if not mcworld_files:
			rprint(f"❌ [red]No .mcworld files found in local directory! Put your .mcworld file(s) in this directory ({CURRENT_DIR}) or choose a custom path.[/]\n")
			exit(0)

		mcworld_prompt = [
			inquirer.List(
				"selected_mcworld",
				message="📃 Choose a .mcworld file",
				choices=mcworld_files,
				carousel=True
			)
		]
		selected_mcworld = inquirer.prompt(mcworld_prompt)
		rprint(f"📃 You chose [bold green]{selected_mcworld['selected_mcworld']}[/]")

		return selected_mcworld['selected_mcworld']

	def select_custom_mcworld_path(self) -> str:
		selected_folder = ""
		while not is_valid_path(selected_folder):
			selected_folder = Prompt.ask(
				"📂 Enter the path to the world directory",
				default=DEFAULT_PACKED_WORLD_OUTPUT_DIR
			)

			if not is_valid_path(selected_folder):
				rprint("[red]Invalid path. Please enter a valid path.[/]")

		rprint(f"📁 You chose [bold green]{selected_folder}[/]")
		return selected_folder

	def select_output_folder(self) -> str:
		output_folder_path = ""
		while not is_valid_path(output_folder_path):
			output_folder_path = Prompt.ask(
				"📂 Enter the output folder path",
				default=DEFAULT_UNPACKED_WORLD_OUTPUT_DIR
			)

			if not is_valid_path(output_folder_path):
				rprint("[red]Invalid path. Please enter a valid path.[/]")

		rprint(f"📁 You chose [bold green]{output_folder_path}[/]")
		return output_folder_path

	def unpack_mcworld(self, mcworld_file: str, output_folder: str) -> None:
		with zipfile.ZipFile(mcworld_file, 'r') as zip_ref:
			file_count = len(zip_ref.namelist())
			mcworld_dir_name = re.sub(r'[\/:*?"<>|]', '', os.path.splitext(os.path.basename(mcworld_file))[0])
			target_dir = os.path.join(output_folder, mcworld_dir_name)

			with Progress() as progress:
				extracted_file_count = 0
				task = progress.add_task("🔓 [cyan]Extracting files...[/]", total=file_count)
				for member in zip_ref.infolist():
					# Extract the files
					zip_ref.extract(member, target_dir)
					# Print out the progress of file extracting
					extracted_file_count += 1
					progress.console.print(f"Extracting file {extracted_file_count} / {file_count} - [bold blue]{member.filename}[/] [bold green]({convert_size(member.compress_size)} -> {convert_size(member.file_size)})[/]")
					progress.advance(task)

def main() -> None:
	# Banner
	print(
""" __  __  _____      __       _    _   _____         _
|  \/  |/ __\ \    / /__ _ _| |__| | |_   _|__  ___| |___
| |\/| | (__ \ \/\/ / _ \ '_| / _` |   | |/ _ \/ _ \ (_-<
|_|  |_|\___| \_/\_/\___/_| |_\__,_|   |_|\___/\___/_/__/
""")
	rprint(f"Made by [blue]TrueMLGPro[/] | [bold green]{version}[/]")

	# Create folders required for the script to function
	create_folder_if_absent(DEFAULT_PACKED_WORLD_OUTPUT_DIR)
	create_folder_if_absent(DEFAULT_UNPACKED_WORLD_OUTPUT_DIR)

	operation_type: str = init_operation_type()

	# Minecraft Bedrock world folder to .mcworld conversion
	if operation_type == WORLD_FOLDER_TO_MCWORLD:
		mcworld_packer = FolderToMcWorld()
		dir_type: str = mcworld_packer.init_input_dir()

		if dir_type == LOCAL_DIRECTORY_TYPE:
			input_world_directory: str = mcworld_packer.select_local_world_folder()
		elif dir_type == CUSTOM_PATH_DIRECTORY_TYPE:
			input_world_directory: str = mcworld_packer.select_custom_world_folder_path()

		compression_level: int = IntPrompt.ask("🥽 Enter the compression level for the output archive (0-9)", default=0)
		rprint(f"💾 You chose the compression level of [bold green]{compression_level}[/]")

		output_dir: str = mcworld_packer.select_output_folder()
		output_zip_file_str: str = mcworld_packer.select_output_filename()
		output_zip_file: str = output_zip_file_str if output_zip_file_str.endswith(".zip") else output_zip_file_str + ".zip"

		output_mcworld_path: str = os.path.join(output_dir, output_zip_file)
		rprint("🔒 Packing the [blue]world folder[/] to [blue].mcworld[/]...")

		mcworld_packer.pack_mcworld(input_world_directory, output_mcworld_path, compression_level)
		change_ext_to_mcworld(output_mcworld_path)

		world_folder_name = os.path.basename(input_world_directory)
		final_output_file_path = os.path.splitext(output_mcworld_path)[0] + ".mcworld"

		world_folder_size = convert_size(get_folder_size(input_world_directory))
		packed_mcworld_size = convert_size(os.path.getsize(final_output_file_path))

		rprint(f"✅ [green]Successfully packed world [bold cyan]{world_folder_name}[/] [bold blue]({world_folder_size})[/] to [bold cyan]{final_output_file_path}[/] [bold blue]({packed_mcworld_size})[/]! :)[/]")
	# .mcworld to Minecraft Bedrock world folder conversion
	elif operation_type == MCWORLD_TO_WORLD_FOLDER:
		mcworld_unpacker = McWorldToFolder()
		dir_type: str = mcworld_unpacker.init_input_mcworld()

		if dir_type == LOCAL_MCWORLD_TYPE:
			input_mcworld_path: str = mcworld_unpacker.select_local_mcworld_file()
		elif dir_type == CUSTOM_PATH_MCWORLD_TYPE:
			input_mcworld_path: str = mcworld_unpacker.select_custom_mcworld_path()

		output_folder: str = mcworld_unpacker.select_output_folder()
		rprint("🔓 Unpacking [blue].mcworld[/] to a [blue]world folder[/]...")

		mcworld_unpacker.unpack_mcworld(input_mcworld_path, output_folder)

		input_mcworld_name = os.path.basename(input_mcworld_path)
		final_output_folder_path = os.path.join(output_folder, input_mcworld_name.split(".")[0])

		mcworld_size = convert_size(os.path.getsize(input_mcworld_path))
		unpacked_world_size = convert_size(get_folder_size(output_folder))
		rprint(f"✅ [green]Successfully unpacked [bold cyan]{input_mcworld_name}[/] [bold blue]({mcworld_size})[/] to [bold cyan]{final_output_folder_path}[/] [bold blue]({unpacked_world_size})[/]! :)[/]")

if __name__ == '__main__':
	try:
		main()
	except Exception as e:
		exception_type = type(e)
		tb_obj = e.__traceback__
		rprint(traceback.Traceback.from_exception(exc_type=exception_type, exc_value=e, traceback=tb_obj))
	except KeyboardInterrupt:
		rprint("\n⏹  [bold blue]Exiting...[/]")