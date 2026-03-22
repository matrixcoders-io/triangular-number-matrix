from pybaseconv import Converter, BASE
import re
def is_single_repetitive(s):
    """
    Returns True if the string consists of the same character repeated 2 or more times.
    Otherwise, returns False.
    """
    # Regex explanation:
    # ^      -> start of string
    # (.)    -> capture any single character (letter or digit)
    # \1+    -> match the same character one or more times (total length >= 2)
    # $      -> end of string
    pattern = r"^(.)\1+$"
    
    return bool(re.match(pattern, s))

def right_align(text: str, width: int) -> str:
    # If text is longer than width, return the text as is
    if len(text) >= width:
        return text
    # Otherwise, pad with spaces on the left
    padding = width - len(text)
    return ' ' * padding + text

def triangular_number(n):
    if n < 1:
        raise ValueError("Input must be a positive integer.")
    return n * (n + 1) // 2

#alldigits = "0123456789abcdefghijklmnopqrstuvwxyzა"
#alldigits = "0123456789abcdefg"
alldigits = "0123456"
#alldigits = "0123456789abcdefghi"

base10ToBase36 = Converter(BASE.DEC, alldigits)
base36Tobase10 = Converter(alldigits, BASE.DEC)
def show_conversion_table(base36Tobase10, base10ToBase36, digits):
    print()
    print(right_align(str(len(digits)) + " Base  ", 60) + "10 base")
    print()    
    for char in digits[1:]:
        rep_digit = char
        for i in range(len(digits)):
            rep_digit += char
            tri_num = triangular_number(int(base36Tobase10.convert(rep_digit)))
            print(right_align( str(base10ToBase36.convert(str(tri_num)))  + " = " + rep_digit+ "  ", 60) + base36Tobase10.convert(rep_digit) + " = " + str(tri_num))
            #print(str(base10ToBase36.convert(str(tri_num))))


show_conversion_table(base36Tobase10, base10ToBase36, alldigits)
#print(base10ToBase36.convert('123456789'))
#print(base36Tobase10.convert('21i3v9'))
