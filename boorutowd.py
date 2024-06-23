import os
import requests
import re
import contextlib

class BooruToWD:
    """
    A example node

    Class methods
    -------------
    INPUT_TYPES (dict): 
        Tell the main program input parameters of nodes.
    IS_CHANGED:
        optional method to control when the node is re executed.

    Attributes
    ----------
    RETURN_TYPES (`tuple`): 
        The type of each element in the output tulple.
    RETURN_NAMES (`tuple`):
        Optional: The name of each output in the output tulple.
    FUNCTION (`str`):
        The name of the entry-point method. For example, if `FUNCTION = "execute"` then it will run Example().execute()
    OUTPUT_NODE ([`bool`]):
        If this node is an output node that outputs a result/image from the graph. The SaveImage node is an example.
        The backend iterates on these output nodes and tries to execute all their parents if their parent graph is properly connected.
        Assumed to be False if not present.
    CATEGORY (`str`):
        The category the node should appear in the UI.
    execute(s) -> tuple || None:
        The entry point method. The name of this method must be the same as the value of property `FUNCTION`.
        For example, if `FUNCTION = "execute"` then this method's name must be `execute`, if `FUNCTION = "foo"` then it must be `foo`.
    """
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        """
            Return a dictionary which contains config for all input fields.
            Some types (string): "MODEL", "VAE", "CLIP", "CONDITIONING", "LATENT", "IMAGE", "INT", "STRING", "FLOAT".
            Input types "INT", "STRING" or "FLOAT" are special values for fields on the node.
            The type can be a list for selection.

            Returns: `dict`:
                - Key input_fields_group (`string`): Can be either required, hidden or optional. A node class must have property `required`
                - Value input_fields (`dict`): Contains input fields config:
                    * Key field_name (`string`): Name of a entry-point method's argument
                    * Value field_config (`tuple`):
                        + First value is a string indicate the type of field or a list for selection.
                        + Secound value is a config for type "INT", "STRING" or "FLOAT".
        """
        return {
            "required": {
                "booru_tags": ("STRING", {
                    "multiline": True, #True if you want the field to look like the one on the ClipTextEncode node
                    "default": ""
                }),
                "booru_url": ("STRING", {
                    "multiline": False, #True if you want the field to look like the one on the ClipTextEncode node
                    "default": ""
                }),
                "remove_meta_artist": ("BOOLEAN",{
                    "default": False
                }),
                "to_animagine_style": ("BOOLEAN",{
                    "default": False
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    #RETURN_NAMES = ("image_output_name",)

    FUNCTION = "convert_to_wd"

    #OUTPUT_NODE = False

    CATEGORY = "utils"

    def convert_to_wd(
            self,
            booru_tags: str, 
            booru_url: str,
            remove_meta_artist: bool,
            to_animagine_style: bool,
            ):
        source = ""
        dest = ""
        if booru_url:
            try:
                burl = booru_url + ".json"
                with requests.get(
                    url=burl,
                    headers={'user-agent': 'my-app/1.0.0'}
                ) as r:
                    raw_json = r.json()
                    if not to_animagine_style:
                        if remove_meta_artist:
                            txt = raw_json["tag_string_character"]
                            if txt:
                                source += f"{txt} "
                            txt = raw_json["tag_string_copyright"]
                            if txt:
                                source += f"{txt} "
                            txt = raw_json["tag_string_general"]
                            if txt:
                                source += f"{txt} "
                        else:
                            source = raw_json["tag_string"]
                    else:
                        pattern = "[1-6]\\+?(girl|boy)s?"
                        repatter = re.compile(pattern)
                        rawtag_general = raw_json["tag_string_general"]
                        general_tags_list = rawtag_general.split(' ')
                        # girl/boyを先に追加
                        for i, tag in enumerate(general_tags_list):
                            is_match = repatter.match(tag)
                            if is_match:
                                source += f"{tag} "
                        # character
                        rawtag_character = raw_json["tag_string_character"]
                        if rawtag_character:
                            source += f"{rawtag_character} "
                        # copyright
                        rawtag_copyright = raw_json["tag_string_copyright"]
                    if rawtag_copyright:
                        source += f"{rawtag_copyright} "
                        # girl/boy以外のgeneralタグ
                        for i, tag in enumerate(general_tags_list):
                            is_match = repatter.match(tag)
                            if not is_match:
                                source += f"{tag} "
                        if not remove_meta_artist:
                            txt = raw_json["tag_string_artist"]
                            if txt:
                                source += f"{txt} "
                            txt = raw_json["tag_string_meta"]
                            if txt:
                                source += f"{txt} "
            except:
                print("Failed to fetch danbooru tags.")
                raise RuntimeError("Bad URL, missing post or request refused(cloudflare wall?)")
        else:
            source = booru_tags

        if not source:
            print("Warning: booru_tag is empty")
            return ("",)

        source = source.strip()


        if os.path.exists("custom_nodes/ComfyUI-BooruToWd/removal-list.txt") and remove_meta_artist and not booru_url:
            f = open("custom_nodes/ComfyUI-BooruToWd/removal-list.txt", 'r', encoding='UTF-8') 
            removal = f.read()
            f.close()
            removal = removal.replace('\r\n', '\n')
            tags = removal.split('\n')
            sourceTags = source.split(' ')
            for i, tag in enumerate(tags):
                for j, src in enumerate(sourceTags):
                    if(tag == src and tag) or ("user_" in src):
                        # print(f"Found removal tag: {src}")
                        sourceTags[j] = ''

            for i, tag in enumerate(sourceTags):
                if i < (len(sourceTags) - 1) and tag:
                    sourceTags[i] += ", "

            dest = ''.join(sourceTags)
        else:
            dest = source.replace(' ', ", ")

    
        dest = dest.replace('_', ' ')
        # 制御文字のエスケープ
        dest = dest.replace('\\', "\\\\")
        dest = dest.replace('(', "\(")
        dest = dest.replace(')', "\)")

        dest = dest.replace('<', "\<")
        dest = dest.replace('>', "\>")

        dest = dest.replace('|', "\|")

        dest = dest.replace('[', "\[")
        dest = dest.replace(']', "\]")
    

        return (dest,)

    """
        The node will always be re executed if any of the inputs change but
        this method can be used to force the node to execute again even when the inputs don't change.
        You can make this node return a number or a string. This value will be compared to the one returned the last time the node was
        executed, if it is different the node will be executed again.
        This method is used in the core repo for the LoadImage node where they return the image hash as a string, if the image hash
        changes between executions the LoadImage node is executed again.
    """
    #@classmethod
    #def IS_CHANGED(s, image, string_field, int_field, float_field, print_to_screen):
    #    return ""

# Set the web directory, any .js file in that directory will be loaded by the frontend as a frontend extension
# WEB_DIRECTORY = "./somejs"

# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "BooruToWD": BooruToWD
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "BooruToWD": "Booru to WD"
}
