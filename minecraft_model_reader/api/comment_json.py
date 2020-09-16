import json
from typing import TextIO

"""
Some of the Bedrock json files contain comments which is not valid JSON and the standard json parser
will throw errors. This will first try and use the vanilla json parser and fall back to the slower version if that fails.
"""


class CommentJSONDecodeError(json.JSONDecodeError):
    pass


def from_file(path: str):
    with open(path) as f:
        return load(f)


def load(obj: TextIO):
    return loads(obj.read())


def loads(s: str):
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return _loads(s)


def _loads(_json):
    # given a valid MinecraftJSON string will return the values as python objects
    # in this context MinecraftJSON is standard JSON but with comment blocks and
    # line comments that would normally be illegal in standard JSON
    _number = set("0123456789-")
    _float = set("0123456789-.")
    _whitespace = set(" \t\r\n")

    def strip_whitespace(_json, index):
        # skips whitespace characters (<space>, <tab>, <charrage return> and <newline>)
        # as well as block comments and line comments
        while _json[index] in _whitespace:
            index += 1
        if _json[index] == "/":
            if _json[index + 1] == "/":
                index += 2
                while _json[index] != "\n":
                    index += 1
                index = strip_whitespace(_json, index)
            elif _json[index + 1] == "*":
                index += 2
                while _json[index : index + 2] != "*/":
                    index += 1
                    if index + 1 >= len(_json):
                        raise json.JSONDecodeError(
                            "expected */ but reached the end of file", _json, index
                        )
                index += 2
                index = strip_whitespace(_json, index)
            else:
                raise json.JSONDecodeError(
                    f"unexpected / at index {index}", _json, index
                )
        return index

    def parse_json_recursive(_json, index=0):
        index = strip_whitespace(_json, index)
        if _json[index] == "{":
            index += 1
            # dictionary
            json_obj = {}
            repeat = True
            while repeat:
                index = strip_whitespace(_json, index)
                # }"
                if _json[index] == '"':
                    index += 1
                    key = ""
                    while _json[index] != '"':
                        key += _json[index]
                        index += 1
                    index += 1

                    index = strip_whitespace(_json, index)

                    if _json[index] == ":":
                        index += 1
                    else:
                        raise json.JSONDecodeError(
                            f"expected : got {_json[index]} at index {index}",
                            _json,
                            index,
                        )

                    index = strip_whitespace(_json, index)

                    json_obj[key], index = parse_json_recursive(_json, index)

                    index = strip_whitespace(_json, index)

                    if _json[index] == ",":
                        index += 1
                    else:
                        repeat = False
                else:
                    repeat = False

            if index >= len(_json):
                raise json.JSONDecodeError(
                    "expected } but reached end of file", _json, index
                )
            elif _json[index] == "}":
                index += 1
            else:
                raise json.JSONDecodeError(
                    f"expected }} got {_json[index]} at index {index}", _json, index
                )
            return json_obj, index

        elif _json[index] == "[":
            index += 1
            # list
            json_obj = []
            index = strip_whitespace(_json, index)
            repeat = _json[index] != "]"
            while repeat:
                val, index = parse_json_recursive(_json, index)
                json_obj.append(val)

                index = strip_whitespace(_json, index)

                if _json[index] == ",":
                    index += 1
                else:
                    repeat = False
                index = strip_whitespace(_json, index)

            if index >= len(_json):
                raise json.JSONDecodeError(
                    "expected ] but reached end of file", _json, index
                )
            elif _json[index] == "]":
                index += 1
            else:
                raise json.JSONDecodeError(
                    f"expected ] got {_json[index]} at index {index}", _json, index
                )
            return json_obj, index

        elif _json[index] == '"':
            index += 1
            # string
            json_obj_list = []
            while _json[index] != '"':
                json_obj_list.append(_json[index])
                index += 1
            index += 1
            return "".join(json_obj_list), index

        elif _json[index] in _number:
            # number
            json_obj_list = []
            while _json[index] in _float:
                json_obj_list += _json[index]
                index += 1
            if "." in json_obj_list:
                return float("".join(json_obj_list)), index
            else:
                return int("".join(json_obj_list)), index

        elif _json[index] == "n" and _json[index : index + 4] == "null":
            index += 4
            return None, index

        elif _json[index] == "t" and _json[index : index + 4] == "true":
            index += 4
            return True, index

        elif _json[index] == "f" and _json[index : index + 5] == "false":
            index += 5
            return False, index
        else:
            raise json.JSONDecodeError(
                f'unexpected key {_json[index]} at {index}. Expected {{, [, ", num, null, true or false',
                _json,
                index,
            )

    # call recursive function and pass back python object
    return parse_json_recursive(_json)[0]
