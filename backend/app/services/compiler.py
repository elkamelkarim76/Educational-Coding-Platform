"""
Code compilation and execution service.

This module handles compiling and executing student/teacher code using
subprocess to invoke gcc, javac, or python3 depending on the language.
"""

import os
import tempfile
import subprocess

from app.schemas.schemas import File, Language
from app.utils.syntax_code import COMPILER_CONFIG


def get_filename_on_disk(file: File, config: dict) -> str:
    """
    Determine the filename to write on disk.
    If is_main is True, the file is renamed to the language's main file name.
    """
    base_name = config["main_name"] if file.is_main else file.name

    if base_name.endswith(f".{file.extension}"):
        return base_name

    return f"{base_name}.{file.extension}"


def write_files_to_folder(files: list[File], folder_path: str, config: dict) -> None:
    """
    Write all file objects to the specified folder.
    """
    try:
        main_found = False

        for file in files:
            filename = get_filename_on_disk(file, config)

            if filename == f"main.{file.extension}":
                if main_found:
                    raise ValueError("Multiple main files found")
                main_found = True

            file_path = os.path.join(folder_path, filename)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file.content)

        print(f"Files written in folder {folder_path}")

    except Exception as e:
        print(f"Writing error: {e}")
        raise e


def build_compilation_command(config: dict, files: list[File]) -> list[str]:
    """
    Generate the compilation command by replacing placeholders.
    Replaces {input_files} with actual source file names.
    """
    cmd = []
    target_extension = config["extension"]

    for arg in config["compiler_cmd"]:
        if arg == "{input_files}":
            for f in files:
                if f.extension == target_extension:
                    cmd.append(get_filename_on_disk(f, config))
        else:
            cmd.append(arg)

    return cmd


def run_compilation(config: dict, files: list[File], tmp_dir: str) -> dict:
    """
    Execute the compilation command in the tmp_dir.
    """
    cmd = build_compilation_command(config, files)

    print("compilation:", cmd)

    try:
        result = subprocess.run(
            cmd,
            cwd=tmp_dir,
            capture_output=True,
            text=True,
            timeout=10  # sécurité : évite une compilation bloquée
        )

        is_success = result.returncode == 0

        return {
            "status": is_success,
            "message": "Compilation successful" if is_success else "Compilation failed",
            "data": {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        }

    except subprocess.TimeoutExpired:
        return {
            "status": False,
            "message": "Compilation timeout",
            "data": {
                "stdout": "",
                "stderr": "Compilation stopped: time limit exceeded.",
                "exit_code": -1
            }
        }

    except Exception as e:
        return {
            "status": False,
            "message": f"Internal system error: {str(e)}",
            "data": {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }
        }


def run_execution(config: dict, tmp_dir: str, argv: str) -> dict:
    """
    Execute the compiled program with arguments.
    """
    cmd = config["run_cmd"].copy()

    if argv:
        cmd.extend(argv.split())

    print("execution:", cmd)

    try:
        result = subprocess.run(
            cmd,
            cwd=tmp_dir,
            capture_output=True,
            text=True,
            timeout=3  # sécurité : évite les boucles infinies
        )

        is_success = result.returncode == 0

        return {
            "status": is_success,
            "message": "Execution successful" if is_success else "Execution failed",
            "data": {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        }

    except subprocess.TimeoutExpired:
        return {
            "status": False,
            "message": "Execution timeout",
            "data": {
                "stdout": "",
                "stderr": "Execution stopped: time limit exceeded.",
                "exit_code": -1
            }
        }

    except Exception as e:
        return {
            "status": False,
            "message": f"Execution error: {str(e)}",
            "data": {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }
        }


def prepare_and_compile(files: list[File], language: Language, tmp_dir: str) -> tuple[dict, dict]:
    """
    Write files to the tmp_dir and compile them.
    """
    config = COMPILER_CONFIG.get(language)

    try:
        write_files_to_folder(files, tmp_dir, config)
    except Exception as e:
        return {"status": False, "message": str(e)}, {}

    compile_result = run_compilation(config, files, tmp_dir)

    return compile_result, config


async def compile_logic(files: list[File], language: Language) -> dict:
    """
    Compile code without execution.
    Used by teachers to check their code.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        compile_result, _ = prepare_and_compile(files, language, tmp_dir)
        return compile_result


async def compile_and_run_logic(files: list[File], language: Language, argv: str) -> dict:
    """
    Compile and execute code with a single test case.
    Used by teachers to test their exercises.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        compile_result, config = prepare_and_compile(files, language, tmp_dir)

        if not compile_result["status"]:
            return compile_result

        exec_result = run_execution(config, tmp_dir, argv)
        return exec_result


async def compile_and_run_logics(files: list[File], language: Language, argvs: list[str]) -> dict | list[dict]:
    """
    Compile once and execute with multiple test cases.
    Used for student submissions.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        compile_result, config = prepare_and_compile(files, language, tmp_dir)

        if not compile_result["status"]:
            return compile_result

        exec_results = []

        for argv in argvs:
            exec_results.append(run_execution(config, tmp_dir, argv))

        return exec_results