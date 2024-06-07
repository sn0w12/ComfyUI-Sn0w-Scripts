<h1 align="center">
    sn0w-scripts
</h1>

A collection of nodes and improvements created for general ease and testing loras. These are just nodes I made and found useful, they should work with most other nodes. Most nodes that take in a prompt are made with booru tags in mind and might not work as expected with other prompts.

# Get Started

## Install

1. Install [ComfyUi](https://github.com/comfyanonymous/ComfyUI).
2. Clone this repo into `custom_nodes`:
    ```
    git clone https://github.com/sn0w12/ComfyUI-Sn0w-Scripts
    ```
3. Start up ComfyUI.

# Configuration

In the ComfyUI settings, you can modify various settings. Some changes will apply immediately, while others require a refresh to take effect.

## Important Note
Many of the nodes require these paths to be in your extra_model_paths.yaml (with your real directories of course).

```yaml
loras:
    base_path: D:/Ai/Lora/loras

    loras_xl: /XL
    loras_15: /1.5
```

# Major Features

## Lora Management

A major focus for me was making loras more manageable by letting users create their own lora loaders with specific folder paths and automatically loading loras based on tags. This makes it a lot easier to look through your loras, although also limits what loras you can use depending on your configuration. The custom lora loaders are configured in the ComfyUI settings and should look like this:
```
ExampleName1:Value1
Pony Styles:pony/style
```

### Favourite Loras & Characters

The custom lora loaders and the character selecter let you favourite loras and characters that are always at the top of the loaders. The favourite loras are across all your custom lora loaders and the normal lora loader, however the normal one is not sorted correctly.

![Favourite Showcase](./imgs/favourite_list.png)

## Sigmoid Scheduler

A custom scheduler that generally produces similar quality results as most other schedulers in my testing. However it works very poorly at low steps which may be an issue for some. 

### Sigmoid vs Align your steps

> <details>
>    <summary><i>Comparisons</i></summary>
>    Images generated at 20 steps, 8 cfg, 1152 x 896, no upscaling
>
>```
>(score_9, score_8_up, score_7_up, score_6_up, source_anime, BREAK:1.1), 1girl, lips, long hair, grey eyes, black coat, medium breasts, cowboy shot, black robe, gold jewelry, looking at viewer, simple background, solo, white background, closed mouth, arms behind back, (red hair, dress, long dress, robe, white dress, gold trim:1.1)
>```
>    ![Sigmoid Comparison](./imgs/comparison_1.png)
>    ```
>(power \(chainsaw man\), chainsaw man:1.1), blonde hair, cross-shaped pupils, demon girl, demon horns, double-parted bangs, hair between eyes, long hair, red horns, symbol-shaped pupils, yellow eyes, 1girl, black necktie, black pants, collared shirt, double v, looking at viewer, necktie, orange eyes, pants, parted lips, red background, red jacket, sharp teeth, shirt partially tucked in, shirt tucked in, simple background, sleeves past wrists, smile, solo, teeth, v, white shirt, (score_9, score_8_up, score_7_up, score_6_up, source_anime, BREAK:1.1)
>```
>    ![Sigmoid Comparison](./imgs/comparison_2.png)
>    ```
>(score_9, score_8_up, score_7_up, score_6_up, source_anime, BREAK:1.1), (makima \(chainsaw man\), chainsaw man:1.1), hair between eyes, long hair, medium breasts, red hair, ringed eyes, yellow eyes, 1836547, 1girl, @ \(symbol\), black necktie, braided ponytail, business suit, collared shirt, formal, light smile, looking at viewer, necktie, office lady, sidelocks, simple background, smile, solo, suit, white shirt
>```
>    ![Sigmoid Comparison](./imgs/comparison_3.png)
>    ```
>(score_9, score_8_up, score_7_up, score_6_up, source_anime, BREAK:1.1), (makima \(chainsaw man\), chainsaw man:1.1), hair between eyes, long hair, medium breasts, red hair, ringed eyes, yellow eyes, 1girl, black jacket, black necktie, black pants, black vest, closed eyes, collared shirt, formal, necktie, pants, shirt tucked in, simple background, sitting, solo, suit jacket, vest, white background, white shirt
>```
>    ![Sigmoid Comparison](./imgs/comparison_4.png)
>    </details>

### Sigmoid graph

![Sigmoid Graph](./imgs/sigmoid_graph.png)

# Nodes

## Image Processing

Nodes that are specifically for generating and processing images.

### Simple Sampler Custom
> Ksampler with more settings and optional inputs. Support for custom schedulers
> <details>
>    <summary>ℹ️ <i>See More Information</i></summary>
>
>    - Can take both text and conditioning as positive and negative input.
>    - Can take a latent image or can generate one if none is provided.
>    - Supports schedulers such as align your steps, you can also create your own scheduler in `src/custom_schedulers/`, make sure to follow the example provided in `get_sigmas_sigmoid.py`.
>    - You can also just get the sigmas from any of the scheduler nodes and drag them into `sigmas (optional)`, if you do the scheduler widget will not be used.
>
>    ![Simple Sampler](./imgs/simple_sampler.png)
>    </details>

### Lora Tester
> Automatically generates X amount of images with provided loras.
> <details>
>    <summary>ℹ️ <i>See More Information</i></summary>
>
>    - I recommend making lora_info and add_default_generation inputs and using the outputs from the Lora Selector.
>    - Takes normal KSampler input but takes positive and negative inputs as text.
>    - Outputs a batch of images.
> 
>    ![Lora Tester](./imgs/lora_tester.png)
>    </details>

## Lora Management

Nodes that handle lora selection, stacking, and loading.

### Load Lora XL/1.5
> Normal load lora but from another folder.
> <details>
>    <summary>ℹ️ <i>See More Information</i></summary>
>
>    - Add these to your extra_model_paths.yaml (for example):
>    - loras_xl: C:/path/XL
>    - loras_15: C:/path/1.5
>
>    ![Load Lora](./imgs/load_lora.png)
>    ![Example](./imgs/lora_paths_example.png)
>    </details>

### Load Lora Folder
> Dynamically applies Lora models based on similarity to a provided prompt.
> <details>
>    <summary>ℹ️ <i>See More Information</i></summary>
>
>    - This node processes a given prompt to identify and apply the most similar Lora models of the tags found in the prompt.
>    - For each part of the prompt, the node calculates a distance between tags and available Lora model filenames. The max distance can be chosen in the settings.
>    - **Example folder input:** `*master_folder, subfolder1:3, -excludefolder, subfolder2`
>        - `*master_folder` specifies all paths must include `master_folder`.
>        - `subfolder1:3` indicates up to 3 models from `subfolder1` can be loaded.
>        - `-excludefolder` ensures any path containing `excludefolder` is ignored.
>        - `subfolder2` loads models from this subfolder without a numeric limit.
>    - Note: You need the loras separated into XL and 1.5 as stated in the `Important Note`.
>    - Note: Loras need to be named very similarly to the tag, with at most 5 characters different. Words in the lora filename can be separated by spaces or underscores.
>
>    ![Load Lora Folder](./imgs/load_lora_Folder.png)
>    </details>

### Lora Selector
> Automatically selects X amount of loras between two numbers.
> <details>
>    <summary>ℹ️ <i>See More Information</i></summary>
>
>    - Loras have to be formatted like the default kohya_ss outputs. (lora_name-000001)
>    - Select the first lora.
>    - Select the number of the highest lora you want to test.
>    - Select the amount of loras you want to test.
>    - Outputs list of loras like this: \<lora:name:strength>
>    - Add default generation adds an extra "nothing" at the end of the list, used in Lora Tester to generate an image without the lora.
> 
>    ![Lora Selector](./imgs/lora_selector.png)
>    </details>

### Lora Stacker
> Outputs a list of loras for Lora Tester. Does not load any loras by itself.
> <details>
>    <summary>ℹ️ <i>See More Information</i></summary>
>
>    - Basically Lora Selector but manual.
>    - Specifically for the lora testers.
> 
>    ![Lora Stacker](./imgs/lora_stacker.png)
>    </details>

## Character and Text Processing
Nodes for selecting and combining character and textual elements.

### Character Selector
> Outputs a character name and prompt.
> <details>
>    <summary>ℹ️ <i>See More Information</i></summary>
>
>    - Loads `characters.json` and outputs prompt based on it.
>    - You can create a file named `custom_characters.json` and add characters there if you want, they will be loaded with all the other characters if you format it like the `characters.json` file.
>    - If `custom_characters.json` has a character with the same name as `characters.json` it will add the custom prompt at the end of the normal one, this can be useful if you have loras that need activation tags.
> 
>    ![Character Selector](./imgs/character_selector.png)
>    </details>

### Prompt Combine
> Combines multiple strings with a specified separator and optionally simplifies the result by removing redundant or incompatible tags.
> <details>
>    <summary>ℹ️ <i>See More Information</i></summary>
>
>    - If simplify is enabled, the simplification process identifies and removes redundant tags (e.g., when a tag is fully encompassed by another, more descriptive tag) and tags incompatible with factors such as facing away, covered eyes, etc. Any tags that are in parentheses will not be removed.
>    - Simplify will also move 1girl/ 1boy to the front of the prompt to be in line with animagine 3's tagging if the option is enabled.
> 
>    ![Prompt Combine](./imgs/prompt_combine.png)
>    </details>

## Utility Nodes
Nodes that provide utility functions across the system.

### Get Font Size Node
> Estimates the optimal font size for text to fit within an image based on Lora information.
> <details>
>    <summary>ℹ️ <i>See More Information</i></summary>
>
>    - This node takes an image and a string, estimating the best font size to ensure that the longest piece of the string fits within the image. The approach considers the image's width and the length of the text to find a size that balances visibility and fit.
>
>    ![Get Font Size](./imgs/get_font_size.png)
>    </details>

### Copy/Paste Textbox
> A multiline textbox with copy and paste functionality
> <details>
>    <summary>ℹ️ <i>See More Information</i></summary>
>
>    ![Textbox](./imgs/textbox.png)
>    </details>

### Get Face Tags
> Filters a string to only returns tags that have to do with the head/ face. 
<br>

# Example Workflows
## Lora Tester
Note: Uses [ImagesGrid](https://github.com/LEv145/images-grid-comfy-plugin) for making the actual grid from the image output.

![Lora Tester](./imgs/lora_tester_workflow.png)