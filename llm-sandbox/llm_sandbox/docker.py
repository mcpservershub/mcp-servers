import io
import os
import docker
import tarfile
import tempfile
from typing import List, Optional, Union

from docker.models.images import Image
from docker.models.containers import Container
from docker.types import Mount
from llm_sandbox.utils import (
    image_exists,
    get_libraries_installation_command,
    get_code_file_extension,
    get_code_execution_command,
)
from llm_sandbox.base import Session, ConsoleOutput
from llm_sandbox.const import (
    SupportedLanguage,
    SupportedLanguageValues,
    DefaultImage,
    NotSupportedLibraryInstallation,
)


class SandboxDockerSession(Session):
    def __init__(
        self,
        client: Optional[docker.DockerClient] = None,
        image: Optional[str] = None,
        dockerfile: Optional[str] = None,
        lang: str = SupportedLanguage.PYTHON,
        keep_template: bool = False,
        commit_container: bool = False,
        verbose: bool = False,
        mounts: Optional[list[Mount]] = None,
        stream: bool = True,
        runtime_configs: Optional[dict] = None,
        **kwargs,
    ):
        """
        Create a new sandbox session
        :param client: Docker client, if not provided, a new client will be created based on local Docker context
        :param image: Docker image to use
        :param dockerfile: Path to the Dockerfile, if image is not provided
        :param lang: Language of the code
        :param keep_template: if True, the image and container will not be removed after the session ends
        :param commit_container: if True, the Docker container will be commited after the session ends
        :param verbose: if True, print messages
        :param mounts: List of mounts to be mounted to the container
        :param stream: if True, the output will be streamed (enabling this option prevents obtaining an exit code of run command)
        :param runtime_configs: Additional configurations for the container, i.e. resources limits (cpu_count, mem_limit), etc.
        """
        super().__init__(lang, verbose)
        if image and dockerfile:
            raise ValueError("Only one of image or dockerfile should be provided")

        if lang not in SupportedLanguageValues:
            raise ValueError(
                f"Language {lang} is not supported. Must be one of {SupportedLanguageValues}"
            )

        if not image and not dockerfile:
            image = DefaultImage.__dict__[lang.upper()]

        self.lang: str = lang
        self.client: Optional[docker.DockerClient] = None

        if not client:
            if self.verbose:
                print("Using local Docker context since client is not provided..")

            self.client = docker.from_env()
        else:
            self.client = client

        self.image: Union[Image, str] = image
        self.dockerfile: Optional[str] = dockerfile
        self.container: Optional[Container] = None
        self.path = None
        self.keep_template = keep_template
        self.commit_container = commit_container
        self.is_create_template: bool = False
        self.verbose = verbose
        self.mounts = mounts
        self.stream = stream
        self.runtime_configs = runtime_configs

    def open(self):
        warning_str = (
            "Since the `keep_template` flag is set to True the docker image will not be removed after the session ends "
            "and remains for future use."
        )
        if self.dockerfile:
            self.path = os.path.dirname(self.dockerfile)
            if self.verbose:
                f_str = f"Building docker image from {self.dockerfile}"
                f_str = f"{f_str}\n{warning_str}" if self.keep_template else f_str
                print(f_str)

            self.image, _ = self.client.images.build(
                path=self.path,
                dockerfile=os.path.basename(self.dockerfile),
                tag=f"sandbox-{self.lang.lower()}-{os.path.basename(self.path)}",
            )
            self.is_create_template = True

        if isinstance(self.image, str):
            if not image_exists(self.client, self.image):
                if self.verbose:
                    f_str = f"Pulling image {self.image}.."
                    f_str = f"{f_str}\n{warning_str}" if self.keep_template else f_str
                    print(f_str)

                self.image = self.client.images.pull(self.image)
                self.is_create_template = True
            else:
                self.image = self.client.images.get(self.image)
                if self.verbose:
                    print(f"Using image {self.image.tags[-1]}")

        self.container = self.client.containers.run(
            self.image,
            detach=True,
            tty=True,
            mounts=self.mounts,
            **self.runtime_configs if self.runtime_configs else {},
        )

    def close(self):
        if self.container:
            if self.commit_container and isinstance(self.image, Image):
                self.container.commit(self.image.tags[-1])

            self.container.remove(force=True)
            self.container = None

        if self.is_create_template and not self.keep_template:
            # check if the image is used by any other container
            containers = self.client.containers.list(all=True)
            image_id = (
                self.image.id
                if isinstance(self.image, Image)
                else self.client.images.get(self.image).id
            )

            try:
                image_in_use = any(
                    container.image.id == image_id for container in containers
                )
            except docker.errors.ImageNotFound:
                image_in_use = False

            if not image_in_use:
                if isinstance(self.image, str):
                    self.client.images.remove(self.image)
                elif isinstance(self.image, Image):
                    self.image.remove(force=True)
                else:
                    raise ValueError("Invalid image type")
            else:
                if self.verbose:
                    print(
                        f"Image {self.image.tags[-1]} is in use by other containers. Skipping removal.."
                    )

    def run(self, code: str, libraries: Optional[List] = None) -> ConsoleOutput:
        if not self.container:
            raise RuntimeError(
                "Session is not open. Please call open() method before running code."
            )

        if libraries:
            if self.lang.upper() in NotSupportedLibraryInstallation:
                raise ValueError(
                    f"Library installation has not been supported for {self.lang} yet!"
                )

            if self.lang == SupportedLanguage.GO:
                self.execute_command("mkdir -p /example")
                self.execute_command("go mod init example", workdir="/example")
                self.execute_command("go mod tidy", workdir="/example")

                for library in libraries:
                    command = get_libraries_installation_command(self.lang, library)
                    _ = self.execute_command(command, workdir="/example")
            elif self.lang == SupportedLanguage.CSHARP:
                # Create a new C# console project in the /example directory
                self.execute_command("mkdir -p /example")
                self.execute_command("dotnet new console -o /example", workdir="/example")
                for library in libraries:
                    command = get_libraries_installation_command(self.lang, library)
                    _ = self.execute_command(command, workdir="/example")
            else:
                for library in libraries:
                    command = get_libraries_installation_command(self.lang, library)
                    _ = self.execute_command(command)

        with tempfile.TemporaryDirectory() as directory_name:
            if self.lang == SupportedLanguage.CSHARP:
                # For C#, update the project by replacing the default Program.cs.
                code_file_local = os.path.join(directory_name, "Program.cs")
                with open(code_file_local, "w") as f:
                    f.write(code)
                # Copy the updated Program.cs to the project folder in the container
                self.copy_to_runtime(code_file_local, os.path.join("/example", "Program.cs"))
                # Execution target is the project directory.
                execution_target = "/example"
            elif self.lang == SupportedLanguage.GO:
                # For Go, write the code to a file named code.go in the /example folder.
                code_file_local = os.path.join(directory_name, "code.go")
                with open(code_file_local, "w") as f:
                    f.write(code)
                execution_target = "/example/code.go"
                self.copy_to_runtime(code_file_local, execution_target)
            else:
                # For other languages, use a single code file.
                file_ext = get_code_file_extension(self.lang)
                code_file_local = os.path.join(directory_name, f"code.{file_ext}")
                with open(code_file_local, "w") as f:
                    f.write(code)
                execution_target = f"/tmp/code.{file_ext}"
                self.copy_to_runtime(code_file_local, execution_target)

            output = ConsoleOutput(text="", exit_code=0)
            commands = get_code_execution_command(self.lang, execution_target)
            for command in commands:
                if self.lang in (SupportedLanguage.GO, SupportedLanguage.CSHARP):
                    output = self.execute_command(command, workdir="/example")
                else:
                    output = self.execute_command(command)

                if output.exit_code != 0:
                    return output

            return output

    def copy_from_runtime(self, src: str, dest: str):
        if not self.container:
            raise RuntimeError(
                "Session is not open. Please call open() method before copying files."
            )

        if self.verbose:
            print(f"Copying {self.container.short_id}:{src} to {dest}..")

        bits, stat = self.container.get_archive(src)
        if stat["size"] == 0:
            raise FileNotFoundError(f"File {src} not found in the container")

        tarstream = io.BytesIO(b"".join(bits))
        with tarfile.open(fileobj=tarstream, mode="r") as tar:
            tar.extractall(os.path.dirname(dest))

    def copy_to_runtime(self, src: str, dest: str):
        if not self.container:
            raise RuntimeError(
                "Session is not open. Please call open() method before copying files."
            )

        is_created_dir = False
        directory = os.path.dirname(dest)
        if directory and not self.container.exec_run(f"test -d {directory}")[0] == 0:
            self.container.exec_run(f"mkdir -p {directory}")
            is_created_dir = True

        if self.verbose:
            if is_created_dir:
                print(f"Creating directory {self.container.short_id}:{directory}")
            print(f"Copying {src} to {self.container.short_id}:{dest}..")

        tarstream = io.BytesIO()
        with tarfile.open(fileobj=tarstream, mode="w") as tar:
            tar.add(src, arcname=os.path.basename(src))

        tarstream.seek(0)
        self.container.put_archive(os.path.dirname(dest), tarstream)

    def execute_command(
        self, command: Optional[str], workdir: Optional[str] = None
    ) -> ConsoleOutput:
        if not command:
            raise ValueError("Command cannot be empty")

        if not self.container:
            raise RuntimeError(
                "Session is not open. Please call open() method before executing commands."
            )

        if self.verbose:
            print(f"Executing command: {command}")

        if workdir:
            exit_code, exec_log = self.container.exec_run(
                command, stream=self.stream, tty=True, workdir=workdir
            )
        else:
            exit_code, exec_log = self.container.exec_run(
                command, stream=self.stream, tty=True
            )

        output = ""
        if self.verbose:
            print("Output:", end=" ")

        if not self.stream:
            exec_log = [exec_log]

        for chunk in exec_log:
            chunk_str = chunk.decode("utf-8")
            output += chunk_str
            if self.verbose:
                print(chunk_str, end="")

        return ConsoleOutput(text=output, exit_code=exit_code)

    def _list_dangling_images(self) -> list[str]:
        # List all dangling images (those without a repository or tag)
        dangling_images = self.client.images.list(filters={"dangling": True})       
        return [img.id for img in dangling_images]

    def _build_ancestry_map(self, images: list) -> dict:
        """
        Build a mapping from image ID to the image object for quick lookup.
        """
        return {img.id: img for img in images}

    def _get_image_ancestry(self, image_map: dict) -> set:
        """
        Recursively traverse the parent chain of an image.
        Returns a set of all ancestor image IDs.
        """
        ancestry = set()
        # The parent's ID is stored in the image's attributes (if available)
        parent_id = self.image.attrs.get("Parent")
        while parent_id:
            ancestry.add(parent_id)
            parent = image_map.get(parent_id)
            if parent:
                parent_id = parent.attrs.get("Parent")
            else:
                break
        return ancestry

    def _identify_dangling_intermediates(self, all_images: list[Image]) -> list:
        """
        Identify the dangling images (untagged images) that are part of the build chain
        (ancestry) of the final image.
        """
        image_map = self._build_ancestry_map(all_images)
        final_ancestry = self._get_image_ancestry(image_map)
        # Only consider images that have no tags (dangling)
        dangling_images = [img for img in all_images if not img.tags]
        images_to_delete = []
        for img in dangling_images:
            if img.id in final_ancestry:
                images_to_delete.append(img)
        return images_to_delete

    def _delete_images(self, images: list[Image]) -> None:
        """
        Delete a list of images using the Docker client.
        """
        for img in images:
            try:
                self.client.images.remove(img.id, force=True)
                if self.verbose:
                    print(f"Removed dangling image {img.id}")
            except Exception as e:
                if self.verbose:
                    print(f"Failed to remove dangling image {img.id}: {e}")

    def _cleanup_intermediate_images(self):
        """
        Retrieve all images, identify the intermediate (dangling) images from the final image's ancestry,
        and delete them.
        """
        all_images = self.client.images.list()
        intermediates: list[Image] = self._identify_dangling_intermediates(all_images)
        print("HERE", intermediates)
        if intermediates and self.verbose:
            print("Cleaning up the following dangling intermediate images:")
            for img in intermediates:
                print(f"  - {img.id}")
        self._delete_images(intermediates)
