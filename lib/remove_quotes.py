#!/usr/bin/python3
'''Removes quotes from IWYU output'''
import sys
def replace_quotes_with_angle_brackets(text):
    '''Replaces odd " with < and even " with >'''
    result = []
    replace_with = '<'
    for char in text:
        if char == '"':
            result.append(replace_with)
            replace_with = '>' if replace_with == '<' else '<'
        else:
            result.append(char)
    return ''.join(result)

if __name__ == "__main__":
    print(replace_quotes_with_angle_brackets(sys.stdin.read()))
