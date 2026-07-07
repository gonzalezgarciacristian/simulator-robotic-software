"""
This module includes all needed Arduino libraries for
the programming of a Linear Actuator and a Mobile Robot.
Those libraries are:
    - The standard ones of Arduino
    - Serial
    - Servo
    - Keyboard
"""
import libraries.standard as std
import libraries.serial as serial
import libraries.servo as servo
import libraries.keyboard as keyboard
import libraries.string as string
import libraries.braccio as braccio
import libraries.stdlib as stdlib


class LibraryManager:
    OK = 0
    ERROR = -1
    NOT_IMPL_WARNING = -2

    def __init__(self):
        """
        Constructor for library manager
        """
        self.library_methods = {
            std.get_name(): std.get_methods(),
            serial.get_name(): serial.get_methods(),
            string.get_name(): string.get_methods()
        }
        self.libraries = {
            std.get_name(): (std, std.get_not_implemented()),
            serial.get_name(): (serial, serial.get_not_implemented()),
            string.get_name(): (string.get_methods(), string.get_not_implemented()),
            servo.get_name(): (servo.get_methods(), string.get_not_implemented()),
            keyboard.get_name(): (keyboard.get_methods(), string.get_not_implemented()),
            braccio.get_name(): (braccio.get_methods(), braccio.get_not_implemented()),
            stdlib.get_name(): (stdlib.get_methods(), stdlib.get_not_implemented()),
        }
        self.library_not_impl = {
            std.get_name(): std.get_not_implemented(),
            serial.get_name(): serial.get_not_implemented(),
            string.get_name(): string.get_not_implemented(),
        }

    def get_libraries(self):
        """
        Returns a list with the name of the libraries
        """
        list_libs = []
        for key in self.libraries:
            list_libs.append(key)
        return list_libs

    def find(self, library, method):
        """
        Finds a method within a library
        Arguments:
            library: the library in which to search
            method: the method to search
        Returns:
            The method if it exists or None if else
        """
        if library in self.library_methods:
            if method in self.library_methods[library]:
                return self.library_methods[library][method]
        return None

    def not_implemented(self, library, method):
        message = ""
        if library in self.library_not_impl:
            if method in self.library_not_impl[library]:
                message = f"La función {method} de {library} no está implementada, con lo que no cumplirá con su funcionalidad"
        return message

    def add_library(self, library):
        """
        Adds a library to the library_methods dict, so its methods
        can be found.
        Arguments:
            library: "Braccio.h" (from semantic analysis) or
                     "libraries.braccio" (from code generator)
        """
        # Normalise to bare name: "Braccio.h" → "Braccio", "libraries.braccio" → "braccio"
        if library.endswith('.h'):
            lib_name = library[:-2]
        else:
            lib_name = library.split('.')[-1]
        # Case-insensitive match against registered libraries
        matched_key = None
        for key in self.libraries:
            if key.lower() == lib_name.lower():
                matched_key = key
                break
        if matched_key is not None:
            self.library_methods[matched_key] = self.libraries[matched_key][0]
            self.library_not_impl[matched_key] = self.libraries[matched_key][1]
            return self.OK
        return self.ERROR
