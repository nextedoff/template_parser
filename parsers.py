import re
import yaml
import base64

from typing import Iterable, Union, List
from openai.types.chat import ChatCompletionRole, ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam, ChatCompletionSystemMessageParam, ChatCompletionContentPartParam, ChatCompletionMessageParam
from jinja2 import Template

class TemplateParser():
    
    def __init__(self):
        self.roles = ["assistant", "function", "system", "user"]
        self.messages: List[ChatCompletionMessageParam] = []
    
    def read(self, path) -> dict:
        pattern = r"-{3,}\n(.*)-{3,}\n(.*)"
        
        with open(path, encoding="utf-8") as file:
            file_contents = file.read()
        
        result = re.search(pattern, file_contents, re.DOTALL)
        
        if not result:
            raise ValueError("Invalid template format, it should be markdown-like format that is divided into two parts, where first part is yaml-like config, and the second is prompt for jinja2.")
        
        config_content, prompt_template = result.groups()

        return {
            "attributes": yaml.load(config_content, Loader=yaml.FullLoader),
            "body": prompt_template,
        }
    
    def render_template(self, template, **kwargs):
        universal_template = Template(template)
        return universal_template.render(**kwargs)
    
    def inline_image(self, image_item: str) -> str:
        """ Inline Image

        Parameters
        ----------
        image_item : str
            The image item to inline
        
        Returns
        -------
        str
            The inlined image
        """
        # pass through if it's a url or base64 encoded
        if image_item.startswith("http") or image_item.startswith("data"):
            return image_item
        # otherwise, it's a local file - need to base64 encode it
        else:
            image_path = self.path / image_item
            with open(image_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode("utf-8")

            if image_path.suffix == ".png":
                return f"data:image/png;base64,{base64_image}"
            elif image_path.suffix == ".jpg":
                return f"data:image/jpeg;base64,{base64_image}"
            elif image_path.suffix == ".jpeg":
                return f"data:image/jpeg;base64,{base64_image}"
            else:
                raise ValueError(
                    f"Invalid image format {image_path.suffix} - currently only .png and .jpg / .jpeg are supported."
                )
                
                
    def parse_content(self, content: str):
        # regular expression to parse markdown images
        image = r"(?P<alt>!\[[^\]]*\])\((?P<filename>.*?)(?=\"|\))\)"
        matches = re.findall(image, content, flags=re.MULTILINE)
        if len(matches) > 0:
            content_items = []
            content_chunks = re.split(image, content, flags=re.MULTILINE)
            current_chunk = 0
            for i in range(len(content_chunks)):
                # image entry
                if (
                    current_chunk < len(matches)
                    and content_chunks[i] == matches[current_chunk][0]
                ):
                    content_items.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": self.inline_image(
                                    matches[current_chunk][1].split(" ")[0].strip()
                                )
                            },
                        }
                    )
                # second part of image entry
                elif (
                    current_chunk < len(matches)
                    and content_chunks[i] == matches[current_chunk][1]
                ):
                    current_chunk += 1
                # text entry
                else:
                    if len(content_chunks[i].strip()) > 0:
                        content_items.append(
                            {"type": "text", "text": content_chunks[i].strip()}
                        )
            return content_items
        else:
            return content
    
    def add_formatted_message(self, role: ChatCompletionRole, content: Union[str, Iterable[ChatCompletionContentPartParam]]):
        message: ChatCompletionMessageParam
        if role == "user":
            message = ChatCompletionUserMessageParam(
                role=role,
                content=content
            )
        elif role == "assistant":
            message = ChatCompletionAssistantMessageParam(
                role=role,
                content=content
            )
        elif role == "system":
            message = ChatCompletionSystemMessageParam(
                role=role,
                content=content
            )
        else:
            raise ValueError(f"Invalid role {role}")
        
        return message
        
        
        
    def build_messages(self, 
            body: str, 
            few_shots: list[ChatCompletionMessageParam] = []
            ) -> list:
        
        messages = []
        separator = r"(?i)^\s*#?\s*(" + "|".join(self.roles) + r")\s*:\s*\n"

        # get valid chunks - remove empty items
        chunks = [
            item
            for item in re.split(separator, body, flags=re.MULTILINE)
            if len(item.strip()) > 0
        ]

        # if last chunk is role entry, then remove (no content?)
        if chunks[-1].strip().lower() in self.roles:
            chunks.pop()

        # create messages
        for i in range(0, len(chunks), 2):
            role = chunks[i].strip().lower()
            content = chunks[i + 1].strip()
            messages.append(self.add_formatted_message(role=role, content=self.parse_content(content)))
            
            if(i == 0 and role == "system"):
                for shot in few_shots:
                    messages.append(shot)
        
        return messages
        
    
    