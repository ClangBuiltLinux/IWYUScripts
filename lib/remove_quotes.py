#!/usr/bin/python3
"""Removes quotes from IWYU output"""
import sys


def replace_quotes_with_angle_brackets(text):
    """Replaces odd " with < and even " with >"""
    replace_with = "<"
    text = text.split("\n")
    formatted = []
    for line in text:
        if "/" in line and ".." not in line:
            result = []
            for char in line:
                if char == '"':
                    result.append(replace_with)
                    replace_with = ">" if replace_with == "<" else "<"
                else:
                    result.append(char)
            formatted.append("".join(result))
        else:
            formatted.append(line)
    return "\n".join(formatted)


if __name__ == "__main__":
    print(replace_quotes_with_angle_brackets(sys.stdin.read()))
