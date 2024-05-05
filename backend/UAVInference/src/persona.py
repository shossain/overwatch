# Import Required Packages
import os
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from jinja2 import Environment, PackageLoader
from openai import OpenAI

# Set Up Packages
load_dotenv()
env = Environment(loader=PackageLoader("utils", package_path="prompts"))


class Persona:
    def __init__(
        self,
        name: str,
        prompt_path: str = None,
        prompt: str = None,
        system_prompt: str = "",
        model_name: str = "gpt-4",
        api_key: str = None,
        client: OpenAI = None,
        temperature: float = 0.8,
    ):
        """
        Persona
        Creates and maintains a persona that you can interact with using the conversation
        API from openAI. Either the prompt path (which is a jinja txt file stored in ../utils/prompts)
        or a naive string format string ({var_name} for arguments) must be passed. If both are passed,
        jinja files are preferred. If none are passed, an exception is thrown.
        """
        if not os.getenv("OPENAI_API_KEY"):
            raise Exception(
                "OpenAI API key not found, please set OPENAI_API_KEY env variable"
            )
        self.api_key = os.getenv("OPENAI_API_KEY")

        if prompt_path is None and prompt is None:
            raise ValueError(
                "Either prompt_path or prompt parameters should be specified, but both cannot be empty."
            )

        self.prompt = prompt
        self.system_prompt = system_prompt
        if prompt_path:
            self.prompt = env.get_template(f"user/{prompt_path}")
            self.system_prompt = env.get_template(f"system/{prompt_path}")

        self.name = name
        self.model_name = model_name
        self.temperature = temperature

        self.client = OpenAI(api_key=self.api_key)

    def format_prompt(self, args: Dict, system: bool = False) -> str:
        """
        Formats the prompt depending on whether it's a string prompt or a more complex jinja prompt
        if it's the latter, then render with the appropriate arguments, and if former, format.

        Params:
            args (Dict): argument dictionary
            system (bool): whether the arguments should be applied to system prmpt

        Returns:
            str: complete formatted prompt
        """
        if not isinstance(self.prompt, str):
            return (
                self.system_prompt.render(**args)
                if system
                else self.prompt.render(**args)
            )
        return (
            self.system_prompt.format(**args) if system else self.prompt.format(**args)
        )

    def chat(
        self,
        system_args: Dict,
        prompt_args: Dict,
        prev_context: List[Dict[str, str]] = None,
    ) -> Tuple[str, List[Dict]]:
        """
        Sends a request to the OpenAI API to generate a response.
        If the prompt_args does not cover all the fields specified in the prompt string,
        then it will throw a KeyError exception. Previous context is a list of dicts formatted
        as such: [{"role": "assistant", "content", "bla bla"}, {"role", "user",
        "content": "bla bla"}, ...].

        Method will return a tuple of the immediately returned message as well as an updated list
        of previous messages that can be used as context to be passed into this method

        Params:
            prompt_args (Dict): specifies arguments to the prompt
            prev_context (List[Dict[str,str]]): context for previous conversations
        """
        complete_prompt = self.format_prompt(prompt_args, system=False)
        messages = [
            {"role": "system", "content": self.format_prompt(system_args, system=True)}
        ]

        if prev_context:
            messages.extend(prev_context)
        messages.append({"role": "user", "content": complete_prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
        )

        content = response.choices[0].message.content
        messages = messages[1:] + [{"role": "assistant", "content": content}]
        return content, messages
