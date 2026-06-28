import sys
import os

try:
    with open("abaqus_test_out.txt", "w") as f:
        f.write("sys.argv: " + str(sys.argv) + "\n")
        try:
            f.write("__file__: " + __file__ + "\n")
        except NameError:
            f.write("__file__ is not defined\n")
            
        script_dir = os.path.dirname(os.path.abspath(sys.argv[-1]))
        f.write("Resolved dir: " + script_dir + "\n")
except Exception as e:
    pass
