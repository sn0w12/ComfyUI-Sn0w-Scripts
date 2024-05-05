from server import PromptServer
from ..sn0w import MessageHolder

class TextboxNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"

    CATEGORY = "utils"
    
    def run(self, unique_id):
        PromptServer.instance.send_sync("textbox", {
            "id": unique_id,
        })
        outputs = MessageHolder.waitForMessage(unique_id)
        return (outputs['output'],)
    