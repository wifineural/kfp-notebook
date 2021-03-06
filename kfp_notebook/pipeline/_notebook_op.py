# -*- coding: utf-8 -*-
#
# Copyright 2018-2020 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from kfp.dsl._container_op import BaseOp, ContainerOp


"""
The NotebookOp uses a python script to bootstrap the user supplied image with the required dependencies.
In order for the script run properly, the image used, must at a minimum, have the 'curl' utility available
and have python3
"""


class NotebookOp(ContainerOp):

    def __init__(self,
                 notebook: str,
                 cos_endpoint: str,
                 cos_bucket: str,
                 cos_directory: str,
                 cos_dependencies_archive: str,
                 pipeline_outputs: str,
                 pipeline_inputs: str,
                 requirements_url: str = None,
                 bootstrap_script_url: str = None,
                 **kwargs):
        """Create a new instance of ContainerOp.
        Args:
          notebook: name of the notebook that will be executed per this operation
          cos_endpoint: object storage endpoint e.g weaikish1.fyre.ibm.com:30442
          cos_bucket: bucket to retrieve archive from
          cos_directory: name of the directory in the object storage bucket to pull
          cos_dependencies_archive: archive file name to get from object storage bucket e.g archive1.tar.gz
          pipeline_outputs: comma delimited list of files produced by the notebook
          pipeline_inputs: comma delimited list of files to be consumed/are required by the notebook
          requirements_url: URL to a python requirements.txt file to be installed prior to running the notebook
          bootstrap_script_url: URL to a custom python bootstrap script to run
          kwargs: additional key value pairs to pass e.g. name, image, sidecars & is_exit_handler.
                  See Kubeflow pipelines ContainerOp definition for more parameters or how to use
                  https://kubeflow-pipelines.readthedocs.io/en/latest/source/kfp.dsl.html#kfp.dsl.ContainerOp
        """

        self.notebook = notebook
        self.notebook_name = self._get_file_name_with_extension(notebook, 'ipynb')
        self.cos_endpoint = cos_endpoint
        self.cos_bucket = cos_bucket
        self.cos_directory = cos_directory
        self.cos_dependencies_archive = cos_dependencies_archive
        self.container_work_dir = "jupyter-work-dir"
        self.bootstrap_script_url = bootstrap_script_url
        self.requirements_url = requirements_url
        self.pipeline_outputs = pipeline_outputs
        self.pipeline_inputs = pipeline_inputs

        if self.bootstrap_script_url is None:
            self.bootstrap_script_url = 'https://raw.githubusercontent.com/elyra-ai/' \
                                        'kfp-notebook/master/etc/docker-scripts/bootstrapper.py'

        if self.requirements_url is None:
            self.requirements_url = 'https://raw.githubusercontent.com/elyra-ai/' \
                                    'kfp-notebook/master/etc/requirements-elyra.txt'

        if 'image' not in kwargs:
            ValueError("You need to provide an image.")

        if notebook is None:
            ValueError("You need to provide a notebook.")

        if 'arguments' not in kwargs:
            """ If no arguments are passed, we use our own.
                If ['arguments'] are set, we assume container's ENTRYPOINT is set and dependencies are installed
                NOTE: Images being pulled must have python3 available on PATH and cURL utility
            """

            kwargs['command'] = ['sh', '-c']
            kwargs['arguments'] = ['mkdir -p ./%s && cd ./%s && '
                                   'curl -H "Cache-Control: no-cache" -L %s --output bootstrapper.py && '
                                   'curl -H "Cache-Control: no-cache" -L %s --output requirements-elyra.txt && '
                                   'python -m pip install packaging &&'
                                   'python -m pip freeze > requirements-current.txt &&'
                                   'python bootstrapper.py '
                                   ' --cos-endpoint %s '
                                   ' --cos-bucket %s '
                                   ' --cos-directory "%s" '
                                   ' --cos-dependencies-archive "%s" '
                                   ' --outputs %s '
                                   ' --inputs %s '
                                   ' --notebook "%s" ' % (
                                       self.container_work_dir,
                                       self.container_work_dir,
                                       self.bootstrap_script_url,
                                       self.requirements_url,
                                       self.cos_endpoint,
                                       self.cos_bucket,
                                       self.cos_directory,
                                       self.cos_dependencies_archive,
                                       self.pipeline_outputs,
                                       self.pipeline_inputs,
                                       self.notebook
                                       )
                                   ]

        super().__init__(**kwargs)

    def _get_file_name_with_extension(self, name, extension):
        """ Simple function to construct a string filename
        Args:
            name: name of the file
            extension: extension to append to the name

        Returns:
            name_with_extension: string filename
        """
        name_with_extension = name
        if extension not in name_with_extension:
            name_with_extension = '{}.{}'.format(name, extension)

        return name_with_extension
