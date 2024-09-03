import os
import logging
from llama_parse import LlamaParse
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)


class FileLoaderConfig(BaseModel):
    data_dir: str = "data"
    use_llama_parse: bool = False

    @validator("data_dir")
    def data_dir_must_exist(cls, v):
        if not os.path.isdir(v):
            raise ValueError(f"Directory '{v}' does not exist")
        return v


def llama_parse_parser():
    if os.getenv("LLAMA_CLOUD_API_KEY") is None:
        raise ValueError(
            "LLAMA_CLOUD_API_KEY environment variable is not set. "
            "Please set it in .env file or in your shell environment then run again!"
        )
    parser = LlamaParse(
        result_type="markdown",
        verbose=True,
        language="en",
        ignore_errors=False,
    )
    return parser


def get_file_documents(config: FileLoaderConfig):
    from llama_index.core.readers import SimpleDirectoryReader

    try:
        reader = SimpleDirectoryReader(
            config.data_dir, recursive=True, filename_as_id=True, raise_on_error=True
        )
        if config.use_llama_parse:
            # LlamaParse is async first,
            # so we need to use nest_asyncio to run it in sync mode
            import nest_asyncio

            nest_asyncio.apply()

            parser = llama_parse_parser()
            reader.file_extractor = {".pdf": parser}

            data_path = os.path.join(config.data_dir, "AT00011245_02.01.pdf")
            # vanilaParsing = LlamaParse(result_type="markdown").load_data(data_path)

            parsingInstruction = """
It is an operator's manual containing many specifications set out in tables. 
Usually the text is divided into 2 columns per page. 
There are many charts with indications that we will ignore.
The numbering of the sections defines a hierarchy that is important to keep in mind to avoid confusion between sections.
"""
            withInstructionParsing = LlamaParse(result_type="markdown", parsing_instruction=parsingInstruction).load_data(data_path)

        return reader.load_data()
    except Exception as e:
        import sys, traceback

        # Catch the error if the data dir is empty
        # and return as empty document list
        _, _, exc_traceback = sys.exc_info()
        function_name = traceback.extract_tb(exc_traceback)[-1].name
        if function_name == "_add_files":
            logger.warning(
                f"Failed to load file documents, error message: {e} . Return as empty document list."
            )
            return []
        else:
            # Raise the error if it is not the case of empty data dir
            raise e
