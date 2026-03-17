import ast
from detectors.high import HighDetectors
from detectors.medium import MediumDetectors

code = open("code.py").read()
tree = ast.parse(code)

for DetectorClass in [HighDetectors, MediumDetectors]:
    detector = DetectorClass()
    detector.visit(tree)
    
    if detector.warnings:
        for w in detector.warnings:
            print(w)
    else:
        print("No issues found!")