from server import PromptServer
from ..sn0w import MessageHolder
from PIL import Image
import numpy as np
import base64
from io import BytesIO
import torch

class ShowSigmasNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sigmas": ("SIGMAS", ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("SIGMAS", "IMAGE",)
    FUNCTION = "run"

    CATEGORY = "utils"

    def sigmas_to_list(self, sigmas):
         # Convert tensor to a numpy array if it's not already
        if isinstance(sigmas, np.ndarray):
            temporary_sigmas = sigmas
        else:
            try:
                temporary_sigmas = sigmas.numpy()
            except AttributeError:
                try:
                    temporary_sigmas = sigmas.detach().cpu().numpy()
                except AttributeError:
                    temporary_sigmas = np.array(sigmas)
        
        if temporary_sigmas.ndim == 0:
            sigmas_list = [[float(temporary_sigmas)]]
        elif temporary_sigmas.ndim == 1:
            sigmas_list = [[float(value)] for value in temporary_sigmas]
        else:
            sigmas_list = temporary_sigmas.tolist()
        
        return sigmas_list
    
    def image_to_tensor(self, outputs):
        output_data = outputs['output']
        if ',' in output_data:
            image_data = output_data.split(',', 1)[1]
        else:
            image_data = output_data
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        image_np = np.array(image)

        print("Initial image array values (sample):", image_np[0, 0, :])

        # Normalize the image values to [0, 1]
        image_np = image_np / 255.0
        print("Normalized image values (sample):", image_np[0, 0, :])

        # Ensure the image is in RGB format if it's RGBA
        if image_np.ndim == 3 and image_np.shape[2] == 4:
            image_np = image_np[:, :, :3]

        # Convert the numpy image to a tensor and permute dimensions to (H, W, C)
        image_tensor = torch.tensor(image_np).float()

        # Ensure the tensor is in the shape (1, H, W, C)
        if image_tensor.ndim == 3:
            image_tensor = image_tensor.unsqueeze(0)
        
        print("Tensor shape for SaveImage node:", image_tensor.shape)

        return image_tensor
    
    def run(self, sigmas, unique_id):
        sigmas_list = self.sigmas_to_list(sigmas)

        PromptServer.instance.send_sync("sn0w_get_sigmas", {
            "id": unique_id,
            "sigmas": sigmas_list,
        })
        outputs = MessageHolder.waitForMessage(unique_id)
        
        final_tensor = self.image_to_tensor(outputs)

        return (sigmas, final_tensor,)
