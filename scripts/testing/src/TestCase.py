from typing import List
from pathlib import Path
from dataclasses import dataclass

@dataclass
class TestCase:
    input_str: str
    output_str: str
    origin_file: Path
    fst: str
    passed: bool = None
    real_output: List[str] = None

    def check_pass(self, real_output: List[str]) -> bool:
        self.real_output = real_output
        self.passed = self.output_str in self.real_output
        return self.passed

    def __str__(self):
        status = 'Unkn ?'
        if self.passed == True:
            status = 'Pass ✅' 
        elif self.passed == False:
            status = 'Fail ❌'
        comment = ''
        if self.real_output:
            comment = f" (fst output: {'|'.join(self.real_output)})"
        
        return f'{status} [{self.origin_file.name}:{self.fst}] {self.input_str}:{self.output_str}{comment}'