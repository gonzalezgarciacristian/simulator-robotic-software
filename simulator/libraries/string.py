"""
String library from arduino. More details at:
https://www.arduino.cc/reference/en/language/variables/data-types/stringobject/
"""


def get_name():
    return "String"


def get_methods():
    """
    Returns the methods of the library as a dict, whose
    key is the naming in Arduino and whose value is the
    corresponding method.
    Returns:
        A dict with the methods
    """
    methods = {}
    methods["charAt"] = ("char", "char_at", ["int"], -1)
    methods["compareTo"] = ("int", "compare_to", ["string"], -1)
    methods["concat"] = ("bool", "concat", ["any"], -1)
    methods["c_str"] = ("string", "c_str", [], -1)
    methods["endsWith"] = ("bool", "ends_with", ["string"], -1)
    methods["equals"] = ("bool", "equals", ["string"], -1)
    methods["equalsIgnoreCase"] = (
        "bool", "equals_ignore_case", ["string"], -1)
    methods["getBytes"] = ("byte", "get_bytes", [], -1)
    methods["indexOf"] = ("int", "index_of", ["char", "(int)"], -1)
    methods["lastIndexOf"] = ("int", "last_index_of", ["char", "(int)"], -1)
    methods["length"] = ("int", "length", [], -1)
    methods["remove"] = ("void", "remove", ["int", "(int)"], -1)
    methods["replace"] = ("void", "replace", ["string", "string"], -1)
    methods["reserve"] = ("void", "reserve", [], -1)  # not implemented
    methods["setCharAt"] = ("void", "set_char_at", ["int", "char"], -1)
    methods["startsWith"] = ("bool", "starts_with", ["string"], -1)
    methods["substring"] = ("string", "substring", ["int", "(int)"], -1)
    methods["toCharArray"] = ("char", "to_char_array", ["char", "int"], 0)
    methods["toDouble"] = ("double", "to_double", [], -1)
    methods["toInt"] = ("int", "to_int", [], -1)
    methods["toFloat"] = ("float", "to_float", [], -1)
    methods["toLowerCase"] = ("string", "to_lower_case", [], -1)
    methods["toUpperCase"] = ("string", "to_upper_case", [], -1)
    methods["trim"] = ("string", "trim", [], -1)
    return methods


def get_not_implemented():
    return [
        "reserve"
    ]


class String:
    """
    Represents Arduino String object
    """

    OK = 0
    ERROR = -1
    NOT_IMPL_WARNING = -2

    def __init__(self, string="", *args, **kwargs):
        self.string = string

    def __repr__(self) -> str:
        return self.string

    def __str__(self) -> str:
        return self.string

    def __add__(self, string):
        if isinstance(string, String):
            return String(self.string + string.string)
        return self.string + str(string)

    def __iadd__(self, string):
        if isinstance(string, String):
            self.string += string.string
        else:
            self.string += str(string)
        return String(self.string)

    def __lt__(self, string):
        return self.string < string.string

    def __le__(self, string):
        return self.string <= string.string

    def __gt__(self, string):
        return self.string > string.string

    def __ge__(self, string):
        return self.string >= string.string

    def __eq__(self, string):
        other = string.string if isinstance(string, String) else str(string)
        return self.string == other

    def __ne__(self, string):
        other = string.string if isinstance(string, String) else str(string)
        return self.string != other

    def __getitem__(self, index):
        if -len(self.string) <= index < len(self.string):
            return self.string[index]
        return '\0'

    def char_at(self, n):
        """
        Access a particular character of the string
        Arguments:
            string: the string to access
            n: the index to access
        """
        return self.string[n]

    def compare_to(self, string):
        """
        Compares two Strings, testing whether one comes
        before or after the other, or whether they’re equal.
        The strings are compared character by character,
        using the ASCII values
        Arguments:
            string: the string to compare to
        """
        if self.string < string.string:
            return -1
        elif self.string == string.string:
            return 0
        else:
            return 1

    def concat(self, param):
        """
        Appends the parameter to a string
        Arguments:
            param: the value to add (allowed string, char, byte, int,
            uint, long, ulong, float and double)
        """
        self.string = str(self.string) + str(param)
        return True

    def c_str(self):
        """
        Converts the contents of a String as a C-style, null-terminated string
        """
        return self.string + '\0'

    def ends_with(self, string):
        """
        Tests wether or not string1 ends with the characters of
        string
        Arguments:
            string: the end characters to check
        """
        len_str2 = len(string.string)
        return self.string[-len_str2:] == string.string

    def equals(self, string):
        """
        Compares string1 with string for equality
        Arguments:
            string: a string
        """
        return self.string == string.string

    def equals_ignore_case(self, string):
        """
        Compares string1 with string for equality ignoring case
        sentitivity
        Arguments:
            string: a string
        """
        return str(self.string).lower() == str(string.string).lower()

    def get_bytes(self):
        """
        Copies the String’s characters to the supplied buffer.
        """
        return bytes(self.string, 'UTF-8')

    def index_of(self, val, from_c=0):
        """
        Locates a character or String within another String. By default,
        searches from the beginning of the String, but can also start
        from a given index, allowing for the locating of all instances
        of the character or String.
        Arguments:
            val: the value to search for (char)
            from_c: the index of start
        """
        str_temp = self.string[from_c:]
        return str(str_temp).find(val)

    def last_index_of(self, val, from_c=-1):
        """
        Locates a character or String within another String. By default,
        searches from the end of the String, but can also work backwards
        from a given index, allowing for the locating of all instances
        of the character or String.
        Arguments:
            val: the value to search for (char)
            from_c: the index of start (backwards from)
        """
        str_temp = self.string[:from_c]
        return str(str_temp)[::-1].find(val)

    def length(self):
        """
        Returns the length of a given string
        """
        return len(self.string)

    def remove(self, index, count=-1):
        """
        Modify in place a String removing chars from the provided
        index to the end of the String or from the provided index
        to index plus count.
        Arguments:
            index: the position of start (0-indexed)
            count: number of characters to remove
        """
        str_1 = self.string[:index]
        str_2 = ""
        if count != -1:
            str_2 = self.string[count:]
        self.string = str(str_1) + str(str_2)

    def replace(self, substring1, substring2):
        """
        Replaces all instances of a given character with another character.
        You can also use replace to replace substrings of a String
        with a different substring.
        Arguments:
            substring1: a string to be replaced
            substring2: a string to replace
        """
        self.string = str(self.string).replace(
            substring1.string, substring2.string)

    def reserve(self):
        """
        Not needed. Not implemented
        """
        return self.NOT_IMPL_WARNING

    def set_char_at(self, index, c):
        """
        Sets a character of the String.
        Arguments:
            index: the index to set the char at
            c: the char to set
        """
        self.string = self.string[index:] + c + self.string[index + 1:]

    def starts_with(self, string):
        """
        Check wether a string starts with the characters of another
        string
        Arguments:
            string: a string
        """
        other = string.string if isinstance(string, String) else str(string)
        len_str2 = len(other)
        substr = self.string[:len_str2]
        return substr == other

    def substring(self, from_c, to_c=-1):
        """
        Creates a substring [from_c, to_c)
        Arguments:
            from_c: inclusive start index
            to_c: exclusive end index
        """
        return String(self.string[from_c: to_c] if to_c != -1 else self.string[from_c:])

    def to_char_array(self, buf, len):
        """
        Copies the String’s characters to the supplied buffer.
        """
        return list(self.string)

    def to_double(self):
        """
        Parses string to double
        """
        try:
            return float(self.string)
        except ValueError:
            return 0.0

    def to_int(self):
        """
        Parses string to int
        """
        try:
            return int(self.string)
        except ValueError:
            return 0

    def to_float(self):
        """
        Parses string to float
        """
        try:
            return float(self.string)
        except ValueError:
            return 0.0

    def to_lower_case(self):
        """
        Converts string to lower case
        """
        self.string = str(self.string).lower()

    def to_upper_case(self):
        """
        Converts string to upper case
        """
        self.string = str(self.string).upper()

    def trim(self):
        """
        Deletes leading and trailing whitespaces from string
        """
        self.string = str(self.string).strip()
        return self
